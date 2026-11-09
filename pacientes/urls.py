from django.urls import path
from .views import pagina_inicial
from . import views

urlpatterns = [
    path('', pagina_inicial, name='pagina_inicial'),
    path('painel/', views.view_painel_tv, name='Painel_Tv'),
    path('bemvindo/', views.view_bemvindo, name='Bemvindo'),

    # Painel de senhas
    path('senhas/', views.view_portal_senhas, name='senhas_portal'),
    path('totem/', views.view_totem, name='Totem'),
    path('operador/', views.view_operador, name='operador_senhas'),
    path('acompanhar/<uuid:token>/', views.view_acompanhar, name='acompanhar_senha'),

    # API do painel de senhas (consumida via JavaScript)
    path('api/senhas/emitir/', views.api_emitir_senha, name='api_emitir_senha'),
    path('api/senhas/painel/', views.api_estado_painel, name='api_estado_painel'),
    path('api/senhas/operador/', views.api_estado_operador, name='api_estado_operador'),
    path('api/senhas/chamar-proxima/', views.api_chamar_proxima, name='api_chamar_proxima'),
    path('api/senhas/<int:pk>/chamar/', views.api_chamar_senha, name='api_chamar_senha'),
    path('api/senhas/encerrar/', views.api_encerrar_expediente, name='api_encerrar_expediente'),
    path('api/senhas/acompanhar/<uuid:token>/', views.api_acompanhar, name='api_acompanhar'),
]
