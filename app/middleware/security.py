"""
Middleware e decorators de segurança
- enforce_plan: bloqueia ações além do limite do plano
- tenant_required: garante que o recurso pertence ao usuário logado
- rate_limit simples por IP
"""
from functools import wraps
from flask import abort, flash, redirect, url_for, request, g, current_app
from flask_login import current_user
from ..models import Condominio


# ─── Enforcement de plano ─────────────────────────────────────────────────────

def enforce_plan(recurso: str):
    """
    Decorator que bloqueia criação de recursos além do plano.
    Uso: @enforce_plan("condominio")
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if recurso == "condominio":
                if not current_user.pode_criar_condominio():
                    plano = current_user.plano_atual.capitalize()
                    limite = current_user.limites["condominios"]
                    flash(
                        f"Limite do plano {plano} atingido ({limite} condomínio(s)). "
                        f"Faça upgrade para continuar.",
                        "danger"
                    )
                    return redirect(url_for("dashboard.index"))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─── Tenant isolation ─────────────────────────────────────────────────────────

def get_tenant_condominio(condo_id: str) -> Condominio:
    """
    Busca condomínio garantindo que pertence ao tenant logado.
    Retorna 404 se não existir OU se pertencer a outro tenant (previne IDOR).
    """
    condo = Condominio.query.filter_by(
        id=condo_id,
        tenant_id=current_user.id
    ).first_or_404()
    return condo


def tenant_ids_condominios() -> list[str]:
    """Retorna os IDs dos condomínios do tenant logado."""
    from ..models import Condominio
    return [
        str(c.id)
        for c in Condominio.query.filter_by(tenant_id=current_user.id)
                                  .with_entities(Condominio.id).all()
    ]


# ─── Rate limiting simples (sem Redis) ───────────────────────────────────────

_rate_store: dict[str, list] = {}

def rate_limit(max_calls: int = 10, window: int = 60):
    """
    Decorator de rate limit por IP.
    max_calls: máximo de chamadas por janela
    window: janela em segundos
    """
    import time

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            ip = request.remote_addr or "unknown"
            now = time.time()
            hits = _rate_store.get(ip, [])
            hits = [t for t in hits if now - t < window]
            if len(hits) >= max_calls:
                abort(429)
            hits.append(now)
            _rate_store[ip] = hits
            return f(*args, **kwargs)
        return decorated
    return decorator
