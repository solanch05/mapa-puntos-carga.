from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.moderacion.admin_base import SoloModeradoresMixin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(SoloModeradoresMixin, UserAdmin):
    ordering = ["-creado_en"]
    list_display = ["email", "nombre", "rol", "reputacion", "is_active", "creado_en"]
    list_filter = ["rol", "is_active"]
    search_fields = ["email", "nombre"]
    readonly_fields = ["creado_en", "last_login"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Datos", {"fields": ["nombre", "rol", "reputacion", "is_active"]}),
        ("Fechas", {"fields": ["last_login", "creado_en"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["email", "nombre", "rol", "password1", "password2"]})
    ]

    def has_change_permission(self, request, obj=None):
        # Los moderadores pueden ver usuarios, pero solo un admin los modifica.
        return request.user.is_superuser
