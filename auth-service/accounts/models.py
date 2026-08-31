from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Apartamento(models.Model):
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
        unique_together = ('bloque', 'apto')
        ordering = ['bloque', 'apto']