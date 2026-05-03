def test_dashboard_requer_login(client):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code == 302
    assert "login" in r.headers.get("Location", "").lower()
