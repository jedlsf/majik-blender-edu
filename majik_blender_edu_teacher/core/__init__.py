from .crypto import (
    fernet_key_from_string,
    is_crypto_available,
    install_crypto_wheel,
    encrypt_metadata,
    decrypt_metadata,
)

from .hash import (
    compute_object_hash,
    timestamp_to_readable,
)

from .constants import (
    SCENE_ENCRYPTED_KEY,
    SCENE_SIGNATURE_MODE,
    SCENE_LOGS,
    SCENE_TEACHER_DOUBLE_HASH,
    SCENE_SIGNATURE_VERSION,
    SCENE_STUDENT_ID_HASH,
)

from .properties import register_properties, unregister_properties

from .handlers import on_file_load

from .runtime import (
    _runtime_metadata,
    _runtime_logs,
    clear_runtime,
    _is_tampered,
    mark_dirty,
    mark_tampered,
)

from .logging import (
    load_logs_from_scene,
    save_logs_to_scene,
    export_encrypted_logs,
    export_decrypted_logs,
    validate_log_integrity,
    get_student_id_hash,
    get_teacher_double_hash,
    get_security_mode,
)

__all__ = [
    "fernet_key_from_string",
    "is_crypto_available",
    "install_crypto_wheel",
    "decrypt_metadata",
    "encrypt_metadata",
    "compute_object_hash",
    "timestamp_to_readable",
    "SCENE_ENCRYPTED_KEY",
    "SCENE_SIGNATURE_MODE",
    "SCENE_LOGS",
    "SCENE_TEACHER_DOUBLE_HASH",
    "SCENE_SIGNATURE_VERSION",
    "SCENE_STUDENT_ID_HASH",
    "register_properties",
    "unregister_properties",
    "on_file_load",
    "_runtime_metadata",
    "_runtime_logs",
    "_is_tampered",
    "mark_dirty",
    "mark_tampered",
    "clear_runtime",
    "load_logs_from_scene",
    "save_logs_to_scene",
    "export_encrypted_logs",
    "export_decrypted_logs",
    "validate_log_integrity",
    "get_student_id_hash",
    "get_teacher_double_hash",
    "get_security_mode",
]
