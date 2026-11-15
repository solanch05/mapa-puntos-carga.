"""
POST /api/ia/borrador/   {"texto": "..."} -> borrador validado + avisos

Solo existe si IA_HABILITADA=True. El frontend lo sabe por /api/config/.
"""

from django.conf import settings
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.puntos.serializers import PuntoEscrituraSerializer

from .detector import motivos_sospecha
from .extractor import generar_borrador


class BorradorPuntoSerializer(PuntoEscrituraSerializer):
    """El MISMO serializador del alta, pero sin exigir ubicación ni contacto."""

    lat = serializers.FloatField(required=False)
    lng = serializers.FloatField(required=False)

    class Meta(PuntoEscrituraSerializer.Meta):
        fields = [f for f in PuntoEscrituraSerializer.Meta.fields if f not in {"id", "contacto"}]


class TextoSerializer(serializers.Serializer):
    texto = serializers.CharField(min_length=10, max_length=600)


class BorradorView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "ia"

    def post(self, request):
        if not settings.IA_HABILITADA:
            return Response(
                {"detail": "El asistente de IA no está activado."}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        entrada = TextoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        texto = entrada.validated_data["texto"]

        crudo, avisos, origen = generar_borrador(texto)

        # Validación campo a campo: lo que no pase se descarta y se avisa,
        # en lugar de rechazar el borrador entero.
        validador = BorradorPuntoSerializer(data=crudo, partial=True)
        validador.is_valid()
        borrador = {k: v for k, v in crudo.items() if k not in validador.errors and k in validador.fields}
        for campo in validador.errors:
            avisos.append(f"El campo «{campo}» no se pudo interpretar; complétalo a mano.")

        if motivos := motivos_sospecha(texto):
            avisos.append("El texto parece sospechoso (" + "; ".join(motivos) + "). Irá a revisión.")

        return Response({"borrador": borrador, "avisos": avisos, "origen": origen})
