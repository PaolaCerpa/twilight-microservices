from decimal import Decimal, InvalidOperation

from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import Cargo, EstadoApartamento, PagoAplicado
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


def _leer_pago(request):
    """Valida pago_id y monto del body. Devuelve (pago_id, monto, error_response)."""
    pago_id = request.data.get('pago_id')
    monto_crudo = request.data.get('monto')

    if pago_id is None or monto_crudo is None:
        return None, None, Response(
            {'error': 'Los campos "pago_id" y "monto" son requeridos.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        monto = Decimal(str(monto_crudo))
        pago_id = int(pago_id)
    except (InvalidOperation, ValueError):
        return None, None, Response(
            {'error': 'pago_id o monto con formato inválido.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if monto <= 0:
        return None, None, Response(
            {'error': 'El monto debe ser mayor a cero.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    return pago_id, monto, None


class ActualizarDeudaView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, apartamento_id):
        pago_id, monto, error = _leer_pago(request)
        if error:
            return error

        try:
            with transaction.atomic():
                estado = EstadoApartamento.objects.select_for_update().get(
                    apartamento_id=apartamento_id
                )
                # Idempotencia: pago_id es único, así que un aviso repetido
                # no se vuelve a sumar.
                _, creado = PagoAplicado.objects.get_or_create(
                    pago_id=pago_id,
                    defaults={'apartamento_id': apartamento_id, 'monto': monto}
                )
                if creado:
                    estado.total_pagado += monto
                    estado.save()
        except EstadoApartamento.DoesNotExist:
            return Response(
                {'error': 'Este apartamento no tiene registros de deudas'},
                status=status.HTTP_404_NOT_FOUND
            )

        estado.actualizar_estado()
        return Response(EstadoApartamentoSerializer(estado).data)


class RevertirDeudaView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, apartamento_id):
        pago_id, _, error = _leer_pago(request)
        if error:
            return error

        try:
            with transaction.atomic():
                estado = EstadoApartamento.objects.select_for_update().get(
                    apartamento_id=apartamento_id
                )
                aplicado = PagoAplicado.objects.select_for_update().get(
                    pago_id=pago_id, apartamento_id=apartamento_id
                )
                if not aplicado.revertido:
                    # Se resta el monto que guardamos al aplicar, no el que llega
                    # en la petición: así no se puede revertir una cifra distinta.
                    estado.total_pagado -= aplicado.monto
                    estado.save()
                    aplicado.revertido = True
                    aplicado.save()
        except (EstadoApartamento.DoesNotExist, PagoAplicado.DoesNotExist):
            return Response(
                {'error': 'No existe un pago aplicado con ese pago_id para este apartamento.'},
                status=status.HTTP_404_NOT_FOUND
            )

        estado.actualizar_estado()
        return Response(EstadoApartamentoSerializer(estado).data)