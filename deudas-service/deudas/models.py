from django.db import models
from django.db.models import Sum

ESTADO_CHOICES = [
    ('Normal', 'Normal'),
    ('Pre-Juridico', 'Pre-Jurídico'),
    ('Juridico', 'Jurídico'),
    ('Acuerdo', 'Acuerdo'),
]


class Cargo(models.Model):
    conjunto_id = models.IntegerField()
    apartamento_id = models.IntegerField()
    periodo = models.DateField()
    concepto = models.CharField(max_length=200, default='Cuota administración')
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Apto {self.apartamento_id} - {self.periodo}"

    class Meta:
        ordering = ['-periodo']

class EstadoApartamento(models.Model):
    conjunto_id = models.IntegerField()
    apartamento_id = models.IntegerField(unique=True)
    estado_gestion = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Normal')
    total_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notas = models.TextField(blank=True, null=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Apto {self.apartamento_id} - {self.estado_gestion}"

    def saldo(self):
        total_cargos = Cargo.objects.filter(
            apartamento_id=self.apartamento_id
        ).aggregate(t=Sum('monto'))['t'] or 0
        return total_cargos - self.total_pagado

    def actualizar_estado(self):
        from django.utils import timezone

        saldo = self.saldo()

        if saldo <= 0:
            self.estado_gestion = 'Normal'
            self.save()
            return

        if self.estado_gestion == 'Acuerdo':
            return

        cargo_antiguo = Cargo.objects.filter(
            apartamento_id=self.apartamento_id
        ).order_by('periodo').first()

        if not cargo_antiguo:
            return

        hoy = timezone.now().date()
        meses = (hoy.year - cargo_antiguo.periodo.year) * 12 + (hoy.month - cargo_antiguo.periodo.month)

        if meses >= 6:
            nuevo_estado = 'Juridico'
        elif meses >= 3:
            nuevo_estado = 'Pre-Juridico'
        else:
            nuevo_estado = 'Normal'

        if self.estado_gestion != nuevo_estado:
            self.estado_gestion = nuevo_estado
            self.save()

    class Meta:
        ordering = ['apartamento_id']