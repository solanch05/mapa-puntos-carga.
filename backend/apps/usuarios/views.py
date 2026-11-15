"""
POST /api/auth/registro/        crear cuenta con email y contraseña
POST /api/auth/token/           iniciar sesión -> {access, refresh}
POST /api/auth/token/refresh/   renovar el token de acceso
POST /api/auth/logout/          invalidar el token de refresco
GET  /api/auth/yo/              datos del usuario autenticado
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import RegistroSerializer, UsuarioSerializer


class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        refresh = RefreshToken.for_user(usuario)  # entra directamente tras registrarse
        return Response(
            {
                "usuario": UsuarioSerializer(usuario).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    throttle_scope = "auth"  # frena ataques de fuerza bruta


class RefreshView(TokenRefreshView):
    throttle_scope = "auth"


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh")).blacklist()
        except TokenError:
            pass  # un token ya inválido no es un error para el usuario
        return Response(status=status.HTTP_205_RESET_CONTENT)


class YoView(generics.RetrieveAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
