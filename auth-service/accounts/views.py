import jwt
from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import Apartamento
from .serializers import ApartamentoSerializer, LoginSerializer


def generar_token(apartamento):
    payload = {
        'apartamento_id': apartamento.id,
        'bloque': apartamento.bloque,
        'apto': apartamento.apto,
        'exp': datetime.now(dt_timezone.utc) + timedelta(hours=24),
        'iat': datetime.now(dt_timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conjunto = serializer.validated_data['conjunto']
        bloque = serializer.validated_data['bloque']
        apto = serializer.validated_data['apto']
        password = serializer.validated_data['password']

        try:
            apartamento = Apartamento.objects.get(
                conjunto_id=conjunto, bloque=bloque, apto=apto, activo=True
            )
        except Apartamento.DoesNotExist:
            apartamento = None

        if apartamento is None or not apartamento.check_password(password):
            return Response(
                {'error': 'Credenciales incorrectas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = generar_token(apartamento)

        return Response({
            'token': token,
            'apartamento': ApartamentoSerializer(apartamento).data
        })


class ValidateTokenView(APIView):
        permission_classes = [AllowAny]

        def get(self, request):
            auth_header = request.headers.get('Authorization', '')

            if not auth_header.startswith('Bearer '):
                return Response(
                    {'valid': False, 'error': 'Token no porporcionado'},
                    status=status.HTTP_401_UNAUTHORIZED)

            token = auth_header.split(' ')[1]

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return Response({'valid': False, 'error': 'Token expirado'},
                                status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({'valid': False, 'error': 'Token inválido'},
                                status=status.HTTP_401_UNAUTHORIZED)

            return Response({'valid': True, 'payload': payload})


class ApartamentoDetailView(APIView):
        permission_classes = [AllowAny]

        def get(self, request, apartamento_id):
            try:
                apartamento = Apartamento.objects.get(id=apartamento_id)
            except Apartamento.DoesNotExist:
                return Response({'error': 'Apartamento no encontrado.'},
                                status=status.HTTP_404_NOT_FOUND)

            return Response(ApartamentoSerializer(apartamento).data)