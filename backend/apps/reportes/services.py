"""
Cálculo del ESTADO ACTUAL de un punto.

Decisión de diseño clave (sección 5): el estado actual NO se guarda, se
calcula. Es el último reporte válido dentro de la ventana de validez
(3 horas por defecto). Si no hay ninguno, el punto está "sin confirmar",
nunca "con energía". Así no mostramos datos viejos como si fueran ciertos.

Los reportes de usuarios con reputación por debajo del mínimo no cuentan
(sección 8: "los reportes de usuarios con buena reputación pesan más").
"""

from datetime import timedelta

from django.conf import settings
from django.db.models import CharField, OuterRef, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import SIN_CONFIRMAR, ReporteEstado


def ventana_validez() -> timedelta:
    return timedelta(hours=settings.VENTANA_VALIDEZ_HORAS)


def reportes_vigentes(ahora=None) -> QuerySet:
    """Reportes que cuentan para el estado en este momento."""
    ahora = ahora or timezone.now()
    return ReporteEstado.objects.filter(
        valido=True,
        creado_en__gte=ahora - ventana_validez(),
        usuario__reputacion__gte=settings.REPUTACION_MINIMA_REPORTE,
    )


def anotar_estado_actual(puntos: QuerySet, ahora=None) -> QuerySet:
    """Añade `estado_actual` y `confirmado_en` a cada punto en UNA sola consulta.

    Usa una subconsulta correlacionada: para cada punto, el último reporte
    vigente. Evita el problema N+1 (una consulta por punto).
    """
    ultimo = reportes_vigentes(ahora).filter(punto=OuterRef("pk")).order_by("-creado_en")
    return puntos.annotate(
        estado_actual=Coalesce(
            Subquery(ultimo.values("estado")[:1]),
            Value(SIN_CONFIRMAR),
            output_field=CharField(),
        ),
        confirmado_en=Subquery(ultimo.values("creado_en")[:1]),
    )


def estado_actual(punto, ahora=None) -> tuple[str, object]:
    """Versión para un solo punto (útil en tests y en el admin)."""
    reporte = reportes_vigentes(ahora).filter(punto=punto).order_by("-creado_en").first()
    if reporte is None:
        return SIN_CONFIRMAR, None
    return reporte.estado, reporte.creado_en
