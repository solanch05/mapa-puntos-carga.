"""
Acciones de moderación (flujo 4). Las usa el panel de administración.

Cada acción: cambia el estado, ajusta la reputación de quien publicó y deja
registro en el historial del panel (LogEntry de Django), para saber quién
hizo qué y cuándo.
"""

from django.contrib.admin.models import CHANGE, LogEntry
from django.db import transaction

from apps.puntos.models import EstadoPublicacion
from apps.usuarios import reputacion

from .models import EstadoDenuncia


def registrar(moderador, objeto, mensaje: str) -> None:
    LogEntry.objects.log_actions(
        user_id=moderador.pk,
        queryset=[objeto],
        action_flag=CHANGE,
        change_message=mensaje,
        single_object=True,
    )


@transaction.atomic
def aprobar_punto(punto, moderador) -> None:
    ya_estaba_activo = punto.estado_publicacion == EstadoPublicacion.ACTIVO
    punto.estado_publicacion = EstadoPublicacion.ACTIVO
    punto.nota_moderacion = ""
    punto.save(update_fields=["estado_publicacion", "nota_moderacion"])
    if not ya_estaba_activo:
        punto.creado_por.ajustar_reputacion(reputacion.PUNTOS_PUNTO_APROBADO)
    registrar(moderador, punto, "Punto aprobado")


@transaction.atomic
def ocultar_punto(punto, moderador, motivo: str = "") -> None:
    ya_estaba_oculto = punto.estado_publicacion == EstadoPublicacion.OCULTO
    punto.estado_publicacion = EstadoPublicacion.OCULTO
    if motivo:
        punto.nota_moderacion = motivo
    punto.save(update_fields=["estado_publicacion", "nota_moderacion"])
    if not ya_estaba_oculto:
        punto.creado_por.ajustar_reputacion(reputacion.PUNTOS_PUNTO_OCULTADO)
    registrar(moderador, punto, f"Punto ocultado. {motivo}".strip())


@transaction.atomic
def pedir_correcciones(punto, moderador, nota: str) -> None:
    punto.estado_publicacion = EstadoPublicacion.PENDIENTE
    punto.nota_moderacion = nota
    punto.save(update_fields=["estado_publicacion", "nota_moderacion"])
    registrar(moderador, punto, f"Correcciones pedidas: {nota}")


@transaction.atomic
def resolver_denuncia(denuncia, moderador, aceptada: bool) -> None:
    """Aceptada: se oculta el punto o se invalida el reporte denunciado,
    y el autor pierde reputación. Descartada: solo se cierra."""
    if denuncia.estado == EstadoDenuncia.RESUELTA:
        return
    if aceptada:
        if denuncia.reporte_id:
            reporte = denuncia.reporte
            reporte.valido = False
            reporte.save(update_fields=["valido"])
            reporte.usuario.ajustar_reputacion(reputacion.PUNTOS_DENUNCIA_ACEPTADA)
        else:
            # ocultar_punto ya resta reputación a quien publicó el punto.
            ocultar_punto(denuncia.punto, moderador, f"Denuncia aceptada: {denuncia.get_motivo_display()}")
        denuncia.usuario.ajustar_reputacion(reputacion.PUNTOS_DENUNCIA_UTIL)
    denuncia.estado = EstadoDenuncia.RESUELTA
    denuncia.resuelta_por = moderador
    denuncia.save(update_fields=["estado", "resuelta_por"])
    registrar(moderador, denuncia, "Denuncia aceptada" if aceptada else "Denuncia descartada")
