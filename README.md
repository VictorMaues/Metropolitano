# Hospital Metropolitano

Sistema de gerenciamento de pacientes e fluxos hospitalares, desenvolvido com o framework web Django.

## Características

- **Gerenciamento de Pacientes**: Controle completo com RH (Registro Hospitalar).
- **Classificação de Risco**: Baseado em cores (Vermelho, Laranja, Amarelo, Verde, Azul, Branco).
- **Controle de Especialidades Médicas**: Acompanhamento de especialidades desde o primeiro atendimento (FAU) até as subsequentes (Clínica Geral, Neurocirurgia, Traumatologia, Bucomaxilofacial, Cirurgia Vascular, Pediatria, etc).
- **Status de Procedimentos e Exames**: Gerenciamento de exames e procedimentos (pendentes e concluídos).
- **Enfermagem e Solicitações**: Controle sobre rotinas de enfermagem (como SAE, Administração de Medicamentos) e solicitações gerais.
- **Painel Administrativo Customizado**: Interface amigável utilizando `django-jazzmin`.

## Tecnologias

- Python
- Django 5.2
- SQLite (Banco de dados padrão)
- [Django Jazzmin](https://github.com/farridav/django-jazzmin) (Painel Administrativo)
- [Django MultiSelectField](https://github.com/goinnn/django-multiselectfield)
- Django Rangefilter

## Como executar o projeto localmente

1. **Clone o repositório ou acesse a pasta do projeto.**

2. **Ative o ambiente virtual:**
   ```bash
   source venv/bin/activate
   ```

3. **Realize as migrações do banco de dados:**
   ```bash
   python manage.py migrate
   ```

4. **Crie um superusuário** para acessar o painel administrativo:
   ```bash
   python manage.py createsuperuser
   ```

5. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

6. **Acesse o painel:**
   Abra seu navegador e acesse `http://127.0.0.1:8000/admin`. Faça o login com as credenciais do superusuário recém-criado.

## Estrutura do Projeto

- `core/`: Configurações globais do projeto (settings, urls).
- `pacientes/`: Aplicativo focado nas regras de negócio de triagem, registro e atendimento de pacientes.
- `templates/`: Arquivos HTML.
- `pacientes/static/`: Arquivos estáticos (CSS, imagens).
