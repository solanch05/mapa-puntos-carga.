"""
Mapa de URLs de la API. Un solo punto de entrada: /api/...
El panel de moderación es el admin de Django: /admin/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.ia.views import BorradorView
from apps.moderacion.views import DenunciaCreateView, MetricasView
from apps.puntos.views import FavoritosView, PuntoViewSet
from apps.reportes.views import ReportesDePuntoView
from apps.usuarios.views import LoginView, LogoutView, RefreshView, RegistroView, YoView

admin.site.site_header = "Mapa de Puntos de Carga · Moderación"
admin.site.site_title = "Moderación"
admin.site.index_title = "Cola de moderación"

router = DefaultRouter()
router.register("puntos", PuntoViewSet, basename="punto")


def config_publica(request):
    """Lo que el frontend necesita saber del servidor (sin secretos)."""
    return JsonResponse(
        {
            "ia_habilitada": settings.IA_HABILITADA,
            "ventana_validez_horas": settings.VENTANA_VALIDEZ_HORAS,
            "radio_maximo_km": settings.RADIO_MAXIMO_KM,
        }
    )


def salud(request):
    return JsonResponse({"estado": "ok"})


api = [
    path("", include(router.urls)),
    path("puntos/<int:punto_id>/reportes/", ReportesDePuntoView.as_view(), name="reportes-punto"),
    path("favoritos/", FavoritosView.as_view(), name="favoritos"),
    path("denuncias/", DenunciaCreateView.as_view(), name="denuncias"),
    path("metricas/", MetricasView.as_view(), name="metricas"),
    path("ia/borrador/", BorradorView.as_view(), name="ia-borrador"),
    path("auth/registro/", RegistroView.as_view(), name="registro"),
    path("auth/token/", LoginView.as_view(), name="token"),
    path("auth/token/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/yo/", YoView.as_view(), name="yo"),
    path("config/", config_publica, name="config"),
    path("salud/", salud, name="salud"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
