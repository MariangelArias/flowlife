from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def crear_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    vio_scratch = models.BooleanField(default=False)

    last_scratch_date = models.DateField(null=True, blank=True)

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Actividad(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PROGRESO', 'En progreso'),
        ('COMPLETADO', 'Completado'),
    ]

    TIPOS = [
        ('ESTUDIO', 'Estudio'),
        ('HABITO', 'Hábito'),
        ('TRABAJO', 'Trabajo'),
        ('EVENTO', 'Evento'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    tipo = models.CharField(max_length=20, choices=TIPOS)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    fecha = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.titulo


# models.py
class DailyMood(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()

    # carga del día (1-5 estrellas)
    stress_level = models.IntegerField(default=1)

    # opcional: estado emocional
    mood = models.CharField(max_length=30, null=True, blank=True)

    # métricas calculadas
    tasks_done = models.IntegerField(default=0)
    tasks_total = models.IntegerField(default=0)


class ActividadProgreso(models.Model):
    actividad = models.OneToOneField(Actividad, on_delete=models.CASCADE, related_name="progreso_privado")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    progreso = models.PositiveSmallIntegerField(default=0)
    nota = models.TextField(blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.actividad.titulo} - {self.progreso}%"