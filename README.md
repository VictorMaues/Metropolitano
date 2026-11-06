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
- Django
- SQLite (Banco de dados padrão)
- [Django Jazzmin](https://github.com/farridav/django-jazzmin) (Painel Administrativo)
- [Django MultiSelectField](https://github.com/goinnn/django-multiselectfield)
- [Django Rangefilter](https://github.com/silviogutierrez/django-rangefilter)
- [xhtml2pdf](https://github.com/xhtml2pdf/xhtml2pdf) (Exportação de relatórios em PDF)

## Como executar o projeto localmente

1. **Acesse a pasta do projeto:**
   ```bash
   cd Metropolitano
   ```

2. **Crie o ambiente virtual (venv):**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual:**
   - No Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - No Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```

4. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Realize as migrações do banco de dados:**
   ```bash
   python manage.py migrate
   ```

6. **Crie um superusuário** para acessar o painel administrativo (se necessário):
   ```bash
   python manage.py createsuperuser
   ```

7. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

8. **Acesse o sistema:**
   - Painel Administrativo: `http://127.0.0.1:8000/admin`
   - Painel de TV: `http://127.0.0.1:8000/painel/`
   - Página Inicial: `http://127.0.0.1:8000/`

## Estrutura do Projeto

- `core/`: Configurações globais do projeto (settings, urls).
- `pacientes/`: Aplicativo focado nas regras de negócio de triagem, registro e atendimento de pacientes.
- `templates/`: Arquivos HTML.
- `pacientes/static/`: Arquivos estáticos (CSS, imagens).
