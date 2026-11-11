from rest_framework import serializers
from .models import Apartamento

class ApartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartamento
        fields = ['id', 'conjunto', 'bloque', 'apto', 'propietario', 'telefono', 'email', 'activo']

class LoginSerializer(serializers.Serializer):
    conjunto = serializers.IntegerField()
    bloque = serializers.IntegerField()
    apto = serializers.CharField()
    password = serializers.CharField(write_only=True)