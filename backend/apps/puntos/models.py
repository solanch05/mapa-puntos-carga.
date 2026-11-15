"""
Tablas `punto_carga`, `horario` y `favorito` del esquema (sección 5).

Campos añadidos respecto al documento, y por qué:
- ubicacion_publica: la ubicación que se enseña y se consulta. Para viviendas
  con ubicación aproximada se "ajusta" a una rejilla de ~200 m, así la
  dirección exacta nunca sale en una consulta pública (sección 10).
- nota_moderacion: texto con el que el moderador pide correcciones (flujo 4)
  o donde el detector deja avisos de posible duplicado.
- estado_publicacion "pausado": el anfitrión puede pausar su punto en
  cualquier momento (sección 8, privacidad).
"""

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point


class TipoPunto(models.TextChoices):
    VIVIENDA = "vivienda", "Vivienda"
    NEGOCIO = "negocio", "Negocio"
    INSTITUCION = "institucion", "Institución"
    ESPACIO_PUBLICO = "espacio_publico", "Espacio público"


class Respaldo(models.TextChoices):
    NINGUNO = "ninguno", "Sin respaldo (red eléctrica)"
    BATERIA = "bateria", "Batería"
    PLANTA = "planta", "Planta eléctrica"
    SOLAR = "solar", "Paneles solares"


class Acceso(models.TextChoices):
    LIBRE = "libre", "Libre"
    CON_CONSUMO = "con_consumo", "Con consumo"
    PREVIA_SOLICITUD = "previa_solicitud", "Previa solicitud"
    PAGO = "pago", "De pago"


class Conector(models.TextChoices):
    ENCHUFE = "enchufe", "Enchufe (110/220 V)"
    USB = "usb", "USB"
    AMBOS = "ambos", "Enchufe y USB"


class EstadoPublicacion(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente de revisión"
    ACTIVO = "activo", "Activo"
    PAUSADO = "pausado", "Pausado por el anfitrión"
    OCULTO = "oculto", "Oculto por moderación"


def ajustar_a_rejilla(punto: Point, tam: float) -> Point:
    """Lleva un punto al centro de su celda en una rejilla de `tam` grados.

    Es determinista: el mismo punto siempre da la misma celda. Si añadiéramos
    ruido aleatorio, consultando muchas veces y promediando se podría
    recuperar la ubicación exacta.
    """
    lng = (punto.x // tam) * tam + tam / 2
    lat = (punto.y // tam) * tam + tam / 2
    return Point(round(lng, 6), round(lat, 6), srid=4326)


class PuntoCarga(models.Model):
    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=TipoPunto.choices)
    descripcion = models.TextField(
        blank=True,
        help_text='Referencias para llegar, p. ej. "frente al parque, portal azul".',
    )
    # geography=True: las distancias se calculan en metros sobre la esfera.
    # spatial_index=True (por defecto) crea un índice GiST en PostGIS.
    ubicacion = models.PointField(geography=True, spatial_index=True)
    ubicacion_publica = models.PointField(geography=True, spatial_index=True, editable=False)
    ubicacion_aproximada = models.BooleanField(default=False)
    numero_tomas = models.PositiveSmallIntegerField(default=1)
    tipo_conector = models.CharField(max_length=10, choices=Conector.choices, default=Conector.ENCHUFE)
    respaldo = models.CharField(max_length=10, choices=Respaldo.choices, default=Respaldo.NINGUNO)
    acceso = models.CharField(max_length=20, choices=Acceso.choices, default=Acceso.LIBRE)
    contacto = models.CharField(max_length=120, blank=True)
    estado_publicacion = models.CharField(
        max_length=10, choices=EstadoPublicacion.choices, default=EstadoPublicacion.PENDIENTE
    )
    nota_moderacion = models.TextField(blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="puntos")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "punto_carga"
        verbose_name = "punto de carga"
        verbose_name_plural = "puntos de carga"
        ordering = ["-creado_en"]
        indexes = [models.Index(fields=["estado_publicacion"])]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Las viviendas siempre usan ubicación aproximada (privacidad por defecto).
        if self.tipo == TipoPunto.VIVIENDA:
            self.ubicacion_aproximada = True
        if self.ubicacion_aproximada:
            self.ubicacion_publica = ajustar_a_rejilla(self.ubicacion, settings.REJILLA_UBICACION_APROXIMADA)
        else:
            self.ubicacion_publica = self.ubicacion
        super().save(*args, **kwargs)


class Horario(models.Model):
    class Dia(models.IntegerChoices):
        LUNES = 0, "Lunes"
        MARTES = 1, "Martes"
        MIERCOLES = 2, "Miércoles"
        JUEVES = 3, "Jueves"
        VIERNES = 4, "Viernes"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    punto = models.ForeignKey(PuntoCarga, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.PositiveSmallIntegerField(choices=Dia.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField(help_text="Si es menor que la hora de inicio, cruza la medianoche.")

    class Meta:
        db_table = "horario"
        ordering = ["dia_semana", "hora_inicio"]

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M}"


class Favorito(models.Model):
    """Relación muchos a muchos con clave compuesta (usuario_id, punto_id)."""

    pk = models.CompositePrimaryKey("usuario", "punto")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favoritos")
    punto = models.ForeignKey(PuntoCarga, on_delete=models.CASCADE, related_name="favoritos")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorito"
