from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Usuario


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "password"]

    def validate_email(self, valor):
        valor = valor.lower().strip()
        if Usuario.objects.filter(email=valor).exists():
            raise serializers.ValidationError("Ya existe una cuenta con ese email.")
        return valor

    def validate(self, datos):
        # Valida la contraseña con las reglas de settings (longitud, comunes...).
        validate_password(
            datos["password"], user=Usuario(**{k: v for k, v in datos.items() if k != "password"})
        )
        return datos

    def create(self, datos):
        return Usuario.objects.create_user(**datos)


class UsuarioSerializer(serializers.ModelSerializer):
    es_moderador = serializers.BooleanField(read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "rol", "reputacion", "es_moderador", "creado_en"]
        read_only_fields = fields
