"""
POST /api/denuncias/   denunciar un punto o un reporte (registrados)
GET  /api/metricas/    las tres métricas de éxito del piloto (moderadores)
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.puntos.models import EstadoPublicacion, PuntoCarga
from apps.puntos.permissions import EsModerador
from apps.reportes.models import ReporteEstado
from apps.reportes.services import reportes_vigentes, ventana_validez

from .models import Denuncia, EstadoDenuncia
from .serializers import DenunciaSerializer


class DenunciaCreateView(generics.CreateAPIView):
    serializer_class = DenunciaSerializer
    permission_classes = [IsAuthenticated]
    throttle_scope = "denuncias"

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class MetricasView(APIView):
    """Métricas de éxito a tres meses (sección 1 del documento).

    La tercera (llegar a la ficha en menos de 30 s) se mide en el cliente y
    en la prueba end-to-end con Playwright.
    """

    permission_classes = [EsModerador]

    def get(self, request):
        activos = PuntoCarga.objects.filter(estado_publicacion=EstadoPublicacion.ACTIVO)
        total = activos.count()
        confirmados = activos.filter(reportes__in=reportes_vigentes()).distinct().count() if total else 0
        semana = timezone.now() - timedelta(days=7)
        return Response(
            {
                "puntos_activos": total,
                "meta_puntos_activos": 30,
                "puntos_confirmados_en_ventana": confirmados,
                "porcentaje_confirmados": round(100 * confirmados / total, 1) if total else 0.0,
                "meta_porcentaje_confirmados": 50,
                "ventana_horas": ventana_validez().total_seconds() / 3600,
                "puntos_pendientes": PuntoCarga.objects.filter(
                    estado_publicacion=EstadoPublicacion.PENDIENTE
                ).count(),
                "denuncias_abiertas": Denuncia.objects.filter(estado=EstadoDenuncia.ABIERTA).count(),
                "reportes_ultima_semana": ReporteEstado.objects.filter(creado_en__gte=semana).count(),
            }
        )
