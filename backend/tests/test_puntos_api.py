"""API de puntos: mapa, filtros, alta, permisos y privacidad."""

import pytest
from django.contrib.gis.geos import Point

from apps.puntos.models import EstadoPublicacion, PuntoCarga

from .conftest import CENTRO

URL = "/api/puntos/"
pytestmark = pytest.mark.django_db


def nombres(respuesta):
    return {p["nombre"] for p in respuesta.json()["results"]}


def datos_alta(**extra):
    datos = {
        "nombre": "Mi cafetería",
        "tipo": "negocio",
        "lat": CENTRO[0],
        "lng": CENTRO[1],
        "numero_tomas": 3,
        "acceso": "con_consumo",
        "horarios": [{"dia_semana": 0, "hora_inicio": "09:00", "hora_fin": "18:00"}],
    }
    datos.update(extra)
    return datos


# --- Mapa y filtros -------------------------------------------------------------
def test_el_mapa_solo_muestra_puntos_activos(api, crear_punto):
    crear_punto(nombre="Activo")
    crear_punto(nombre="Pendiente", estado=EstadoPublicacion.PENDIENTE)
    crear_punto(nombre="Oculto", estado=EstadoPublicacion.OCULTO)
    crear_punto(nombre="Pausado", estado=EstadoPublicacion.PAUSADO)
    assert nombres(api.get(URL)) == {"Activo"}


def test_busqueda_por_radio_usa_postgis(api, crear_punto):
    crear_punto(nombre="Cerca")  # en el centro
    crear_punto(nombre="A 3 km", lat=CENTRO[0] + 0.027)  # ~3 km al norte
    respuesta = api.get(URL, {"lat": CENTRO[0], "lng": CENTRO[1], "radio_km": 1})
    assert nombres(respuesta) == {"Cerca"}
    respuesta = api.get(URL, {"lat": CENTRO[0], "lng": CENTRO[1], "radio_km": 5})
    assert nombres(respuesta) == {"Cerca", "A 3 km"}


def test_filtro_con_energia_ahora(api, crear_punto, reportar):
    reportar(crear_punto(nombre="Con luz"), "con_energia", hace_min=10)
    reportar(crear_punto(nombre="Sin luz"), "sin_energia", hace_min=10)
    reportar(crear_punto(nombre="Viejo"), "con_energia", hace_min=300)
    assert nombres(api.get(URL, {"con_energia": "1"})) == {"Con luz"}


def test_filtros_por_tipo_y_tomas(api, crear_punto):
    crear_punto(nombre="Negocio grande", tipo="negocio", numero_tomas=6)
    crear_punto(nombre="Negocio pequeño", tipo="negocio", numero_tomas=1)
    crear_punto(nombre="Parque", tipo="espacio_publico", numero_tomas=8)
    assert nombres(api.get(URL, {"tipo": "negocio", "min_tomas": 2})) == {"Negocio grande"}
    assert nombres(api.get(URL, {"tipo": "negocio,espacio_publico", "min_tomas": 5})) == {
        "Negocio grande",
        "Parque",
    }


def test_parametros_invalidos_devuelven_400(api):
    assert api.get(URL, {"lat": "abc", "lng": 1}).status_code == 400


# --- Alta de puntos (flujo 2) ---------------------------------------------------------
def test_anonimo_no_puede_crear_puntos(api):
    assert api.post(URL, datos_alta(), format="json").status_code == 401


def test_usuario_nuevo_crea_punto_pendiente_de_revision(api_de, usuario):
    respuesta = api_de(usuario).post(URL, datos_alta(), format="json")
    assert respuesta.status_code == 201, respuesta.json()
    assert respuesta.json()["estado_publicacion"] == "pendiente"
    punto = PuntoCarga.objects.get()
    assert punto.horarios.count() == 1
    assert punto.creado_por == usuario


def test_usuario_de_confianza_publica_directo(api_de, crear_usuario):
    confiable = crear_usuario("confiable@test.cu", reputacion=50)
    respuesta = api_de(confiable).post(URL, datos_alta(), format="json")
    assert respuesta.json()["estado_publicacion"] == "activo"


def test_posible_duplicado_va_a_revision_aunque_sea_de_confianza(api_de, crear_usuario, crear_punto):
    crear_punto(nombre="Cafetería El Portal")
    confiable = crear_usuario("confiable@test.cu", reputacion=50)
    respuesta = api_de(confiable).post(URL, datos_alta(nombre="Cafeteria el portal"), format="json")
    cuerpo = respuesta.json()
    assert cuerpo["estado_publicacion"] == "pendiente"
    assert "duplicado" in cuerpo["nota_moderacion"]


def test_texto_con_enlaces_va_a_revision(api_de, crear_usuario):
    confiable = crear_usuario("confiable@test.cu", reputacion=50)
    datos = datos_alta(descripcion="Gana dinero con cripto en www.estafa.com")
    assert api_de(confiable).post(URL, datos, format="json").json()["estado_publicacion"] == "pendiente"


@pytest.mark.parametrize(
    "campo,valor", [("lat", 120), ("numero_tomas", 0), ("nombre", "ab"), ("tipo", "nave_espacial")]
)
def test_validacion_de_entrada(api_de, usuario, campo, valor):
    respuesta = api_de(usuario).post(URL, datos_alta(**{campo: valor}), format="json")
    assert respuesta.status_code == 400
    assert campo in respuesta.json()


