from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Conjunto(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=300, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Apartamento(models.Model):
    conjunto = models.ForeignKey(Conjunto, on_delete=models.CASCADE, related_name='apartamentos')
    bloque = models.IntegerField()
    apto = models.CharField(max_length=10)
    propietario = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    password = models.CharField(max_length=128)
    activo = models.BooleanField(default=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.bloque} - {self.apto}"

    class Meta:
        unique_together = ('conjunto', 'bloque', 'apto')
        ordering = ['conjunto', 'bloque', 'apto']