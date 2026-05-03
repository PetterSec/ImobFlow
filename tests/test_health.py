def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_health_content_type_json(client):
    r = client.get("/health")
    assert "application/json" in (r.headers.get("Content-Type") or "")
