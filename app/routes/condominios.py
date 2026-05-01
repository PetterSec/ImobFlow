from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Condominio, Unidade
from ..middleware.security import enforce_plan, get_tenant_condominio
from ..services.webhook import disparar_webhook

condominios_bp = Blueprint("condominios", __name__, url_prefix="/condominios")


@condominios_bp.route("/")
@login_required
def listar():
    # Multi-tenant: filtra por tenant_id — nunca expõe dados de outros usuários
    condominios = Condominio.query.filter_by(
        tenant_id=current_user.id
    ).order_by(Condominio.nome).all()
    return render_template("condominios/listar.html", condominios=condominios)


@condominios_bp.route("/novo", methods=["GET", "POST"])
@login_required
@enforce_plan("condominio")  # bloqueia se plano atingiu limite
def novo():
    if request.method == "POST":
        nome   = request.form.get("nome", "").strip()
        end    = request.form.get("endereco", "").strip()
        cidade = request.form.get("cidade", "").strip()
        cep    = request.form.get("cep", "").strip()
        unids  = int(request.form.get("total_unidades", 0) or 0)

        if not nome:
            flash("Nome é obrigatório.", "danger")
            return render_template("condominios/form.html", condo=None)

        condo = Condominio(
            nome=nome, endereco=end, cidade=cidade, cep=cep,
            total_unidades=unids,
            tenant_id=current_user.id,  # ← multi-tenant
        )
        db.session.add(condo)
        db.session.flush()

        # Cria unidades com tenant_id propagado
        for i in range(1, unids + 1):
            db.session.add(Unidade(
                identificacao=str(i),
                condominio_id=condo.id,
                tenant_id=current_user.id,  # ← multi-tenant
            ))

        db.session.commit()
        flash(f"Condomínio '{nome}' criado com {unids} unidades!", "success")

        # Dispara webhook n8n de forma assíncrona
        disparar_webhook("condominio.criado", {
            "id": str(condo.id),
            "nome": condo.nome,
            "cidade": condo.cidade,
            "total_unidades": condo.total_unidades,
            "tenant_email": current_user.email,
        })

        return redirect(url_for("condominios.listar"))

    return render_template("condominios/form.html", condo=None)


@condominios_bp.route("/<string:cid>")
@login_required
def detalhe(cid):
    # get_tenant_condominio garante isolamento — retorna 404 se for de outro tenant
    condo = get_tenant_condominio(cid)
    return render_template("condominios/detalhe.html", condo=condo)


@condominios_bp.route("/<string:cid>/deletar", methods=["POST"])
@login_required
def deletar(cid):
    condo = get_tenant_condominio(cid)
    db.session.delete(condo)
    db.session.commit()
    flash("Condomínio removido.", "info")
    return redirect(url_for("condominios.listar"))
