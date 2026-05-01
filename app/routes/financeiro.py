from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from ..models import db, Lancamento, Condominio, CATEGORIAS_DESPESA, CATEGORIAS_RECEITA
from datetime import date
import csv, io

financeiro_bp = Blueprint("financeiro", __name__, url_prefix="/financeiro")

def _condominios():
    return Condominio.query.filter_by(usuario_id=current_user.id).all()

@financeiro_bp.route("/")
@login_required
def listar():
    ids   = [c.id for c in _condominios()]
    tipo  = request.args.get("tipo", "")
    cid   = request.args.get("condo", "")
    query = Lancamento.query.filter(Lancamento.condominio_id.in_(ids))
    if tipo:
        query = query.filter_by(tipo=tipo)
    if cid:
        query = query.filter_by(condominio_id=int(cid))
    lancamentos = query.order_by(Lancamento.data.desc()).all()
    return render_template("financeiro/listar.html",
        lancamentos=lancamentos,
        condominios=_condominios(),
        filtro_tipo=tipo, filtro_condo=cid,
    )

@financeiro_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    condominios = _condominios()
    if request.method == "POST":
        descricao     = request.form.get("descricao", "").strip()
        valor_str     = request.form.get("valor", "0").replace(",", ".")
        tipo          = request.form.get("tipo", "despesa")
        categoria     = request.form.get("categoria", "Outros")
        data_str      = request.form.get("data") or str(date.today())
        pago          = request.form.get("pago") == "on"
        observacao    = request.form.get("observacao", "").strip()
        condominio_id = int(request.form.get("condominio_id", 0))

        try:
            valor = float(valor_str)
            if valor <= 0: raise ValueError
        except ValueError:
            flash("Valor inválido.", "danger")
            return render_template("financeiro/form.html",
                condominios=condominios,
                cats_despesa=CATEGORIAS_DESPESA,
                cats_receita=CATEGORIAS_RECEITA,
            )

        l = Lancamento(
            descricao=descricao, valor=valor, tipo=tipo,
            categoria=categoria, data=date.fromisoformat(data_str),
            pago=pago, observacao=observacao,
            condominio_id=condominio_id, usuario_id=current_user.id,
        )
        db.session.add(l)
        db.session.commit()
        flash("Lançamento registrado!", "success")
        return redirect(url_for("financeiro.listar"))

    return render_template("financeiro/form.html",
        condominios=condominios,
        cats_despesa=CATEGORIAS_DESPESA,
        cats_receita=CATEGORIAS_RECEITA,
    )

@financeiro_bp.route("/<int:lid>/deletar", methods=["POST"])
@login_required
def deletar(lid):
    l = Lancamento.query.get_or_404(lid)
    db.session.delete(l)
    db.session.commit()
    flash("Lançamento removido.", "info")
    return redirect(url_for("financeiro.listar"))

@financeiro_bp.route("/exportar-csv")
@login_required
def exportar_csv():
    ids = [c.id for c in _condominios()]
    lancamentos = Lancamento.query.filter(Lancamento.condominio_id.in_(ids)).order_by(Lancamento.data.desc()).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["ID", "Descrição", "Valor", "Tipo", "Categoria", "Data", "Pago"])
    for l in lancamentos:
        w.writerow([l.id, l.descricao, f"{l.valor:.2f}", l.tipo, l.categoria, l.data, "Sim" if l.pago else "Não"])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=lancamentos.csv"
    response.headers["Content-type"] = "text/csv"
    return response
