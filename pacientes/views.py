from django.shortcuts import render
from django.http import JsonResponse
from .models import Paciente, Senha_de_atendimento
from django.utils import timezone

def pagina_inicial(request):
    pacientes = Paciente.objects.all()
    return render(request, 'pacientes/pagina_inicial.html', {'pacientes': pacientes})

def view_painel_tv(request):
    """View que exibe o painel de TV."""
    return render(request, ' pacientes/Painel_Tv.html') 