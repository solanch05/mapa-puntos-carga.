"""Tabla `denuncia` (sección 5): apunta a un punto o a un reporte concreto."""

from django.conf import settings
from django.db import models

from apps.puntos.models import PuntoCarga
from apps.reportes.models import ReporteEstado


class Motivo(models.TextChoices):
    NO_EXISTE = "no_existe", "El punto no existe"
    DATOS_FALSOS = "datos_falsos", "Información falsa"
    DUPLICADO = "duplicado", "Punto duplicado"
    SPAM = "spam", "Spam o publicidad"
    INSEGURO = "inseguro", "Lugar inseguro o trato inadecuado"
    OTRO = "otro", "Otro"


class EstadoDenuncia(models.TextChoices):
    ABIERTA = "abierta", "Abierta"
    RESUELTA = "resuelta", "Resuelta"


class Denuncia(models.Model):
    punto = models.ForeignKey(PuntoCarga, on_delete=models.CASCADE, related_name="denuncias")
    reporte = models.ForeignKey(
        ReporteEstado, on_delete=models.CASCADE, null=True, blank=True, related_name="denuncias"
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="denuncias")
    motivo = models.CharField(max_length=15, choices=Motivo.choices)
    detalle = models.CharField(max_length=280, blank=True)
    estado = models.CharField(max_length=10, choices=EstadoDenuncia.choices, default=EstadoDenuncia.ABIERTA)
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="denuncias_resueltas",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "denuncia"
        ordering = ["estado", "-creado_en"]

    def __str__(self):
        objetivo = f"reporte #{self.reporte_id}" if self.reporte_id else f"punto «{self.punto}»"
        return f"{self.get_motivo_display()} sobre {objetivo}"
