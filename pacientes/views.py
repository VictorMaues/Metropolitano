import json
import socket
from functools import wraps
from urllib.parse import urlparse, urlunparse

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Paciente, Senha_de_atendimento

Senha = Senha_de_atendimento


def view_bemvindo(request):
    """View que exibe a página institucional de boas-vindas."""
    return render(request, 'pacientes/BemVindo.html')


def pagina_inicial(request):
    """Painel geral de pacientes e visão geral do sistema."""
    pacientes = Paciente.objects.all()
    return render(request, 'pacientes/pagina_inicial.html', {'pacientes': pacientes})


def view_painel_tv(request):
    """View que exibe o painel de TV."""
    return render(request, 'pacientes/Painel_Tv.html')


# ---------------------------------------------------------------------------
# Dashboard de Atendimento de Pacientes (Restrito: Doutor, Enfermeira ou Adm)
# ---------------------------------------------------------------------------

def user_tem_permissao_dashboard(user):
    """
    Verifica se o usuário tem permissão para visualizar o dashboard de atendimento.
    Regra do projeto: Apenas o doutor/enfermeira vai poder visualizar (como teste, apenas adm vai ver).
    """
    if not user.is_authenticated:
        return False

    # Em teste: adm ou superusuário tem permissão total
    if user.username.lower() == 'adm' or user.is_superuser:
        return True

    # Grupos autorizados para Doutores e Enfermeiras
    grupos_autorizados = {
        'doutor', 'doutores', 'doutora', 'doutoras',
        'medico', 'médico', 'medicos', 'médicos', 'medica', 'médica',
        'enfermeira', 'enfermeiras', 'enfermeiro', 'enfermeiros',
    }
    user_grupos = {g.name.lower() for g in user.groups.all()}
    if user_grupos.intersection(grupos_autorizados):
        return True

    return False


