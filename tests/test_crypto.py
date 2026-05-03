from app.services.crypto import CryptoService


def test_encrypt_decrypt_roundtrip(app):
    with app.app_context():
        plain = "123.456.789-00"
        token = CryptoService.encrypt(plain)
        assert token != plain
        assert CryptoService.decrypt(token) == plain


def test_encrypt_none_returns_none(app):
    with app.app_context():
        assert CryptoService.encrypt(None) is None
        assert CryptoService.decrypt(None) is None
