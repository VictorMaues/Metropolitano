from django.db import models
import datetime

class Paciente(models.Model):
    nome = models.CharField(max_length=100)
    idade = models.IntegerField()
    data_nascimento = models.DateField(default=datetime.date(2000, 1, 1))
    leito = models.CharField(max_length=10)
    cpf = models.CharField(max_length=14, default='000.000.000-00')    
    risco = models.CharField(max_length=20, choices=[
        ('baixo', 'Baixo'),
        ('medio', 'Médio'),
        ('alto', 'Alto'),
    ])
    description = models.TextField(null=True, blank=True, verbose_name='Descrição')
    liberado_para_alta = models.BooleanField(default=False)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Paciente'

    def __str__(self):
        return self.nome
