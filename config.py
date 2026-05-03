import os
from cryptography.fernet import Fernet


def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url or "sqlite:///imobflow.db"


def _get_or_create_fernet_key() -> bytes:
    raw = (os.environ.get("ENCRYPTION_KEY") or "").strip()
    if raw:
        try:
            Fernet(raw.encode())
            return raw.encode()
        except Exception:
            debug = os.environ.get("FLASK_DEBUG", "").lower() == "true"
            msg = (
                "ENCRYPTION_KEY inválida ou corrompida — deve ser o output de "
                "Fernet.generate_key().decode()."
            )
            if debug:
                print(f"[AVISO] {msg} Usando chave temporária em FLASK_DEBUG.")
                return Fernet.generate_key()
            raise RuntimeError(msg) from None
    generated = Fernet.generate_key()
    print(
        "[AVISO] ENCRYPTION_KEY não definida — usando chave temporária. "
        "Dados criptografados não sobreviverão ao restart. "
        "Defina ENCRYPTION_KEY no .env para produção."
    )
    return generated


class Config:
    # ── Flask core ────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-never-use-in-prod")
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # ── Banco de dados ────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str = _get_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,       # verifica conexão antes de usar
        "pool_recycle": 300,         # recicla conexões a cada 5 min
    }

    # ── Criptografia de campos sensíveis (LGPD) ────────────────────────────────
    FERNET_KEY: bytes = _get_or_create_fernet_key()

    # ── CSRF ──────────────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int = 3600  # 1 hora

    # ── Sessão segura ─────────────────────────────────────────────────────────
    SESSION_COOKIE_SECURE: bool = not DEBUG
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PERMANENT_SESSION_LIFETIME: int = 86400  # 24h

    # ── Stripe ────────────────────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    # ── Planos e limites ──────────────────────────────────────────────────────
    PLAN_LIMITS: dict = {
        "free":    {"condominios": 1,  "unidades": 30},
        "pro":     {"condominios": 3,  "unidades": 9999},
        "gestora": {"condominios": 999, "unidades": 9999},
    }

    # ── n8n Webhooks ──────────────────────────────────────────────────────────
    N8N_WEBHOOK_URL: str = os.environ.get("N8N_WEBHOOK_URL", "")
    N8N_WEBHOOK_SECRET: str = os.environ.get("N8N_WEBHOOK_SECRET", "")
