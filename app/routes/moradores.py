from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Morador, Unidade, Condominio
from ..middleware.security import tenant_ids_condominios
from datetime import date

moradores_bp = Blueprint("moradores", __name__, url_prefix="/moradores")


def _unidades_do_tenant():
    """Retorna apenas unidades do tenant logado."""
    ids_condos = tenant_ids_condominios()
    return Unidade.query.filter(
        Unidade.condominio_id.in_(ids_condos),
        Unidade.tenant_id == current_user.id,
    ).all()


@moradores_bp.route("/")
@login_required
def listar():
    ids_condos = tenant_ids_condominios()
    moradores = Morador.query.filter(
        Morador.unidade_id.in_(
            [u.id for u in Unidade.query.filter(
                Unidade.condominio_id.in_(ids_condos)
            ).all()]
        ),
        Morador.tenant_id == current_user.id,
    ).order_by(Morador.nome).all()
    return render_template("moradores/listar.html", moradores=moradores)


@moradores_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    unidades = _unidades_do_tenant()
    if request.method == "POST":
        nome       = request.form.get("nome", "").strip()
        tipo       = request.form.get("tipo", "proprietario")
        unidade_id = request.form.get("unidade_id", "")
        entrada    = request.form.get("data_entrada") or None

        if not nome or not unidade_id:
            flash("Nome e unidade são obrigatórios.", "danger")
            return render_template("moradores/form.html", unidades=unidades, morador=None)

        # Valida que a unidade pertence ao tenant (previne IDOR)
        unidade = Unidade.query.filter_by(
            id=unidade_id,
            tenant_id=current_user.id
        ).first_or_404()

        m = Morador(
            nome=nome,
            tipo=tipo,
            unidade_id=unidade.id,
            tenant_id=current_user.id,  # ← multi-tenant
            data_entrada=date.fromisoformat(entrada) if entrada else None,
        )
        # Campos sensíveis — setter chama CryptoService.encrypt automaticamente
        m.cpf      = request.form.get("cpf", "").strip() or None
        m.telefone = request.form.get("telefone", "").strip() or None
        m.email    = request.form.get("email", "").strip() or None

        db.session.add(m)
        db.session.commit()
        flash(f"Morador '{nome}' cadastrado com dados criptografados!", "success")
        return redirect(url_for("moradores.listar"))

    return render_template("moradores/form.html", unidades=unidades, morador=None)


@moradores_bp.route("/<string:mid>/desativar", methods=["POST"])
@login_required
def desativar(mid):
    m = Morador.query.filter_by(id=mid, tenant_id=current_user.id).first_or_404()
    m.ativo = False
    m.data_saida = date.today()
    db.session.commit()
    flash(f"'{m.nome}' marcado como saiu.", "info")
    return redirect(url_for("moradores.listar"))
