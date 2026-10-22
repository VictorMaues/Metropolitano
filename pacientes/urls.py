from django.urls import path
from .views import pagina_inicial

urlpatterns = [
    path('', pagina_inicial, name='pagina_inicial'),
    path('Painel_Tv/', views.view_painel_tv, name='Painel_Tv')
]
