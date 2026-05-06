from flask import Flask, jsonify
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from .models import db, Usuario
from config import Config

login_manager = LoginManager()
csrf = CSRFProtect()

CSP = {
    "default-src": "'self'",
    "script-src":  ["'self'", "cdn.jsdelivr.net", "accounts.google.com"],
    "style-src":   ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
    "font-src":    ["'self'", "fonts.gstatic.com"],
    "img-src":     ["'self'", "data:", "*.googleusercontent.com"],
    "connect-src": "'self'",
    "frame-src":   ["accounts.google.com"],
    "frame-ancestors": "'none'",
}

def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="../static")
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    Talisman(
        app,
        force_https=not app.config["DEBUG"],
        strict_transport_security=not app.config["DEBUG"],
        content_security_policy=CSP,
        x_content_type_options=True,
        x_xss_protection=True,
    )

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, user_id)

    # ── Blueprints ─────────────────────────────────────────────────────────
    from .routes.auth        import auth_bp, init_oauth
    from .routes.dashboard   import dashboard_bp
    from .routes.condominios import condominios_bp
    from .routes.moradores   import moradores_bp
    from .routes.financeiro  import financeiro_bp
    from .routes.saas        import saas_bp
    from .routes.pwa         import pwa_bp
    from .routes.portal      import portal_bp

    # Inicia OAuth ANTES de registrar o blueprint
    init_oauth(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(condominios_bp)
    app.register_blueprint(moradores_bp)
    app.register_blueprint(financeiro_bp)
    app.register_blueprint(saas_bp)
    app.register_blueprint(pwa_bp)
    app.register_blueprint(portal_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    with app.app_context():
        db.create_all()

    return app