def doutor_ou_enfermeira_required(view_func):
    """Decorator que restringe o acesso exclusivamente a Médicos, Enfermeiras ou Adm."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('admin:login')}?next={request.path}")

        if not user_tem_permissao_dashboard(request.user):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return JsonResponse({
                    'erro': 'Acesso negado. Apenas doutores, enfermeiras ou adm têm acesso ao dashboard.'
                }, status=403)
            return render(request, 'pacientes/acesso_negado.html', {'usuario': request.user}, status=403)

        return view_func(request, *args, **kwargs)

    return _wrapped


@doutor_ou_enfermeira_required
def view_dashboard_atendimento(request):
    """View principal do dashboard de atendimento (baseado no modelo Clara.care)."""
    user = request.user
    if user.username.lower() == 'adm' or user.is_superuser:
        user_role = 'Administrador'
    else:
        grupos = [g.name for g in user.groups.all()]
        user_role = ', '.join(grupos) if grupos else 'Equipe de Saúde'

    initials = (
        (user.first_name[:1] + user.last_name[:1]).upper()
        if user.first_name and user.last_name
        else user.username[:2].upper()
    )

    return render(request, 'pacientes/dashboard_atendimento.html', {
        'user_role': user_role,
        'user_initials': initials,
    })


@doutor_ou_enfermeira_required
@require_GET
def api_dashboard_pacientes(request):
    """API que alimenta a lista de pacientes e métricas do dashboard em tempo real."""
    agora = timezone.now()
    pacientes_qs = Paciente.objects.all().order_by('data_agendamento')

    pacientes_lista = []
    espera_total_minutos = 0
    total_aguardando = 0
    total_atendimento = 0

    for p in pacientes_qs:
        delta_segundos = max(0, (agora - p.data_agendamento).total_seconds())
        espera_minutos = int(delta_segundos / 60)

        # Se for do mesmo dia, mostra a espera real; se for data histórica de teste, exibe valor proporcional
        if p.data_agendamento.date() == timezone.localdate():
            espera_exibida = espera_minutos
        else:
            espera_exibida = min(espera_minutos, 120)

        if p.status == 'waiting':
            total_aguardando += 1
            espera_total_minutos += espera_exibida
        elif p.status == 'service':
            total_atendimento += 1

        chegada_local = timezone.localtime(p.data_agendamento)

        pacientes_lista.append({
            'id': p.pk,
            'nome': p.nome,
            'codigo': p.numero_registro,
            'risco': p.risco,
            'status': p.status,
            'especialidade': p.get_especialidade_primeiro_atendimento_display(),
            'chegada_hora': chegada_local.strftime('%H:%M'),
            'chegada_iso': p.data_agendamento.isoformat(),
            'espera_minutos': espera_exibida,
            'hora_primeiro_atendimento': (
                p.hora_primeiro_atendimento.strftime('%H:%M')
                if p.hora_primeiro_atendimento
                else None
            ),
        })

    espera_media = round(espera_total_minutos / total_aguardando) if total_aguardando > 0 else 0

    return JsonResponse({
        'sucesso': True,
        'metricas': {
            'aguardando': total_aguardando,
            'em_atendimento': total_atendimento,
            'espera_media_minutos': espera_media,
        },
        'pacientes': pacientes_lista,
    })


@doutor_ou_enfermeira_required
@require_POST
def api_atualizar_status_paciente(request, pk):
    """API para atualizar o status do atendimento do paciente (waiting, service, done)."""
    dados = _ler_json(request)
    novo_status = dados.get('status')
    if novo_status not in ['waiting', 'service', 'done']:
        return JsonResponse({'erro': 'Status inválido informado.'}, status=400)

    paciente = get_object_or_404(Paciente, pk=pk)
    paciente.status = novo_status
    if novo_status == 'service' and not paciente.hora_primeiro_atendimento:
        paciente.hora_primeiro_atendimento = timezone.localtime().time()
    paciente.save()

    return JsonResponse({
        'sucesso': True,
        'id': paciente.pk,
        'status': paciente.status,
        'hora_primeiro_atendimento': (
            paciente.hora_primeiro_atendimento.strftime('%H:%M')
            if paciente.hora_primeiro_atendimento
            else None
        ),
    })


def _itens_com_status(pendentes, concluidos, choices):
    """Monta a lista de itens solicitados indicando se cada um já foi concluído."""
    rotulos = dict(choices)
    pendentes = list(pendentes or [])
    concluidos = list(concluidos or [])
    itens = []
    for codigo in pendentes + [c for c in concluidos if c not in pendentes]:
        itens.append({
            'codigo': codigo,
            'rotulo': rotulos.get(codigo, codigo),
            'concluido': codigo in concluidos,
        })
    return itens


@doutor_ou_enfermeira_required
@require_GET
def api_detalhe_paciente(request, pk):
    """Ficha detalhada do paciente exibida no modal "Ver Ficha" do dashboard."""
    p = get_object_or_404(Paciente, pk=pk)
    entrada = timezone.localtime(p.data_agendamento)
    espera = int(max(0, (timezone.now() - p.data_agendamento).total_seconds()) / 60)

    grupos = [
        ('Especialidades', p.especialidades_pendentes, p.especialidades_concluidas, Paciente.ESPECIALIDADES),
        ('Exames', p.exames_pendentes, p.exames_concluidos, Paciente.EXAMES),
        ('Procedimentos', p.procedimentos_pendentes, p.procedimentos_concluidos, Paciente.PROCEDIMENTOS),
        ('Enfermagem', p.enfermagem_pendentes, p.enfermagem_concluidos, Paciente.ENFERMAGEM),
        ('Outras Solicitações', p.solicitacoes_pendentes, p.solicitacoes_concluidos, Paciente.SOLICITACOES),
    ]

    return JsonResponse({
        'id': p.pk,
        'nome': p.nome,
        'codigo': p.numero_registro,
        'risco': p.risco,
        'status': p.status,
        'status_label': p.get_status_display(),
        'entrada_data': entrada.strftime('%d/%m/%Y'),
        'entrada_hora': entrada.strftime('%H:%M'),
        'espera_minutos': espera,
        'especialidade': p.get_especialidade_primeiro_atendimento_display() or None,
        'hora_primeiro_atendimento': (
            p.hora_primeiro_atendimento.strftime('%H:%M') if p.hora_primeiro_atendimento else None
        ),
        'grupos': [
            {'titulo': titulo, 'itens': _itens_com_status(pend, conc, choices)}
            for titulo, pend, conc, choices in grupos
        ],
        'url_admin': reverse('admin:pacientes_paciente_change', args=[p.pk]),
    })


# ---------------------------------------------------------------------------
# Painel de senhas — telas
# ---------------------------------------------------------------------------

def view_portal_senhas(request):
    """Portal com os atalhos para Totem, Painel de TV e Operador."""
    return render(request, 'pacientes/index.html')


def view_totem(request):
    """Totem de autoatendimento onde o paciente emite a senha."""
    return render(request, 'pacientes/Totem.html', {
        'servicos': Senha.SERVICOS,
    })


@login_required
def view_operador(request):
    """Mesa do atendente: chama, rechama e acompanha a fila."""
    return render(request, 'pacientes/operador_senhas.html', {
        'servicos': Senha.SERVICOS,
        'guiches': range(1, 6),
    })


def view_acompanhar(request, token):
    """Página aberta pelo QR Code do ticket para acompanhar pelo celular."""
    senha = get_object_or_404(Senha, token=token)
    return render(request, 'pacientes/acompanhar.html', {'senha': senha})


# ---------------------------------------------------------------------------
# Painel de senhas — regras de negócio
# ---------------------------------------------------------------------------

def _hora(dt):
    return timezone.localtime(dt).strftime('%H:%M') if dt else None


def _serializar(senha):
    return {
        'id': senha.pk,
        'token': str(senha.token),
        'codigo': senha.numero,
        'servico': senha.servico,
        'servico_label': senha.get_servico_display(),
        'prioridade': senha.prioridade,
        'prioridade_label': senha.get_prioridade_display(),
        'status': senha.status,
        'guiche': senha.guiche,
        'criado_em': _hora(senha.criando_em),
        'chamado_em': _hora(senha.chamado_em),
        # Carimbo em microssegundos: o painel usa para detectar chamadas novas.
        'chamada_ts': int(senha.ultima_chamada_em.timestamp() * 1_000_000) if senha.ultima_chamada_em else None,
    }


def _senhas_de_hoje():
    return Senha.objects.filter(data_emissao=timezone.localdate())


def _fila_ordenada(qs):
    """Ordena a fila: superprioridade > preferencial > comum, depois por chegada."""
    peso = {'SUPER': 0, 'PREFERENCIAL': 1, 'NORMAL': 2}
    return sorted(qs, key=lambda s: (peso.get(s.prioridade, 3), s.criando_em, s.pk))


def _ler_json(request):
    try:
        return json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return {}


def _emitir_senha(servico, prioridade):
    """Gera a próxima senha do dia para o par serviço/prioridade (ex.: RN-001)."""
    hoje = timezone.localdate()
    for _ in range(5):  # nova tentativa caso dois totens emitam ao mesmo tempo
        try:
            with transaction.atomic():
                ultima = Senha.objects.filter(
                    data_emissao=hoje, servico=servico, prioridade=prioridade,
                ).aggregate(m=Max('sequencia'))['m'] or 0
                sequencia = ultima + 1
                codigo = (
                    f"{Senha.PREFIXO_SERVICO[servico]}"
                    f"{Senha.PREFIXO_PRIORIDADE[prioridade]}-{sequencia:03d}"
                )
                return Senha.objects.create(
                    servico=servico, prioridade=prioridade, sequencia=sequencia,
                    numero=codigo, data_emissao=hoje,
                )
        except IntegrityError:
            continue
    raise IntegrityError('Não foi possível gerar uma senha única.')


def _chamar(senha, guiche, posicao_ciclo=None):
    """Chama (ou rechama) uma senha no guichê, finalizando a anterior do guichê.

    Retorna False se outra mesa chamou a mesma senha primeiro.
    """
    agora = timezone.now()
    with transaction.atomic():
        if senha.status == 'AGUARDANDO':
            campos = {
                'status': 'ATENDENDO', 'guiche': guiche,
                'chamado_em': agora, 'ultima_chamada_em': agora,
            }
            if posicao_ciclo is not None:
                campos['posicao_ciclo'] = posicao_ciclo
            # Update condicional evita que duas mesas peguem a mesma senha.
            if not Senha.objects.filter(pk=senha.pk, status='AGUARDANDO').update(**campos):
                return False
        else:
            # Rechamada (senha já chamada antes): só atualiza guichê e horário.
            Senha.objects.filter(pk=senha.pk).update(
                status='ATENDENDO', guiche=guiche, ultima_chamada_em=agora,
                finalizado_em=None,
            )

        # A senha que estava neste guichê passa para o histórico.
        _senhas_de_hoje().filter(status='ATENDENDO', guiche=guiche).exclude(
            pk=senha.pk,
        ).update(status='CONCLUIDO', finalizado_em=agora)
    return True


def _proxima_do_ciclo(escopo):
    """Escolhe a próxima senha seguindo o ciclo S, S, P, P, C."""
    aguardando = _senhas_de_hoje().filter(status='AGUARDANDO')
    if escopo and escopo != 'any':
        aguardando = aguardando.filter(servico=escopo)
    fila = _fila_ordenada(aguardando)
    if not fila:
        return None, None

    ultima_auto = _senhas_de_hoje().filter(
        posicao_ciclo__isnull=False,
    ).order_by('-chamado_em').first()
    inicio = (ultima_auto.posicao_ciclo + 1) % 5 if ultima_auto else 0

    for deslocamento in range(5):
        posicao = (inicio + deslocamento) % 5
        tipo = Senha.CICLO_CHAMADA[posicao]
        for senha in fila:
            if senha.prioridade == tipo:
                return senha, posicao
    return None, None


# ---------------------------------------------------------------------------
# Painel de senhas — API JSON
# ---------------------------------------------------------------------------

def _obter_ip_rede_local():
    """Retorna o IP da máquina na rede local para que celulares e tablets consigam acessar."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def _montar_url_acompanhar(request, token):
    """Gera a URL absoluta de acompanhamento.

    Se a requisição veio de localhost/loopback, substitui pelo IP da rede local
    para que o QR Code lido pelo celular aponte para a máquina correta na rede.
    """
    url = request.build_absolute_uri(reverse('acompanhar_senha', args=[token]))
    parsed = urlparse(url)
    if parsed.hostname in ('127.0.0.1', 'localhost', 'testserver'):
        ip_lan = _obter_ip_rede_local()
        porta = f":{parsed.port}" if parsed.port else ""
        url = urlunparse(parsed._replace(netloc=f"{ip_lan}{porta}"))
    return url


