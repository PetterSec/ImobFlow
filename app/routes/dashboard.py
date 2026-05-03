from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models import db, Condominio, Lancamento, Morador, Unidade
from sqlalchemy import extract, func
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def index():
    condominios = Condominio.query.filter_by(tenant_id=current_user.id).all()
    ids = [c.id for c in condominios]

    mes_atual = datetime.utcnow().month
    ano_atual = datetime.utcnow().year

    # Contagem de moradores ativos nos condomínios do usuário (join corrigido)
    total_moradores = (
        db.session.query(func.count(Morador.id))
        .join(Unidade, Morador.unidade_id == Unidade.id)
        .join(Condominio, Unidade.condominio_id == Condominio.id)
        .filter(Condominio.tenant_id == current_user.id, Morador.ativo == True)
        .scalar() or 0
    )

    receitas_mes = db.session.query(func.sum(Lancamento.valor)).filter(
        Lancamento.condominio_id.in_(ids),
        Lancamento.tipo == "receita",
        extract("month", Lancamento.data) == mes_atual,
        extract("year", Lancamento.data) == ano_atual,
    ).scalar() or 0.0

    despesas_mes = db.session.query(func.sum(Lancamento.valor)).filter(
        Lancamento.condominio_id.in_(ids),
        Lancamento.tipo == "despesa",
        extract("month", Lancamento.data) == mes_atual,
        extract("year", Lancamento.data) == ano_atual,
    ).scalar() or 0.0

    ultimos = Lancamento.query.filter(
        Lancamento.condominio_id.in_(ids)
    ).order_by(Lancamento.criado_em.desc()).limit(5).all()

    cat_data = db.session.query(
        Lancamento.categoria, func.sum(Lancamento.valor)
    ).filter(
        Lancamento.condominio_id.in_(ids),
        Lancamento.tipo == "despesa",
        extract("month", Lancamento.data) == mes_atual,
        extract("year", Lancamento.data) == ano_atual,
    ).group_by(Lancamento.categoria).all()

    return render_template("dashboard.html",
        total_condominios=len(condominios),
        total_moradores=total_moradores,
        receitas_mes=receitas_mes,
        despesas_mes=despesas_mes,
        saldo_mes=receitas_mes - despesas_mes,
        ultimos=ultimos,
        cat_labels=[c[0] for c in cat_data],
        cat_valores=[c[1] for c in cat_data],
        condominios=condominios,
    )
