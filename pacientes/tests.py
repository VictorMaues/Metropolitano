from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Senha_de_atendimento
import json

class PainelSenhasTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='operador1',
            password='password123'
        )

    def test_emitir_senha_api(self):
        """Testa geração de senha no Totem"""
        payload = {'servico': 'RECEPCAO', 'prioridade': 'NORMAL'}
        response = self.client.post(
            reverse('api_emitir_senha'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['codigo'], 'RN-001')
        self.assertEqual(data['status'], 'AGUARDANDO')
        self.assertIn('url_acompanhar', data)

        # Segunda senha da mesma categoria deve incrementar sequência
        response2 = self.client.post(
            reverse('api_emitir_senha'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 201)
        self.assertEqual(response2.json()['codigo'], 'RN-002')

    def test_chamar_proxima_ciclo_prioridade(self):
        """Testa se a chamada respeita o ciclo de prioridade: Superprioridade > Preferencial > Comum"""
        # Criar 1 Comum, 1 Preferencial, 1 Superprioridade
        self.client.post(reverse('api_emitir_senha'), data=json.dumps({'servico': 'RECEPCAO', 'prioridade': 'NORMAL'}), content_type='application/json')
        self.client.post(reverse('api_emitir_senha'), data=json.dumps({'servico': 'RECEPCAO', 'prioridade': 'PREFERENCIAL'}), content_type='application/json')
        self.client.post(reverse('api_emitir_senha'), data=json.dumps({'servico': 'RECEPCAO', 'prioridade': 'SUPER'}), content_type='application/json')

        # Operador precisa estar autenticado
        self.client.login(username='operador1', password='password123')

        # Chamada 1: deve ser a Superprioridade (RS-001)
        resp1 = self.client.post(
            reverse('api_chamar_proxima'),
            data=json.dumps({'guiche': '1', 'escopo': 'any'}),
            content_type='application/json'
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()['codigo'], 'RS-001')
        self.assertEqual(resp1.json()['guiche'], '1')
        self.assertEqual(resp1.json()['status'], 'ATENDENDO')

        # Chamada 2: deve ser a Preferencial (RP-001)
        resp2 = self.client.post(
            reverse('api_chamar_proxima'),
            data=json.dumps({'guiche': '1', 'escopo': 'any'}),
            content_type='application/json'
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()['codigo'], 'RP-001')

        # Chamada 3: deve ser a Comum (RN-001)
        resp3 = self.client.post(
            reverse('api_chamar_proxima'),
            data=json.dumps({'guiche': '1', 'escopo': 'any'}),
            content_type='application/json'
        )
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(resp3.json()['codigo'], 'RN-001')

    def test_estado_painel_tv(self):
        """Testa se o estado do painel retorna senha atual e histórico"""
        self.client.post(reverse('api_emitir_senha'), data=json.dumps({'servico': 'EXAMES', 'prioridade': 'NORMAL'}), content_type='application/json')
        self.client.login(username='operador1', password='password123')
        self.client.post(reverse('api_chamar_proxima'), data=json.dumps({'guiche': '2', 'escopo': 'any'}), content_type='application/json')

        resp_painel = self.client.get(reverse('api_estado_painel'))
        self.assertEqual(resp_painel.status_code, 200)
        data = resp_painel.json()
        self.assertIsNotNone(data['atual'])
        self.assertEqual(data['atual']['codigo'], 'EN-001')
        self.assertEqual(data['atual']['guiche'], '2')

    def test_acompanhar_senha_celular(self):
        """Testa a visualização e contagem de pessoas na frente no celular"""
        r1 = self.client.post(reverse('api_emitir_senha'), data=json.dumps({'servico': 'RECEPCAO', 'prioridade': 'NORMAL'}), content_type='application/json')
        r2 = self.client.post(reverse('api_emitir_senha'), data=json.dumps({'servico': 'RECEPCAO', 'prioridade': 'NORMAL'}), content_type='application/json')
        
        token2 = r2.json()['token']
        resp_celular = self.client.get(reverse('api_acompanhar', args=[token2]))
        self.assertEqual(resp_celular.status_code, 200)
        self.assertEqual(resp_celular.json()['pessoas_na_frente'], 1)

    def test_render_views(self):
        """Testa se todas as páginas renderizam com código HTTP 200"""
        self.client.login(username='operador1', password='password123')
        
        # Portal de senhas
        resp = self.client.get(reverse('senhas_portal'))
        self.assertEqual(resp.status_code, 200)
        
        # Totem
        resp = self.client.get(reverse('Totem'))
        self.assertEqual(resp.status_code, 200)
        
        # Painel TV
        resp = self.client.get(reverse('Painel_Tv'))
        self.assertEqual(resp.status_code, 200)
        
        # Operador (autenticado)
        resp = self.client.get(reverse('operador_senhas'))
        self.assertEqual(resp.status_code, 200)
