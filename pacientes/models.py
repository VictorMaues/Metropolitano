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

    data_agendamento = models.DateField(null=True, blank=True)
    numero_registro = models.CharField(max_length=50, default='REG000')

    # adicionar outras especialidades conforme necessário

    ESPECIALIDADES = [
        ('clinica_geral', 'Clínica Geral'),
        ('cardiologia', 'Cardiologia'),
        ('neurologia', 'Neurologia'),
        ('ortopedia', 'Ortopedia'),
        ('pediatria', 'Pediatria'),
        
    ]

    especialidade_primeiro_atendimento = models.CharField(max_length=50, choices=ESPECIALIDADES, null=True, blank=True)
    hora_primeiro_atendimento = models.TimeField(null=True, blank=True)

    # Avaliações solicitadas
    TIPOS_ATENDIMENTO = [
        ('psiquiatria', 'Psiquiatria'),
        ('fisioterapia', 'Fisioterapia'),
        ('nutricao', 'Nutrição'),
        ('fonoaudiologia', 'Fonoaudiologia'),
        # adicione mais se quiser
    ]
    atendimentos_solicitados = models.ManyToManyField(
        'AtendimentoSolicitado',
        blank=True,
        related_name='pacientes'
    )

    # Exames
    EXAMES = [
        ('sangue', 'Exame de Sangue'),
        ('raio_x', 'Raio-X'),
        ('tomografia', 'Tomografia'),
        ('urina', 'Exame de Urina'),
        # adicione mais conforme necessário
    ]
    exames_solicitados = models.ManyToManyField(
        'ExameSolicitado',
        blank=True,
        related_name='pacientes'
    )

    # Solicitações diversas
    bloco_cirurgico_solicitado = models.BooleanField(default=False)
    leito_solicitado = models.BooleanField(default=False)
    hora_solicitacao = models.TimeField(null=True, blank=True)
    conduta_paciente = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Paciente'

    def __str__(self):
        return self.nome
    
    # Modelos auxiliares para registrar status de atendimento/exame
class AtendimentoSolicitado(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=Paciente.TIPOS_ATENDIMENTO)
    efetuado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_tipo_display()} - {'Efetuado' if self.efetuado else 'Pendente'}"

class ExameSolicitado(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=Paciente.EXAMES)
    efetuado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_tipo_display()} - {'Efetuado' if self.efetuado else 'Pendente'}"
