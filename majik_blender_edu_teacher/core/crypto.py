import bpy  # type: ignore
import hashlib
import base64
import json


from .constants import (
    SCENE_LOGS,
    SCENE_STUDENT_ID_HASH,
    SCENE_TEACHER_DOUBLE_HASH,
    SCENE_SIGNATURE_MODE,
)

from ..core import runtime


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
    if not is_crypto_available():
        raise RuntimeError("cryptography is not available")

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


def install_crypto_wheel(report_fn=None):
    """
    Install bundled cryptography + dependencies wheels into _vendor folder.
    report_fn: optional function like operator.report
    """
    import platform
    import subprocess
    import traceback
    import os
    import sys

    def log(msg, level="INFO"):
        print(f"[CRYPTO INSTALL][{level}] {msg}")
        if report_fn:
            report_fn({level}, msg)

    try:
        log("Starting cryptography wheel installation")

        addon_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        wheel_dir = os.path.join(addon_root, "wheels")
        vendor_dir = os.path.join(addon_root, "_vendor")
        os.makedirs(vendor_dir, exist_ok=True)

        log(f"Addon root: {addon_root}")
        log(f"Wheel dir: {wheel_dir}")
        log(f"Vendor dir: {vendor_dir}")

        if not os.path.isdir(wheel_dir):
            raise FileNotFoundError(f"Wheels directory not found: {wheel_dir}")

        # Determine OS-specific wheel files
        system = platform.system()
        if system == "Windows":
            cffi_wheel = "cffi-2.0.0-cp311-cp311-win_amd64.whl"
            crypto_wheel = "cryptography-46.0.3-cp311-abi3-win_amd64.whl"
        elif system == "Darwin":
            cffi_wheel = "cffi-2.0.0-cp311-cp311-macosx_10_9_universal2.whl"
            crypto_wheel = "cryptography-46.0.3-cp311-abi3-macosx_10_9_universal2.whl"
        elif system == "Linux":
            cffi_wheel = "cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.whl"
            crypto_wheel = "cryptography-46.0.3-cp311-abi3-manylinux2014_x86_64.whl"
        else:
            raise RuntimeError(f"Unsupported OS: {system}")

        cffi_path = os.path.join(wheel_dir, cffi_wheel)
        crypto_path = os.path.join(wheel_dir, crypto_wheel)

        for path, name in [(cffi_path, "CFFI"), (crypto_path, "Cryptography")]:
            if not os.path.isfile(path):
                raise FileNotFoundError(f"{name} wheel not found: {path}")

        # Ensure pip exists
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                check=True,
                capture_output=True,
                text=True,
            )
            log("pip is available")
        except Exception:
            raise RuntimeError("pip is not available in Blender's Python")

        # --------------------------------------------------
        # Install CFFI first
        # --------------------------------------------------
        log(f"Installing CFFI from {cffi_wheel}")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--force-reinstall",
                "--target",
                vendor_dir,
                cffi_path,
            ],
            capture_output=True,
            text=True,
        )
        log("pip stdout:\n" + result.stdout)
        log("pip stderr:\n" + result.stderr)
        if result.returncode != 0:
            raise RuntimeError("CFFI installation failed")

        # --------------------------------------------------
        # Install Cryptography next
        # --------------------------------------------------
        log(f"Installing Cryptography from {crypto_wheel}")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--force-reinstall",
                "--target",
                vendor_dir,
                crypto_path,
            ],
            capture_output=True,
            text=True,
        )
        log("pip stdout:\n" + result.stdout)
        log("pip stderr:\n" + result.stderr)
        if result.returncode != 0:
            raise RuntimeError("Cryptography installation failed")

        # --------------------------------------------------
        # Add _vendor to sys.path and verify
        # --------------------------------------------------
        if vendor_dir not in sys.path:
            sys.path.insert(0, vendor_dir)
        import importlib

        importlib.invalidate_caches()

        import cryptography

        log("Cryptography successfully installed", "INFO")
        log("Cryptography ready for use (no restart required)")

        # Refresh Blender UI
        try:
            bpy.context.area.tag_redraw()
        except Exception:
            pass

        return True

    except Exception as e:
        log("Installation failed", "ERROR")
        log(str(e), "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False


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
    encrypted = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data.encode('utf-8')))
    return base64.b64encode(encrypted).decode('ascii')


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
    return decrypted.decode('utf-8')  # force string



def is_crypto_available():
    """
    Returns True if the 'cryptography' package is available, False otherwise.
    """
    try:
        import importlib

        importlib.invalidate_caches()
        import cryptography

        return True
    except Exception:
        return False


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


