"""
Portal do Morador — acesso restrito em /portal
Login separado: morador usa CPF + senha cadastrada pelo síndico.
Morador vê APENAS dados da sua própria unidade.
"""
from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, session)
from functools import wraps
from ..models import db, Morador, Cobranca, Comunicado, Unidade, Condominio
from ..middleware.security import rate_limit

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")

# ── Sessão isolada do portal (não mistura com admin) ─────────────────────────

def portal_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("portal_morador_id"):
            flash("Faça login para acessar o portal.", "info")
            return redirect(url_for("portal.login"))
        return f(*args, **kwargs)
    return decorated

def get_morador_logado() -> Morador | None:
    mid = session.get("portal_morador_id")
    if not mid:
        return None
    return db.session.get(Morador, mid)

# ── Login ─────────────────────────────────────────────────────────────────────

@portal_bp.route("/login", methods=["GET", "POST"])
@rate_limit(max_calls=10, window=60)
def login():
    if session.get("portal_morador_id"):
        return redirect(url_for("portal.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        # Busca por email criptografado — decripta para comparar
        from ..services.crypto import CryptoService
        moradores = Morador.query.filter_by(ativo=True).all()
        morador = next(
            (m for m in moradores
             if CryptoService.decrypt(m._email) == email),
            None
        )

        if morador and morador.check_senha_portal(senha):
            session["portal_morador_id"] = str(morador.id)
            session.permanent = True
            return redirect(url_for("portal.dashboard"))

        flash("E-mail ou senha incorretos.", "danger")

    return render_template("portal/login.html")


@portal_bp.route("/logout")
def logout():
    session.pop("portal_morador_id", None)
    flash("Você saiu do portal.", "info")
    return redirect(url_for("portal.login"))

# ── Dashboard do morador ──────────────────────────────────────────────────────

@portal_bp.route("/")
@portal_bp.route("/dashboard")
@portal_login_required
def dashboard():
    morador   = get_morador_logado()
    unidade   = morador.unidade
    condo     = unidade.condominio

    # Cobranças — em aberto e pagas (últimas 6)
    pendentes = (Cobranca.query
                 .filter_by(morador_id=morador.id, pago=False)
                 .order_by(Cobranca.vencimento)
                 .all())
    pagas = (Cobranca.query
             .filter_by(morador_id=morador.id, pago=True)
             .order_by(Cobranca.pago_em.desc())
             .limit(6).all())

    # Comunicados do condomínio (últimos 5)
    comunicados = (Comunicado.query
                   .filter_by(condominio_id=condo.id)
                   .order_by(Comunicado.criado_em.desc())
                   .limit(5).all())

    total_pendente = sum(c.valor for c in pendentes)

    return render_template("portal/dashboard.html",
        morador=morador,
        unidade=unidade,
        condo=condo,
        pendentes=pendentes,
        pagas=pagas,
        comunicados=comunicados,
        total_pendente=total_pendente,
    )
