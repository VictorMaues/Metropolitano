import uuid

import django.utils.timezone
from django.db import migrations, models


def preencher_registros_existentes(apps, schema_editor):
    """Garante token e sequência únicos para senhas criadas antes desta migração."""
    Senha = apps.get_model('pacientes', 'Senha_de_atendimento')
    for senha in Senha.objects.all():
        senha.token = uuid.uuid4()
        senha.sequencia = senha.pk
        senha.data_emissao = django.utils.timezone.localtime(senha.criando_em).date()
        senha.save(update_fields=['token', 'sequencia', 'data_emissao'])


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0009_senha_de_atendimento_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='senha_de_atendimento',
            options={
                'ordering': ['-criando_em'],
                'verbose_name': 'Senha de Atendimento',
                'verbose_name_plural': 'Senhas de Atendimento',
            },
        ),
        migrations.AddField(
            model_name='senha_de_atendimento',
            name='servico',
            field=models.CharField(choices=[('RECEPCAO', 'Recepção e Cadastro'), ('EXAMES', 'Exames e Resultados'), ('INFORMACOES', 'Informações e Visitas')], default='RECEPCAO', max_length=20, verbose_name='Serviço'),
        ),
        migrations.AddField(
            model_name='senha_de_atendimento',
            name='prioridade',
            field=models.CharField(choices=[('NORMAL', 'Comum'), ('PREFERENCIAL', 'Preferencial'), ('SUPER', 'Superprioridade')], default='NORMAL', max_length=20, verbose_name='Prioridade'),
        ),
        migrations.AddField(
            model_name='senha_de_atendimento',
            name='sequencia',
            field=models.PositiveIntegerField(default=0, verbose_name='Sequência do dia'),
        ),
        migrations.AddField(
            model_name='senha_de_atendimento',
            name='data_emissao',
            field=models.DateField(db_index=True, default=django.utils.timezone.localdate, verbose_name='Data de emissão'),
        ),
        migrations.AddField(
            model_name='senha_de_atendimento',
            name='ultima_chamada_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Última chamada em'),
        ),
        migrations.AddField(
            model_name='senha_de_atendimento',
            name='finalizado_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Finalizada em'),
        ),
        migrations.AddField(
            model_name='senha_de_atendimento',
            name='posicao_ciclo',
            field=models.PositiveSmallIntegerField(blank=True, editable=False, null=True),
        ),
        # Token: adicionado como nulo, preenchido e só então tornado único.
        migrations.AddField(
            model_name='senha_de_atendimento',
            name='token',
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(preencher_registros_existentes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='senha_de_atendimento',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='senha_de_atendimento',
            name='numero',
            field=models.CharField(max_length=10, verbose_name='Senha'),
        ),
        migrations.AlterField(
            model_name='senha_de_atendimento',
            name='guiche',
            field=models.CharField(blank=True, default='', max_length=10, verbose_name='Guichê'),
        ),
        migrations.AlterField(
            model_name='senha_de_atendimento',
            name='status',
            field=models.CharField(choices=[('AGUARDANDO', 'Aguardando'), ('ATENDENDO', 'Atendendo'), ('CONCLUIDO', 'Concluído'), ('CANCELADO', 'Cancelado')], default='AGUARDANDO', max_length=10),
        ),
        migrations.AlterField(
            model_name='senha_de_atendimento',
            name='criando_em',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Emitida em'),
        ),
        migrations.AlterField(
            model_name='senha_de_atendimento',
            name='chamado_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Primeira chamada em'),
        ),
        migrations.AddConstraint(
            model_name='senha_de_atendimento',
            constraint=models.UniqueConstraint(fields=('data_emissao', 'servico', 'prioridade', 'sequencia'), name='senha_unica_por_dia'),
        ),
    ]

