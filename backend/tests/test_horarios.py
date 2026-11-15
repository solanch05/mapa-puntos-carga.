"""Filtro "abierto ahora", incluidos horarios que cruzan la medianoche."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from apps.puntos import services
from apps.puntos.models import Horario, PuntoCarga

HABANA = ZoneInfo("America/Havana")
# 2026-11-16 es lunes (dia_semana=0)
LUNES_10H = datetime(2026, 11, 16, 10, 0, tzinfo=HABANA)
LUNES_23H = datetime(2026, 11, 16, 23, 0, tzinfo=HABANA)
MARTES_01H = datetime(2026, 11, 17, 1, 0, tzinfo=HABANA)
MARTES_03H = datetime(2026, 11, 17, 3, 0, tzinfo=HABANA)


def abierto(punto, ahora):
    return services.anotar_abierto_ahora(PuntoCarga.objects.filter(pk=punto.pk), ahora).get().abierto_ahora


def test_horario_normal(crear_punto):
    punto = crear_punto()
    Horario.objects.create(punto=punto, dia_semana=0, hora_inicio=time(9), hora_fin=time(17))
    assert abierto(punto, LUNES_10H)
    assert not abierto(punto, LUNES_23H)


def test_horario_que_cruza_medianoche(crear_punto):
    punto = crear_punto()
    Horario.objects.create(punto=punto, dia_semana=0, hora_inicio=time(22), hora_fin=time(2))
    assert abierto(punto, LUNES_23H)
    assert abierto(punto, MARTES_01H)  # sigue abierto: pertenece al lunes
    assert not abierto(punto, MARTES_03H)
    assert not abierto(punto, LUNES_10H)


def test_inicio_igual_a_fin_es_todo_el_dia(crear_punto):
    punto = crear_punto()
    Horario.objects.create(punto=punto, dia_semana=0, hora_inicio=time(0), hora_fin=time(0))
    assert abierto(punto, LUNES_10H)
    assert abierto(punto, LUNES_23H)


def test_sin_horario_no_cuenta_como_abierto(crear_punto):
    assert not abierto(crear_punto(), LUNES_10H)
