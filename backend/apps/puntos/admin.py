"""
Flujo 4 · Moderar. El panel de Django es la herramienta de moderación.

El estado de publicación es de solo lectura en el formulario: se cambia
SOLO con las acciones (aprobar, ocultar, pedir correcciones), que ajustan la
reputación y dejan registro en el historial.
"""

from django.contrib import admin, messages
from django.contrib.gis.admin import GISModelAdmin

from apps.moderacion import services as moderacion
from apps.moderacion.admin_base import SoloModeradoresMixin
from apps.reportes.services import estado_actual

from .models import EstadoPublicacion, Horario, PuntoCarga


class HorarioInline(admin.TabularInline):
    model = Horario
    extra = 0


@admin.register(PuntoCarga)
class PuntoCargaAdmin(SoloModeradoresMixin, GISModelAdmin):
    list_display = [
        "nombre",
        "tipo",
        "estado_publicacion",
        "estado_ahora",
        "creado_por",
        "reputacion_autor",
        "tiene_avisos",
        "creado_en",
    ]
    list_filter = ["estado_publicacion", "tipo", "acceso", "respaldo"]
    search_fields = ["nombre", "descripcion", "creado_por__email"]
    readonly_fields = ["estado_publicacion", "creado_por", "creado_en", "actualizado_en", "estado_ahora"]
    fields = [
        "nombre",
        "tipo",
        "descripcion",
        "ubicacion",
        "ubicacion_aproximada",
        "numero_tomas",
        "tipo_conector",
        "respaldo",
        "acceso",
        "contacto",
        "estado_publicacion",
        "nota_moderacion",
        "estado_ahora",
        "creado_por",
        "creado_en",
        "actualizado_en",
    ]
    inlines = [HorarioInline]
    actions = ["aprobar", "ocultar", "pedir_correcciones"]
    gis_widget_kwargs = {"attrs": {"default_lat": 22.4067, "default_lon": -79.9646, "default_zoom": 15}}

    def get_queryset(self, request):
        # Primero los pendientes: así la lista ES la cola de moderación.
        return (
            super()
            .get_queryset(request)
            .select_related("creado_por")
            .order_by("estado_publicacion", "-creado_en")
        )

    @admin.display(description="Estado ahora")
    def estado_ahora(self, obj):
        estado, cuando = estado_actual(obj)
        return estado if not cuando else f"{estado} ({cuando:%H:%M})"

    @admin.display(description="Reputación autor")
    def reputacion_autor(self, obj):
        return obj.creado_por.reputacion

    @admin.display(description="Avisos", boolean=True)
    def tiene_avisos(self, obj):
        return bool(obj.nota_moderacion)

    @admin.action(description="Aprobar los puntos seleccionados")
    def aprobar(self, request, queryset):
        for punto in queryset:
            moderacion.aprobar_punto(punto, request.user)
        self.message_user(request, f"{queryset.count()} punto(s) aprobados.", messages.SUCCESS)

    @admin.action(description="Ocultar los puntos seleccionados")
    def ocultar(self, request, queryset):
        for punto in queryset:
            moderacion.ocultar_punto(punto, request.user)
        self.message_user(request, f"{queryset.count()} punto(s) ocultados.", messages.WARNING)

    @admin.action(description="Pedir correcciones (usa la nota de moderación de cada punto)")
    def pedir_correcciones(self, request, queryset):
        for punto in queryset:
            nota = punto.nota_moderacion or "Revisa los datos del punto y vuelve a enviarlo."
            moderacion.pedir_correcciones(punto, request.user, nota)
        self.message_user(request, "Se pidieron correcciones. El autor verá la nota en «Mis puntos».")

    def save_model(self, request, obj, form, change):
        # Editar desde el panel no cambia el estado: eso va por las acciones.
        if not change:
            obj.creado_por = request.user
            obj.estado_publicacion = EstadoPublicacion.PENDIENTE
        super().save_model(request, obj, form, change)