# --- Permisos por objeto ---------------------------------------------------------------
def test_solo_el_dueno_edita_su_punto(api_de, crear_punto, crear_usuario):
    punto = crear_punto()
    otro = crear_usuario("otro@test.cu")
    respuesta = api_de(otro).patch(f"{URL}{punto.pk}/", {"nombre": "Hackeado"}, format="json")
    assert respuesta.status_code == 403


def test_el_dueno_puede_editar_y_vuelve_a_revision(api_de, crear_punto, usuario):
    punto = crear_punto()
    respuesta = api_de(usuario).patch(f"{URL}{punto.pk}/", {"numero_tomas": 5}, format="json")
    assert respuesta.status_code == 200
    assert respuesta.json()["numero_tomas"] == 5
    assert respuesta.json()["estado_publicacion"] == "pendiente"


def test_el_anfitrion_puede_pausar_y_reanudar(api_de, crear_punto, usuario):
    punto = crear_punto()
    cliente = api_de(usuario)
    assert cliente.post(f"{URL}{punto.pk}/pausar/").json()["estado_publicacion"] == "pausado"
    assert cliente.post(f"{URL}{punto.pk}/pausar/").json()["estado_publicacion"] == "activo"


def test_el_anfitrion_puede_retirar_su_punto(api_de, crear_punto, usuario):
    punto = crear_punto()
    assert api_de(usuario).delete(f"{URL}{punto.pk}/").status_code == 204
    assert not PuntoCarga.objects.exists()


def test_un_moderador_no_puede_borrar_puntos_ajenos(api_de, crear_punto, moderador):
    punto = crear_punto()
    assert api_de(moderador).delete(f"{URL}{punto.pk}/").status_code == 403


def test_un_pendiente_ajeno_no_es_visible(api_de, crear_punto, crear_usuario):
    punto = crear_punto(estado=EstadoPublicacion.PENDIENTE)
    assert api_de(crear_usuario("x@test.cu")).get(f"{URL}{punto.pk}/").status_code == 404


def test_mis_puntos_incluye_pendientes_con_nota(api_de, crear_punto, usuario):
    crear_punto(estado=EstadoPublicacion.PENDIENTE, nota_moderacion="Falta el horario")
    respuesta = api_de(usuario).get(f"{URL}mios/")
    assert respuesta.json()[0]["nota_moderacion"] == "Falta el horario"


# --- Privacidad ---------------------------------------------------------------------------
def test_vivienda_muestra_ubicacion_aproximada(api, crear_punto):
    exacta = (22.40893, -79.96151)
    punto = crear_punto(tipo="vivienda", lat=exacta[0], lng=exacta[1])
    ficha = api.get(f"{URL}{punto.pk}/").json()
    assert ficha["ubicacion_aproximada"] is True
    assert (ficha["lat"], ficha["lng"]) != exacta
    assert "lat_exacta" not in ficha
    # Sigue estando cerca (misma celda de ~220 m)
    publica = Point(ficha["lng"], ficha["lat"], srid=4326)
    assert publica.distance(Point(exacta[1], exacta[0], srid=4326)) < 0.002


def test_la_rejilla_es_determinista(crear_punto):
    a = crear_punto(tipo="vivienda", lat=22.40893, lng=-79.96151)
    b = crear_punto(tipo="vivienda", lat=22.40895, lng=-79.96149)  # vecino de la misma celda
    assert a.ubicacion_publica == b.ubicacion_publica


def test_el_dueno_ve_su_ubicacion_exacta(api_de, crear_punto, usuario):
    punto = crear_punto(tipo="vivienda", lat=22.40893, lng=-79.96151)
    ficha = api_de(usuario).get(f"{URL}{punto.pk}/").json()
    assert ficha["lat_exacta"] == pytest.approx(22.40893)


def test_el_contacto_no_viaja_en_la_ficha(api, crear_punto):
    punto = crear_punto(contacto="5555-1234")
    ficha = api.get(f"{URL}{punto.pk}/").json()
    assert "contacto" not in ficha
    assert ficha["tiene_contacto"] is True


def test_contacto_bajo_solicitud_solo_para_registrados(api, api_de, crear_punto, crear_usuario):
    punto = crear_punto(contacto="5555-1234")
    assert api.post(f"{URL}{punto.pk}/contacto/").status_code == 401
    respuesta = api_de(crear_usuario("vecino@test.cu")).post(f"{URL}{punto.pk}/contacto/")
    assert respuesta.json() == {"contacto": "5555-1234"}


# --- Favoritos ---------------------------------------------------------------------------
def test_favoritos(api_de, crear_punto, usuario):
    punto = crear_punto()
    cliente = api_de(usuario)
    assert cliente.post(f"{URL}{punto.pk}/favorito/").status_code == 201
    assert cliente.post(f"{URL}{punto.pk}/favorito/").status_code == 201  # idempotente
    assert [p["id"] for p in cliente.get("/api/favoritos/").json()] == [punto.pk]
    assert cliente.get(f"{URL}{punto.pk}/").json()["es_favorito"] is True
    cliente.delete(f"{URL}{punto.pk}/favorito/")
    assert cliente.get("/api/favoritos/").json() == []
