from rest_framework import serializers
from .models import Cargo, EstadoApartamento

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['id', 'conjunto_id','apartamento_id', 'periodo', 'concepto', 'monto']


class EstadoApartamentoSerializer(serializers.ModelSerializer):
    saldo = serializers.SerializerMethodField()

    class Meta:
        model = EstadoApartamento
        fields = ['conjunto_id', 'apartamento_id', 'estado_gestion', 'total_pagado', 'saldo', 'notas', 'actualizado_en']

    def get_saldo(self, obj):
        return obj.saldo()