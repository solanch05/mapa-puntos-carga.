from django.contrib import admin, messages

from . import services
from .admin_base import SoloModeradoresMixin
from .models import Denuncia


@admin.register(Denuncia)
class DenunciaAdmin(SoloModeradoresMixin, admin.ModelAdmin):
    list_display = ["__str__", "motivo", "estado", "usuario", "resuelta_por", "creado_en"]
    list_filter = ["estado", "motivo"]
    search_fields = ["punto__nombre", "detalle"]
    readonly_fields = [
        "punto",
        "reporte",
        "usuario",
        "motivo",
        "detalle",
        "estado",
        "resuelta_por",
        "creado_en",
    ]
    actions = ["aceptar", "descartar"]

    @admin.action(description="Aceptar: ocultar el punto o invalidar el reporte")
    def aceptar(self, request, queryset):
        for denuncia in queryset:
            services.resolver_denuncia(denuncia, request.user, aceptada=True)
        self.message_user(request, "Denuncias aceptadas.", messages.WARNING)

    @admin.action(description="Descartar: cerrar sin cambios")
    def descartar(self, request, queryset):
        for denuncia in queryset:
            services.resolver_denuncia(denuncia, request.user, aceptada=False)
        self.message_user(request, "Denuncias descartadas.")
