from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from ..models import db, Usuario

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        user  = Usuario.query.filter_by(email=email).first()
        if user and user.check_senha(senha):
            login_user(user)
            return redirect(url_for("dashboard.index"))
        flash("E-mail ou senha incorretos.", "danger")
    return render_template("auth/login.html")

@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome   = request.form.get("nome", "").strip()
        email  = request.form.get("email", "").strip().lower()
        senha  = request.form.get("senha", "")
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
