"""
Token Encryption Service using Fernet (AES-128-CBC with HMAC-SHA256).
Supports key rotation via cryptography.fernet.MultiFernet.
"""

import os
import base64
import hashlib
from typing import List, Tuple
from cryptography.fernet import Fernet, MultiFernet
from config import settings

def _derive_fernet_key(secret: str) -> bytes:
    key_32 = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key_32)

def _get_multi_fernet() -> MultiFernet:
    """
    Returns MultiFernet instance initialized with primary encryption key
    followed by any fallback keys for seamless key rotation.
    Keys can be passed as comma-separated list in ENCRYPTION_SECRET_KEYS.
    """
    raw_keys = os.getenv("ENCRYPTION_SECRET_KEYS", "")
    if raw_keys:
        secret_list = [k.strip() for k in raw_keys.split(",") if k.strip()]
    else:
        primary = os.getenv("ENCRYPTION_SECRET", "actionloop-primary-secret-key-32-bytes!")
        secret_list = [primary]

    fernets = [Fernet(_derive_fernet_key(s)) for s in secret_list]
    return MultiFernet(fernets)

def encrypt_token(raw_token: str) -> str:
    """
    Encrypts sensitive OAuth tokens using AES-128-CBC + HMAC-SHA256 (Fernet)
    with the primary active key.
    """
    if not raw_token:
        return ""
    mf = _get_multi_fernet()
    encrypted = mf.encrypt(raw_token.encode("utf-8"))
    return encrypted.decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypts token trying primary key first, then falling back to previous keys in rotation.
    """
    if not encrypted_token:
        return ""
    mf = _get_multi_fernet()
    decrypted = mf.decrypt(encrypted_token.encode("utf-8"))
    return decrypted.decode("utf-8")

def reencrypt_token_for_rotation(encrypted_token: str) -> str:
    """
    Rotates an encrypted token to the newest primary key.
    """
    if not encrypted_token:
        return ""
    mf = _get_multi_fernet()
    rotated = mf.rotate(encrypted_token.encode("utf-8"))
    return rotated.decode("utf-8")
