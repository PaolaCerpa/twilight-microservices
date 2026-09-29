from django.contrib import admin
from .models import Conjunto, Apartamento

@admin.register(Conjunto)
class ConjuntoAdemin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'activo')
    search_fields = ('nombre', 'ciudad')

@admin.register(Apartamento)
class ApartamentoAdmin(admin.ModelAdmin):
    list_display = ('bloque', 'apto', 'conjunto', 'propietario', 'email', 'activo')
    search_fields = ('bloque', 'apto', 'propietario')

    def save_model(self, request, obj, form, change):
        if not obj.password.startswith('pbkdf2_'):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)