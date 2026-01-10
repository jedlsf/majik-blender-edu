from .crypto import (
    fernet_key_from_string,
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
    SCENE_TEACHER_DOUBLE_HASH,
    SCENE_SIGNATURE_VERSION,
    SCENE_STUDENT_ID_HASH,
    SCENE_ACTIVE_TIMER,
)

from .properties import register_properties, unregister_properties

from .handlers import on_file_load

from .timer import (
    get_total_time,
    load_timer_from_scene,
    save_timer_to_scene,
    start_timer,
    stop_timer,
)

from .runtime import (
    _runtime_metadata,
    _runtime_logs,
    _runtime_logs_raw,
    _is_tampered,
    clear_runtime,
    is_tampered,
    mark_tampered,
    mark_log_dirty,
)

from .logging import (
    operator_monitor,
    add_log,
    on_depsgraph_update,
    detect_mesh_action,
    log_simple_action,
    operator_post_handler,
    register_logging_handlers,
    unregister_logging_handlers,
    load_logs_from_scene,
    save_logs_to_scene,
    export_encrypted_logs,
    export_decrypted_logs,
    validate_log_integrity,
    get_security_mode,
)

__all__ = [
    "fernet_key_from_string",
    "decrypt_metadata",
    "encrypt_metadata",
    "compute_object_hash",
    "timestamp_to_readable",
    "SCENE_ENCRYPTED_KEY",
    "SCENE_SIGNATURE_MODE",
    "SCENE_TEACHER_DOUBLE_HASH",
    "SCENE_SIGNATURE_VERSION",
    "SCENE_STUDENT_ID_HASH",
    "SCENE_ACTIVE_TIMER",
    "register_properties",
    "unregister_properties",
    "on_file_load",
    "_runtime_metadata",
    "_runtime_logs",
    "_runtime_logs_raw",
    "_is_tampered",
    "clear_runtime",
    "is_tampered",
    "mark_tampered",
    "mark_log_dirty",
    "get_total_time",
    "load_timer_from_scene",
    "save_timer_to_scene",
    "start_timer",
    "stop_timer",
    "operator_monitor",
    "add_log",
    "on_depsgraph_update",
    "detect_mesh_action",
    "log_simple_action",
    "operator_post_handler",
    "register_logging_handlers",
    "unregister_logging_handlers",
    "load_logs_from_scene",
    "save_logs_to_scene",
    "export_encrypted_logs",
    "export_decrypted_logs",
    "validate_log_integrity",
    "get_security_mode",
]
