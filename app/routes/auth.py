"""
Autenticação — login tradicional + Google OAuth 2.0
"""
from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, session, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from ..models import db, Usuario
from ..middleware.security import rate_limit

auth_bp = Blueprint("auth", __name__)
oauth    = OAuth()


def init_oauth(app):
    """Registra o provider Google. Chamado no app factory."""
    oauth.init_app(app)
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


# ── Login tradicional ─────────────────────────────────────────────────────────

@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
@rate_limit(max_calls=10, window=60)
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        user  = Usuario.query.filter_by(email=email).first()
        if user and user.check_senha(senha):
            login_user(user, remember=True)
            return redirect(url_for("dashboard.index"))
        flash("E-mail ou senha incorretos.", "danger")
    return render_template("auth/login.html")


# ── Google OAuth ──────────────────────────────────────────────────────────────

@auth_bp.route("/login/google")
def login_google():
    """Redireciona o usuário para a tela de login do Google."""
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/login/google/callback")
def google_callback():
    """Recebe o token do Google e faz login/cadastro automático."""
    try:
        token    = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or oauth.google.userinfo()
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {e}")
        flash("Falha ao autenticar com o Google. Tente novamente.", "danger")
        return redirect(url_for("auth.login"))

    google_id = userinfo.get("sub")
    email     = userinfo.get("email", "").lower()
    nome      = userinfo.get("name", email.split("@")[0])

    # Busca por google_id ou email
    user = (Usuario.query.filter_by(google_id=google_id).first()
            or Usuario.query.filter_by(email=email).first())

    if user:
        # Vincula o google_id se ainda não tiver
        if not user.google_id:
            user.google_id = google_id
            db.session.commit()
    else:
        # Cria conta automaticamente
        user = Usuario(
            nome=nome,
            email=email,
            google_id=google_id,
            perfil="sindico",
        )
        user.set_senha(google_id + current_app.config["SECRET_KEY"])
        db.session.add(user)
        db.session.commit()
        flash(f"Bem-vindo ao ImobFlow, {nome}! Conta criada com sucesso.", "success")

    login_user(user, remember=True)
    return redirect(url_for("dashboard.index"))


# ── Cadastro ──────────────────────────────────────────────────────────────────

@auth_bp.route("/cadastro", methods=["GET", "POST"])
@rate_limit(max_calls=5, window=60)
def cadastro():
    if request.method == "POST":
        nome   = request.form.get("nome",   "").strip()
        email  = request.form.get("email",  "").strip().lower()
        senha  = request.form.get("senha",  "")
        perfil = request.form.get("perfil", "sindico")

        if not nome or not email or not senha:
            flash("Preencha todos os campos.", "danger")
            return render_template("auth/cadastro.html")
        if len(senha) < 6:
            flash("Senha precisa ter ao menos 6 caracteres.", "danger")
            return render_template("auth/cadastro.html")
        if Usuario.query.filter_by(email=email).first():
            flash("E-mail já cadastrado.", "danger")
            return render_template("auth/cadastro.html")

        user = Usuario(nome=nome, email=email, perfil=perfil)
        user.set_senha(senha)
        db.session.add(user)
        db.session.commit()
        flash("Conta criada! Faça login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/cadastro.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
