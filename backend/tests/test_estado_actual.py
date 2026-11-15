"""
El estado actual se calcula, no se guarda (sección 5).

Criterio de aceptación del documento (sección 9):
"un reporte de más de 3 horas no puede mostrarse como estado actual".
"""

from apps.puntos import services
from apps.puntos.models import PuntoCarga
from apps.reportes.services import estado_actual


def anotado(punto):
    return services.con_anotaciones(PuntoCarga.objects.filter(pk=punto.pk)).get()


def test_sin_reportes_el_punto_esta_sin_confirmar(crear_punto):
    punto = crear_punto()
    assert estado_actual(punto) == ("sin_confirmar", None)
    assert anotado(punto).estado_actual == "sin_confirmar"


def test_reporte_reciente_es_el_estado_actual(crear_punto, reportar):
    punto = crear_punto()
    reportar(punto, "con_energia", hace_min=12)
    assert anotado(punto).estado_actual == "con_energia"


def test_reporte_de_mas_de_3_horas_no_es_estado_actual(crear_punto, reportar):
    punto = crear_punto()
    reportar(punto, "con_energia", hace_min=181)
    assert anotado(punto).estado_actual == "sin_confirmar"
    assert anotado(punto).confirmado_en is None


def test_manda_el_ultimo_reporte_vigente(crear_punto, reportar):
    punto = crear_punto()
    reportar(punto, "con_energia", hace_min=60)
    reportar(punto, "lleno", hace_min=5)
    assert anotado(punto).estado_actual == "lleno"


def test_la_ventana_es_configurable(settings, crear_punto, reportar):
    settings.VENTANA_VALIDEZ_HORAS = 1
    punto = crear_punto()
    reportar(punto, "con_energia", hace_min=90)
    assert anotado(punto).estado_actual == "sin_confirmar"


def test_reportes_de_usuarios_con_mala_reputacion_no_cuentan(crear_punto, reportar, crear_usuario):
    punto = crear_punto()
    troll = crear_usuario("troll@test.cu", reputacion=-10)
    reportar(punto, "con_energia", hace_min=30)
    reportar(punto, "sin_energia", hace_min=1, por=troll)
    assert anotado(punto).estado_actual == "con_energia"


def test_reporte_invalidado_por_moderacion_no_cuenta(crear_punto, reportar):
    punto = crear_punto()
    r = reportar(punto, "con_energia", hace_min=5)
    r.valido = False
    r.save()
    assert anotado(punto).estado_actual == "sin_confirmar"