@require_POST
def api_emitir_senha(request):
    dados = _ler_json(request)
    servico = dados.get('servico')
    prioridade = dados.get('prioridade')
    if servico not in Senha.PREFIXO_SERVICO or prioridade not in Senha.PREFIXO_PRIORIDADE:
        return JsonResponse({'erro': 'Serviço ou prioridade inválidos.'}, status=400)

    senha = _emitir_senha(servico, prioridade)
    dados_senha = _serializar(senha)
    dados_senha['url_acompanhar'] = _montar_url_acompanhar(request, senha.token)
    return JsonResponse(dados_senha, status=201)


@require_GET
def api_estado_painel(request):
    """Estado do painel de TV: senha atual + últimas chamadas."""
    chamadas = _senhas_de_hoje().filter(
        status__in=['ATENDENDO', 'CONCLUIDO'], ultima_chamada_em__isnull=False,
    ).order_by('-ultima_chamada_em')[:6]
    chamadas = [_serializar(s) for s in chamadas]
    return JsonResponse({
        'atual': chamadas[0] if chamadas else None,
        'historico': chamadas[1:],
    })


@login_required
@require_GET
def api_estado_operador(request):
    guiche = request.GET.get('guiche', '')
    hoje = _senhas_de_hoje()

    aguardando = _fila_ordenada(hoje.filter(status='AGUARDANDO'))
    contadores = {
        f"{s}-{p}": 0 for s in Senha.PREFIXO_SERVICO for p in Senha.PREFIXO_PRIORIDADE
    }
    for senha in aguardando:
        contadores[f"{senha.servico}-{senha.prioridade}"] += 1

    minha = hoje.filter(status='ATENDENDO', guiche=guiche).order_by('-ultima_chamada_em').first()
    historico = hoje.filter(
        status__in=['ATENDENDO', 'CONCLUIDO'], ultima_chamada_em__isnull=False,
    ).order_by('-ultima_chamada_em')[:20]

    return JsonResponse({
        'fila': [_serializar(s) for s in aguardando],
        'contadores': contadores,
        'minha_senha': _serializar(minha) if minha else None,
        'historico': [_serializar(s) for s in historico],
    })


