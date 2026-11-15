"""
Configuración de Django para el Mapa Comunitario de Puntos de Carga.

Todo lo que cambia entre entornos (claves, base de datos, IA) se lee de
variables de entorno. Así no hay secretos en el repositorio (sección 10 del
documento: "Claves en variables de entorno").
"""

import mimetypes
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(nombre: str, defecto: bool = False) -> bool:
    return os.environ.get(nombre, str(defecto)).lower() in {"1", "true", "yes", "si", "sí"}


def env_list(nombre: str, defecto: str = "") -> list[str]:
    return [v.strip() for v in os.environ.get(nombre, defecto).split(",") if v.strip()]


# --- Núcleo -----------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "solo-para-desarrollo-cambiar-en-produccion")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8080")
# Enviar el origen a otros sitios: OpenStreetMap lo exige para servir las losetas del mapa.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",  # GeoDjango: campos geográficos y consultas por distancia
    # Terceros
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # Apps del proyecto (monolito modular: un módulo por responsabilidad)
    "apps.usuarios",
    "apps.puntos",
    "apps.reportes",
    "apps.moderacion",
    "apps.ia",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Base de datos: PostgreSQL + PostGIS --------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB", "puntos"),
        "USER": os.environ.get("POSTGRES_USER", "puntos"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "puntos"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

if url_bd := os.environ.get("DATABASE_URL"):
    partes = urlparse(url_bd)
    DATABASES["default"].update(
        {
            "NAME": partes.path.lstrip("/"),
            "USER": unquote(partes.username or ""),
            "PASSWORD": unquote(partes.password or ""),
            "HOST": partes.hostname,
            "PORT": str(partes.port or 5432),
        }
    )

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "usuarios.Usuario"

# Contraseñas: Django usa PBKDF2 con sal por defecto (hash seguro estándar).
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Havana"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Despliegue en un solo servicio: Django sirve también la PWA compilada.
# WhiteNoise entrega sus archivos (index.html, sw.js, assets...) desde la raíz.
FRONTEND_DIST = os.environ.get("FRONTEND_DIST", "")
if FRONTEND_DIST and Path(FRONTEND_DIST).is_dir():
    WHITENOISE_ROOT = FRONTEND_DIST
    WHITENOISE_INDEX_FILE = True
    mimetypes.add_type("application/manifest+json", ".webmanifest")

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

# --- API: DRF + JWT ------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 200,
    # Límite de peticiones por IP (anónimos) y por usuario (registrados).
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("THROTTLE_ANON", "120/min"),
        "user": os.environ.get("THROTTLE_USER", "240/min"),
        "reportes": os.environ.get("THROTTLE_REPORTES", "20/hour"),
        "puntos_nuevos": os.environ.get("THROTTLE_PUNTOS", "10/day"),
        "denuncias": os.environ.get("THROTTLE_DENUNCIAS", "20/day"),
        "contacto": os.environ.get("THROTTLE_CONTACTO", "10/hour"),
        "auth": os.environ.get("THROTTLE_AUTH", "10/min"),
        "ia": os.environ.get("THROTTLE_IA", "20/hour"),
    },
}

SIMPLE_JWT = {
    # Token de acceso corto + token de refresco (sección 6 del documento).
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

# --- Reglas de negocio (configurables) -----------------------------------------
# Ventana de validez de un reporte: pasado este tiempo el punto se muestra
# como "sin confirmar", nunca como "con energía".
VENTANA_VALIDEZ_HORAS = float(os.environ.get("VENTANA_VALIDEZ_HORAS", "3"))
# Reputación a partir de la cual un usuario publica sin pasar por revisión.
REPUTACION_CONFIANZA = int(os.environ.get("REPUTACION_CONFIANZA", "20"))
# Por debajo de esta reputación los reportes no cuentan para el estado.
REPUTACION_MINIMA_REPORTE = int(os.environ.get("REPUTACION_MINIMA_REPORTE", "0"))
# Tamaño de la rejilla (en grados) para la ubicación aproximada de viviendas.
# 0.002° ≈ 220 m en latitud.
REJILLA_UBICACION_APROXIMADA = float(os.environ.get("REJILLA_UBICACION_APROXIMADA", "0.002"))
RADIO_MAXIMO_KM = float(os.environ.get("RADIO_MAXIMO_KM", "20"))

# --- IA (opcional) --------------------------------------------------------------
# El producto funciona sin IA. Si IA_HABILITADA es False, el endpoint no existe
# para el frontend. Si está habilitada pero no hay clave, se usa un extractor
# por reglas que funciona sin conexión externa.
IA_HABILITADA = env_bool("IA_HABILITADA", False)
IA_API_KEY = os.environ.get("IA_API_KEY", "")
IA_API_URL = os.environ.get("IA_API_URL", "https://api.anthropic.com/v1/messages")
IA_MODELO = os.environ.get("IA_MODELO", "claude-haiku-5-5")
IA_TIMEOUT_S = float(os.environ.get("IA_TIMEOUT_S", "15"))

# --- Seguridad en producción ----------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# --- Registro de errores ---------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
