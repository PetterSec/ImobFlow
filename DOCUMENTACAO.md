# 🏢 ImobFlow — Documentação Completa

> Sistema web de gestão financeira para condomínios e imobiliárias.  
> Desenvolvido em Python com Flask — roda no navegador, funciona em qualquer dispositivo.

---

## 📋 Índice

1. [O que é o ImobFlow?](#o-que-é-o-imobflow)
2. [Como Instalar e Rodar](#como-instalar-e-rodar)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [Como o Flask Funciona](#como-o-flask-funciona)
5. [Banco de Dados](#banco-de-dados)
6. [Funcionalidades](#funcionalidades)
7. [Próximos Passos (Etapa 3)](#próximos-passos-etapa-3)

---

## 🎯 O que é o ImobFlow?

O ImobFlow é a evolução do FinanceFlow (app desktop) para uma **aplicação web completa**.

A diferença principal:

| FinanceFlow (anterior) | ImobFlow (agora) |
|---|---|
| App desktop (só no seu PC) | Roda no navegador |
| Um usuário por vez | Múltiplos usuários simultâneos |
| SQLite simples | SQLite agora, PostgreSQL depois |
| Controle pessoal | Gestão de condomínios e imóveis |
| Sem mobile | Responsivo — funciona no celular |

---

## 🚀 Como Instalar e Rodar

### 1. Entre na pasta do projeto
```bash
cd imobflow
```

### 2. Crie um ambiente virtual e instale as dependências
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Rode o servidor
```bash
python run.py
```

### 4. Abra no navegador
```
http://localhost:5000
```

Pronto! Crie sua conta e comece a usar. O banco de dados (`imobflow.db`) é criado automaticamente.

---

## 📁 Estrutura do Projeto

```
imobflow/
│
├── run.py                    ← Ponto de entrada. Você sempre roda este arquivo.
├── config.py                 ← Configurações (chave secreta, banco de dados)
├── requirements.txt          ← Lista de dependências para instalar com pip
│
├── app/
│   ├── __init__.py           ← "Fábrica" do Flask. Monta o app e registra as rotas.
│   ├── models.py             ← Define as tabelas do banco de dados
│   │
│   ├── routes/               ← Cada arquivo é um módulo de funcionalidades
│   │   ├── auth.py           ← Login, cadastro, logout
│   │   ├── dashboard.py      ← Página inicial com KPIs e gráficos
│   │   ├── condominios.py    ← CRUD de condomínios
│   │   ├── moradores.py      ← CRUD de moradores
│   │   └── financeiro.py     ← Lançamentos, filtros, exportação CSV
│   │
│   └── templates/            ← Arquivos HTML que o Flask renderiza
│       ├── base.html         ← Layout base (sidebar + topbar). Todos herdam deste.
│       ├── dashboard.html
│       ├── auth/
│       ├── condominios/
│       ├── moradores/
│       └── financeiro/
│
└── static/
    └── css/
        └── style.css         ← Todo o visual (dark mode, responsivo)
```

---

## 🧠 Como o Flask Funciona

Se você nunca usou Flask, aqui está a lógica de forma simples:

### O ciclo de uma requisição

```
Usuário abre o navegador e acessa /dashboard
        ↓
Flask recebe a requisição
        ↓
Encontra a função em routes/dashboard.py que trata /dashboard
        ↓
A função busca dados no banco de dados (via models.py)
        ↓
Passa os dados para o template dashboard.html
        ↓
Flask renderiza o HTML com os dados e envia para o navegador
        ↓
Usuário vê a página pronta
```

### Blueprints (módulos de rotas)

Em vez de colocar todas as rotas num arquivo só (que ficaria enorme), usamos **Blueprints** — cada funcionalidade tem seu próprio arquivo:

```python
# routes/condominios.py
condominios_bp = Blueprint("condominios", __name__, url_prefix="/condominios")

@condominios_bp.route("/")          # URL: /condominios/
def listar(): ...

@condominios_bp.route("/novo")      # URL: /condominios/novo
def novo(): ...
```

### Templates Jinja2

Os HTMLs usam uma linguagem de template chamada **Jinja2** que permite lógica dentro do HTML:

```html
{% for morador in moradores %}           <!-- loop -->
  <tr>
    <td>{{ morador.nome }}</td>          <!-- variável -->
    {% if morador.ativo %}               <!-- condicional -->
      <span class="badge">Ativo</span>
    {% endif %}
  </tr>
{% endfor %}
```

### Herança de templates

O `base.html` tem a sidebar e topbar. Todos os outros templates **herdam** dele:

```html
{% extends "base.html" %}              <!-- herda o layout -->
{% block content %}
  <!-- aqui vai só o conteúdo da página -->
{% endblock %}
```

---

## 🗄️ Banco de Dados

### Tabelas e relacionamentos

```
usuarios
  └── condominios (um usuário tem vários condomínios)
        └── unidades (um condomínio tem várias unidades)
        │     └── moradores (uma unidade tem um morador)
        └── lancamentos (um condomínio tem vários lançamentos)
```

### Modelos principais

**Usuario** — quem faz login
```python
id, nome, email, senha_hash, perfil (sindico|imobiliaria|admin)
```

**Condominio** — o imóvel gerenciado
```python
id, nome, endereco, cidade, cep, total_unidades, usuario_id
```

**Unidade** — cada apartamento/sala do condomínio
```python
id, identificacao (101, 102...), tipo (apto|sala), condominio_id
```

**Morador** — quem mora na unidade
```python
id, nome, cpf, telefone, email, tipo (proprietario|inquilino), ativo, unidade_id
```

**Lancamento** — receita ou despesa
```python
id, descricao, valor, tipo (receita|despesa), categoria, data, pago, condominio_id
```

---

## ✨ Funcionalidades

### 🔐 Autenticação
- Login por e-mail e senha
- Senha com hash seguro (Werkzeug)
- Sessão persistente com Flask-Login
- Perfis: Síndico ou Imobiliária

### 📊 Dashboard
- KPIs: total de condomínios, moradores, receitas, despesas e saldo do mês
- Gráfico de pizza interativo (Chart.js) — despesas por categoria
- Tabela dos últimos 5 lançamentos
- Cards de acesso rápido aos condomínios

### 🏢 Condomínios
- Cadastrar condomínio com endereço, cidade, CEP
- Definir número de unidades (criadas automaticamente: 1, 2, 3...)
- Ver detalhe com lista de unidades e ocupação
- Deletar condomínio (e todos os dados relacionados)

### 👥 Moradores
- Cadastrar morador vinculado a uma unidade
- Tipo: Proprietário ou Inquilino
- Data de entrada e saída
- Registrar saída (marca como inativo, não deleta os dados)

### 💰 Financeiro
- Registrar receitas e despesas
- Categorias dinâmicas por tipo (despesa: Manutenção, Água... / receita: Taxa, Aluguel...)
- Filtro por tipo e por condomínio
- Marcar como pago/pendente
- Exportar tudo para CSV

### 📱 Interface
- Dark mode moderno
- Totalmente responsivo (funciona no celular)
- Sidebar com navegação clara
- Feedback visual para todas as ações

---

## 🔮 Próximos Passos (Etapa 3)

### Funcionalidades prioritárias

- [ ] **Cobranças automáticas** — gerar taxa condominial para todos os moradores de uma vez
- [ ] **Relatório mensal em PDF** — balancete com receitas, despesas e saldo
- [ ] **Painel do morador** — login separado para moradores verem suas cobranças
- [ ] **Notificações por e-mail** — boleto vencendo, inadimplência
- [ ] **Upload de documentos** — atas de assembleia, contratos
- [ ] **Múltiplos administradores** — por condomínio

### Infraestrutura para escalar

- [ ] **Deploy no Railway/Render** — colocar online com URL pública (gratuito para começar)
- [ ] **Trocar SQLite por PostgreSQL** — necessário para produção
- [ ] **Variáveis de ambiente** — proteger chaves e senhas
- [ ] **Domínio próprio** — imobflow.com.br

### Monetização

- [ ] **Plano Free** — 1 condomínio, até 30 unidades
- [ ] **Plano Pro** — R$ 49/mês — ilimitado + relatórios PDF
- [ ] **Plano Gestora** — R$ 149/mês — múltiplos condomínios + painel do morador
- [ ] **Integração Stripe/Asaas** — pagamento recorrente automatizado

---

## 🛠️ Tecnologias Usadas

| Tecnologia | Para que serve |
|---|---|
| **Flask** | Framework web — recebe requisições e serve páginas |
| **Flask-SQLAlchemy** | ORM — traduz Python para SQL (você não escreve SQL na mão) |
| **Flask-Login** | Gerencia sessão de usuário (quem está logado) |
| **Werkzeug** | Hash de senhas e utilitários web |
| **Jinja2** | Motor de templates HTML (já vem com Flask) |
| **Chart.js** | Gráficos interativos no navegador (JavaScript) |
| **SQLite** | Banco de dados local (arquivo .db) |

---

*Desenvolvido por Petterson — projeto de estudos evoluindo para produto real.*


---

## 🚀 Deploy no Railway (colocar online)

### O que é o Railway?
Railway é uma plataforma de hospedagem que pega seu código do GitHub e coloca ele rodando na internet automaticamente. Você não precisa configurar servidor. É gratuito até ~5 dólares de uso/mês.

Resultado: seu sistema ficará acessível em uma URL pública como `imobflow.up.railway.app`.

### Arquivos criados para o deploy

| Arquivo | Para que serve |
|---|---|
| `Procfile` | Diz ao Railway como iniciar o sistema (`gunicorn`) |
| `railway.json` | Configurações de build e restart automático |
| `config.py` | Lê variáveis de ambiente (SECRET_KEY, DATABASE_URL) |
| `.env.example` | Modelo das variáveis que precisam ser configuradas |
| `requirements.txt` | Agora inclui `gunicorn` (servidor de produção) |

### Por que Gunicorn?

Quando você roda `python run.py` localmente, o Flask usa um servidor simples que **não aguenta múltiplos usuários simultâneos**. O `gunicorn` é um servidor de produção que resolve isso — aguentando dezenas de usuários ao mesmo tempo.

### Passo a passo do deploy

**1. Sobe os novos arquivos para o GitHub**
```bash
git add .
git commit -m "feat: configura deploy no Railway"
git push
```

**2. Cria conta no Railway**
- Acesse: `railway.app`
- Clique em **"Start a New Project"**
- Escolha **"Deploy from GitHub repo"**
- Autorize o Railway a acessar seu GitHub
- Selecione o repositório `ImobFlow`

**3. Adiciona o banco de dados PostgreSQL**
- No painel do projeto, clique em **"+ New"**
- Escolha **"Database" → "PostgreSQL"**
- Railway cria o banco e define a variável `DATABASE_URL` automaticamente

**4. Configura as variáveis de ambiente**
- Clique no seu serviço Flask → aba **"Variables"**
- Adicione:
  ```
  SECRET_KEY = uma-string-aleatoria-longa-aqui
  FLASK_DEBUG = false
  ```
- A `DATABASE_URL` já é preenchida automaticamente pelo PostgreSQL

**5. Deploy automático**
- Após configurar, o Railway faz o deploy automaticamente
- Aguarde ~2 minutos
- Clique em **"View Logs"** para acompanhar
- Quando aparecer `Listening on 0.0.0.0:XXXX` → está no ar!

**6. Acessa a URL pública**
- Clique em **"Settings" → "Domains"**
- Clique em **"Generate Domain"**
- Sua URL pública estará disponível!

### Como gerar a SECRET_KEY

No terminal, rode:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copie o resultado e use como valor da `SECRET_KEY` no Railway.

### Deploy automático a cada push

Após configurar, **todo `git push` faz um novo deploy automaticamente**. Você atualiza o código, sobe para o GitHub e em 2 minutos o sistema online já está atualizado.

---

## 📋 Checklist completo antes de lançar

- [ ] Subiu os arquivos de deploy para o GitHub
- [ ] Criou conta no Railway
- [ ] Conectou o repositório ImobFlow
- [ ] Adicionou PostgreSQL ao projeto
- [ ] Configurou `SECRET_KEY` nas variáveis
- [ ] Deploy concluído sem erros nos logs
- [ ] Gerou domínio público
- [ ] Testou criar conta e fazer login na URL pública
