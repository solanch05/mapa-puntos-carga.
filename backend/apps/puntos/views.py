"""
Endpoints de puntos de carga.

GET    /api/puntos/                  mapa: lista filtrable (pública)
GET    /api/puntos/{id}/             ficha del punto (pública si está activo)
POST   /api/puntos/                  agregar un punto (flujo 2)
PATCH  /api/puntos/{id}/             editar (dueño o moderador)
DELETE /api/puntos/{id}/             retirar el punto (dueño o admin)
GET    /api/puntos/mios/             mis puntos con su estado de publicación
POST   /api/puntos/{id}/pausar/      pausar / reanudar (dueño)
POST   /api/puntos/{id}/contacto/    ver el contacto bajo solicitud (registrados)
POST   /api/puntos/{id}/favorito/    marcar favorito  · DELETE: quitarlo
GET    /api/favoritos/               mis favoritos
"""

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.ia.detector import revisar_punto
from apps.usuarios.reputacion import es_de_confianza

from . import services
from .models import EstadoPublicacion, Favorito, PuntoCarga
from .permissions import EsDuenoOModerador
from .serializers import (
    PuntoDetalleSerializer,
    PuntoEscrituraSerializer,
    PuntoListaSerializer,
    PuntoPrivadoSerializer,
)

ESCALAS_POR_ACCION = {
    "create": "puntos_nuevos",
    "contacto": "contacto",
}


class PuntoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, EsDuenoOModerador]

    def get_throttles(self):
        self.throttle_scope = ESCALAS_POR_ACCION.get(self.action)
        return super().get_throttles()

    # --- Qué puntos ve cada quién -------------------------------------------------
    def get_queryset(self):
        usuario = self.request.user
        if self.action == "list":
            puntos = services.base_publica()
        elif usuario.is_authenticated and usuario.es_moderador:
            puntos = PuntoCarga.objects.all()
        elif usuario.is_authenticated:
            # Los activos de todos + los míos en cualquier estado.
            puntos = PuntoCarga.objects.filter(
                Q(estado_publicacion=EstadoPublicacion.ACTIVO) | Q(creado_por=usuario)
            )
        else:
            puntos = services.base_publica()
        return services.con_anotaciones(puntos.select_related("creado_por"))

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return PuntoEscrituraSerializer
        if self.action == "list":
            return PuntoListaSerializer
        return PuntoDetalleSerializer

    def _serializar_ficha(self, punto):
        usuario = self.request.user
        privado = usuario.is_authenticated and (usuario.es_moderador or punto.creado_por_id == usuario.pk)
        clase = PuntoPrivadoSerializer if privado else PuntoDetalleSerializer
        punto = self.get_queryset().get(pk=punto.pk)  # recarga con anotaciones
        return clase(punto, context=self.get_serializer_context()).data

    # --- Lectura -----------------------------------------------------------------
    def list(self, request, *args, **kwargs):
        try:
            puntos = services.filtrar_puntos(self.get_queryset(), request.query_params)
        except ValueError as exc:
            raise ValidationError({"detalle": str(exc)})
        pagina = self.paginate_queryset(puntos)
        return self.get_paginated_response(self.get_serializer(pagina, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self._serializar_ficha(self.get_object()))

    # --- Escritura -----------------------------------------------------------------
    def _decidir_publicacion(self, punto):
        """Usuarios de confianza publican directo; el resto pasa por revisión.

        Si el detector encuentra un posible duplicado o texto sospechoso, el
        punto va SIEMPRE a revisión, aunque el autor sea de confianza.
        """
        avisos = revisar_punto(punto)
        directo = es_de_confianza(self.request.user) and not avisos
        punto.estado_publicacion = EstadoPublicacion.ACTIVO if directo else EstadoPublicacion.PENDIENTE
        punto.nota_moderacion = "\n".join(avisos)
        punto.save(update_fields=["estado_publicacion", "nota_moderacion"])

    def perform_create(self, serializer):
        self._decidir_publicacion(serializer.save(creado_por=self.request.user))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(self._serializar_ficha(serializer.instance), status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        punto = self.get_object()
        serializer = self.get_serializer(punto, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        punto = serializer.save()
        # Un punto pausado sigue pausado; el resto vuelve a evaluarse.
        if punto.estado_publicacion != EstadoPublicacion.PAUSADO and not request.user.es_moderador:
            self._decidir_publicacion(punto)
        return Response(self._serializar_ficha(punto))

    def destroy(self, request, *args, **kwargs):
        punto = self.get_object()
        if punto.creado_por_id != request.user.pk and request.user.rol != "admin":
            return Response(
                {"detail": "Solo quien creó el punto puede retirarlo."},
                status=status.HTTP_403_FORBIDDEN,
            )
        punto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- Acciones extra ------------------------------------------------------------
    @action(detail=False, permission_classes=[IsAuthenticated])
    def mios(self, request):
        puntos = services.con_anotaciones(PuntoCarga.objects.filter(creado_por=request.user))
        return Response(PuntoPrivadoSerializer(puntos, many=True, context={"request": request}).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def pausar(self, request, pk=None):
        punto = self.get_object()
        if punto.creado_por_id != request.user.pk:
            return Response({"detail": "Solo el anfitrión puede pausar su punto."}, status=403)
        cambios = {
            EstadoPublicacion.ACTIVO: EstadoPublicacion.PAUSADO,
            EstadoPublicacion.PAUSADO: EstadoPublicacion.ACTIVO,
        }
        if punto.estado_publicacion not in cambios:
            return Response(
                {"detail": "Solo se pueden pausar o reanudar puntos activos o pausados."}, status=400
            )
        punto.estado_publicacion = cambios[punto.estado_publicacion]
        punto.save(update_fields=["estado_publicacion"])
        return Response(self._serializar_ficha(punto))

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def contacto(self, request, pk=None):
        """El contacto no viaja en la ficha: se pide explícitamente y con límite."""
        punto = self.get_object()
        if not punto.contacto:
            return Response({"detail": "Este punto no compartió contacto."}, status=404)
        return Response({"contacto": punto.contacto})

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favorito(self, request, pk=None):
        punto = self.get_object()
        if request.method == "DELETE":
            Favorito.objects.filter(usuario=request.user, punto=punto).delete()
            return Response({"es_favorito": False})
        Favorito.objects.get_or_create(usuario=request.user, punto=punto)
        return Response({"es_favorito": True}, status=status.HTTP_201_CREATED)


class FavoritosView(ListAPIView):
    serializer_class = PuntoListaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        puntos = services.base_publica().filter(favoritos__usuario=self.request.user)
        return services.con_anotaciones(puntos)
