from django.shortcuts import render
from .models import Paciente

def pagina_inicial(request):
    pacientes = Paciente.objects.all()
    return render(request, 'pacientes/pagina_inicial.html', {'pacientes': pacientes})
