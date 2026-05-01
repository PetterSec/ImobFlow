"""
Models — Arquitetura Multi-tenant com isolamento por tenant_id
Todos os modelos carregam tenant_id e são filtrados automaticamente.
IDs públicos usam UUID para evitar enumeração (IDOR).
Campos sensíveis são armazenados criptografados (AES-256/Fernet).
"""
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
import sqlalchemy as sa

db = SQLAlchemy()


# ─── Tipo UUID cross-DB (PostgreSQL nativo / SQLite como CHAR) ────────────────

class GUID(TypeDecorator):
    """UUID que funciona tanto em PostgreSQL quanto em SQLite."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(str(value)))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(str(value))


def _new_uuid():
    return str(uuid.uuid4())


# ─── USUÁRIO ──────────────────────────────────────────────────────────────────

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id          = db.Column(GUID(), primary_key=True, default=_new_uuid)
    nome        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha_hash  = db.Column(db.String(256), nullable=False)
    perfil      = db.Column(db.String(20), default="sindico", nullable=False)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ── SaaS / Stripe ─────────────────────────────────────────────────────────
    plano_atual       = db.Column(db.String(20), default="free", nullable=False)
    status_pagamento  = db.Column(db.String(20), default="ativo", nullable=False)
    stripe_customer_id = db.Column(db.String(100), nullable=True, unique=True)
    plano_expira_em   = db.Column(db.DateTime, nullable=True)

    condominios = db.relationship("Condominio", backref="dono", lazy="dynamic",
                                  cascade="all, delete-orphan")
    lancamentos = db.relationship("Lancamento", backref="autor", lazy="dynamic",
                                  cascade="all, delete-orphan")

    def set_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    @property
    def limites(self) -> dict:
        from flask import current_app
        return current_app.config["PLAN_LIMITS"].get(self.plano_atual, {"condominios": 1, "unidades": 30})

    def pode_criar_condominio(self) -> bool:
        return self.condominios.count() < self.limites["condominios"]

    def pode_criar_unidade(self, condominio) -> bool:
        total = sum(c.total_unidades for c in self.condominios)
        return total < self.limites["unidades"]

    def __repr__(self):
        return f"<Usuario {self.email} [{self.plano_atual}]>"


# ─── CONDOMÍNIO ───────────────────────────────────────────────────────────────

class Condominio(db.Model):
    __tablename__ = "condominios"

    id             = db.Column(GUID(), primary_key=True, default=_new_uuid)
    nome           = db.Column(db.String(150), nullable=False)
    endereco       = db.Column(db.String(250))
    cidade         = db.Column(db.String(100))
    cep            = db.Column(db.String(10))
    total_unidades = db.Column(db.Integer, default=0)
    criado_em      = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Multi-tenant: chave de isolamento ──────────────────────────────────────
    tenant_id = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

    unidades    = db.relationship("Unidade", backref="condominio", lazy="dynamic",
                                  cascade="all, delete-orphan")
    lancamentos = db.relationship("Lancamento", backref="condominio", lazy="dynamic",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Condominio {self.nome}>"


# ─── UNIDADE ──────────────────────────────────────────────────────────────────

class Unidade(db.Model):
    __tablename__ = "unidades"

    id            = db.Column(GUID(), primary_key=True, default=_new_uuid)
    identificacao = db.Column(db.String(20), nullable=False)
    tipo          = db.Column(db.String(20), default="apto")
    condominio_id = db.Column(GUID(), db.ForeignKey("condominios.id"), nullable=False, index=True)

    # ── Multi-tenant ───────────────────────────────────────────────────────────
    tenant_id = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

    morador = db.relationship("Morador", backref="unidade", uselist=False,
                              cascade="all, delete-orphan")


# ─── MORADOR (campos sensíveis criptografados) ────────────────────────────────

class Morador(db.Model):
    __tablename__ = "moradores"

    id         = db.Column(GUID(), primary_key=True, default=_new_uuid)
    nome       = db.Column(db.String(150), nullable=False)

    # Campos sensíveis — armazenados CRIPTOGRAFADOS no banco (AES-256)
    _cpf       = db.Column("cpf",      db.Text, nullable=True)
    _telefone  = db.Column("telefone", db.Text, nullable=True)
    _email     = db.Column("email",    db.Text, nullable=True)

    tipo        = db.Column(db.String(20), default="proprietario")
    data_entrada = db.Column(db.Date)
    data_saida   = db.Column(db.Date, nullable=True)
    ativo        = db.Column(db.Boolean, default=True)
    unidade_id   = db.Column(GUID(), db.ForeignKey("unidades.id"), nullable=False, index=True)
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Multi-tenant ───────────────────────────────────────────────────────────
    tenant_id = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

    # ── Properties que encriptam/decriptam transparentemente ──────────────────

    @property
    def cpf(self) -> str | None:
        from .services.crypto import CryptoService
        return CryptoService.decrypt(self._cpf)

    @cpf.setter
    def cpf(self, valor: str | None):
        from .services.crypto import CryptoService
        self._cpf = CryptoService.encrypt(valor) if valor else None

    @property
    def telefone(self) -> str | None:
        from .services.crypto import CryptoService
        return CryptoService.decrypt(self._telefone)

    @telefone.setter
    def telefone(self, valor: str | None):
        from .services.crypto import CryptoService
        self._telefone = CryptoService.encrypt(valor) if valor else None

    @property
    def email(self) -> str | None:
        from .services.crypto import CryptoService
        return CryptoService.decrypt(self._email)

    @email.setter
    def email(self, valor: str | None):
        from .services.crypto import CryptoService
        self._email = CryptoService.encrypt(valor) if valor else None

    def __repr__(self):
        return f"<Morador {self.nome}>"


# ─── LANÇAMENTO FINANCEIRO ────────────────────────────────────────────────────

class Lancamento(db.Model):
    __tablename__ = "lancamentos"

    id          = db.Column(GUID(), primary_key=True, default=_new_uuid)
    descricao   = db.Column(db.String(200), nullable=False)
    valor       = db.Column(db.Float, nullable=False)
    tipo        = db.Column(db.String(10), nullable=False)
    categoria   = db.Column(db.String(50), default="Outros")
    data        = db.Column(db.Date, default=datetime.utcnow)
    pago        = db.Column(db.Boolean, default=False)
    observacao  = db.Column(db.Text, nullable=True)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    condominio_id = db.Column(GUID(), db.ForeignKey("condominios.id"), nullable=False, index=True)
    usuario_id    = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

    # ── Multi-tenant ───────────────────────────────────────────────────────────
    tenant_id = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

    def __repr__(self):
        return f"<Lancamento {self.descricao} R${self.valor}>"


# ─── Categorias padrão ────────────────────────────────────────────────────────

CATEGORIAS_DESPESA = [
    "Manutenção", "Limpeza", "Segurança", "Energia", "Água",
    "Internet", "Elevador", "Jardinagem", "Seguro", "Administração", "Outros",
]

CATEGORIAS_RECEITA = [
    "Taxa Condominial", "Multa", "Reserva de Área", "Aluguel", "Outros",
]
