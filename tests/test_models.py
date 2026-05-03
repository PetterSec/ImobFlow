"""Garante que o ORM mapeia sem AmbiguousForeignKeysError (regressão cadastro)."""

from app.models import Condominio, Lancamento, Usuario, db


def test_instanciar_usuario_sem_erro_mapeamento(app):
    with app.app_context():
        u = Usuario(nome="Mapeamento", email="map@test.com", perfil="sindico")
        u.set_senha("senhaSegura1")
        db.session.add(u)
        db.session.commit()
        assert u.id is not None


def test_lancamento_relaciona_autor_e_tenant(app):
    with app.app_context():
        owner = Usuario(nome="Dono", email="dono@test.com", perfil="sindico")
        owner.set_senha("senhaSegura1")
        db.session.add(owner)
        db.session.flush()

        condo = Condominio(
            nome="Residencial Teste",
            tenant_id=owner.id,
        )
        db.session.add(condo)
        db.session.flush()

        l = Lancamento(
            descricao="Taxa",
            valor=100.0,
            tipo="receita",
            condominio_id=condo.id,
            usuario_id=owner.id,
            tenant_id=owner.id,
        )
        db.session.add(l)
        db.session.commit()

        assert l.autor is not None
        assert l.autor.email == "dono@test.com"
