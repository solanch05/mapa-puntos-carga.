"""
Alta asistida con IA (sección 4, uso 1; demo "Extra").

Convierte un texto libre como
    "hay corriente en casa de Pedro, de 6 a 10 de la noche, dos enchufes"
en un BORRADOR de punto. Reglas del documento:
- La IA propone; una persona confirma. Este módulo nunca guarda nada.
- La clave de la API vive en el backend; nunca llega al navegador.
- No se envían datos personales al servicio externo: antes se ocultan
  teléfonos y correos.
- La salida se valida con el MISMO serializador que el alta normal.
- El producto funciona sin IA: si no hay clave o el servicio falla, se usa
  un extractor por reglas que funciona sin conexión.
"""

import json
import logging
import re
import unicodedata

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

# --- Privacidad ---------------------------------------------------------------
PATRON_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PATRON_TELEFONO = re.compile(r"\+?\d[\d\s-]{6,}\d")


def anonimizar(texto: str) -> str:
    texto = PATRON_EMAIL.sub("[dato oculto]", texto)
    return PATRON_TELEFONO.sub("[dato oculto]", texto)


# --- Extractor por reglas (sin conexión) ---------------------------------------
NUMEROS = {
    "un": 1,
    "una": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
}
PATRON_TOMAS = re.compile(
    r"\b(\d{1,2}|"
    + "|".join(NUMEROS)
    + r")\s+(enchufes?|tomas?|tomacorrientes?|conectores?|puertos? usb|usb)\b"
)
PATRON_HORAS = re.compile(
    r"\b(?:de|desde)\s+(?:las\s+)?(\d{1,2})(?::(\d{2}))?(?:\s*(am|pm))?\s+"
    r"(?:a|hasta)\s+(?:las\s+)?(\d{1,2})(?::(\d{2}))?(?:\s*(am|pm))?"
    r"(?:\s+de\s+la\s+(manana|tarde|noche|madrugada))?"
)
PATRON_NOMBRE = re.compile(r"\ben\s+((?:la|el)\s+)?([^,.;]{3,60})")

TIPOS = [
    ("vivienda", ("casa", "apartamento", "vivienda", "hogar")),
    (
        "negocio",
        ("cafeteria", "tienda", "paladar", "negocio", "restaurante", "bar ", "mipyme", "taller", "barberia"),
    ),
    (
        "institucion",
        (
            "escuela",
            "universidad",
            "policlinico",
            "hospital",
            "biblioteca",
            "iglesia",
            "centro comunitario",
            "casa de cultura",
        ),
    ),
    ("espacio_publico", ("parque", "plaza", "terminal", "estacion")),
]
RESPALDOS = [
    ("planta", ("planta",)),
    ("solar", ("solar", "panel")),
    ("bateria", ("bateria", "ecoflow", "inversor")),
]
ACCESOS = [
    ("pago", ("cobra", "pagar", "de pago", "pesos", "cup", "precio")),
    ("con_consumo", ("consumo", "consumir", "comprando")),
    ("previa_solicitud", ("avisar", "preguntar", "llamar antes", "previa", "pedir permiso")),
    ("libre", ("gratis", "libre", "sin costo", "gratuito")),
]
DIAS_TODOS = list(range(7))


def _a_24h(hora: int, sufijo: str | None, periodo: str | None) -> int:
    if sufijo == "pm" or periodo in {"tarde", "noche"}:
        return hora if hora == 12 else hora + 12
    if (sufijo == "am" or periodo in {"manana", "madrugada"}) and hora == 12:
        return 0
    return hora


def _dias(texto: str) -> tuple[list[int], str | None]:
    if "lunes a viernes" in texto or "entre semana" in texto:
        return list(range(5)), None
    if "fin de semana" in texto or "fines de semana" in texto:
        return [5, 6], None
    nombres = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    sueltos = [i for i, d in enumerate(nombres) if re.search(rf"\b{d}s?\b", texto)]
    if sueltos:
        return sueltos, None
    if "todos los dias" in texto or "diario" in texto:
        return DIAS_TODOS, None
    return DIAS_TODOS, "No se indicaron días: se asumen todos. Revísalo."


def _primero(texto: str, tabla, defecto):
    for valor, claves in tabla:
        if any(c in texto for c in claves):
            return valor
    return defecto


