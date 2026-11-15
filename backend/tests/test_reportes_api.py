"""Flujo 3: confirmar el estado en un toque, reputación y fotos seguras."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.puntos.models import EstadoPublicacion
from apps.reportes.models import ReporteEstado

pytestmark = pytest.mark.django_db


def url(punto):
    return f"/api/puntos/{punto.pk}/reportes/"


def test_anonimo_no_puede_reportar(api, crear_punto):
    assert api.post(url(crear_punto()), {"estado": "con_energia"}).status_code == 401


def test_reportar_en_un_toque_actualiza_el_estado(api_de, crear_punto, usuario):
    punto = crear_punto()
    respuesta = api_de(usuario).post(url(punto), {"estado": "con_energia"})
    assert respuesta.status_code == 201
    assert respuesta.json()["estado_actual"] == "con_energia"
    # Lo ve todo el mundo al instante:
    assert api_de(usuario).get(f"/api/puntos/{punto.pk}/").json()["estado_actual"] == "con_energia"


def test_reportar_sube_la_reputacion_una_vez_cada_30_min(api_de, crear_punto, usuario):
    punto = crear_punto()
    cliente = api_de(usuario)
    cliente.post(url(punto), {"estado": "con_energia"})
    cliente.post(url(punto), {"estado": "lleno"})
    usuario.refresh_from_db()
    assert usuario.reputacion == 1
    assert ReporteEstado.objects.count() == 2


def test_no_se_reporta_un_punto_pendiente(api_de, crear_punto, usuario):
    punto = crear_punto(estado=EstadoPublicacion.PENDIENTE)
    assert api_de(usuario).post(url(punto), {"estado": "con_energia"}).status_code == 404


def test_estado_invalido(api_de, crear_punto, usuario):
    assert api_de(usuario).post(url(crear_punto()), {"estado": "quizas"}).status_code == 400


def test_limite_de_reportes_por_usuario(settings, api_de, crear_punto, usuario):
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {**settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "reportes": "2/hour"},
    }
    from rest_framework.throttling import ScopedRateThrottle

    ScopedRateThrottle.THROTTLE_RATES = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    try:
        punto, cliente = crear_punto(), api_de(usuario)
        codigos = [cliente.post(url(punto), {"estado": "con_energia"}).status_code for _ in range(3)]
        assert codigos == [201, 201, 429]
    finally:
        from rest_framework.settings import api_settings

        ScopedRateThrottle.THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES


# --- Fotos -------------------------------------------------------------------------------
def jpeg_con_gps():
    """JPEG con metadatos EXIF de GPS, como los de una foto de teléfono."""
    imagen = Image.new("RGB", (64, 48), "orange")
    exif = Image.Exif()
    exif[0x010F] = "MarcaTelefono"  # Make
    gps = exif.get_ifd(0x8825)
    gps[1], gps[2] = "N", (22.0, 24.0, 24.12)
    gps[3], gps[4] = "W", (79.0, 57.0, 52.56)
    buffer = io.BytesIO()
    imagen.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def test_la_foto_se_recodifica_sin_metadatos_exif(api_de, crear_punto, usuario):
    original = jpeg_con_gps()
    assert Image.open(io.BytesIO(original)).getexif().get_ifd(0x8825)  # el original SÍ tiene GPS

    foto = SimpleUploadedFile("foto.jpg", original, content_type="image/jpeg")
    respuesta = api_de(usuario).post(
        url(crear_punto()), {"estado": "lleno", "foto": foto}, format="multipart"
    )
    assert respuesta.status_code == 201, respuesta.json()

    guardada = Image.open(ReporteEstado.objects.get().foto.path)
    assert guardada.format == "JPEG"
    assert len(guardada.getexif()) == 0
    assert not guardada.getexif().get_ifd(0x8825)


def test_un_archivo_que_no_es_imagen_se_rechaza(api_de, crear_punto, usuario):
    falso = SimpleUploadedFile("foto.jpg", b"<?php echo 'hola'; ?>", content_type="image/jpeg")
    respuesta = api_de(usuario).post(
        url(crear_punto()), {"estado": "lleno", "foto": falso}, format="multipart"
    )
    assert respuesta.status_code == 400
    assert "foto" in respuesta.json()
