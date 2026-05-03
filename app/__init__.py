"""
App factory — monta a aplicação Flask com todas as extensões de segurança.
"""
import uuid

from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from werkzeug.exceptions import HTTPException

from .models import db, Usuario
from config import Config

login_manager = LoginManager()
csrf = CSRFProtect()


# ── Content Security Policy ────────────────────────────────────────────────────
CSP = {
    "default-src": "'self'",
    "script-src": [
        "'self'",
        "'unsafe-inline'",          # AdSense usa push inline no partial (mitigar depois com nonce)
        "cdn.jsdelivr.net",       # Chart.js
        "pagead2.googlesyndication.com",
    ],
    "style-src": [
        "'self'",
        "'unsafe-inline'",        # necessário para estilos inline
        "fonts.googleapis.com",
    ],
    "font-src": [
        "'self'",
        "fonts.gstatic.com",
    ],
    "img-src": ["'self'", "data:", "pagead2.googlesyndication.com"],
    "connect-src": "'self'",
    "frame-ancestors": "'none'",  # previne clickjacking
}


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="../static")
    app.config.from_object(config_class)

    # ── Extensões core ─────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ── Talisman — Security Headers + HSTS ────────────────────────────────────
    # Em dev (DEBUG=True) não força HTTPS para não quebrar localhost
    Talisman(
        app,
        force_https=not app.config["DEBUG"],
        strict_transport_security=not app.config["DEBUG"],
        strict_transport_security_max_age=31536000,  # 1 ano
        content_security_policy=CSP,
        referrer_policy="strict-origin-when-cross-origin",
        x_content_type_options=True,
        x_xss_protection=True,
    )

    # ── Login manager ──────────────────────────────────────────────────────────
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para continuar."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None
        try:
            uid = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return None
        return db.session.get(Usuario, uid)

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.condominios import condominios_bp
    from .routes.moradores import moradores_bp
    from .routes.financeiro import financeiro_bp
    from .routes.saas import saas_bp
    from .routes.pwa import pwa_bp
    # portal_bp será adicionado quando app/routes/portal.py for implementado

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(condominios_bp)
    app.register_blueprint(moradores_bp)
    app.register_blueprint(financeiro_bp)
    app.register_blueprint(saas_bp)
    app.register_blueprint(pwa_bp)

    # Webhook Stripe envia POST sem token CSRF — isentar só esta rota
    from .routes.saas import stripe_webhook
    csrf.exempt(stripe_webhook)

    # ── Health check (Railway / Docker) ────────────────────────────────────────
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(Exception)
    def handle_unhandled_exception(exc):
        if isinstance(exc, HTTPException):
            return exc
        if app.debug:
            raise exc
        app.logger.exception(
            "Erro não tratado em %s %s",
            request.method,
            request.path,
        )
        return render_template("errors/500.html"), 500

    # ── Cria tabelas ───────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app