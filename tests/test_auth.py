import uuid


def test_cadastro_get_ok(client):
    r = client.get("/cadastro")
    assert r.status_code == 200
    assert "csrf_token" in r.get_data(as_text=True)


def test_cadastro_post_sem_csrf_400(client):
    r = client.post(
        "/cadastro",
        data={
            "nome": "X",
            "email": "a@b.com",
            "senha": "123456",
            "perfil": "sindico",
        },
    )
    assert r.status_code == 400


def test_cadastro_sucesso_redireciona_login(client, csrf_token):
    email = f"new_{uuid.uuid4().hex[:10]}@example.com"
    r = client.post(
        "/cadastro",
        data={
            "csrf_token": csrf_token(),
            "nome": "Novo Usuário",
            "email": email,
            "senha": "senhaSegura1",
            "perfil": "sindico",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)
    assert r.headers.get("Location", "").endswith("/login")


def test_cadastro_email_duplicado(client, csrf_token, registered_user):
    email = registered_user["email"]
    r = client.post(
        "/cadastro",
        data={
            "csrf_token": csrf_token(),
            "nome": "Outro Nome",
            "email": email,
            "senha": "outraSenha2",
            "perfil": "sindico",
        },
    )
    assert r.status_code == 200
    assert "já cadastrado" in r.get_data(as_text=True).lower()


def test_cadastro_senha_curta(client, csrf_token):
    r = client.post(
        "/cadastro",
        data={
            "csrf_token": csrf_token(),
            "nome": "A",
            "email": f"short_{uuid.uuid4().hex[:8]}@ex.com",
            "senha": "12345",
            "perfil": "sindico",
        },
    )
    assert r.status_code == 200
    assert "6 caracteres" in r.get_data(as_text=True)


def test_login_sucesso_redirect_dashboard(client, csrf_token, registered_user):
    token_login = csrf_token("/login")
    r = client.post(
        "/login",
        data={
            "csrf_token": token_login,
            "email": registered_user["email"],
            "senha": registered_user["password"],
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)
    loc = r.headers.get("Location", "")
    assert "dashboard" in loc


def test_login_falha(client, csrf_token, registered_user):
    r = client.post(
        "/login",
        data={
            "csrf_token": csrf_token("/login"),
            "email": registered_user["email"],
            "senha": "senhaErrada!!!",
        },
    )
    assert r.status_code == 200
    assert "incorretos" in r.get_data(as_text=True).lower()
