import re
import uuid

import pytest

from app import create_app
from app.models import Usuario
from config import TestConfig


def _csrf_from_page(client, path: str) -> str:
    r = client.get(path)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    m = re.search(r'name="csrf_token" value="([^"]+)"', r.get_data(as_text=True))
    assert m, f"csrf_token não encontrado em {path}"
    return m.group(1)


@pytest.fixture
def app():
    application = create_app(TestConfig)
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf_token(client):
    """Token CSRF da página de cadastro (fixture parametrizável via factory)."""

    def _get(path: str = "/cadastro") -> str:
        return _csrf_from_page(client, path)

    return _get


@pytest.fixture
def registered_user(app, client):
    """Usuário criado via fluxo HTTP /cadastro."""
    mail = f"fixture_{uuid.uuid4().hex[:12]}@example.com"
    token = _csrf_from_page(client, "/cadastro")
    r = client.post(
        "/cadastro",
        data={
            "csrf_token": token,
            "nome": "Fixture User",
            "email": mail,
            "senha": "senhaSegura1",
            "perfil": "sindico",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), r.status_code
    with app.app_context():
        u = Usuario.query.filter_by(email=mail).first()
        assert u is not None
        return {
            "email": mail,
            "password": "senhaSegura1",
            "user_id": str(u.id),
        }
