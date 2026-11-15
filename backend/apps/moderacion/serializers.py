from rest_framework import serializers

from apps.puntos.models import EstadoPublicacion

from .models import Denuncia, EstadoDenuncia


class DenunciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Denuncia
        fields = ["id", "punto", "reporte", "motivo", "detalle", "estado", "creado_en"]
        read_only_fields = ["id", "estado", "creado_en"]

    def validate(self, datos):
        punto, reporte = datos["punto"], datos.get("reporte")
        if punto.estado_publicacion != EstadoPublicacion.ACTIVO:
            raise serializers.ValidationError("Solo se pueden denunciar puntos publicados.")
        if reporte and reporte.punto_id != punto.pk:
            raise serializers.ValidationError("El reporte no pertenece a ese punto.")
        usuario = self.context["request"].user
        if Denuncia.objects.filter(
            usuario=usuario, punto=punto, reporte=reporte, estado=EstadoDenuncia.ABIERTA
        ).exists():
            raise serializers.ValidationError("Ya tienes una denuncia abierta sobre esto.")
        return datos
