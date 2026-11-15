"""Registro e inicio de sesión con JWT de acceso corto + refresco."""

import pytest

from apps.usuarios.models import Usuario

pytestmark = pytest.mark.django_db


def test_registro_devuelve_tokens_y_guarda_hash(api):
    datos = {"nombre": "Marta", "email": "Marta@Test.cu", "password": "UnaClaveLarga2026"}
    respuesta = api.post("/api/auth/registro/", datos)
    assert respuesta.status_code == 201
    assert {"access", "refresh", "usuario"} <= respuesta.json().keys()
    usuario = Usuario.objects.get(email="marta@test.cu")
    assert usuario.password != "UnaClaveLarga2026"
    assert usuario.password.startswith("pbkdf2_sha256$")
    assert usuario.rol == "usuario"


def test_contrasena_debil_se_rechaza(api):
    respuesta = api.post("/api/auth/registro/", {"nombre": "X", "email": "x@test.cu", "password": "12345678"})
    assert respuesta.status_code == 400


def test_email_duplicado(api, usuario):
    respuesta = api.post(
        "/api/auth/registro/", {"nombre": "Y", "email": usuario.email, "password": "UnaClaveLarga2026"}
    )
    assert respuesta.status_code == 400


def test_login_refresco_y_perfil(api, usuario):
    tokens = api.post("/api/auth/token/", {"email": usuario.email, "password": "ClaveSegura123"}).json()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert api.get("/api/auth/yo/").json()["email"] == usuario.email

    nuevo = api.post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]})
    assert nuevo.status_code == 200
    # Rotación: el refresh antiguo queda invalidado
    assert api.post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]}).status_code == 401


def test_login_incorrecto(api, usuario):
    assert api.post("/api/auth/token/", {"email": usuario.email, "password": "mala"}).status_code == 401


def test_el_rol_controla_el_acceso_al_panel(crear_usuario):
    assert not crear_usuario("a@test.cu").is_staff
    mod = crear_usuario("m@test.cu", rol="moderador")
    assert mod.is_staff and not mod.is_superuser
    admin = crear_usuario("ad@test.cu", rol="admin")
    assert admin.is_staff and admin.is_superuser
