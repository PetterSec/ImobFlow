import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

db = SQLAlchemy()

class GUID(TypeDecorator):
    """UUID compatível com PostgreSQL e SQLite."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value) if isinstance(value, uuid.UUID) else str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        return uuid.UUID(str(value)) if value else None

def _new_uuid():
    return str(uuid.uuid4())

# ── Usuario ───────────────────────────────────────────────────────────────────
class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id          = db.Column(GUID(), primary_key=True, default=_new_uuid)
    nome        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha_hash  = db.Column(db.String(256), nullable=False)
    perfil      = db.Column(db.String(20), default="sindico", nullable=False)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    # Login social
    google_id   = db.Column(db.String(120), unique=True, nullable=True)

    # SaaS
    plano_atual        = db.Column(db.String(20), default="free")
    status_pagamento   = db.Column(db.String(20), default="ativo")
    stripe_customer_id = db.Column(db.String(100), nullable=True, unique=True)
    plano_expira_em    = db.Column(db.DateTime, nullable=True)

    condominios = db.relationship("Condominio", backref="dono",
                                  lazy="dynamic", cascade="all, delete-orphan",
                                  foreign_keys="Condominio.tenant_id")
    lancamentos = db.relationship("Lancamento", backref="autor",
                                  lazy="dynamic", cascade="all, delete-orphan",
                                  foreign_keys="Lancamento.usuario_id")

    def set_senha(self, senha: str):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    @property
    def limites(self) -> dict:
        from flask import current_app
        return current_app.config["PLAN_LIMITS"].get(
            self.plano_atual, {"condominios": 1, "unidades": 30}
        )

    def pode_criar_condominio(self) -> bool:
        return self.condominios.count() < self.limites["condominios"]

    def __repr__(self):
        return f"<Usuario {self.email} [{self.plano_atual}]>"

# ── Condominio ────────────────────────────────────────────────────────────────
class Condominio(db.Model):
    __tablename__ = "condominios"

    id             = db.Column(GUID(), primary_key=True, default=_new_uuid)
    nome           = db.Column(db.String(150), nullable=False)
    endereco       = db.Column(db.String(250))
    cidade         = db.Column(db.String(100))
    cep            = db.Column(db.String(10))
    total_unidades = db.Column(db.Integer, default=0)
    criado_em      = db.Column(db.DateTime, default=datetime.utcnow)
    tenant_id      = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

    unidades    = db.relationship("Unidade", backref="condominio",
                                  lazy="dynamic", cascade="all, delete-orphan")
    lancamentos = db.relationship("Lancamento", backref="condominio",
                                  lazy="dynamic", cascade="all, delete-orphan",
                                  foreign_keys="Lancamento.condominio_id")

# ── Unidade ───────────────────────────────────────────────────────────────────
class Unidade(db.Model):
    __tablename__ = "unidades"

    id            = db.Column(GUID(), primary_key=True, default=_new_uuid)
    identificacao = db.Column(db.String(20), nullable=False)
    tipo          = db.Column(db.String(20), default="apto")
    condominio_id = db.Column(GUID(), db.ForeignKey("condominios.id"), nullable=False, index=True)
    tenant_id     = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

    morador = db.relationship("Morador", backref="unidade",
                              uselist=False, cascade="all, delete-orphan")

# ── Morador ───────────────────────────────────────────────────────────────────
class Morador(db.Model):
    __tablename__ = "moradores"

    id           = db.Column(GUID(), primary_key=True, default=_new_uuid)
    nome         = db.Column(db.String(150), nullable=False)
    _cpf         = db.Column("cpf",      db.Text, nullable=True)
    _telefone    = db.Column("telefone", db.Text, nullable=True)
    _email       = db.Column("email",    db.Text, nullable=True)
    tipo         = db.Column(db.String(20), default="proprietario")
    data_entrada = db.Column(db.Date, nullable=True)
    data_saida   = db.Column(db.Date, nullable=True)
    ativo        = db.Column(db.Boolean, default=True)
    unidade_id   = db.Column(GUID(), db.ForeignKey("unidades.id"), nullable=False, index=True)
    tenant_id    = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)


    # Senha do portal (síndico define para o morador)
    _senha_portal = db.Column("senha_portal", db.String(256), nullable=True)

    def set_senha_portal(self, senha: str):
        from werkzeug.security import generate_password_hash
        self._senha_portal = generate_password_hash(senha)

    def check_senha_portal(self, senha: str) -> bool:
        if not self._senha_portal:
            return False
        from werkzeug.security import check_password_hash
        return check_password_hash(self._senha_portal, senha)

    @property
    def cpf(self):
        from .services.crypto import CryptoService
        return CryptoService.decrypt(self._cpf)

    @cpf.setter
    def cpf(self, v):
        from .services.crypto import CryptoService
        self._cpf = CryptoService.encrypt(v) if v else None

    @property
    def telefone(self):
        from .services.crypto import CryptoService
        return CryptoService.decrypt(self._telefone)

    @telefone.setter
    def telefone(self, v):
        from .services.crypto import CryptoService
        self._telefone = CryptoService.encrypt(v) if v else None

    @property
    def email(self):
        from .services.crypto import CryptoService
        return CryptoService.decrypt(self._email)

    @email.setter
    def email(self, v):
        from .services.crypto import CryptoService
        self._email = CryptoService.encrypt(v) if v else None

# ── Lancamento ────────────────────────────────────────────────────────────────
class Lancamento(db.Model):
    __tablename__ = "lancamentos"

    id            = db.Column(GUID(), primary_key=True, default=_new_uuid)
    descricao     = db.Column(db.String(200), nullable=False)
    valor         = db.Column(db.Float, nullable=False)
    tipo          = db.Column(db.String(10), nullable=False)
    categoria     = db.Column(db.String(50), default="Outros")
    data          = db.Column(db.Date, default=datetime.utcnow)
    pago          = db.Column(db.Boolean, default=False)
    observacao    = db.Column(db.Text, nullable=True)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    condominio_id = db.Column(GUID(), db.ForeignKey("condominios.id"), nullable=False, index=True)
    usuario_id    = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)
    tenant_id     = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

# ── Categorias padrão ─────────────────────────────────────────────────────────
CATEGORIAS_DESPESA = [
    "Manutenção", "Limpeza", "Segurança", "Energia", "Água",
    "Internet", "Elevador", "Jardinagem", "Seguro", "Administração", "Outros",
]
CATEGORIAS_RECEITA = [
    "Taxa Condominial", "Multa", "Reserva de Área", "Aluguel", "Outros",
]

# ── Comunicado ────────────────────────────────────────────────────────────────
class Comunicado(db.Model):
    __tablename__ = "comunicados"

    id            = db.Column(GUID(), primary_key=True, default=_new_uuid)
    titulo        = db.Column(db.String(200), nullable=False)
    corpo         = db.Column(db.Text, nullable=False)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    condominio_id = db.Column(GUID(), db.ForeignKey("condominios.id"), nullable=False, index=True)
    tenant_id     = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)

# ── Cobrança do morador ───────────────────────────────────────────────────────
class Cobranca(db.Model):
    __tablename__ = "cobranças"

    id          = db.Column(GUID(), primary_key=True, default=_new_uuid)
    descricao   = db.Column(db.String(200), nullable=False)
    valor       = db.Column(db.Float, nullable=False)
    vencimento  = db.Column(db.Date, nullable=False)
    pago        = db.Column(db.Boolean, default=False)
    pago_em     = db.Column(db.DateTime, nullable=True)
    morador_id  = db.Column(GUID(), db.ForeignKey("moradores.id"), nullable=False, index=True)
    tenant_id   = db.Column(GUID(), db.ForeignKey("usuarios.id"), nullable=False, index=True)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    morador = db.relationship("Morador", backref="cobranças")
