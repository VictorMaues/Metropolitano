import csv
from django.contrib import admin
from .models import Paciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'idade', 'leito', 'risco', 'liberado_para_alta', 'data_nascimento', 'cpf', 'description')
    list_filter = ('risco', 'liberado_para_alta')
    search_fields = ('nome', 'leito', 'cpf', 'liberado_para_alta')
    list_filter = ('liberado_para_alta',)
