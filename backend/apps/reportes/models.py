"""
Tabla `reporte_estado` (sección 5): el corazón del mapa junto a los puntos.

Campo añadido: `valido`. Si un moderador acepta una denuncia contra un
reporte, el reporte se invalida (deja de contar para el estado) pero no se
borra, para que quede rastro.
"""

from django.conf import settings
from django.db import models

from apps.puntos.models import PuntoCarga


class Estado(models.TextChoices):
    CON_ENERGIA = "con_energia", "Con energía"
    SIN_ENERGIA = "sin_energia", "Sin energía"
    LLENO = "lleno", "Lleno"
    CERRADO = "cerrado", "Cerrado"


# Valor calculado cuando no hay ningún reporte vigente. No se guarda nunca.
SIN_CONFIRMAR = "sin_confirmar"


def ruta_foto(instancia, nombre):
    return f"reportes/{instancia.punto_id}/{nombre}"


class ReporteEstado(models.Model):
    punto = models.ForeignKey(PuntoCarga, on_delete=models.CASCADE, related_name="reportes")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reportes")
    estado = models.CharField(max_length=12, choices=Estado.choices)
    comentario = models.CharField(max_length=280, blank=True)
    foto = models.ImageField(upload_to=ruta_foto, blank=True)
    valido = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "reporte_estado"
        verbose_name = "reporte de estado"
        verbose_name_plural = "reportes de estado"
        ordering = ["-creado_en"]
        indexes = [models.Index(fields=["punto", "-creado_en"])]

    def __str__(self):
        return f"{self.punto} · {self.get_estado_display()} · {self.creado_en:%d/%m %H:%M}"
