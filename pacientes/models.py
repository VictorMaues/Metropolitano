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
