"""
Tabla `usuario` del esquema de datos (sección 5).

Campos del documento: id, nombre, email, contraseña (hash), rol, reputación,
creado_en. Heredamos de AbstractUser para reutilizar el hash de contraseñas,
los permisos y el panel de administración de Django.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import F


class Rol(models.TextChoices):
    USUARIO = "usuario", "Usuario"
    MODERADOR = "moderador", "Moderador"
    ADMIN = "admin", "Administrador"


class UsuarioManager(BaseUserManager):
    """Gestor que usa el email como identificador en lugar de un username."""

    use_in_migrations = True

    def _crear(self, email, password, **extra):
        if not email:
            raise ValueError("El email es obligatorio")
        usuario = self.model(email=self.normalize_email(email), **extra)
        usuario.set_password(password)  # guarda el hash, nunca la contraseña
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        extra.setdefault("rol", Rol.USUARIO)
        return self._crear(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra["rol"] = Rol.ADMIN
        return self._crear(email, password, **extra)


class Usuario(AbstractUser):
    username = None  # iniciamos sesión con email
    first_name = None
    last_name = None

    nombre = models.CharField(max_length=80)
    email = models.EmailField("email", unique=True)
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.USUARIO)
    reputacion = models.IntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]

    objects = UsuarioManager()

    class Meta:
        db_table = "usuario"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return f"{self.nombre} <{self.email}>"

    def save(self, *args, **kwargs):
        # El rol decide el acceso al panel: moderadores y admins entran,
        # solo los admins son superusuarios.
        self.is_staff = self.rol in (Rol.MODERADOR, Rol.ADMIN)
        self.is_superuser = self.rol == Rol.ADMIN
        super().save(*args, **kwargs)

    @property
    def es_moderador(self) -> bool:
        return self.rol in (Rol.MODERADOR, Rol.ADMIN)

    def ajustar_reputacion(self, puntos: int) -> None:
        """Suma o resta reputación de forma atómica (sin condiciones de carrera)."""
        Usuario.objects.filter(pk=self.pk).update(reputacion=F("reputacion") + puntos)
        self.refresh_from_db(fields=["reputacion"])
