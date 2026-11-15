"""Alta asistida con IA: propone un borrador; nunca guarda nada por sí sola."""

import httpx
import pytest

from apps.ia import extractor
from apps.ia.detector import motivos_sospecha
from apps.puntos.models import PuntoCarga

pytestmark = pytest.mark.django_db
URL = "/api/ia/borrador/"
EJEMPLO = "hay corriente en casa de Pedro, de 6 a 10 de la noche, dos enchufes"


def test_extractor_por_reglas_con_el_ejemplo_del_documento():
    borrador, avisos = extractor.extraer_por_reglas(EJEMPLO)
    assert borrador["nombre"] == "Casa de Pedro"
    assert borrador["tipo"] == "vivienda"
    assert borrador["numero_tomas"] == 2
    assert borrador["acceso"] == "previa_solicitud"
    assert len(borrador["horarios"]) == 7
    assert borrador["horarios"][0] == {"dia_semana": 0, "hora_inicio": "18:00", "hora_fin": "22:00"}
    assert any("aproximada" in a for a in avisos)


@pytest.mark.parametrize(
    "texto,esperado",
    [
        (
            "cafetería La Rosa de lunes a viernes de 9:00 a 17:30, 3 tomas, planta",
            ("negocio", [0, 1, 2, 3, 4], "09:00", "17:30", "planta"),
        ),
        (
            "en el parque hay paneles solares con usb de 8am a 6pm todos los días",
            ("espacio_publico", list(range(7)), "08:00", "18:00", "solar"),
        ),
    ],
)
def test_extractor_otros_formatos(texto, esperado):
    tipo, dias, inicio, fin, respaldo = esperado
    borrador, _ = extractor.extraer_por_reglas(texto)
    assert borrador["tipo"] == tipo
    assert [h["dia_semana"] for h in borrador["horarios"]] == dias
    assert borrador["horarios"][0]["hora_inicio"] == inicio
    assert borrador["horarios"][0]["hora_fin"] == fin
    assert borrador["respaldo"] == respaldo


def test_no_se_envian_datos_personales():
    texto = "llamar a Pedro al +53 5 123 4567 o escribir a pedro@correo.cu"
    limpio = extractor.anonimizar(texto)
    assert "4567" not in limpio and "pedro@correo.cu" not in limpio


def test_detector_de_spam():
    assert motivos_sospecha("Gana dinero con USDT en t.me/estafa")
    assert motivos_sospecha("Casa de Pedro, portal azul") == []


def test_endpoint_desactivado_por_defecto(api_de, usuario):
    assert api_de(usuario).post(URL, {"texto": EJEMPLO}).status_code == 503


def test_endpoint_devuelve_borrador_y_no_guarda_nada(settings, api_de, usuario):
    settings.IA_HABILITADA = True
    respuesta = api_de(usuario).post(URL, {"texto": EJEMPLO})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["origen"] == "reglas"
    assert cuerpo["borrador"]["nombre"] == "Casa de Pedro"
    assert not PuntoCarga.objects.exists()  # la IA propone; la persona confirma


def test_salida_del_llm_se_valida_con_el_serializador(settings, api_de, usuario, monkeypatch):
    settings.IA_HABILITADA, settings.IA_API_KEY = True, "clave-de-prueba"
    monkeypatch.setattr(
        extractor,
        "extraer_con_llm",
        lambda texto: {"nombre": "Casa de Pedro", "tipo": "mansion", "numero_tomas": 2},
    )
    cuerpo = api_de(usuario).post(URL, {"texto": EJEMPLO}).json()
    assert cuerpo["origen"] == "llm"
    assert "tipo" not in cuerpo["borrador"]  # valor inventado: descartado
    assert any("tipo" in a for a in cuerpo["avisos"])


def test_si_el_servicio_de_ia_falla_se_usan_reglas(settings, api_de, usuario, monkeypatch):
    settings.IA_HABILITADA, settings.IA_API_KEY = True, "clave-de-prueba"

    def falla(texto):
        raise httpx.ConnectError("sin conexión")

    monkeypatch.setattr(extractor, "extraer_con_llm", falla)
    cuerpo = api_de(usuario).post(URL, {"texto": EJEMPLO}).json()
    assert cuerpo["origen"] == "reglas"
    assert cuerpo["borrador"]["numero_tomas"] == 2
