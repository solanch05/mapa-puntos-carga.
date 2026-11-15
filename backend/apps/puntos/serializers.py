"""
Serializadores de puntos: convierten modelos <-> JSON y VALIDAN la entrada.

La API expone `lat` y `lng` (más fáciles de entender que GeoJSON). Hay tres
vistas de un punto según quién pregunta:
- Lista (pública y ligera): lo justo para pintar los pines.
- Detalle (pública): la ficha completa, sin contacto ni ubicación exacta.
- Detalle de dueño/moderador: añade ubicación exacta, contacto y moderación.
"""

from django.contrib.gis.geos import Point
from django.db import transaction
from rest_framework import serializers

from .models import Horario, PuntoCarga


class HorarioSerializer(serializers.ModelSerializer):
    dia_nombre = serializers.CharField(source="get_dia_semana_display", read_only=True)

    class Meta:
        model = Horario
        fields = ["dia_semana", "dia_nombre", "hora_inicio", "hora_fin"]


class PuntoListaSerializer(serializers.ModelSerializer):
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    estado_actual = serializers.CharField(read_only=True)
    confirmado_en = serializers.DateTimeField(read_only=True)
    abierto_ahora = serializers.BooleanField(read_only=True)

    class Meta:
        model = PuntoCarga
        fields = [
            "id",
            "nombre",
            "tipo",
            "lat",
            "lng",
            "ubicacion_aproximada",
            "numero_tomas",
            "tipo_conector",
            "respaldo",
            "acceso",
            "estado_actual",
            "confirmado_en",
            "abierto_ahora",
        ]

    # Siempre la ubicación pública (aproximada en viviendas).
    def get_lat(self, obj):
        return obj.ubicacion_publica.y

    def get_lng(self, obj):
        return obj.ubicacion_publica.x


class ReporteResumenSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    estado = serializers.CharField()
    comentario = serializers.CharField()
    foto = serializers.ImageField()
    usuario_nombre = serializers.CharField(source="usuario.nombre")
    creado_en = serializers.DateTimeField()


class PuntoDetalleSerializer(PuntoListaSerializer):
    horarios = HorarioSerializer(many=True, read_only=True)
    tiene_contacto = serializers.SerializerMethodField()
    creado_por_nombre = serializers.CharField(source="creado_por.nombre", read_only=True)
    ultimos_reportes = serializers.SerializerMethodField()
    es_favorito = serializers.SerializerMethodField()
    es_mio = serializers.SerializerMethodField()

    class Meta(PuntoListaSerializer.Meta):
        fields = PuntoListaSerializer.Meta.fields + [
            "descripcion",
            "horarios",
            "tiene_contacto",
            "creado_por_nombre",
            "ultimos_reportes",
            "es_favorito",
            "es_mio",
            "creado_en",
        ]

    def _usuario(self):
        request = self.context.get("request")
        return request.user if request and request.user.is_authenticated else None

    def get_tiene_contacto(self, obj):
        return bool(obj.contacto)

    def get_ultimos_reportes(self, obj):
        reportes = obj.reportes.filter(valido=True).select_related("usuario")[:5]
        return ReporteResumenSerializer(reportes, many=True, context=self.context).data

    def get_es_favorito(self, obj):
        usuario = self._usuario()
        return bool(usuario) and obj.favoritos.filter(usuario=usuario).exists()

    def get_es_mio(self, obj):
        usuario = self._usuario()
        return bool(usuario) and obj.creado_por_id == usuario.pk


class PuntoPrivadoSerializer(PuntoDetalleSerializer):
    """Ficha para el dueño del punto o un moderador."""

    lat_exacta = serializers.SerializerMethodField()
    lng_exacta = serializers.SerializerMethodField()

    class Meta(PuntoDetalleSerializer.Meta):
        fields = PuntoDetalleSerializer.Meta.fields + [
            "lat_exacta",
            "lng_exacta",
            "contacto",
            "estado_publicacion",
            "nota_moderacion",
        ]

    def get_lat_exacta(self, obj):
        return obj.ubicacion.y

    def get_lng_exacta(self, obj):
        return obj.ubicacion.x


class PuntoEscrituraSerializer(serializers.ModelSerializer):
    """Alta y edición de puntos. Toda la validación de entrada vive aquí."""

    lat = serializers.FloatField(min_value=-90, max_value=90, write_only=True)
    lng = serializers.FloatField(min_value=-180, max_value=180, write_only=True)
    horarios = HorarioSerializer(many=True, required=False)
    numero_tomas = serializers.IntegerField(min_value=1, max_value=50, required=False)

    class Meta:
        model = PuntoCarga
        fields = [
            "id",
            "nombre",
            "tipo",
            "descripcion",
            "lat",
            "lng",
            "ubicacion_aproximada",
            "numero_tomas",
            "tipo_conector",
            "respaldo",
            "acceso",
            "contacto",
            "horarios",
        ]
        extra_kwargs = {"descripcion": {"max_length": 500}}

    def validate_nombre(self, valor):
        valor = valor.strip()
        if len(valor) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return valor

    def validate_horarios(self, horarios):
        if len(horarios) > 21:
            raise serializers.ValidationError("Como máximo 3 franjas por día.")
        return horarios

    def _con_ubicacion(self, datos):
        lat, lng = datos.pop("lat", None), datos.pop("lng", None)
        if lat is not None and lng is not None:
            datos["ubicacion"] = Point(lng, lat, srid=4326)
        return datos

    @transaction.atomic
    def create(self, datos):
        horarios = datos.pop("horarios", [])
        punto = PuntoCarga.objects.create(**self._con_ubicacion(datos))
        Horario.objects.bulk_create(Horario(punto=punto, **h) for h in horarios)
        return punto

    @transaction.atomic
    def update(self, punto, datos):
        horarios = datos.pop("horarios", None)
        for campo, valor in self._con_ubicacion(datos).items():
            setattr(punto, campo, valor)
        punto.save()
        if horarios is not None:  # si llegan horarios, sustituyen a los anteriores
            punto.horarios.all().delete()
            Horario.objects.bulk_create(Horario(punto=punto, **h) for h in horarios)
        return punto
