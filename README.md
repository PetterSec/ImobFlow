# 🏢 ImobFlow — Plataforma SaaS de Gestão Condominial & Imobiliária

> Sistema web multi-tenant de gestão financeira para condomínios e imobiliárias.  
> Desenvolvido em Python com Flask — roda no navegador, funciona em qualquer dispositivo.

---

## 📋 Índice

1. [O que é o ImobFlow?](#o-que-é-o-imobflow)
2. [Stack e Arquitetura](#stack-e-arquitetura)
3. [Como Rodar Localmente (Windows)](#como-rodar-localmente-windows)
4. [Como Rodar Localmente (Linux/Mac)](#como-rodar-localmente-linuxmac)
5. [Testes automatizados](#testes-automatizados)
6. [CI no GitHub Actions](#ci-no-github-actions)
7. [Monetização e Stripe (`docs/`)](#monetização-stripe-e-anuncios)
8. [Deploy no Railway](#deploy-no-railway)
9. [Estrutura do Projeto](#estrutura-do-projeto)
10. [Banco de Dados](#banco-de-dados)
11. [Funcionalidades Implementadas](#funcionalidades-implementadas)
12. [Próximas Etapas](#próximas-etapas)

---

## 🎯 O que é o ImobFlow?

O ImobFlow é uma plataforma SaaS completa de gestão condominial e imobiliária, com arquitetura de segurança profissional e identidade visual premium.

| FinanceFlow (origem) | ImobFlow (atual) |
|---|---|
| App desktop (só no PC) | Roda no navegador |
| Um usuário por vez | Multi-tenant (múltiplos clientes) |
| SQLite simples | SQLite (dev) / PostgreSQL (prod) |
| Controle pessoal | Gestão de condomínios e imóveis |
| Sem segurança avançada | AES-256, HSTS, CSP, rate limiting |

---

## 🛠️ Stack e Arquitetura

- **Backend:** Python 3.12 + Flask 3.0 + SQLAlchemy + Flask-Login + Flask-WTF
- **Segurança:** Flask-Talisman (HSTS/CSP), criptografia AES-256/Fernet nos campos sensíveis (LGPD)
- **Banco:** SQLite em dev, PostgreSQL em produção (Railway)
- **Deploy:** Railway (gunicorn com `gunicorn.conf.py`)
- **Frontend:** Jinja2 + CSS próprio (identidade premium dourado/vinho) + Chart.js
- **PWA:** manifest.json + service worker implementados
- **SaaS:** Stripe para pagamento, 3 planos (Free / Pro R$79 / Gestora R$199)
- **Multi-tenant:** todos os modelos têm `tenant_id` (UUID) — isolamento total entre clientes
- **IDs públicos:** UUID em todas as rotas (previne IDOR)

### Identidade Visual
- **Paleta:** Noir `#0E0A06` · Vinho `#6B1E3C` · Ouro `#C9963A` · Creme `#FAF6EF`
- **Tipografia:** Cormorant Garamond (display) + DM Sans (corpo) + DM Mono (valores)
- **Logo:** hexágono SVG com gradiente vinho → ouro em `static/logo.svg`

---

## 🚀 Como Rodar Localmente (Windows)

### Pré-requisito: Python 3.12

Instale o Python 3.12 em: https://www.python.org/downloads/release/python-3120/  
Durante a instalação, marque **"Add Python to PATH"**.

### Setup automático

Dê duplo clique em `setup_windows.bat` na raiz do projeto.  
Ele vai criar o venv, instalar as dependências e criar o `.env`.

### Setup manual

```bat
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env
python run.py
```

Acesse: http://localhost:5000 (ou a porta indicada no terminal).

**Se o PowerShell bloquear `Activate.ps1`:** rode `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` **ou** use `venv\Scripts\activate.bat` no **Prompt de Comando** **ou** chame o Python direto: `venv\Scripts\python.exe run.py`.

**Dependências:** `requirements.txt` é o conjunto completo do app (inclui `psycopg2-binary` no Windows use wheel pré-compilado). `requirements-dev.txt` acrescenta apenas **pytest** e **pytest-cov** para testes locais e CI.

---

## 🐧 Como Rodar Localmente (Linux/Mac)

```bash
# 1. Crie e ative o ambiente virtual
python3.12 -m venv venv
source venv/bin/activate

# 2. Instale dependências de produção + testes
pip install -r requirements.txt -r requirements-dev.txt

# 3. Crie o arquivo de ambiente
cp .env.example .env

# 4. Rode o servidor
python run.py
```

Acesse: http://localhost:5000

### Rodando com Docker

```bash
cp .env.example .env   # preencha as variáveis
docker-compose up -d
# Acesse: http://localhost:8000
```

---

## 🧪 Testes automatizados

O projeto usa **pytest** com `config.TestConfig` (SQLite em memória, sem depender de PostgreSQL).

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -v
```

Com cobertura:

```bash
python -m pytest -v --cov=app --cov=config --cov-report=term-missing
```

Pastas: `tests/` (fixtures em `conftest.py`), configuração em `pytest.ini`.

---

## Monetização, Stripe e anuncios

Guia completo (variáveis, webhook, AdSense no plano Free, como você recebe via Stripe):  
**[docs/MONETIZACAO_E_SAAS.md](docs/MONETIZACAO_E_SAAS.md)**

Resumo: configure no Railway `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_PRO`, `STRIPE_PRICE_ID_GESTORA` e cadastre a URL do webhook no Dashboard Stripe. Anúncios no Free são opcionais (`SHOW_ADS_ON_FREE_PLAN`, `GOOGLE_ADSENSE_*`).

---

## 🔄 CI no GitHub Actions

O workflow `.github/workflows/ci.yml` roda em **push** e **pull request** para `main` e `master`:

- Python **3.12**
- `pip install -r requirements.txt -r requirements-dev.txt`
- `python -m pytest -v` com cobertura

---

## ☁️ Deploy no Railway

### Como o app sobe

O Railway usa `railway.json` → comando de start:

`gunicorn run:app --config gunicorn.conf.py`

A porta vem da variável **`PORT`** (o Railway define automaticamente). O `gunicorn.conf.py` lê `PORT` em Python.

O **Procfile** na raiz também está alinhado (`gunicorn run:app --config gunicorn.conf.py`) para ambientes que leem Procfile.

### Variáveis de ambiente obrigatórias

No painel do **serviço web** (não só do Postgres): **Settings → Variables**.

| Variável | Valor / como obter |
|---|---|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` — guarde em lugar seguro; **não troque** depois que houver dados de moradores criptografados |
| `DATABASE_URL` | Referência ao Postgres: **`${{Postgres.DATABASE_URL}}`** (substitua `Postgres` pelo **nome exato** do plugin Postgres no seu projeto, se for diferente) |
| `FLASK_DEBUG` | `false` |

Opcionais: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `N8N_WEBHOOK_URL`, `N8N_WEBHOOK_SECRET`.

**Não defina `PORT` manualmente** — o Railway injeta.

### Checklist rápido — colocar no ar hoje

1. **Postgres:** no projeto Railway, **+ New → Database → PostgreSQL**. Espere provisionar.
2. **Serviço Flask:** conectado ao mesmo repositório GitHub; **Deploy** após `git push`.
3. **Variables** no serviço web: cole `SECRET_KEY`, `ENCRYPTION_KEY`, `FLASK_DEBUG=false`, `DATABASE_URL=${{Postgres.DATABASE_URL}}` (ajuste o nome do serviço Postgres).
4. **Domínio:** **Settings → Networking → Generate Domain** (ex.: `seuprojeto.up.railway.app`).
5. **Logs:** **Deployments → último deploy → View logs** — procure erros de boot ou de conexão com o banco.
6. **Smoke test:** abra `https://sua-url.up.railway.app/health` → deve retornar JSON `{"status":"ok"}`. Depois teste `/cadastro` e login.

**Primeiro deploy / banco novo:** o app executa `db.create_all()` na inicialização e cria as tabelas no Postgres.

**Migrações:** hoje não há Alembic; se já existia um SQLite antigo só na sua máquina, não afeta o Postgres novo na nuvem.

### Fluxo de deploy contínuo

```bash
git add .
git commit -m "feat: descrição do que foi feito"
git push
```

### Padrão de commits

| Prefixo | Uso |
|---|---|
| `feat:` | nova funcionalidade |
| `fix:` | correção de bug |
| `style:` | mudança visual/CSS |
| `docs:` | atualização de documentação |
| `security:` | melhoria de segurança |
| `chore:` | tarefas de manutenção (gitignore, deps, etc.) |

> ⚠️ **NUNCA** suba o arquivo `.env` para o GitHub. Ele já está no `.gitignore`.

---

## 📁 Estrutura do Projeto

```
imobflow/
│
├── run.py                         ← Entry point
├── config.py                      ← Configurações (lê variáveis de ambiente)
├── requirements.txt               ← Dependências de produção
├── requirements-dev.txt         ← pytest + pytest-cov (dev/CI)
├── pytest.ini                    ← Configuração do pytest
├── gunicorn.conf.py               ← Gunicorn (lê PORT do Railway)
├── Procfile                       ← gunicorn run:app (fallback para plataformas Procfile)
├── railway.json                   ← Deploy Railway (startCommand + Nixpacks)
├── docker-compose.yml             ← Postgres + web local
├── .env.example                   ← Template de variáveis (copiar para .env)
│
├── .github/workflows/ci.yml       ← GitHub Actions (testes em push/PR)
├── tests/                         ← Suite pytest (auth, health, models, crypto…)
│
├── app/
│   ├── __init__.py                ← Factory com Talisman, CSRF, blueprints
│   ├── models.py                  ← Modelos com UUID + tenant_id + crypto
│   │
│   ├── routes/
│   │   ├── auth.py                ← Login, cadastro, logout
│   │   ├── dashboard.py           ← KPIs e gráficos
│   │   ├── condominios.py         ← CRUD + webhook n8n
│   │   ├── moradores.py           ← CRUD com campos criptografados
│   │   ├── financeiro.py          ← Lançamentos, filtros, CSV
│   │   ├── saas.py                ← Planos + Stripe
│   │   └── pwa.py                 ← Manifest + service worker
│   │
│   ├── services/
│   │   ├── crypto.py              ← CryptoService (AES-256/Fernet)
│   │   └── webhook.py             ← Webhooks n8n com HMAC-SHA256
│   │
│   ├── middleware/
│   │   └── security.py            ← enforce_plan, get_tenant, rate_limit
│   │
│   └── templates/                 ← HTMLs Jinja2
│       ├── base.html              ← Layout base (sidebar + topbar)
│       ├── dashboard.html
│       ├── auth/
│       ├── condominios/
│       ├── moradores/
│       └── financeiro/
│
└── static/
    ├── logo.svg                   ← Logo hexágono vinho→ouro
    └── css/
        └── style.css              ← Identidade visual premium
```

---

## 🗄️ Banco de Dados

```
usuarios
  └── condominios (tenant_id = usuario.id)
        ├── unidades
        │     └── moradores (CPF/tel/email criptografados)
        └── lancamentos (receitas e despesas)
```

### Regras de segurança obrigatórias no código

- Sempre filtrar queries por `tenant_id=current_user.id`
- Novos modelos herdam `GUID()` como PK e incluem `tenant_id`
- Campos sensíveis (CPF, telefone, email) sempre usam properties com `CryptoService`
- Novas rotas sempre têm `@login_required` e validam tenant via middleware
- CSS: sempre usar variáveis `--gold`, `--wine`, `--noir` — nunca hardcode cores

---

## ✨ Funcionalidades Implementadas

### 🔐 Autenticação e Segurança
- Login por e-mail e senha com hash seguro
- Multi-tenant isolado por UUID
- Flask-Talisman: HSTS, CSP, X-XSS-Protection
- Rate limiting por IP nos endpoints críticos
- IDs públicos UUID (previne IDOR)

### 📊 Dashboard
- KPIs: condomínios, moradores, receitas, despesas, saldo do mês
- Gráfico de pizza interativo (Chart.js)
- Tabela dos últimos lançamentos

### 🏢 Condomínios
- CRUD completo com webhook n8n
- Limite por plano (Free: 1, Pro: 3, Gestora: ilimitado)

### 👥 Moradores
- CPF, telefone e e-mail criptografados (AES-256)
- Registro de entrada e saída

### 💰 Financeiro
- Receitas e despesas com categorias
- Filtros por tipo e condomínio
- Exportação CSV

### 💳 SaaS / Planos
- Integração Stripe (checkout, webhook, atualização automática)
- Decorator `@enforce_plan()` bloqueia ações além do limite
- 3 planos: Free / Pro R$79 / Gestora R$199

### 📱 PWA
- Instalável no Android e iOS
- Service worker com cache offline

---

## 🔮 Próximas Etapas

| Etapa | Descrição | Status |
|---|---|---|
| Portal do Morador | Login separado `/portal` — morador vê cobranças e comunicados | 🔴 Pendente |
| Relatório PDF | Balancete mensal com ReportLab (planos Pro e Gestora) | 🔴 Pendente |
| Templates completos | Identidade visual nos templates de condos/moradores/financeiro | 🟡 Parcial |
| Landing page | Site de vendas público `/landing` | 🔴 Pendente |
| Plano de negócios | Guia de vendas para síndicos e imobiliárias | 🔴 Pendente |

---

*ImobFlow — Desenvolvido por Petterson (PetterSec) · Maio 2026*
