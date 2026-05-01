"""
Serviço de webhooks de saída — integração n8n
Dispara eventos assíncronos com assinatura HMAC-SHA256 para validar autenticidade.
"""
import hashlib
import hmac
import json
import threading
from datetime import datetime
from flask import current_app
import requests


def _assinar_payload(payload_json: str, secret: str) -> str:
    """Gera assinatura HMAC-SHA256 do payload."""
    return hmac.new(
        secret.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()


def _disparar_async(url: str, payload: dict, secret: str) -> None:
    """Dispara o webhook em thread separada — não bloqueia a requisição do usuário."""
    payload_json = json.dumps(payload, default=str)
    assinatura = _assinar_payload(payload_json, secret)

    headers = {
        "Content-Type": "application/json",
        "X-ImobFlow-Signature": f"sha256={assinatura}",
        "X-ImobFlow-Event": payload.get("evento", "desconhecido"),
        "X-ImobFlow-Timestamp": datetime.utcnow().isoformat(),
    }

    try:
        response = requests.post(url, data=payload_json, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        # Log silencioso — webhook falhou mas não quebra o fluxo principal
        print(f"[Webhook] Falha ao disparar para {url}: {e}")


def disparar_webhook(evento: str, dados: dict) -> None:
    """
    Ponto de entrada público. Dispara webhook se configurado.
    Uso: disparar_webhook("condominio.criado", {"id": ..., "nome": ...})
    """
    url = current_app.config.get("N8N_WEBHOOK_URL", "")
    secret = current_app.config.get("N8N_WEBHOOK_SECRET", "")

    if not url or not secret:
        return  # n8n não configurado — ignora silenciosamente

    payload = {
        "evento": evento,
        "timestamp": datetime.utcnow().isoformat(),
        "dados": dados,
    }

    # Dispara em thread separada para não bloquear a response
    thread = threading.Thread(
        target=_disparar_async,
        args=(url, payload, secret),
        daemon=True
    )
    thread.start()
