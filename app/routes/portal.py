"""
Portal do Morador — acesso separado via token seguro
O morador acessa seus lançamentos sem ter conta de administrador.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from ..models import db, Morador, Lancamento, Condominio, Unidade
import hashlib, secrets

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")

def _gerar_token_acesso(morador_id: str, email: str) -> str:
    """Token determinístico baseado em ID + email + secret."""
    from flask import current_app
    base = f"{morador_id}:{email}:{current_app.config['SECRET_KEY']}"
    return hashlib.sha256(base.encode()).hexdigest()[:32]


@portal_bp.route("/")
def index():
    return render_template("portal/index.html")


@portal_bp.route("/acesso", methods=["GET", "POST"])
def acesso():
    """Morador informa e-mail para receber link de acesso."""
    if request.method == "POST":
        email_input = request.form.get("email", "").strip().lower()
        # Busca morador pelo e-mail descriptografado
        moradores = Morador.query.filter_by(ativo=True).all()
        morador_encontrado = None
        for m in moradores:
            if m.email and m.email.lower() == email_input:
                morador_encontrado = m
                break

        if morador_encontrado:
            token = _gerar_token_acesso(str(morador_encontrado.id), email_input)
            # Em produção: enviar por e-mail. Por ora, redireciona direto.
            flash("Acesso autorizado! Em produção, um link seria enviado ao seu e-mail.", "success")
            return redirect(url_for("portal.painel", morador_id=str(morador_encontrado.id), token=token))
        else:
            flash("E-mail não encontrado. Verifique com o síndico.", "danger")

    return render_template("portal/acesso.html")


@portal_bp.route("/painel/<string:morador_id>")
def painel(morador_id: str):
    """Painel do morador — valida token antes de exibir."""
    token = request.args.get("token", "")
    morador = Morador.query.filter_by(id=morador_id, ativo=True).first_or_404()

    # Valida token — evita acesso não autorizado
    if not morador.email:
        abort(403)
    token_esperado = _gerar_token_acesso(morador_id, morador.email.lower())
    if not secrets.compare_digest(token, token_esperado):
        abort(403)

    unidade = morador.unidade
    condo = unidade.condominio if unidade else None

    # Lançamentos do condomínio (visão pública — sem dados de outros moradores)
    lancamentos = []
    if condo:
        lancamentos = Lancamento.query.filter_by(
            condominio_id=condo.id
        ).order_by(Lancamento.data.desc()).limit(24).all()

    receitas = sum(l.valor for l in lancamentos if l.tipo == "receita")
    despesas = sum(l.valor for l in lancamentos if l.tipo == "despesa")

    return render_template("portal/painel.html",
        morador=morador,
        unidade=unidade,
        condo=condo,
        lancamentos=lancamentos,
        receitas=receitas,
        despesas=despesas,
        saldo=receitas - despesas,
        token=token,
    )
