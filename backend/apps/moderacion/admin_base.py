"""Permisos del panel según el rol, sin tener que gestionar grupos a mano."""


class SoloModeradoresMixin:
    """Moderadores: ver y cambiar. Borrar: solo administradores."""

    def has_module_permission(self, request):
        return request.user.is_active and request.user.es_moderador

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
