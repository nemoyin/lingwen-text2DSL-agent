"""AES-256-CBC encryption / decryption for sensitive fields.

Uses the first 32 bytes of ``settings.jwt_secret`` as the AES key.
A random IV is generated per encryption and prepended to the ciphertext.
"""

import base64
import os
from typing import Tuple

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.config import settings

# Number of bytes (256-bit key)
_KEY_LENGTH: int = 32

# Initialisation vector length for CBC mode
_IV_LENGTH: int = 16


def _derive_key() -> bytes:
    """Derive a 32-byte AES key from ``jwt_secret``.

    If the secret is shorter than 32 bytes it is repeated; if longer it is
    truncated.
    """
    secret_bytes = settings.jwt_secret.encode("utf-8")
    if len(secret_bytes) >= _KEY_LENGTH:
        return secret_bytes[:_KEY_LENGTH]
    # Repeat the secret to reach the required length
    repeats = (_KEY_LENGTH // len(secret_bytes)) + 1
    return (secret_bytes * repeats)[:_KEY_LENGTH]


def encrypt_password(plain: str) -> str:
    """Encrypt a plain-text password using AES-256-CBC.

    Args:
        plain: The plain-text password to encrypt.

    Returns:
        Base64-encoded string: ``IV (16 bytes) + ciphertext``.
    """
    iv = os.urandom(_IV_LENGTH)
    key = _derive_key()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    # PKCS7 padding
    plain_bytes = plain.encode("utf-8")
    pad_len = 16 - (len(plain_bytes) % 16)
    padded = plain_bytes + bytes([pad_len] * pad_len)

    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode("utf-8")


def decrypt_password(encrypted: str) -> str:
    """Decrypt a password encrypted with :func:`encrypt_password`.

    Args:
        encrypted: The Base64-encoded ``IV + ciphertext`` string.

    Returns:
        The original plain-text password.

    Raises:
        ValueError: If decryption fails (incorrect key or corrupted data).
    """
    try:
        raw = base64.b64decode(encrypted)
        iv = raw[:_IV_LENGTH]
        ciphertext = raw[_IV_LENGTH:]
        key = _derive_key()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()

        padded = decryptor.update(ciphertext) + decryptor.finalize()
        # Remove PKCS7 padding
        pad_len = padded[-1]
        if pad_len > 16:
            raise ValueError("Invalid padding length")
        plain = padded[:-pad_len]
        return plain.decode("utf-8")
    except Exception as exc:
        raise ValueError(f"Failed to decrypt password: {exc}") from exc
