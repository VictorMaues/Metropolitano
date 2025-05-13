import csv
from django.contrib import admin
from .models import Paciente, AtendimentoSolicitado, ExameSolicitado

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'idade', 'leito', 'risco', 'liberado_para_alta', 'data_nascimento', 'cpf',
        'description', 'data_agendamento', 'numero_registro',
        'especialidade_primeiro_atendimento', 'hora_primeiro_atendimento',
        'bloco_cirurgico_solicitado', 'leito_solicitado', 'hora_solicitacao'
    )
    list_filter = (
        'risco', 'liberado_para_alta', 'especialidade_primeiro_atendimento',
        'bloco_cirurgico_solicitado', 'leito_solicitado'
    )
    search_fields = (
        'nome', 'leito', 'cpf', 'numero_registro',
        'especialidade_primeiro_atendimento'
    )
    filter_horizontal = ('atendimentos_solicitados', 'exames_solicitados')

# Registra os modelos auxiliares para acesso pelo admin
@admin.register(AtendimentoSolicitado)
class AtendimentoSolicitadoAdmin(admin.ModelAdmin):
    list_display = ('get_nome', 'get_numero_registro', 'tipo', 'efetuado')
    list_filter = ('tipo', 'efetuado')
    search_fields = ('tipo', 'paciente__nome', 'paciente__numero_registro')

    @admin.display(description='Nome do Paciente')
    def get_nome(self, obj):
        return obj.paciente.nome if obj.paciente else '(sem paciente)'

    @admin.display(description='Nº Registro')
    def get_numero_registro(self, obj):
        return obj.paciente.numero_registro if obj.paciente else '(sem registro)'


@admin.register(ExameSolicitado)
class ExameSolicitadoAdmin(admin.ModelAdmin):
    list_display = ('get_nome', 'get_numero_registro', 'tipo', 'efetuado')
    list_filter = ('tipo', 'efetuado')
    search_fields = ('tipo', 'paciente__nome', 'paciente__numero_registro')

    @admin.display(description='Nome do Paciente')
    def get_nome(self, obj):
        return obj.paciente.nome if obj.paciente else '(sem paciente)'

    @admin.display(description='Nº Registro')
    def get_numero_registro(self, obj):
        return obj.paciente.numero_registro if obj.paciente else '(sem registro)'
