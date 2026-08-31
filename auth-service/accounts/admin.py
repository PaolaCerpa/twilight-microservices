from django.contrib import admin
from .models import Apartamento

@admin.register(Apartamento)
class ApartamentoAdmin(admin.ModelAdmin):
    list_display = ('bloque', 'apto', 'propietario', 'email', 'activo')
    search_fields = ('bloque', 'apto', 'propietario')

    def save_model(self, request, obj, form, change):
        if not obj.password.startswith('pbkdf2_'):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)