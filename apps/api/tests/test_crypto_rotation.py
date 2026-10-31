import os
import pytest
from services.crypto import encrypt_token, decrypt_token, reencrypt_token_for_rotation, _derive_fernet_key
from cryptography.fernet import Fernet, MultiFernet

def test_crypto_key_rotation():
    key_old = "old-secret-key-that-was-used-in-2025!"
    key_new = "brand-new-secret-key-for-2026-rotation!"

    # 1. Encrypt with old key
    f_old = Fernet(_derive_fernet_key(key_old))
    ciphertext_old = f_old.encrypt(b"secret_linear_token_xyz").decode("utf-8")

    # 2. Configure rotation: new key is primary, old key is fallback
    os.environ["ENCRYPTION_SECRET_KEYS"] = f"{key_new},{key_old}"

    # Decrypt should succeed seamlessly via MultiFernet fallback
    decrypted = decrypt_token(ciphertext_old)
    assert decrypted == "secret_linear_token_xyz"

    # 3. Rotate ciphertext to new key
    rotated_ciphertext = reencrypt_token_for_rotation(ciphertext_old)
    assert rotated_ciphertext != ciphertext_old

    # Decrypt rotated ciphertext using only new key
    os.environ["ENCRYPTION_SECRET_KEYS"] = key_new
    decrypted_new = decrypt_token(rotated_ciphertext)
    assert decrypted_new == "secret_linear_token_xyz"

    # Clean up environment
    os.environ.pop("ENCRYPTION_SECRET_KEYS", None)

