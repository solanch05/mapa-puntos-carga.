"""
Lógica de consulta de puntos: cercanía, filtros y "abierto ahora".

Las vistas solo llaman a estas funciones; así la lógica se prueba sin HTTP.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Exists, F, OuterRef, Q, QuerySet
from django.utils import timezone

from apps.reportes.services import anotar_estado_actual

from .models import EstadoPublicacion, Horario, PuntoCarga


def condicion_abierto(ahora=None) -> Q:
    """Q sobre Horario que es cierta si el horario cubre el momento `ahora`.

    Contempla horarios que cruzan la medianoche (p. ej. 22:00-02:00): la parte
    de después de las 00:00 pertenece al día anterior.
    """
    local = timezone.localtime(ahora or timezone.now())
    hoy, hora = local.weekday(), local.time()
    ayer = (local - timedelta(days=1)).weekday()

    todo_el_dia = Q(dia_semana=hoy, hora_inicio=F("hora_fin"))
    normal = Q(dia_semana=hoy, hora_inicio__lt=F("hora_fin"), hora_inicio__lte=hora, hora_fin__gt=hora)
    cruza_hoy = Q(dia_semana=hoy, hora_inicio__gt=F("hora_fin"), hora_inicio__lte=hora)
    cruza_desde_ayer = Q(dia_semana=ayer, hora_inicio__gt=F("hora_fin"), hora_fin__gt=hora)
    return todo_el_dia | normal | cruza_hoy | cruza_desde_ayer


def anotar_abierto_ahora(puntos: QuerySet, ahora=None) -> QuerySet:
    horarios = Horario.objects.filter(condicion_abierto(ahora), punto=OuterRef("pk"))
    return puntos.annotate(abierto_ahora=Exists(horarios))


def base_publica() -> QuerySet:
    """Puntos visibles para cualquiera: solo los activos."""
    return PuntoCarga.objects.filter(estado_publicacion=EstadoPublicacion.ACTIVO)


def con_anotaciones(puntos: QuerySet, ahora=None) -> QuerySet:
    puntos = anotar_estado_actual(puntos, ahora)
    return anotar_abierto_ahora(puntos, ahora)


def filtrar_puntos(puntos: QuerySet, params) -> QuerySet:
    """Aplica los filtros que llegan en la URL.

    - lat, lng, radio_km: puntos a menos de X km (usa el índice espacial).
    - tipo: uno o varios, separados por comas.
    - min_tomas: número mínimo de tomas.
    - acceso: uno o varios, separados por comas.
    - con_energia=1: solo estado actual "con energía".
    - abierto_ahora=1: solo los que según su horario están abiertos.
    """
    lat, lng = params.get("lat"), params.get("lng")
    if lat is not None and lng is not None:
        try:
            centro = Point(float(lng), float(lat), srid=4326)
            radio = min(float(params.get("radio_km", 2)), settings.RADIO_MAXIMO_KM)
        except (TypeError, ValueError):
            raise ValueError("lat, lng y radio_km deben ser números")
        # Filtramos sobre la ubicación PÚBLICA: la exacta de una vivienda no
        # debe poder deducirse moviendo el centro de búsqueda.
        puntos = puntos.filter(ubicacion_publica__dwithin=(centro, D(km=radio)))

    if tipos := params.get("tipo"):
        puntos = puntos.filter(tipo__in=tipos.split(","))
    if accesos := params.get("acceso"):
        puntos = puntos.filter(acceso__in=accesos.split(","))
    if min_tomas := params.get("min_tomas"):
        try:
            puntos = puntos.filter(numero_tomas__gte=int(min_tomas))
        except ValueError:
            raise ValueError("min_tomas debe ser un número entero")
    if params.get("con_energia") in {"1", "true"}:
        puntos = puntos.filter(estado_actual="con_energia")
    if params.get("abierto_ahora") in {"1", "true"}:
        puntos = puntos.filter(abierto_ahora=True)
    return puntos
