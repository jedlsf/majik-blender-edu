"""
Runtime-only state.
Nothing in this file is saved to the .blend.
"""

# --------------------------------------------------
# RUNTIME CACHE (NOT SAVED)
# --------------------------------------------------

from typing import TypedDict, Dict, Any, List

class SceneStats(TypedDict):
    v: int  # Vertex Count
    f: int  # Face Count
    o: int  # Object Count

class ActionLogEntry(TypedDict):
    t: float  # timestamp
    a: str  # action_type
    o: str  # object_name
    ot: str  # object_type
    d: Dict[str, Any]  # action_details
    dt: float  # duration
    s: SceneStats  # scene_stats
    ph: str  # previous hash or genesis hash


_known_objects: set = set()
_last_modifiers: dict = {}


_double_hash_key: str | None = None
_last_object_state: dict = {}
_transform_debounce: dict = {}
_edit_debounce: dict = {}
_log_dirty: bool = False
_last_autosave_time: float = 0.0
AUTOSAVE_INTERVAL: float = 5.0  # seconds


_last_stats_time: int = 0
_last_scene_stats = {"v": 0, "f": 0, "o": 0}


# Decrypted submission metadata (teacher-only)
_runtime_metadata: dict | None = None
"""Contains the decrypted metadata for the current submission."""

# Encrypted action logs (teacher-only)
_runtime_logs: List[str] = []
"""Contains the encrypted recorded action logs for the current session."""

# Decrypted runtime logs (runtime-only, never saved)
_runtime_logs_raw: List[ActionLogEntry] = []
"""Contains decrypted logs for runtime access. Not saved to .blend."""


_is_tampered: bool = False
"""Indicates whether the submission has been tampered with."""


_timer_start: float | None = None
_timer_elapsed: float = 0.0

_session_active: bool = False
"""Whether a work session (timer) is currently active."""


def is_session_active() -> bool:
    """Whether a work session (timer) is currently active."""
    return _session_active


def start_session():
    global _session_active
    if _session_active:
        return
    _session_active = True


def end_session():
    global _session_active
    if not _session_active:
        return
    _session_active = False


def mark_dirty():
    global _log_dirty
    _log_dirty = True


def mark_tampered():
    global _is_tampered
    _is_tampered = True


def is_tampered() -> bool:
    """Indicates whether the submission has been tampered with."""
    return _is_tampered


def clear_runtime():
    """Reset all runtime-only data."""
    global _timer_start, _timer_elapsed, _double_hash_key, _last_object_state, _transform_debounce, _log_dirty, _last_autosave_time, _runtime_metadata, _runtime_logs, _runtime_logs_raw, _is_tampered, _known_objects, _last_modifiers, _edit_debounce, _session_active, _last_stats_time, _last_scene_stats

    _timer_start = None
    _timer_elapsed = 0.0
    _double_hash_key = None
    _last_object_state.clear()
    _transform_debounce.clear()
    _log_dirty = False
    _last_autosave_time = 0.0
    _runtime_metadata = None
    _runtime_logs.clear()
    _runtime_logs_raw.clear()
    _is_tampered = False
    _known_objects.clear()
    _last_modifiers.clear()
    _edit_debounce.clear()
    _session_active = False
    _last_stats_time = 0
    _last_scene_stats = {"v": 0, "f": 0, "o": 0}
