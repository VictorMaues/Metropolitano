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
        
        # Tela inicial (Bem-Vindo)
        resp = self.client.get(reverse('BemVindo'))
        self.assertEqual(resp.status_code, 200)

        # Gestão de Pacientes
        resp = self.client.get(reverse('pagina_inicial'))
        self.assertEqual(resp.status_code, 200)

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


class DashboardAtendimentoTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Usuário ADM (em teste, apenas adm tem acesso liberado)
        self.adm = User.objects.create_superuser(
            username='adm',
            email='adm@hospital.com',
            password='admpassword'
        )
        # Usuário Comum (não autorizado)
        self.usuario_comum = User.objects.create_user(
            username='comum',
            password='password123'
        )
        # Grupos de saúde
        from django.contrib.auth.models import Group
        self.grupo_doutor = Group.objects.create(name='Doutor')
        self.grupo_enfermeira = Group.objects.create(name='Enfermeira')

        self.doutor = User.objects.create_user(username='dr_roberto', password='password123')
        self.doutor.groups.add(self.grupo_doutor)

        self.enfermeira = User.objects.create_user(username='enf_mariana', password='password123')
        self.enfermeira.groups.add(self.grupo_enfermeira)

        # Paciente de teste
        from .models import Paciente
        self.paciente = Paciente.objects.create(
            numero_registro='PAC-TEST-01',
            nome='Carlos Alberto',
            risco='Amarelo',
            status='waiting'
        )

    def test_acesso_anonimo_redireciona_login(self):
        """Usuário anônimo deve ser redirecionado para a página de login."""
        resp = self.client.get(reverse('dashboard_atendimento'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp.get('Location'))

    def test_usuario_comum_acesso_negado(self):
        """Usuário sem perfil de médico/enfermeiro ou adm deve receber 403."""
        self.client.login(username='comum', password='password123')
        resp = self.client.get(reverse('dashboard_atendimento'))
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, 'Acesso Restrito', status_code=403)

        # API também deve bloquear com 403
        resp_api = self.client.get(reverse('api_dashboard_pacientes'))
        self.assertEqual(resp_api.status_code, 403)

    def test_adm_tem_acesso_total(self):
        """Usuário adm deve conseguir visualizar a tela e consumir a API."""
        self.client.login(username='adm', password='admpassword')
        resp = self.client.get(reverse('dashboard_atendimento'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Fila de atendimento')

        # API
        resp_api = self.client.get(reverse('api_dashboard_pacientes'))
        self.assertEqual(resp_api.status_code, 200)
        data = resp_api.json()
        self.assertTrue(data['sucesso'])
        self.assertIn('metricas', data)
        self.assertIn('pacientes', data)

    def test_dashboard_atendimento_carrega_driver_js(self):
        """Dashboard deve carregar os assets do Driver.js e o botão do tour."""
        self.client.login(username='adm', password='admpassword')
        resp = self.client.get(reverse('dashboard_atendimento'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'pacientes/css/driver.css')
        self.assertContains(resp, 'pacientes/js/driver.js.iife.js')
        self.assertContains(resp, 'id="tour-button"')

    def test_doutor_e_enfermeira_tem_acesso(self):
        """Usuários nos grupos Doutor e Enfermeira devem ter acesso."""
        # Doutor
        self.client.login(username='dr_roberto', password='password123')
        resp = self.client.get(reverse('dashboard_atendimento'))
        self.assertEqual(resp.status_code, 200)

        # Enfermeira
        self.client.login(username='enf_mariana', password='password123')
        resp = self.client.get(reverse('dashboard_atendimento'))
        self.assertEqual(resp.status_code, 200)

    def test_atualizar_status_paciente_api(self):
        """Médico ou adm pode alterar status do paciente na fila."""
        self.client.login(username='adm', password='admpassword')
        
        # Iniciar atendimento
        url_status = reverse('api_atualizar_status_paciente', args=[self.paciente.pk])
        resp = self.client.post(
            url_status,
            data=json.dumps({'status': 'service'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.status, 'service')
        self.assertIsNotNone(self.paciente.hora_primeiro_atendimento)

        # Concluir atendimento
        resp2 = self.client.post(
            url_status,
            data=json.dumps({'status': 'done'}),
            content_type='application/json'
        )
        self.assertEqual(resp2.status_code, 200)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.status, 'done')

    def test_detalhe_paciente_api(self):
        """A ficha detalhada retorna os grupos de solicitações com status de conclusão."""
        self.paciente.exames_pendentes = ['RX', 'TC']
        self.paciente.exames_concluidos = ['RX']
        self.paciente.save()

        self.client.login(username='adm', password='admpassword')
        resp = self.client.get(reverse('api_detalhe_paciente', args=[self.paciente.pk]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['nome'], 'Carlos Alberto')
        self.assertEqual(data['codigo'], 'PAC-TEST-01')

        exames = next(g for g in data['grupos'] if g['titulo'] == 'Exames')
        itens = {i['codigo']: i for i in exames['itens']}
        self.assertTrue(itens['RX']['concluido'])
        self.assertFalse(itens['TC']['concluido'])
        self.assertEqual(itens['TC']['rotulo'], 'Tomografia Computadorizada')

    def test_detalhe_paciente_bloqueado_para_usuario_comum(self):
        """Usuário sem permissão não acessa a ficha detalhada."""
        self.client.login(username='comum', password='password123')
        resp = self.client.get(reverse('api_detalhe_paciente', args=[self.paciente.pk]))
        self.assertEqual(resp.status_code, 403)


class SalaDeEsperaEKanbanPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        from django.contrib.auth.models import Group
        self.grupo_doutor = Group.objects.create(name='Doutor')
        self.grupo_enfermeira = Group.objects.create(name='Enfermeira')

        self.adm = User.objects.create_superuser(
            username='adm',
            email='adm@hospital.com',
            password='admpassword'
        )
        self.usuario_comum = User.objects.create_user(
            username='comum',
            password='password123'
        )
        self.doutor = User.objects.create_user(
            username='dr_roberto',
            password='password123'
        )
        self.doutor.groups.add(self.grupo_doutor)

        self.enfermeira = User.objects.create_user(
            username='enf_mariana',
            password='password123'
        )
        self.enfermeira.groups.add(self.grupo_enfermeira)

    def test_anonimo_redireciona_login(self):
        """Acesso anônimo a /saladeespera e /kanban deve redirecionar para tela de login."""
        for rota in ('sala-de-espera', 'kanban'):
            resp = self.client.get(reverse(rota))
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/admin/login/', resp.get('Location'))

    def test_usuario_comum_acesso_negado(self):
        """Usuário sem perfil Adm ou Enfermeira deve receber 403."""
        self.client.login(username='comum', password='password123')
        for rota in ('sala-de-espera', 'kanban'):
            resp = self.client.get(reverse(rota))
            self.assertEqual(resp.status_code, 403)
            self.assertContains(resp, 'Acesso Restrito', status_code=403)

    def test_doutor_acesso_negado(self):
        """Doutor não deve ter acesso (apenas Adm ou Enfermeiras)."""
        self.client.login(username='dr_roberto', password='password123')
        for rota in ('sala-de-espera', 'kanban'):
            resp = self.client.get(reverse(rota))
            self.assertEqual(resp.status_code, 403)
            self.assertContains(resp, 'Acesso Restrito', status_code=403)

    def test_enfermeira_tem_acesso(self):
        """Usuário no grupo Enfermeira deve conseguir acessar /saladeespera e /kanban."""
        self.client.login(username='enf_mariana', password='password123')
        for rota in ('sala-de-espera', 'kanban'):
            resp = self.client.get(reverse(rota))
            self.assertEqual(resp.status_code, 200)

    def test_adm_tem_acesso(self):
        """Usuário Adm tem acesso a /saladeespera e /kanban."""
        self.client.login(username='adm', password='admpassword')
        for rota in ('sala-de-espera', 'kanban'):
            resp = self.client.get(reverse(rota))
            self.assertEqual(resp.status_code, 200)
