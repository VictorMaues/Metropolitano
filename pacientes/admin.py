from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from .models import Paciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = (
        'data_agendamento',
        'numero_registro',
        'nome',
        'colored_risco',
        'especialidade_primeiro_atendimento',
        'hora_primeiro_atendimento',
        'status_especialidades_pendentes',
        'status_exames_pendentes',
        'status_procedimentos_pendentes',
        'status_enfermagem_pendentes',
        'status_solicitacoes_pendentes',

    )
    #################################################################################################################
    def status_especialidades_pendentes(self, obj):
        return self._generate_status_html(obj.especialidades_pendentes, obj.especialidades_concluidas)
    status_especialidades_pendentes.short_description = 'Status Especialidades'

    def status_exames_pendentes(self, obj):
        return self._generate_status_html(obj.exames_pendentes, obj.exames_concluidos)
    status_exames_pendentes.short_description = 'Status Exames'

    def status_procedimentos_pendentes(self, obj):
        return self._generate_status_html(obj.procedimentos_pendentes, obj.procedimentos_concluidos)
    status_procedimentos_pendentes.short_description = 'Status Procedimentos'

    def status_enfermagem_pendentes(self, obj):
        return self._generate_status_html(obj.enfermagem_pendentes, obj.enfermagem_concluidos)
    status_enfermagem_pendentes.short_description = 'Status Enfermagem'

    def status_solicitacoes_pendentes(self, obj):
        return self._generate_status_html(obj.solicitacoes_pendentes, obj.solicitacoes_concluidos)
    status_solicitacoes_pendentes.short_description = 'Status Solicitações'

    #################################################################################################
      # Função auxiliar para gerar os status ✔️ ✘ em HTML
    def _generate_status_html(self, pendentes, concluidos):
        html = ''
        for item in pendentes:
            if item in concluidos:
                html += f'<span style="color:green; font-weight:bold; margin-right:8px;">{item} ✔</span><br>'
            else:
                html += f'<span style="color:red; font-weight:bold; margin-right:8px;">{item} ✘</span><br>'
        if not html:
            return "Nenhum pendente"
        return format_html(html)

    ####################################################################################################

    list_filter = (
        'risco',
        'especialidade_primeiro_atendimento',
    )

    search_fields = (
        'nome',
        'numero_registro',
    )

    #date_hierarchy = 'data_agendamento'

    actions = ['exportar_csv']

    @admin.display(description='Classificação de Risco')
    def colored_risco(self, obj):
        colors = {
            'Vermelho': 'red',
            'Laranja': 'orange',
            'Amarelo': 'gold',
            'Verde': 'green',
            'Azul': 'blue',
            'Branco': 'gray',
        }
        color = colors.get(obj.risco, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.risco,
        )

    @admin.action(description="Exportar Pacientes Selecionados para CSV")
    def exportar_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="pacientes.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Data Entrada',
            'Registro Hospitalar',
            'Nome',
            'Classificação de Risco',
            'Especialidade FAU',
            'Hora 1º Atendimento'
        ])

        for paciente in queryset:
            writer.writerow([
                paciente.data_agendamento,
                paciente.numero_registro,
                paciente.nome,
                paciente.risco,
                paciente.get_especialidade_primeiro_atendimento_display(),
                paciente.hora_primeiro_atendimento
            ])

        return response
