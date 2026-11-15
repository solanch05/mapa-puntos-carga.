"""
python manage.py sembrar_demo [--reiniciar]

Carga 15 puntos de ejemplo en la zona piloto (centro de Santa Clara) con
reportes a distintas horas, para que el demo muestre todos los estados:
"con energía hace 12 min", "sin confirmar" (reporte de hace 4 h), lleno,
cerrado, un punto pendiente y una denuncia abierta.

Sección 7 del documento: "Antes del demo (no omitir): cargar 10 a 15 puntos
de ejemplo en la zona piloto".
"""

from datetime import time, timedelta

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.moderacion.models import Denuncia
from apps.puntos.models import EstadoPublicacion, Horario, PuntoCarga
from apps.reportes.models import ReporteEstado
from apps.usuarios.models import Rol, Usuario

CONTRASENA_DEMO = "Demo1234!"
DOMINIO = "demo.local"

USUARIOS = [
    ("admin", "Administración", Rol.ADMIN, 100),
    ("moderador", "Equipo de moderación", Rol.MODERADOR, 50),
    ("ana", "Ana", Rol.USUARIO, 25),  # usuaria de confianza: publica directo
    ("luis", "Luis", Rol.USUARIO, 3),  # usuario nuevo: sus puntos pasan revisión
]

TODOS = range(7)
LAB = range(5)

# nombre, tipo, (lat, lng), tomas, conector, respaldo, acceso, descripción,
# (días, inicio, fin), último reporte (estado, minutos atrás) o None, autor
PUNTOS = [
    (
        "Cafetería El Portal",
        "negocio",
        (22.40712, -79.96398),
        4,
        "enchufe",
        "planta",
        "con_consumo",
        "Frente al parque, portal con columnas blancas.",
        (TODOS, time(8), time(22)),
        ("con_energia", 12),
        "ana",
    ),
    (
        "Biblioteca del centro",
        "institucion",
        (22.40598, -79.96512),
        6,
        "enchufe",
        "planta",
        "libre",
        "Sala de lectura, planta baja. Traer cable propio.",
        (LAB, time(9), time(17)),
        ("con_energia", 40),
        "ana",
    ),
    (
        "Kiosco solar del parque",
        "espacio_publico",
        (22.40668, -79.96460),
        8,
        "usb",
        "solar",
        "libre",
        "Junto a la glorieta, lado norte.",
        (TODOS, time(7), time(19)),
        ("con_energia", 5),
        "moderador",
    ),
    (
        "Casa de Pedro",
        "vivienda",
        (22.40890, -79.96150),
        2,
        "enchufe",
        "bateria",
        "previa_solicitud",
        "Portal azul. Avisar antes de llegar.",
        (TODOS, time(18), time(22)),
        ("con_energia", 60),
        "ana",
    ),
    (
        "Taller de electrónica Yoan",
        "negocio",
        (22.40455, -79.96255),
        3,
        "ambos",
        "planta",
        "pago",
        "Cobra una tarifa simbólica por carga.",
        (LAB, time(9), time(18)),
        ("sin_energia", 20),
        "ana",
    ),
    (
        "Centro comunitario del barrio",
        "institucion",
        (22.40980, -79.96620),
        10,
        "enchufe",
        "planta",
        "libre",
        "Salón principal. Suele llenarse por la tarde.",
        (TODOS, time(8), time(20)),
        ("lleno", 30),
        "moderador",
    ),
    (
        "Paladar La Esquina",
        "negocio",
        (22.40530, -79.96800),
        2,
        "enchufe",
        "planta",
        "con_consumo",
        "Esquina con toldo verde.",
        (TODOS, time(12), time(23)),
        ("con_energia", 170),
        "ana",
    ),
    (
        "Casa de Mirta",
        "vivienda",
        (22.41050, -79.96300),
        1,
        "enchufe",
        "solar",
        "previa_solicitud",
        "Preguntar por Mirta.",
        (TODOS, time(10), time(16)),
        ("con_energia", 240),
        "ana",
    ),
    (
        "Terminal de ómnibus",
        "espacio_publico",
        (22.40300, -79.96900),
        4,
        "enchufe",
        "ninguno",
        "libre",
        "Sala de espera, al fondo.",
        (TODOS, time(6), time(22)),
        ("cerrado", 55),
        "moderador",
    ),
    (
        "Policlínico del centro",
        "institucion",
        (22.40800, -79.96850),
        2,
        "enchufe",
        "planta",
        "previa_solicitud",
        "Solo para equipos médicos y teléfonos. Preguntar en recepción.",
        (TODOS, time(0), time(0)),
        ("con_energia", 25),
        "moderador",
    ),
    (
        "Barbería Los Amigos",
        "negocio",
        (22.40620, -79.96150),
        2,
        "ambos",
        "bateria",
        "con_consumo",
        "Tiene una estación de batería portátil.",
        (LAB, time(9), time(19)),
        None,
        "ana",
    ),
    (
        "Iglesia del Carmen",
        "institucion",
        (22.41150, -79.96550),
        3,
        "enchufe",
        "solar",
        "libre",
        "Patio lateral, entrada por la puerta pequeña.",
        (TODOS, time(8), time(12)),
        ("con_energia", 90),
        "ana",
    ),
    (
        "TecnoFix reparaciones",
        "negocio",
        (22.40380, -79.96550),
        5,
        "ambos",
        "planta",
        "pago",
        "Carga rápida por USB.",
        (LAB, time(8), time(20)),
        ("sin_energia", 120),
        "ana",
    ),
    (
        "Plaza del Carmen",
        "espacio_publico",
        (22.41100, -79.96480),
        6,
        "usb",
        "solar",
        "libre",
        "Bancos con puertos USB solares.",
        (TODOS, time(0), time(0)),
        ("con_energia", 15),
        "moderador",
    ),
]

