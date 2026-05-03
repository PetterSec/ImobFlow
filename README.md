# 🏢 ImobFlow — Plataforma SaaS de Gestão Condominial & Imobiliária

> Sistema web multi-tenant de gestão financeira para condomínios e imobiliárias.  
> Desenvolvido em Python com Flask — roda no navegador, funciona em qualquer dispositivo.

---

## 📋 Índice

1. [O que é o ImobFlow?](#o-que-é-o-imobflow)
2. [Stack e Arquitetura](#stack-e-arquitetura)
3. [Como Rodar Localmente (Windows)](#como-rodar-localmente-windows)
4. [Como Rodar Localmente (Linux/Mac)](#como-rodar-localmente-linuxmac)
5. [Deploy no Railway](#deploy-no-railway)
6. [Estrutura do Projeto](#estrutura-do-projeto)
7. [Banco de Dados](#banco-de-dados)
8. [Funcionalidades Implementadas](#funcionalidades-implementadas)
9. [Próximas Etapas](#próximas-etapas)

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
# 1. Crie o ambiente virtual com Python 3.12
py -3.12 -m venv venv

# 2. Ative o ambiente virtual
venv\Scripts\activate

# 3. Instale as dependências de desenvolvimento (sem psycopg2)
pip install -r requirements-dev.txt

# 4. Crie o arquivo de ambiente
copy .env.example .env

# 5. Rode o servidor
python run.py
```

Acesse: http://localhost:5000

> **Nota:** Em desenvolvimento usa SQLite automaticamente. O `requirements-dev.txt` não inclui
> `psycopg2-binary` pois requer ferramentas de compilação C++ no Windows — não é necessário
> para desenvolvimento local.

---

## 🐧 Como Rodar Localmente (Linux/Mac)

```bash
# 1. Crie e ative o ambiente virtual
python3.12 -m venv venv
source venv/bin/activate

# 2. Instale todas as dependências (psycopg2 compila normalmente no Linux)
pip install -r requirements.txt

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

## ☁️ Deploy no Railway

### Variáveis de ambiente obrigatórias

Configure em: **Settings → Variables** no painel do serviço ImobFlow.

| Variável | Como obter | Obrigatória? |
|---|---|---|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` | ✅ Sim |
| `ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | ✅ Sim |
| `DATABASE_URL` | Use `${{Postgres.DATABASE_URL}}` para linkar ao PostgreSQL | ✅ Sim |
| `FLASK_DEBUG` | `false` (sempre em produção) | ✅ Sim |
| `STRIPE_SECRET_KEY` | dashboard.stripe.com → Developers → API Keys | Para pagamentos |
| `STRIPE_WEBHOOK_SECRET` | dashboard.stripe.com → Webhooks | Para pagamentos |
| `N8N_WEBHOOK_URL` | URL do seu workflow n8n | Opcional |
| `N8N_WEBHOOK_SECRET` | String aleatória que você define | Opcional |

> **Atenção:** O valor de `DATABASE_URL` deve ser `${{Postgres.DATABASE_URL}}` — isso linka
> automaticamente ao serviço PostgreSQL do Railway. Não deixe vazio!

### Fluxo de deploy

```bash
# Após qualquer alteração:
git add .
git commit -m "feat: descrição do que foi feito"
git push
# Railway detecta o push e faz deploy automático (~2 min)
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
├── requirements.txt               ← Dependências para produção (Railway/Linux)
├── requirements-dev.txt           ← Dependências para desenvolvimento Windows
├── gunicorn.conf.py               ← Config do servidor (fix PORT Railway)
├── Procfile                       ← Comando de start (Railway usa railway.json)
├── railway.json                   ← Configuração de deploy Railway
├── docker-compose.yml             ← Para rodar com Docker localmente
├── .env.example                   ← Template das variáveis de ambiente
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
