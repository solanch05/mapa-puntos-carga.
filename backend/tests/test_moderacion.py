"""Flujo 4: moderar. Cada acción ajusta reputación y queda registrada."""

import pytest
from django.contrib.admin.models import LogEntry

from apps.moderacion import services
from apps.moderacion.models import Denuncia
from apps.puntos.models import EstadoPublicacion

pytestmark = pytest.mark.django_db


def test_aprobar_publica_suma_reputacion_y_registra(crear_punto, moderador, usuario):
    punto = crear_punto(estado=EstadoPublicacion.PENDIENTE, nota_moderacion="Posible duplicado")
    services.aprobar_punto(punto, moderador)
    punto.refresh_from_db()
    usuario.refresh_from_db()
    assert punto.estado_publicacion == "activo"
    assert punto.nota_moderacion == ""
    assert usuario.reputacion == 5
    assert LogEntry.objects.filter(user=moderador, object_id=str(punto.pk)).exists()


def test_aprobar_dos_veces_no_suma_doble(crear_punto, moderador, usuario):
    punto = crear_punto(estado=EstadoPublicacion.PENDIENTE)
    services.aprobar_punto(punto, moderador)
    services.aprobar_punto(punto, moderador)
    usuario.refresh_from_db()
    assert usuario.reputacion == 5


def test_ocultar_resta_reputacion(crear_punto, moderador, usuario):
    punto = crear_punto()
    services.ocultar_punto(punto, moderador, "Spam")
    usuario.refresh_from_db()
    assert punto.estado_publicacion == "oculto"
    assert usuario.reputacion == -5


def test_pedir_correcciones_deja_nota_para_el_autor(crear_punto, moderador):
    punto = crear_punto()
    services.pedir_correcciones(punto, moderador, "Indica el horario")
    assert punto.estado_publicacion == "pendiente"
    assert punto.nota_moderacion == "Indica el horario"


def test_denuncia_aceptada_contra_reporte_lo_invalida(crear_punto, reportar, moderador, crear_usuario):
    punto = crear_punto()
    mentiroso = crear_usuario("mentiroso@test.cu", reputacion=10)
    denunciante = crear_usuario("vecina@test.cu")
    reporte = reportar(punto, "con_energia", por=mentiroso)
    denuncia = Denuncia.objects.create(
        punto=punto, reporte=reporte, usuario=denunciante, motivo="datos_falsos"
    )

    services.resolver_denuncia(denuncia, moderador, aceptada=True)

    reporte.refresh_from_db()
    mentiroso.refresh_from_db()
    denunciante.refresh_from_db()
    assert reporte.valido is False
    assert mentiroso.reputacion == 7
    assert denunciante.reputacion == 1
    assert denuncia.estado == "resuelta" and denuncia.resuelta_por == moderador


def test_denuncia_aceptada_contra_punto_lo_oculta(crear_punto, moderador, crear_usuario):
    punto = crear_punto()
    denuncia = Denuncia.objects.create(punto=punto, usuario=crear_usuario("v@test.cu"), motivo="no_existe")
    services.resolver_denuncia(denuncia, moderador, aceptada=True)
    punto.refresh_from_db()
    assert punto.estado_publicacion == "oculto"


def test_denunciar_por_api(api_de, crear_punto, crear_usuario):
    punto = crear_punto()
    cliente = api_de(crear_usuario("v@test.cu"))
    datos = {"punto": punto.pk, "motivo": "no_existe"}
    assert cliente.post("/api/denuncias/", datos).status_code == 201
    assert cliente.post("/api/denuncias/", datos).status_code == 400  # ya hay una abierta


def test_metricas_solo_para_moderadores(api_de, usuario, moderador, crear_punto, reportar):
    reportar(crear_punto(), "con_energia", hace_min=10)
    crear_punto()
    assert api_de(usuario).get("/api/metricas/").status_code == 403
    metricas = api_de(moderador).get("/api/metricas/").json()
    assert metricas["puntos_activos"] == 2
    assert metricas["porcentaje_confirmados"] == 50.0


def test_moderador_entra_al_panel_y_usuario_normal_no(client, moderador, usuario):
    client.force_login(moderador)
    assert client.get("/admin/puntos/puntocarga/").status_code == 200
    client.force_login(usuario)
    assert client.get("/admin/puntos/puntocarga/").status_code == 302  # al login
