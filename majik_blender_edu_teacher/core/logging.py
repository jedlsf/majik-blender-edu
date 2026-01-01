import bpy  # type: ignore
import time
import json
import base64
import hashlib


from ..core import runtime
from ..core.text.session_log_controller import SessionLogController

from .constants import (
    SCENE_SIGNATURE_MODE,
)


from typing import TypedDict, Dict, Any, List, Literal


# --------------------------------------------------
# TYPE DEFINITIONS
# --------------------------------------------------


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


class WorkingPeriod(TypedDict):
    start: str
    end: str


class ExportLogsResult(TypedDict):
    data: List[ActionLogEntry]
    status: Literal["valid", "tampered"]
    total_working_time: int
    period: WorkingPeriod
    stats: SceneStats


# --------------------------------------------------
# RUNTIME INITIALIZATION
# --------------------------------------------------


if not hasattr(runtime, "_known_objects"):
    runtime._known_objects = set()

if not hasattr(runtime, "_last_modifiers"):
    runtime._last_modifiers = {}

if not hasattr(runtime, "_last_object_state"):
    runtime._last_object_state = {}

if not hasattr(runtime, "_transform_debounce"):
    runtime._transform_debounce = {}

if not hasattr(runtime, "_edit_debounce"):
    runtime._edit_debounce = {}

if not hasattr(runtime, "_last_autosave_time"):
    runtime._last_autosave_time = 0


# --------------------------------------------------
# ENCRYPTION AND DECRYPTION
# --------------------------------------------------


def get_security_mode(scene) -> str:
    return scene.get(SCENE_SIGNATURE_MODE, "AES")


# --------------------------------------------------
# INTEGRITY HASHING
# --------------------------------------------------


