import json
import socket
from urllib.parse import urlparse, urlunparse

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Paciente, Senha_de_atendimento

Senha = Senha_de_atendimento


def pagina_inicial(request):
    pacientes = Paciente.objects.all()
    return render(request, 'pacientes/pagina_inicial.html', {'pacientes': pacientes})

def view_painel_tv(request):
    """View que exibe o painel de TV."""
    return render(request, 'pacientes/Painel_Tv.html') 

def view_bemvindo(request):
    """view que exibe a pagina de Bem Vindo. """
    return render (request, 'pacientes/BemVindo.html')


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
            return JsonResponse({'erro': 'Não há senhas aguardando nesta fila.'}, status=404)
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
