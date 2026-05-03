# Monetização, Stripe e escala do ImobFlow

Este documento é um **guia vivo**: você pode (e deve) alterar preços, textos e código conforme seu modelo de negócio. Nada aqui é “travado” no código além das variáveis descritas.

---

## 1. Estado atual do produto

| Área | Situação |
|------|----------|
| Multi-tenant, login, planos no banco | Implementado (`plano_atual`, limites em `PLAN_LIMITS`) |
| Página de planos + checkout Stripe | Implementado em `app/routes/saas.py` |
| Webhook Stripe | Implementado; **CSRF isento** só nesta rota |
| Recebimento de dinheiro | Via **Stripe** → repasse para sua **conta bancária** (cadastro no Stripe) |
| Anúncios no plano Free | **Opcional** — slot AdSense no layout (desligado por padrão) |

O que **não** é “SaaS enterprise completo” ainda: observabilidade centralizada (Sentry), filas de trabalho, Alembic/migrações formais, portal do morador, contratos/termos legais revisados por advogado, etc. Isso é normal em MVP — evolua por prioridade.

---

## 2. Como o cliente te paga e como você recebe

### Fluxo resumido

1. Você cria uma **conta Stripe** (Brasil: Stripe suporta modelo conforme sua região; confira [stripe.com](https://stripe.com) para países e requisitos).
2. No **Dashboard Stripe**, você cria **Produtos** (ex.: “ImobFlow Pro”) e **Preços** mensais (ex.: R$ 79). Cada preço tem um ID **`price_...`**.
3. Você copia esses IDs para as variáveis **`STRIPE_PRICE_ID_PRO`** e **`STRIPE_PRICE_ID_GESTORA`** no Railway (ou `.env`).
4. O usuário clica em **Assinar** → o app abre o **Stripe Checkout** (página hospedada pela Stripe, PCI-compliant).
5. O cliente paga com cartão; o Stripe confirma e envia eventos para seu **`/saas/webhook/stripe`**.
6. O webhook atualiza `usuario.plano_atual` no banco.
7. O Stripe **transfere** o saldo para a conta bancária que você cadastrou no Stripe (prazos e taxas dependem do país e do produto Stripe).

**Você não armazena número de cartão** — o Stripe cuida disso.

### Variáveis obrigatórias para pagamentos funcionarem

| Variável | Onde obter |
|----------|------------|
| `STRIPE_SECRET_KEY` | Stripe Dashboard → Developers → API keys (`sk_live_...` ou `sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Developers → Webhooks → adicionar endpoint `https://SEU_DOMINIO/saas/webhook/stripe` → copiar **Signing secret** (`whsec_...`) |
| `STRIPE_PRICE_ID_PRO` | Produtos → Preço Pro → copiar **Price ID** (`price_...`) |
| `STRIPE_PRICE_ID_GESTORA` | Idem para Gestora |

**Teste vs produção:** use chaves `sk_test_` e webhook de teste enquanto desenvolve; em produção, `sk_live_` e endpoint de webhook em URL pública HTTPS.

### URL do webhook no Railway

- Path fixo: **`/saas/webhook/stripe`**
- Exemplo: `https://imobflow-production.up.railway.app/saas/webhook/stripe`
- Eventos recomendados: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted` (já tratados no código).

---

## 3. Anúncios no plano Free (Google AdSense)

### Ideia

Usuários **free** veem um bloco de anúncio; **Pro/Gestora** não veem — incentiva upgrade e pode gerar receita marginal.

### Requisitos reais

1. **Conta Google AdSense** aprovada para o **site/domínio** do seu app.
2. Políticas do Google: conteúdo suficiente, privacidade, cookies — leia as políticas atuais do Google.
3. Áreas **logadas** às vezes têm **restrições** ou menor performance de anúncios; muitos produtos monetizam mais com **landing pública** + AdSense e mantêm o app sem anúncio intrusivo. Você escolhe.

### Como ativar no ImobFlow

1. No AdSense, crie uma unidade de anúncio **Display** e anote:
   - **Client ID** (`ca-pub-...`)
   - **Ad slot** (ID do bloco)
2. No Railway (variáveis do serviço web):

```env
SHOW_ADS_ON_FREE_PLAN=true
GOOGLE_ADSENSE_CLIENT=ca-pub-XXXXXXXX
GOOGLE_ADSENSE_SLOT=1234567890
```

3. Redeploy.

O layout injeta o script do AdSense **apenas** para usuários autenticados com `plano_atual == 'free'`.

### Vídeo (YouTube Ads / instream)

Monetizar **vídeo** dentro do app costuma exigir integração com **Google IMA SDK**, parcerias ou plataformas de vídeo — não é só colar AdSense. Para MVP, o mais simples é **display** (banner) via AdSense; vídeo pode ser fase 2.

---

## 4. Segurança SaaS (checklist prático)

- **HTTPS** obrigatório em produção (Railway fornece).
- **Segredos** só em variáveis de ambiente — nunca no Git.
- **Webhook Stripe:** validação por assinatura (`STRIPE_WEBHOOK_SECRET`) — já usada no código.
- **CSRF** em formulários; **exceção** apenas no webhook Stripe (já configurada).
- **LGPD:** campos sensíveis de moradores via `CryptoService`; política de privacidade e termos são sua responsabilidade legal.
- **Limites de plano:** decorator `enforce_plan` em rotas críticas — revisar ao adicionar features.

---

## 5. O que refatorar depois (prioridade sugerida)

1. **Portal do morador** — novo papel de usuário + rotas isoladas.  
2. **Alembic** — migrações de schema em vez de só `create_all()`.  
3. **Fila (Redis/Celery)** — e-mails, PDFs pesados, webhooks longos.  
4. **Sentry** ou similar — erros 500 em produção.  
5. **Customer Portal Stripe** — permitir que o cliente cancele/altere cartão sem seu suporte.  
6. **Testes de integração Stripe** — mocks ou Stripe CLI no CI.

---

## 6. Liberdade para mudar

- Preços em **R$** na interface (`saas/planos.html`) são só marketing até bater com os **preços reais** criados no Stripe.  
- Limites de plano estão em `config.PLAN_LIMITS` e no modelo `Usuario`.  
- Textos legais (“Assinar”, garantias) devem refletir o que você realmente oferece.

*Última revisão alinhada ao código em `app/routes/saas.py`, `config.py` e `run.py` (context processor de anúncios).*
