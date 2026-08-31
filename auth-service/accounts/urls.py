from django.urls import path
from  .views import LoginView, ValidateTokenView, ApartamentoDetailView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('validate/', ValidateTokenView.as_view(), name='validate'),
    path('apartamento/<int:apartamento_id>/', ApartamentoDetailView.as_view(), name='apartamento-detail'),
]