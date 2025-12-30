"""
Runtime-only state.
Nothing in this file is saved to the .blend.
"""

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


_log_dirty: bool = False


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
    global _runtime_metadata, _runtime_logs, _is_tampered, _runtime_logs_raw, _last_scene_stats, _last_stats_time
    _is_tampered = False
    _runtime_metadata = None
    _runtime_logs.clear()
    _runtime_logs_raw.clear()
    _last_stats_time = 0
    _last_scene_stats = {"v": 0, "f": 0, "o": 0}