@login_required
@require_POST
def api_chamar_proxima(request):
    dados = _ler_json(request)
    guiche = str(dados.get('guiche', '')).strip()
    if not guiche:
        return JsonResponse({'erro': 'Informe o guichê.'}, status=400)

    for _ in range(5):  # se outra mesa pegar a senha antes, tenta a seguinte
        senha, posicao = _proxima_do_ciclo(dados.get('escopo', 'any'))
        if senha is None:
            return JsonResponse({'erro': 'Não há senhas aguardando nesta fila.'}, status=400)
        if _chamar(senha, guiche, posicao_ciclo=posicao):
            senha.refresh_from_db()
            return JsonResponse(_serializar(senha))
    return JsonResponse({'erro': 'Fila muito disputada, tente novamente.'}, status=409)


@login_required
@require_POST
def api_chamar_senha(request, pk):
    """Chama uma senha específica da fila ou rechama uma já chamada."""
    dados = _ler_json(request)
    guiche = str(dados.get('guiche', '')).strip()
    if not guiche:
        return JsonResponse({'erro': 'Informe o guichê.'}, status=400)

    senha = get_object_or_404(_senhas_de_hoje(), pk=pk)
    if senha.status == 'CANCELADO':
        return JsonResponse({'erro': 'Esta senha foi cancelada.'}, status=400)
    if not _chamar(senha, guiche):
        return JsonResponse({'erro': 'Esta senha acabou de ser chamada por outro guichê.'}, status=409)
    senha.refresh_from_db()
    return JsonResponse(_serializar(senha))


@login_required
@require_POST
def api_encerrar_expediente(request):
    """Equivalente ao "Limpar Painel": cancela a fila e finaliza os atendimentos."""
    agora = timezone.now()
    hoje = _senhas_de_hoje()
    canceladas = hoje.filter(status='AGUARDANDO').update(status='CANCELADO', finalizado_em=agora)
    hoje.filter(status='ATENDENDO').update(status='CONCLUIDO', finalizado_em=agora)
    return JsonResponse({'canceladas': canceladas})


@require_GET
def api_acompanhar(request, token):
    senha = get_object_or_404(Senha, token=token)
    dados = _serializar(senha)
    dados['pessoas_na_frente'] = None
    if senha.status == 'AGUARDANDO':
        fila = _fila_ordenada(
            Senha.objects.filter(data_emissao=senha.data_emissao, status='AGUARDANDO')
        )
        dados['pessoas_na_frente'] = next(
            (i for i, s in enumerate(fila) if s.pk == senha.pk), 0,
        )
    return JsonResponse(dados)
