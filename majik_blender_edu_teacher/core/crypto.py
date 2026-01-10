
import hashlib
import base64
import json


# --------------------------------------------------
# UTILS
# --------------------------------------------------


def fernet_key_from_string(password: str, salt: bytes) -> bytes:
    """
    Generates a Fernet-compatible key from a password string using PBKDF2HMAC.

    :param password: The password string
    :type password: str
    :param salt: The salt bytes
    :type salt: bytes
    :return: The Fernet-compatible key
    :rtype: bytes
    """

    import base64
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes = 256 bits
        salt=salt,
        iterations=390000,  # OWASP-recommended range
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))



# --------------------------------------------------
# RUNTIME CACHE (NOT SAVED)
# --------------------------------------------------




def xor_obfuscate(data: str, key: str) -> str:
    """
    Obfuscate data using XOR with the given key.

    :param data: The data to obfuscate
    :param key: The XOR key used for obfuscation
    :return: The obfuscated string (base64-encoded)
    """
    # Use SHA256 of the key consistently as bytes
    key_bytes = hashlib.sha256(key.encode()).digest()
    encrypted = bytes(
        b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data.encode("utf-8"))
    )
    return base64.b64encode(encrypted).decode("ascii")


def xor_deobfuscate(data: str, key: str) -> str:
    """
    Deobfuscate data previously obfuscated with xor_obfuscate.

    :param data: The obfuscated data as a base64-encoded string
    :param key: The XOR key used for obfuscation
    :return: The deobfuscated string
    :raises UnicodeDecodeError: If decryption produces invalid UTF-8
    """
    key_bytes = hashlib.sha256(key.encode()).digest()
    raw = base64.b64decode(data)
    decrypted = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(raw))
    return decrypted.decode("utf-8")  # force string


# ---------------------------
# Low-level AES functions
# ---------------------------


def aes_encrypt(metadata: dict, key: str, salt_bytes: bytes) -> str:
    """
    Encrypt metadata using AES (Fernet).
    """
    from cryptography.fernet import Fernet

    aes_key = fernet_key_from_string(key, salt_bytes)
    cipher = Fernet(aes_key)
    return cipher.encrypt(json.dumps(metadata).encode()).decode()


def aes_decrypt(encrypted_metadata: str, key: str, salt_bytes: bytes) -> str:
    """
    Decrypt metadata using AES (Fernet). Use json.loads() to parse the result.

    :param encrypted_metadata: The encrypted metadata string
    :type encrypted_metadata: str
    :param key: The key used for decryption
    :type key: str
    :param salt_bytes: The salt bytes used for key derivation
    :type salt_bytes: bytes
    :return: The decrypted metadata string
    :rtype: str
    """
    from cryptography.fernet import Fernet

    aes_key = fernet_key_from_string(key, salt_bytes)
    cipher = Fernet(aes_key)
    decrypted = cipher.decrypt(encrypted_metadata.encode()).decode()
    return decrypted


# ---------------------------
# High-level wrapper functions
# ---------------------------


def encrypt_metadata(
    metadata: dict, key: str, salt_bytes: bytes, mode: str = "AES"
) -> str:
    """
    Encrypt metadata with AES (Fernet) or fallback to XOR.
    Raises ImportError if cryptography is not available.

    :param metadata: The metadata to encrypt
    :type metadata: dict
    :param key: The key used for encryption
    :type key: str
    :param salt_bytes: The salt bytes used for key derivation
    :type salt_bytes: bytes
    :param mode: The encryption mode used ("AES" or "XOR")
    :type mode: str
    :return: The encrypted metadata string
    :rtype: tuple[str, str]
    """
    hashed_key = hashlib.sha256(key.encode()).hexdigest()

    if not salt_bytes:
        raise RuntimeError("Missing student ID hash; cannot encrypt securely")

    if mode == "AES":
        return aes_encrypt(metadata, hashed_key, salt_bytes)

    elif mode == "XOR":
        return xor_obfuscate(json.dumps(metadata), key)

    else:
        raise ValueError(f"Unknown encryption mode: {mode}")


def decrypt_metadata(
    encrypted_metadata: str,
    key: str,
    salt_bytes: bytes,
    mode: str = "AES",
) -> dict:
    """
    Decrypt metadata using AES (Fernet) or XOR fallback.
    Raises Exception on failure.

    :param encrypted_metadata: The encrypted metadata string
    :type encrypted_metadata: str
    :param key: The key used for decryption
    :type key: str
    :param salt_bytes: The salt bytes used for key derivation
    :type salt_bytes: bytes
    :param mode: The encryption mode used ("AES" or "XOR")
    :type mode: str
    :return: The decrypted metadata
    :rtype: dict
    """

    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    decrypted = None

    if not salt_bytes:
        raise RuntimeError("Missing student ID hash; cannot encrypt securely")

    if mode == "AES":

        decrypted = aes_decrypt(encrypted_metadata, hashed_key, salt_bytes)

    elif mode == "XOR":
        decrypted = xor_deobfuscate(encrypted_metadata, key)

    else:
        raise ValueError(f"Unknown decryption mode: {mode}")

    return json.loads(decrypted)
