from django.urls import path
from .views import pagina_inicial
from . import views

urlpatterns = [
    path('', pagina_inicial, name='pagina_inicial'),
    path('painel/', views.view_painel_tv, name='Painel_Tv')
]
