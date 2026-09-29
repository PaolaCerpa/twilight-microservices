from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import Cargo, EstadoApartamento
from .serializers import CargoSerializer, EstadoApartamentoSerializer
from .services import obtener_apartamento

class CrearCargoView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        apartamento_id = request.data.get('apartamento_id')
        periodo = request.data.get('periodo')
        monto = request.data.get('monto')
        concepto = request.data.get('concepto', 'Cuota administración')

        if not all([apartamento_id, periodo, monto]):
            return Response(
                {'error': 'apartamento_id, periodo y monto son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        apartamento = obtener_apartamento(apartamento_id)
        if apartamento is None:
            return Response(
                {'error': 'El apartamento no existe o el servicio de autenticacíon no responde.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        conjunto_id = apartamento['conjunto']

        cargo = Cargo.objects.create(
            conjunto_id=conjunto_id,
            apartamento_id=apartamento_id,
            periodo=periodo,
            concepto=concepto,
            monto=Decimal(str(monto))
        )

        estado, creado = EstadoApartamento.objects.get_or_create(
            apartamento_id=apartamento_id,
            defaults={'conjunto_id': conjunto_id}
        )
        estado.actualizar_estado()

        return Response(CargoSerializer(cargo).data, status=status.HTTP_201_CREATED)

class DeudaActualView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, apartamento_id):
        try:
            estado = EstadoApartamento.objects.get(apartamento_id=apartamento_id)
        except EstadoApartamento.DoesNotExist:
            return Response(
                {'error': 'Este apartamento no tiene registro de deudas aún.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(EstadoApartamentoSerializer(estado).data)

class HistorialDeudaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, apartamento_id):
        cargos = Cargo.objects.filter(apartamento_id=apartamento_id)
        return Response(CargoSerializer(cargos, many=True).data)

class ActualizarDeudaView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, apartamento_id):
        monto_pagado = request.data.get('monto')

        if monto_pagado is None:
            return Response(
                {'error': 'El campo "Monto" es requerido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            estado = EstadoApartamento.objects.get(apartamento_id=apartamento_id)
        except EstadoApartamento.DoesNotExist:
            return Response(
                {'error': 'Este apartamento no tiene registros de deudas'},
                status=status.HTTP_404_NOT_FOUND
            )

        estado.total_pagado += Decimal(str(monto_pagado))
        estado.save()
        estado.actualizar_estado()

        return Response(EstadoApartamentoSerializer(estado).data)    