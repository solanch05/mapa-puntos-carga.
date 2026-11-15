"""Permisos por rol y por objeto (sección 10: "Acceso indebido a funciones")."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class EsModerador(BasePermission):
    message = "Solo los moderadores pueden hacer esto."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.es_moderador)


class EsDuenoOModerador(BasePermission):
    """Leer: cualquiera. Modificar: solo el dueño del punto o un moderador."""

    message = "Solo quien creó el punto puede modificarlo."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        usuario = request.user
        return usuario.is_authenticated and (obj.creado_por_id == usuario.pk or usuario.es_moderador)