def compute_entry_hash(entry: dict) -> str:
    """
    Hash a log entry deterministically (excluding its own hash).
    """
    entry_copy = entry.copy()
    entry_copy.pop("ph", None)
    canonical = json.dumps(entry_copy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_log_integrity(scene) -> bool:

    logs = runtime._runtime_logs_raw
    if not logs:
        return True

    # -----------------------------------------
    # 1. Validate Genesis Log
    # -----------------------------------------
    genesis = logs[0]

    expected_genesis = generate_genesis_key(
        teacher_key=scene.teacher_key,
        student_id=scene.student_id,
    )

    if genesis.get("ph") != expected_genesis:
        return False

    expected_prev = compute_entry_hash(genesis)

    # -----------------------------------------
    # 2. Validate Chain
    # -----------------------------------------
    for entry in logs[1:]:
        if entry.get("ph") != expected_prev:
            return False

        expected_prev = compute_entry_hash(entry)

    return True


# --------------------------------------------------
# EXPORT
# --------------------------------------------------


def export_decrypted_logs(scene) -> ExportLogsResult:

    if len(runtime._runtime_logs_raw) <= 0:
        load_logs_from_scene(scene)

    if runtime.is_log_dirty():
        save_logs_to_scene(scene)

    valid = validate_log_integrity(scene)

    return {
        "data": runtime._runtime_logs_raw.copy(),
        "status": "valid" if valid else "tampered",
        "total_working_time": get_total_work_time(),
        "period": get_working_period(),
        "stats": get_total_scene_stats(scene),
    }


def export_encrypted_logs(scene) -> str:
    """
    Export the session log as raw text from the Text datablock.

    Returns:
        str: The full text content of the session log.
    """
    # Ensure logs are loaded into runtime
    load_logs_from_scene(scene)

    # Get raw text from the SessionLogController
    text_content = SessionLogController.get_text_content()
    return text_content


def generate_genesis_key(teacher_key: str, student_id: str) -> str:
    """
    Generate a genesis key by combining teacher_key and student_id,
    encoding in Base64, and hashing with SHA-256.
    """
    combined = f"{teacher_key}:{student_id}"
    combined_b64 = base64.b64encode(combined.encode("utf-8"))
    hashed = hashlib.sha256(combined_b64).hexdigest()
    return hashed


def validate_genesis_key(
    current_genesis_key: str, teacher_key: str, student_id: str
) -> bool:
    """
    Validate if the current genesis key matches the one generated
    from teacher_key and student_id.
    """
    expected_key = generate_genesis_key(teacher_key, student_id)
    return current_genesis_key == expected_key


def create_genesis_log(scene, genesis_hash: str):
    """
    Create a genesis log entry for the scene using a hashed key.
    Does nothing if the log already has entries.

    :param scene: Blender scene
    :param key: Secret key to hash as genesis
    :return: The genesis hash if created, None if skipped
    """
    # If log already exists, return early
    if hasattr(runtime, "_runtime_logs_raw") and len(runtime._runtime_logs_raw) >= 1:
        return None

    # Create initial log entry
    entry: ActionLogEntry = {
        "t": round(time.time(), 3),
        "a": "Genesis Log",
        "o": "__SYSTEM__",
        "ot": "SYSTEM",
        "d": {"description": "Initial genesis log entry"},
        "dt": 0.0,
        "s": {"v": 0, "f": 0, "o": 0},
        "ph": genesis_hash,  # points to itself
    }

    # Store in runtime logs
    if not hasattr(runtime, "_runtime_logs_raw"):
        runtime._runtime_logs_raw = []

    runtime._runtime_logs_raw.append(entry)

    save_logs_to_scene(scene)

    return genesis_hash


def validate_genesis_log(scene, teacher_key: str, student_id: str) -> bool:
    """
    Validate that the first log entry in the scene matches the expected genesis hash.

    :param scene: Blender scene containing logs
    :param teacher_key: Teacher key to generate genesis hash
    :param student_id: Student ID to generate genesis hash
    :return: True if the first log entry matches the expected genesis hash
    :raises RuntimeError: If no logs exist or first log is missing 'ph'
    """
    # Load or ensure logs are in runtime
    if not runtime._runtime_logs_raw:
        load_logs_from_scene(scene)

    if not runtime._runtime_logs_raw:
        raise RuntimeError("No log entries found; cannot validate genesis log")

    # Get the first log entry
    first_entry = runtime._runtime_logs_raw[0]

    if "ph" not in first_entry:
        raise RuntimeError("First log entry missing 'ph' (genesis hash)")

    expected_genesis = generate_genesis_key(teacher_key, student_id)

    return first_entry["ph"] == expected_genesis


def save_logs_to_scene(scene):
    """
    Save the current runtime logs into a Blender Text datablock using SessionLogController.
    """
    print("[Logging] Saving runtime logs to Text datablock")
    SessionLogController.save_logs_to_text(
        scene=scene, raw_logs=runtime._runtime_logs_raw
    )


def load_logs_from_scene(scene):
    """
    Load session logs from Text datablock into runtime._runtime_logs_raw
    """
    print("[Logging] Loading logs from Text datablock")
    logs = SessionLogController.load_logs_from_text(scene=scene)
    runtime._runtime_logs_raw = logs
    return logs


def get_total_scene_stats(scene) -> SceneStats:
    """
    Computes total vertices, faces, and objects in the scene,
    INCLUDING modifiers (evaluated mesh).
    """
    now = time.time()
    last = getattr(runtime, "_last_total_stats_time", 0)

    if now - last < 1.0:
        return runtime._last_total_scene_stats

    depsgraph = bpy.context.evaluated_depsgraph_get()

    total_verts = 0
    total_faces = 0
    total_objects = 0

    for obj in scene.objects:
        if obj.type != "MESH":
            continue

        eval_obj = obj.evaluated_get(depsgraph)
        eval_mesh = eval_obj.to_mesh(
            preserve_all_data_layers=False, depsgraph=depsgraph
        )

        if eval_mesh:
            total_verts += len(eval_mesh.vertices)
            total_faces += len(eval_mesh.polygons)
            total_objects += 1

            # IMPORTANT: free evaluated mesh
            eval_obj.to_mesh_clear()

    stats = {"v": total_verts, "f": total_faces, "o": total_objects}

    runtime._last_total_scene_stats = stats
    runtime._last_total_stats_time = now
    return stats


def get_total_work_time() -> int:
    """
    Returns the total work time in seconds (int) between the 2nd log entry and the last log entry.
    Returns 0 if there are no logs or only the genesis log exists.
    """
    logs = runtime._runtime_logs_raw
    if not logs or len(logs) < 2:
        return 0

    start_item = logs[1]
    end_item = logs[-1]

    start_time = start_item.get("t", 0)
    end_time = end_item.get("t", 0)

    total_seconds = round(max(0, end_time - start_time))
    return int(total_seconds)


def get_working_period() -> WorkingPeriod:
    """
    Returns the working period as a dictionary with ISO 8601 date strings.
    Keys: 'start', 'end'.
    Returns empty strings if insufficient log entries.
    """
    from datetime import datetime

    logs = runtime._runtime_logs_raw
    if not logs or len(logs) < 2:
        return {"start": "", "end": ""}

    start_item = logs[1]
    end_item = logs[-1]

    start_iso = datetime.fromtimestamp(start_item.get("t", 0)).isoformat()
    end_iso = datetime.fromtimestamp(end_item.get("t", 0)).isoformat()

    return {"start": start_iso, "end": end_iso}
