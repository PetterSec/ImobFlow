"""
Serviço de criptografia de campos sensíveis — LGPD
Usa AES-256 via Fernet (biblioteca `cryptography`)

Campos protegidos: CPF, telefone, e-mail de moradores
"""
from cryptography.fernet import Fernet
from flask import current_app


class CryptoService:
    """Encripta/decripta campos sensíveis no banco."""

    @staticmethod
    def _fernet() -> Fernet:
        return Fernet(current_app.config["FERNET_KEY"])

    @classmethod
    def encrypt(cls, valor: str | None) -> str | None:
        """Encripta uma string. Retorna None se valor for None."""
        if valor is None:
            return None
        return cls._fernet().encrypt(valor.encode()).decode()

    @classmethod
    def decrypt(cls, token: str | None) -> str | None:
        """Decripta um token. Retorna None se token for None."""
        if token is None:
            return None
        try:
            return cls._fernet().decrypt(token.encode()).decode()
        except Exception:
            # Loga mas não expõe detalhes para o usuário
            current_app.logger.warning("Falha ao decriptar campo — token inválido ou chave trocada.")
            return "[dado ilegível]"

    @classmethod
    def encrypt_dict(cls, dados: dict, campos: list[str]) -> dict:
        """Encripta múltiplos campos de um dicionário."""
        return {k: cls.encrypt(v) if k in campos and v else v for k, v in dados.items()}
