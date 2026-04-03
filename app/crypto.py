"""
Field-level encryption for sensitive data (broker tokens, API keys).

Uses Fernet symmetric encryption with the app's SECRET_KEY derived through HKDF.
In production, swap the key source to a KMS (AWS KMS, GCP KMS, Vault).
"""
from __future__ import annotations

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger("tradeloop.crypto")


def _derive_key() -> bytes:
    """Derive a Fernet-compatible key from the app secret."""
    secret = get_settings().secret_key.encode()
    raw = hashlib.sha256(secret).digest()
    return base64.urlsafe_b64encode(raw)


_fernet = Fernet(_derive_key())


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string. Returns base64-encoded ciphertext."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext. Returns plaintext."""
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt value — key may have changed")
        return ""