def _plano(texto: str) -> str:
    """Minúsculas y sin tildes, conservando ':' para las horas."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    # "6pm", "6 p.m." -> "6 pm"
    texto = re.sub(r"(\d)\s*([ap])\.?\s*m\b\.?", r"\1 \2m", texto)
    return re.sub(r"\s+", " ", texto) + " "


def extraer_por_reglas(texto_original: str) -> tuple[dict, list[str]]:
    texto = _plano(texto_original)
    texto_horas = texto
    avisos: list[str] = []
    borrador: dict = {}

    if m := PATRON_NOMBRE.search(texto_original):
        nombre = m.group(2).strip()
        borrador["nombre"] = nombre[0].upper() + nombre[1:]
    else:
        avisos.append("No encontré el nombre del lugar.")

    borrador["tipo"] = _primero(texto, TIPOS, "negocio")
    borrador["respaldo"] = _primero(texto, RESPALDOS, "ninguno")
    acceso_defecto = "previa_solicitud" if borrador["tipo"] == "vivienda" else "libre"
    borrador["acceso"] = _primero(texto, ACCESOS, acceso_defecto)

    if m := PATRON_TOMAS.search(texto):
        cantidad = m.group(1)
        borrador["numero_tomas"] = int(cantidad) if cantidad.isdigit() else NUMEROS[cantidad]
    tiene_usb = "usb" in texto
    tiene_enchufe = any(p in texto for p in ("enchufe", "toma", "tomacorriente"))
    borrador["tipo_conector"] = (
        "ambos" if tiene_usb and tiene_enchufe else ("usb" if tiene_usb else "enchufe")
    )

    if m := PATRON_HORAS.search(texto_horas):
        h1, m1, s1, h2, m2, s2, periodo = m.groups()
        inicio = _a_24h(int(h1), s1 or s2, periodo)
        fin = _a_24h(int(h2), s2, periodo)
        if inicio < 24 and fin < 24:
            dias, aviso = _dias(texto)
            if aviso:
                avisos.append(aviso)
            borrador["horarios"] = [
                {
                    "dia_semana": d,
                    "hora_inicio": f"{inicio:02d}:{m1 or '00'}",
                    "hora_fin": f"{fin:02d}:{m2 or '00'}",
                }
                for d in dias
            ]
    else:
        avisos.append("No encontré el horario.")

    if borrador["tipo"] == "vivienda":
        avisos.append("Es una vivienda: se mostrará con ubicación aproximada.")
    avisos.append("Coloca el pin en el mapa: la ubicación no se deduce del texto.")
    return borrador, avisos


# --- Extractor con modelo de lenguaje -------------------------------------------
INSTRUCCIONES_LLM = """Extrae datos de un punto de carga eléctrica a partir del mensaje del usuario.
Responde SOLO con un objeto JSON con estas claves (omite las que no aparezcan):
nombre (texto), tipo (vivienda|negocio|institucion|espacio_publico),
descripcion (texto breve), numero_tomas (entero),
tipo_conector (enchufe|usb|ambos), respaldo (ninguno|bateria|planta|solar),
acceso (libre|con_consumo|previa_solicitud|pago),
horarios (lista de {dia_semana: 0=lunes..6=domingo, hora_inicio: "HH:MM", hora_fin: "HH:MM"}).
Si no se dicen los días, usa los 7. No inventes datos que no estén en el mensaje."""


def _json_de_respuesta(texto: str) -> dict:
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin == -1:
        raise ValueError("La respuesta no contiene JSON")
    return json.loads(texto[inicio : fin + 1])


def extraer_con_llm(texto: str) -> dict:
    respuesta = httpx.post(
        settings.IA_API_URL,
        timeout=settings.IA_TIMEOUT_S,
        headers={
            "x-api-key": settings.IA_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.IA_MODELO,
            "max_tokens": 600,
            "system": INSTRUCCIONES_LLM,
            "messages": [{"role": "user", "content": anonimizar(texto)}],
        },
    )
    respuesta.raise_for_status()
    bloques = respuesta.json().get("content", [])
    return _json_de_respuesta("".join(b.get("text", "") for b in bloques))


def generar_borrador(texto: str) -> tuple[dict, list[str], str]:
    """Devuelve (borrador sin validar, avisos, origen: 'llm' o 'reglas')."""
    if settings.IA_API_KEY:
        try:
            borrador = extraer_con_llm(texto)
            avisos = [
                "Revisa todos los campos antes de enviar.",
                "Coloca el pin en el mapa: la ubicación no se deduce del texto.",
            ]
            return borrador, avisos, "llm"
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning("Fallo del servicio de IA, uso el extractor por reglas: %s", exc)
    borrador, avisos = extraer_por_reglas(texto)
    return borrador, avisos, "reglas"
