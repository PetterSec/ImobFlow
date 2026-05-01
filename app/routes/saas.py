"""
Rotas SaaS — planos, upgrade e webhooks do Stripe
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from ..models import db, Usuario
from ..middleware.security import rate_limit

saas_bp = Blueprint("saas", __name__, url_prefix="/saas")


@saas_bp.route("/planos")
@login_required
def planos():
    return render_template("saas/planos.html")


@saas_bp.route("/criar-checkout/<string:plano>", methods=["POST"])
@login_required
@rate_limit(max_calls=5, window=60)
def criar_checkout(plano: str):
    """Cria sessão de checkout no Stripe."""
    stripe_key = current_app.config.get("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        flash("Pagamentos não configurados ainda. Em breve!", "info")
        return redirect(url_for("saas.planos"))

    import stripe
    stripe.api_key = stripe_key

    PRICE_IDS = {
        "pro":     "price_pro_mensal",     # substitua pelo ID real no Stripe
        "gestora": "price_gestora_mensal",
    }

    if plano not in PRICE_IDS:
        flash("Plano inválido.", "danger")
        return redirect(url_for("saas.planos"))

    try:
        # Cria ou reutiliza customer no Stripe
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.nome,
                metadata={"tenant_id": str(current_user.id)},
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()

        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": PRICE_IDS[plano], "quantity": 1}],
            mode="subscription",
            success_url=url_for("saas.sucesso", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("saas.planos", _external=True),
        )
        return redirect(session.url, code=303)

    except Exception as e:
        current_app.logger.error(f"Stripe error: {e}")
        flash("Erro ao processar pagamento. Tente novamente.", "danger")
        return redirect(url_for("saas.planos"))


@saas_bp.route("/sucesso")
@login_required
def sucesso():
    flash("Assinatura ativada com sucesso! Bem-vindo ao plano Pro 🎉", "success")
    return redirect(url_for("dashboard.index"))


@saas_bp.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    """Recebe eventos do Stripe e atualiza plano do usuário."""
    import stripe
    stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY", "")
    webhook_secret = current_app.config.get("STRIPE_WEBHOOK_SECRET", "")

    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
    except Exception:
        return jsonify({"error": "assinatura inválida"}), 400

    # Atualiza plano quando assinatura é criada/renovada
    if event["type"] in ("customer.subscription.created", "customer.subscription.updated"):
        sub = event["data"]["object"]
        customer_id = sub["customer"]
        status = sub["status"]

        usuario = Usuario.query.filter_by(stripe_customer_id=customer_id).first()
        if usuario:
            # Determina plano pelo price ID
            price_id = sub["items"]["data"][0]["price"]["id"]
            if "gestora" in price_id:
                usuario.plano_atual = "gestora"
            else:
                usuario.plano_atual = "pro"
            usuario.status_pagamento = "ativo" if status == "active" else "inativo"
            db.session.commit()

    elif event["type"] == "customer.subscription.deleted":
        customer_id = event["data"]["object"]["customer"]
        usuario = Usuario.query.filter_by(stripe_customer_id=customer_id).first()
        if usuario:
            usuario.plano_atual = "free"
            usuario.status_pagamento = "cancelado"
            db.session.commit()

    return jsonify({"received": True}), 200
