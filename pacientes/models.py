import uuid

from django.db import models
from django.utils import timezone
from multiselectfield import MultiSelectField



class Paciente(models.Model):
    CLASSIFICACAO_RISCO = [
        ('Vermelho', 'Vermelho'),
        ('Laranja', 'Laranja'),
        ('Amarelo', 'Amarelo'),
        ('Verde', 'Verde'),
        ('Azul', 'Azul'),
        ('Branco', 'Branco'),
    ]

    ESPECIALIDADES = [
        ('CG', 'Clínica Geral'),
        ('NCR', 'Neurocirurgia'),
        ('TM', 'Traumatologia'),
        ('BMF', 'Bucomaxilofacial'),
        ('CV', 'Cirurgia Vascular'),
        ('PED', 'Pediatria'),
        ('INT', 'Internação'),
        ('OUT', 'Outros'),
    ]
    EXAMES = [
        ('RX', 'Raio-X'),
        ('TC', 'Tomografia Computadorizada'),
        ('LAB', 'Laboratório'),
    ]
    PROCEDIMENTOS = [
        ('SWAB', 'SWAB'),
        ('ECG', 'ECG'),
    ]

    ENFERMAGEM = [
        ('ADM', 'Administração de Medicamentos'),
        ('SAE', 'SAE - Sistematização da Assistência de Enfermagem'),
    ]

    SOLICITACOES = [
        ('BC', 'Boletim de Comunicação'),
    ]

    data_agendamento = models.DateTimeField('Data e Hora da Entrada', default=timezone.now)
    numero_registro = models.CharField('RH (Registro Hospitalar)', max_length=20, unique=True) #ver com o admin quantos caracteres são necessários para esse campo.
    nome = models.CharField('Nome', max_length=100)
    risco = models.CharField('Classificação de Risco', max_length=10, choices=CLASSIFICACAO_RISCO)

    especialidade_primeiro_atendimento = models.CharField(
        'Especialidade FAU',
        max_length=10,
        choices=ESPECIALIDADES,
        blank=True,
        null=True
    )
    hora_primeiro_atendimento = models.TimeField('Hora do 1º Atendimento na FAU', blank=True, null=True)

    especialidades_pendentes = MultiSelectField(
        'Especialidades Pós 1º Atendimento',
        choices=ESPECIALIDADES,
        blank=True,
    )

    especialidades_concluidas = MultiSelectField(
        'Especialidades Concluídas',
        choices=ESPECIALIDADES,
        blank=True,
    )
    exames_pendentes = MultiSelectField(
        'Exames Pendentes',
        choices=EXAMES,
        blank=True,
    )
    exames_concluidos = MultiSelectField(
        'Exames Concluídos',
        choices=EXAMES,
        blank=True,
    )
    procedimentos_pendentes = MultiSelectField(
        'Procedimentos Solicitados',
        choices=PROCEDIMENTOS,
        blank=True,
    )

    procedimentos_concluidos = MultiSelectField(
        'Procedimentos Concluídos',
        choices=PROCEDIMENTOS,
        blank=True,
    )

    enfermagem_pendentes = MultiSelectField(
        'Enfermagem Solicitados',
        choices=ENFERMAGEM,
        blank=True,
    )

    enfermagem_concluidos = MultiSelectField(
        'Enfermagem Concluídos',
        choices=ENFERMAGEM,
        blank=True,
    )

    solicitacoes_pendentes = MultiSelectField(
        'Solicitações Pendentes',
        choices=SOLICITACOES,
        blank=True,
    )

    solicitacoes_concluidos = MultiSelectField(
        'Solicitações Concluídas',
        choices=SOLICITACOES,
        blank=True,
    )    
    def __str__(self):
        return f'{self.nome} ({self.numero_registro})'

class Senha_de_atendimento(models.Model):
    """Senha emitida no totem e chamada pelo operador no painel de TV.

    Portado do projeto Painel-de-senhas (Node.js), agora persistido no banco.
    """

    STATUS_CHOICES = [
        ('AGUARDANDO', 'Aguardando'),
        ('ATENDENDO', 'Atendendo'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]

    # Serviços oferecidos no totem. Para adicionar/alterar um serviço, edite
    # apenas esta lista e PREFIXO_SERVICO (a letra inicial do código da senha).
    SERVICOS = [
        ('RECEPCAO', 'Recepção e Cadastro'),
        ('EXAMES', 'Exames e Resultados'),
        ('INFORMACOES', 'Informações e Visitas'),
    ]
    PREFIXO_SERVICO = {
        'RECEPCAO': 'R',
        'EXAMES': 'E',
        'INFORMACOES': 'I',
    }

    PRIORIDADES = [
        ('NORMAL', 'Comum'),
        ('PREFERENCIAL', 'Preferencial'),
        ('SUPER', 'Superprioridade'),
    ]
    PREFIXO_PRIORIDADE = {
        'NORMAL': 'N',
        'PREFERENCIAL': 'P',
        'SUPER': 'S',
    }

    # Ordem de chamada do botão "Próximo": 2 superprioridades, 2 preferenciais,
    # 1 comum (S, S, P, P, C) — mesma regra do projeto original.
    CICLO_CHAMADA = ['SUPER', 'SUPER', 'PREFERENCIAL', 'PREFERENCIAL', 'NORMAL']

    servico = models.CharField('Serviço', max_length=20, choices=SERVICOS, default='RECEPCAO')
    prioridade = models.CharField('Prioridade', max_length=20, choices=PRIORIDADES, default='NORMAL')
    sequencia = models.PositiveIntegerField('Sequência do dia', default=0)
    numero = models.CharField('Senha', max_length=10)
    guiche = models.CharField('Guichê', max_length=10, blank=True, default='')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="AGUARDANDO")
    data_emissao = models.DateField('Data de emissão', default=timezone.localdate, db_index=True)
    criando_em = models.DateTimeField('Emitida em', default=timezone.now)
    chamado_em = models.DateTimeField('Primeira chamada em', blank=True, null=True)
    ultima_chamada_em = models.DateTimeField('Última chamada em', blank=True, null=True)
    finalizado_em = models.DateTimeField('Finalizada em', blank=True, null=True)
    posicao_ciclo = models.PositiveSmallIntegerField(blank=True, null=True, editable=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        verbose_name = 'Senha de Atendimento'
        verbose_name_plural = 'Senhas de Atendimento'
        ordering = ['-criando_em']
        constraints = [
            models.UniqueConstraint(
                fields=['data_emissao', 'servico', 'prioridade', 'sequencia'],
                name='senha_unica_por_dia',
            ),
        ]

    def __str__(self):
        return f"Senha {self.numero} - {self.get_status_display()}"

