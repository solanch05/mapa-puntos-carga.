"""
Reglas de reputación en un solo sitio.

La reputación sirve para tres cosas (secciones 7 y 8 del documento):
- Premiar a quien mantiene el mapa vivo (reportar sube la reputación).
- Dejar que los usuarios de confianza publiquen sin revisión.
- Que los reportes de usuarios con mala reputación no cuenten.
"""

from django.conf import settings

PUNTOS_REPORTE = 1  # confirmar el estado de un punto
PUNTOS_PUNTO_APROBADO = 5  # un moderador aprueba un punto tuyo
PUNTOS_PUNTO_OCULTADO = -5  # un moderador oculta un punto tuyo
PUNTOS_DENUNCIA_ACEPTADA = -3  # se acepta una denuncia contra tu punto o reporte
PUNTOS_DENUNCIA_UTIL = 1  # tu denuncia resultó acertada


def es_de_confianza(usuario) -> bool:
    """Un usuario de confianza publica puntos directamente, sin revisión."""
    return usuario.es_moderador or usuario.reputacion >= settings.REPUTACION_CONFIANZA
