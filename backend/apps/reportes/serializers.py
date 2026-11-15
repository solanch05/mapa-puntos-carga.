from rest_framework import serializers

from .models import ReporteEstado


class ReporteSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)

    class Meta:
        model = ReporteEstado
        fields = ["id", "punto", "estado", "comentario", "foto", "usuario_nombre", "creado_en"]
        read_only_fields = ["id", "punto", "usuario_nombre", "creado_en"]
        extra_kwargs = {"comentario": {"max_length": 280}}
