from django.urls import path
from .views import CrearCargoView, DeudaActualView, HistorialDeudaView, ActualizarDeudaView, RevertirDeudaView

urlpatterns = [
    path('cargos/', CrearCargoView.as_view(), name='crear-cargo'),
    path('<int:apartamento_id>/', DeudaActualView.as_view(), name='deuda-actual'),
    path('<int:apartamento_id>/historial/', HistorialDeudaView.as_view(), name='historial-deuda'),
    path('<int:apartamento_id>/actualizar/', ActualizarDeudaView.as_view(), name='actualizar-deuda'),
    path('<int:apartamento_id>/revertir/', RevertirDeudaView.as_view(), name='revertir-deuda'),
]