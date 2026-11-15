"""
Mapa de URLs de la API. Un solo punto de entrada: /api/...
El panel de moderación es el admin de Django: /admin/
"""

from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, Http404, JsonResponse
from django.urls import include, path, re_path
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

# Fotos de reportes. En el despliegue de un solo servicio no hay nginx delante,
# así que Django las sirve también fuera de DEBUG (volumen pequeño).
if settings.DEBUG or settings.FRONTEND_DIST:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT, show_indexes=False)
    if not settings.DEBUG:
        from django.views.static import serve

        urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]


def spa(request, ruta=""):
    """Cualquier ruta que no sea de la API devuelve la app de React (React Router decide)."""
    indice = Path(settings.FRONTEND_DIST) / "index.html"
    if not indice.is_file():
        raise Http404
    return FileResponse(indice.open("rb"), content_type="text/html")


if settings.FRONTEND_DIST:
    urlpatterns += [re_path(r"^(?!api/|admin/|static/|media/)(?P<ruta>.*)$", spa)]
