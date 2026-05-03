"""Webhook Stripe deve aceitar POST sem CSRF (Stripe não envia token)."""


def test_stripe_webhook_post_sem_csrf_nao_retorna_403(client):
    # Sem payload/signature válidos o endpoint retorna 400 (assinatura inválida), não 403 CSRF
    r = client.post(
        "/saas/webhook/stripe",
        data=b"{}",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code != 403
    assert r.status_code == 400
