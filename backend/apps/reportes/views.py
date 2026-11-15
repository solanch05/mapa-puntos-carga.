"""
Flujo 3 · Confirmar el estado en tiempo real.

GET  /api/puntos/{id}/reportes/   últimos reportes del punto
POST /api/puntos/{id}/reportes/   "¿Hay corriente ahora?" -> un toque

Body del POST: estado (obligatorio), comentario y foto (opcionales).
"""

from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.puntos.models import EstadoPublicacion, PuntoCarga
from apps.usuarios import reputacion

from .imagenes import procesar_foto
from .models import ReporteEstado
from .serializers import ReporteSerializer
from .services import estado_actual

# Para evitar "farmear" reputación: reportar el mismo punto varias veces
# seguidas solo suma reputación una vez cada 30 minutos.
INTERVALO_REPUTACION = timedelta(minutes=30)


class ReportesDePuntoView(generics.ListCreateAPIView):
    serializer_class = ReporteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_throttles(self):
        self.throttle_scope = "reportes" if self.request.method == "POST" else None
        return super().get_throttles()

    def get_punto(self):
        return get_object_or_404(
            PuntoCarga, pk=self.kwargs["punto_id"], estado_publicacion=EstadoPublicacion.ACTIVO
        )

    def get_queryset(self):
        return ReporteEstado.objects.filter(punto=self.get_punto(), valido=True).select_related("usuario")[
            :20
        ]

    def create(self, request, *args, **kwargs):
        punto = self.get_punto()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        foto = serializer.validated_data.pop("foto", None)
        if foto:
            try:
                serializer.validated_data["foto"] = procesar_foto(foto)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"foto": exc.messages})

        reciente = ReporteEstado.objects.filter(
            punto=punto, usuario=request.user, creado_en__gte=timezone.now() - INTERVALO_REPUTACION
        ).exists()
        reporte = serializer.save(punto=punto, usuario=request.user)
        if not reciente:
            request.user.ajustar_reputacion(reputacion.PUNTOS_REPORTE)

        estado, confirmado_en = estado_actual(punto)
        return Response(
            {
                "reporte": ReporteSerializer(reporte, context={"request": request}).data,
                "estado_actual": estado,
                "confirmado_en": confirmado_en,
                "reputacion": request.user.reputacion,
            },
            status=status.HTTP_201_CREATED,
        )