PENDIENTES = [
    (
        "Casa de Lázaro",
        "vivienda",
        (22.40720, -79.96000),
        1,
        "enchufe",
        "planta",
        "previa_solicitud",
        "Planta pequeña, de 7 a 9 de la noche.",
        (TODOS, time(19), time(21)),
        None,
        "luis",
    ),
    (
        "Cafeteria el Portal",
        "negocio",
        (22.40715, -79.96402),
        3,
        "enchufe",
        "planta",
        "con_consumo",
        "Repetido por error.",
        (TODOS, time(8), time(22)),
        None,
        "luis",
    ),
]


class Command(BaseCommand):
    help = "Carga datos de ejemplo para el demo en la zona piloto (centro de Santa Clara)."

    def add_arguments(self, parser):
        parser.add_argument("--reiniciar", action="store_true", help="Borra antes los datos de demo.")

    @transaction.atomic
    def handle(self, *args, **opciones):
        if opciones["reiniciar"]:
            Usuario.objects.filter(email__endswith=f"@{DOMINIO}").delete()  # en cascada

        usuarios = {}
        for alias, nombre, rol, reputacion in USUARIOS:
            usuario, creado = Usuario.objects.get_or_create(
                email=f"{alias}@{DOMINIO}", defaults={"nombre": nombre, "rol": rol, "reputacion": reputacion}
            )
            if creado:
                usuario.set_password(CONTRASENA_DEMO)
                usuario.save()
            usuarios[alias] = usuario

        if PuntoCarga.objects.filter(creado_por__email__endswith=f"@{DOMINIO}").exists():
            self.stdout.write(self.style.WARNING("Ya hay datos de demo. Usa --reiniciar para recrearlos."))
            return

        ahora = timezone.now()
        for fila in PUNTOS:
            self._crear(fila, usuarios, EstadoPublicacion.ACTIVO, ahora)
        pendientes = [self._crear(fila, usuarios, EstadoPublicacion.PENDIENTE, ahora) for fila in PENDIENTES]
        pendientes[1].nota_moderacion = "Posible duplicado de «Cafetería El Portal»"
        pendientes[1].save(update_fields=["nota_moderacion"])

        paladar = PuntoCarga.objects.get(nombre="Paladar La Esquina")
        Denuncia.objects.create(
            punto=paladar,
            usuario=usuarios["luis"],
            motivo="datos_falsos",
            detalle="Fui y me dijeron que no dejan cargar aunque consumas.",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo cargado: {len(PUNTOS)} puntos activos, {len(PENDIENTES)} pendientes, 1 denuncia.\n"
                f"Usuarios: admin, moderador, ana, luis @{DOMINIO} · contraseña: {CONTRASENA_DEMO}"
            )
        )

    def _crear(self, fila, usuarios, estado, ahora):
        nombre, tipo, (lat, lng), tomas, conector, respaldo, acceso, desc, horario, reporte, autor = fila
        punto = PuntoCarga.objects.create(
            nombre=nombre,
            tipo=tipo,
            ubicacion=Point(lng, lat, srid=4326),
            numero_tomas=tomas,
            tipo_conector=conector,
            respaldo=respaldo,
            acceso=acceso,
            descripcion=desc,
            estado_publicacion=estado,
            creado_por=usuarios[autor],
            contacto="Preguntar en el local" if tipo != "vivienda" else "",
        )
        dias, inicio, fin = horario
        Horario.objects.bulk_create(
            Horario(punto=punto, dia_semana=d, hora_inicio=inicio, hora_fin=fin) for d in dias
        )
        if reporte:
            estado_reporte, minutos = reporte
            r = ReporteEstado.objects.create(punto=punto, usuario=usuarios["ana"], estado=estado_reporte)
            # auto_now_add pone "ahora": lo movemos al pasado para el demo.
            ReporteEstado.objects.filter(pk=r.pk).update(creado_en=ahora - timedelta(minutes=minutos))
        return punto
