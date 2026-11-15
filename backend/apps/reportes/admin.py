from django.contrib import admin

from apps.moderacion.admin_base import SoloModeradoresMixin

from .models import ReporteEstado


@admin.register(ReporteEstado)
class ReporteEstadoAdmin(SoloModeradoresMixin, admin.ModelAdmin):
    list_display = ["punto", "estado", "usuario", "valido", "creado_en"]
    list_filter = ["estado", "valido"]
    search_fields = ["punto__nombre", "usuario__email", "comentario"]
    readonly_fields = ["punto", "usuario", "estado", "comentario", "foto", "creado_en"]
