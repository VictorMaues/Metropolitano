<div align="center">

# 🏥 Hospital Metropolitano

**Sistema Integrado de Gestão de Pacientes, Triagem e Fluxo Hospitalar**

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-2ea44f?style=for-the-badge)](#)

</div>

---

## 📋 Sumário

- [Visão Geral](#-visão-geral)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Instalação e Execução Local](#-instalação-e-execução-local)
- [Mapeamento de Rotas](#-mapeamento-de-rotas)
- [Boas Práticas e Padrões de Git](#-boas-práticas-e-padrões-de-git)
- [Autoria e Licença](#-autoria-e-licença)

---

## 📌 Visão Geral

O **Hospital Metropolitano** é uma aplicação web desenvolvida em **Python/Django**, concebida para otimizar o fluxo operacional de unidades de emergência e ambulatório. O sistema centraliza o controle de entrada de pacientes, gerenciamento de triagem com base em protocolo de risco, encaminhamentos médicos por especialidade, controle de exames e procedimentos, além de fornecer um painel de chamada de senhas para exibição pública em telas/TVs.

---

## 🚀 Funcionalidades Principais

### 1. Triagem e Gestão de Pacientes
- **Registro Hospitalar (RH):** Identificação cadastral única por paciente.
- **Protocolo de Classificação de Risco:** Baseado em código de cores (Vermelho, Laranja, Amarelo, Verde, Azul, Branco) com sinalizadores visuais destacados no painel administrativo.
- **Rastreamento FAU:** Registro de especialidade e horário do Primeiro Atendimento de Urgência (FAU).

### 2. Fluxo Clínico e Multidisciplinar
- **Especialidades Médicas:** Acompanhamento de pendências e conclusões pós-FAU (Clínica Geral, Neurocirurgia, Traumatologia, Bucomaxilofacial, Cirurgia Vascular, Pediatria, Internação e outros).
- **Exames Laboratoriais e de Imagem:** Gestão de status de Raio-X, Tomografia Computadorizada (TC) e exames laboratoriais.
- **Procedimentos e Cuidados de Enfermagem:** Acompanhamento de rotinas (SWAB, ECG, Administração de Medicamentos, SAE e Boletins de Comunicação).
- **Indicadores Rápidos de Status:** Visualização intuitiva via badges dinâmicas (`✔` para concluídos e `✘` para pendências).

### 3. Painel de Chamada e Senhas (TV)
- Módulo de gerenciamento de senhas vinculadas a guichês.
- Controle de ciclo de atendimento: `AGUARDANDO`, `ATENDENDO`, `CONCLUIDO` e `CANCELADO`.
- Visão dedicada para exibição contínua em monitores de sala de espera.

### 4. Relatórios e Auditoria
- **Exportação CSV:** Extração ágil de listas de pacientes selecionados para análise em planilhas.
- **Emissão de PDF:** Geração automatizada de relatórios formatados para impressão e documentação médica utilizando `xhtml2pdf`.

### 5. Backoffice Administrativo Customizado
- Interface administrativa estilizada com **Django Jazzmin** (tema Bootstrap Cosmo), com suporte a filtros por período e classificação de risco, busca rápida e navegação intuitiva.

---

## 🛠 Tecnologias Utilizadas

| Tecnologia | Finalidade |
| :--- | :--- |
| **Python 3.11+** | Linguagem principal do backend |
| **Django 5.2** | Framework web de alto nível com arquitetura MTV |
| **SQLite** | Banco de dados relacional padrão para desenvolvimento |
| **Django Jazzmin** | Customização e modernização visual do Django Admin |
| **Django MultiSelectField** | Suporte a seleções múltiplas em campos de modelo |
| **Django Rangefilter** | Filtragem avançada por intervalos de datas e números no Admin |
| **xhtml2pdf** | Engine de conversão HTML/CSS para geração de relatórios em PDF |

---

## 📂 Estrutura do Projeto

```text
Metropolitano/
├── core/                         # Configurações centrais do Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py               # Definições globais, apps, middlewares e Jazzmin
│   ├── urls.py                   # Roteador central de URLs
│   └── wsgi.py
├── pacientes/                    # App principal das regras hospitalares
│   ├── admin.py                  # Customização da interface administrativa e relatórios
│   ├── apps.py
│   ├── models.py                 # Modelos de dados (Paciente, Senha_de_atendimento)
│   ├── views.py                  # Lógica de controle e renderização de páginas
│   ├── urls.py                   # Rotas do aplicativo de pacientes
│   ├── migrations/               # Histórico de evolução do esquema do banco
│   ├── static/                   # Recursos estáticos específicos do app
│   │   └── pacientes/
│   │       ├── css/              # Folhas de estilo (custom.css, painel.css, etc.)
│   │       └── img/              # Imagens institucionais e logos
│   └── templates/                # Templates HTML do app
│       └── pacientes/
│           ├── BemVindo.html
│           ├── Painel_Tv.html
│           ├── operador_senhas.html
│           └── pdf_pacientes.html
├── templates/                    # Templates globais e sobrescrita do Admin
│   ├── admin/
│   │   └── login.html
│   └── registration/
├── requirements.txt              # Especificação de dependências do Python
├── .gitignore                    # Regras de arquivos desconsiderados pelo versionamento
└── manage.py                     # Utilitário de linha de comando do Django
```

---

## 💻 Instalação e Execução Local

### Pré-requisitos
- **Git** instalado no sistema.
- **Python 3.11** ou superior.
- **pip** (gerenciador de pacotes do Python).

### Passo a Passo

1. **Clonar o repositório e acessar o diretório:**
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd Metropolitano
   ```

2. **Criar e isolar o ambiente virtual (venv):**
   ```bash
   python3 -m venv venv
   ```

3. **Ativar o ambiente virtual:**
   - **Linux / macOS:**
     ```bash
     source venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Prompt de Comando - CMD):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```

4. **Instalar as dependências do projeto:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Aplicar as migrações do banco de dados:**
   ```bash
   python manage.py migrate
   ```

6. **Criar uma conta de administrador (Superusuário):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Iniciar o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

O servidor iniciará localmente no endereço `http://127.0.0.1:8000/`.

---

## 🌐 Mapeamento de Rotas

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/admin/` | Painel de controle administrativo, auditoria e cadastros | Restrito (Login) |
| `/` | Página inicial com listagem geral de pacientes | Público |
| `/painel/` | Painel de visualização de TV para chamada de senhas | Público / Recepção |
| `/bemvindo/` | Portal de acolhimento do paciente | Público |

---

## 🛡 Boas Práticas e Padrões de Git

- **Isolamento de Ambiente:** Nunca versione a pasta `venv/` no repositório.
- **Banco de Dados Local:** O arquivo `db.sqlite3` armazena dados voláteis e de testes locais; utilize migrações (`python manage.py makemigrations` e `python manage.py migrate`) para versionar a estrutura do banco sem subir dados binários.
- **Convenção de Commits:** Recomenda-se o padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/):
  - `feat:` Inclusão de nova funcionalidade.
  - `fix:` Correção de bug ou falha de sistema.
  - `docs:` Alterações em documentações ou README.
  - `style:` Ajustes de formatação, CSS ou identidade visual.
  - `refactor:` Refatoração de código sem alteração de comportamento.

---

## 👥 Autoria e Licença

Projeto desenvolvido para modernização da triagem e fluxo ambulatorial do **Hospital Metropolitano**.

*Distribuído para fins institucionais e de desenvolvimento contínuo.*
