"""Fixtures compartidas: clientes de la API, usuarios y una fábrica de puntos."""

from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.puntos.models import EstadoPublicacion, PuntoCarga
from apps.reportes.models import ReporteEstado
from apps.usuarios.models import Rol, Usuario

CENTRO = (22.4067, -79.9646)  # parque Vidal, Santa Clara (lat, lng)


@pytest.fixture(autouse=True)
def entorno_limpio(settings, tmp_path):
    cache.clear()  # los límites de peticiones se guardan en caché
    settings.MEDIA_ROOT = tmp_path
    settings.IA_HABILITADA = False
    settings.IA_API_KEY = ""


@pytest.fixture
def crear_usuario(db):
    def _crear(email="user@test.cu", reputacion=0, rol=Rol.USUARIO):
        return Usuario.objects.create_user(
            email=email, password="ClaveSegura123", nombre=email.split("@")[0], rol=rol, reputacion=reputacion
        )

    return _crear


@pytest.fixture
def usuario(crear_usuario):
    return crear_usuario("usuario@test.cu")


@pytest.fixture
def moderador(crear_usuario):
    return crear_usuario("mod@test.cu", rol=Rol.MODERADOR)


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def api_de():
    """api_de(usuario) -> cliente autenticado como ese usuario."""

    def _cliente(u):
        cliente = APIClient()
        cliente.force_authenticate(u)
        return cliente

    return _cliente


@pytest.fixture
def crear_punto(usuario):
    def _crear(lat=CENTRO[0], lng=CENTRO[1], estado=EstadoPublicacion.ACTIVO, **extra):
        datos = {"nombre": "Cafetería de prueba", "tipo": "negocio", "numero_tomas": 2, "creado_por": usuario}
        datos.update(extra)
        return PuntoCarga.objects.create(
            ubicacion=Point(lng, lat, srid=4326), estado_publicacion=estado, **datos
        )

    return _crear


@pytest.fixture
def reportar(usuario):
    """reportar(punto, estado, hace_min=0, por=usuario) -> reporte con fecha en el pasado."""

    def _reportar(punto, estado="con_energia", hace_min=0, por=None):
        r = ReporteEstado.objects.create(punto=punto, usuario=por or usuario, estado=estado)
        ReporteEstado.objects.filter(pk=r.pk).update(creado_en=timezone.now() - timedelta(minutes=hace_min))
        r.refresh_from_db()
        return r

    return _reportar
