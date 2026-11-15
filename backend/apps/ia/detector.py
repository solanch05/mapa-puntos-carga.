"""
Detección de duplicados y de mensajes sospechosos ANTES de la moderación
(sección 4, servicio de IA, uso 2).

Es una heurística local, sin servicios externos: barata, explicable y
suficiente para el piloto. Si en el futuro hace falta, se puede sustituir por
un modelo sin cambiar quién la llama. Igual que el resto de la IA: solo
avisa; quien decide es un moderador.
"""

import re
import unicodedata
from difflib import SequenceMatcher

from django.contrib.gis.measure import D

DISTANCIA_DUPLICADO_M = 60
SIMILITUD_NOMBRE_MINIMA = 0.6

PATRON_ENLACE = re.compile(r"(https?://|www\.|\.com\b|t\.me/|wa\.me/)", re.IGNORECASE)
PALABRAS_SOSPECHOSAS = {
    "gana dinero",
    "inversion",
    "inversión",
    "cripto",
    "bitcoin",
    "usdt",
    "casino",
    "apuesta",
    "prestamo",
    "préstamo",
    "oferta exclusiva",
    "haz clic",
    "click aqui",
    "click aquí",
    "promo",
    "descuento",
}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", texto)).strip()


def similitud(a: str, b: str) -> float:
    return SequenceMatcher(None, normalizar(a), normalizar(b)).ratio()


def buscar_duplicados(nombre: str, ubicacion, excluir_id=None) -> list:
    """Puntos a menos de 60 m con un nombre parecido."""
    from apps.puntos.models import PuntoCarga

    cercanos = PuntoCarga.objects.filter(ubicacion__dwithin=(ubicacion, D(m=DISTANCIA_DUPLICADO_M))).exclude(
        estado_publicacion="oculto"
    )
    if excluir_id:
        cercanos = cercanos.exclude(pk=excluir_id)
    return [p for p in cercanos if similitud(p.nombre, nombre) >= SIMILITUD_NOMBRE_MINIMA]


def motivos_sospecha(*textos: str) -> list[str]:
    """Devuelve las razones por las que un texto parece spam (lista vacía si no)."""
    motivos = []
    unido = " ".join(t for t in textos if t)
    if PATRON_ENLACE.search(unido):
        motivos.append("contiene enlaces")
    plano = normalizar(unido)
    encontradas = sorted(p for p in PALABRAS_SOSPECHOSAS if normalizar(p) in plano)
    if encontradas:
        motivos.append("palabras típicas de spam: " + ", ".join(encontradas))
    letras = [c for c in unido if c.isalpha()]
    if len(letras) > 15 and sum(c.isupper() for c in letras) / len(letras) > 0.7:
        motivos.append("texto casi todo en mayúsculas")
    return motivos


def revisar_punto(punto) -> list[str]:
    """Avisos para el moderador sobre un punto recién creado o editado."""
    avisos = []
    for dup in buscar_duplicados(punto.nombre, punto.ubicacion, excluir_id=punto.pk):
        avisos.append(f"Posible duplicado de #{dup.pk} «{dup.nombre}»")
    motivos = motivos_sospecha(punto.nombre, punto.descripcion)
    if motivos:
        avisos.append("Texto sospechoso: " + "; ".join(motivos))
    return avisos
