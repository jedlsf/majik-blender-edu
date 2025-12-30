import bpy  # type: ignore
import time
import json
import zlib
import base64
import hashlib
import re

from ..core import runtime
from .crypto import decrypt_metadata, encrypt_metadata

from .constants import (
    SCENE_LOGS,
    SCENE_STUDENT_ID_HASH,
    SCENE_TEACHER_DOUBLE_HASH,
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


# --------------------------------------------------
# RUNTIME INITIALIZATION
# --------------------------------------------------

if not hasattr(runtime, "_runtime_logs"):
    runtime._runtime_logs = []

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


def get_student_id_hash(scene) -> str:
    if SCENE_STUDENT_ID_HASH not in scene:
        raise RuntimeError("Student ID hash missing from scene")
    return scene[SCENE_STUDENT_ID_HASH]


def get_teacher_double_hash(scene) -> str:
    if SCENE_TEACHER_DOUBLE_HASH not in scene:
        raise RuntimeError("Teacher integrity key missing from scene")
    return scene[SCENE_TEACHER_DOUBLE_HASH]


def encrypt_log_item(scene, item: dict) -> str:
    mode = get_security_mode(scene)
    salt_bytes = get_student_id_hash(scene).encode("utf-8")
    key = get_teacher_double_hash(scene)

    return encrypt_metadata(
        metadata=item,
        key=key,
        salt_bytes=salt_bytes,
        mode=mode,
    )


def decrypt_log_item(scene, encrypted_item: str) -> dict:
    mode = get_security_mode(scene)
    salt_bytes = get_student_id_hash(scene).encode("utf-8")
    key = get_teacher_double_hash(scene)

    return decrypt_metadata(
        encrypted_metadata=encrypted_item,
        key=key,
        salt_bytes=salt_bytes,
        mode=mode,
    )


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
    sync_logs_decrypted(scene)

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
# COMPRESSION FUNCTION
# --------------------------------------------------


def compress_logs(logs: list[str]) -> str:
    raw = json.dumps(logs).encode("utf-8")
    compressed = zlib.compress(raw, level=3)
    return base64.b64encode(compressed).decode("utf-8")


def decompress_logs(data: str) -> list[str]:
    compressed = base64.b64decode(data.encode("utf-8"))
    raw = zlib.decompress(compressed)
    return json.loads(raw.decode("utf-8"))


# --------------------------------------------------
# EXPORT
# --------------------------------------------------


def export_decrypted_logs(scene) -> ExportLogsResult:
    load_logs_from_scene(scene)

    valid = validate_log_integrity(scene)

    return {
        "data": runtime._runtime_logs_raw.copy(),
        "status": "valid" if valid else "tampered",
        "total_working_time": get_total_work_time(scene),
        "period": get_working_period(scene),
    }


def export_encrypted_logs(scene) -> list[str]:
    if not runtime._runtime_logs:
        load_logs_from_scene(scene)
    return list(runtime._runtime_logs)


# --------------------------------------------------
# SYNCING
# --------------------------------------------------


def is_runtime_sync() -> bool:
    return len(runtime._runtime_logs_raw) == len(runtime._runtime_logs)


def sync_index() -> int:
    """Return the index to start syncing (encrypt/decrypt)"""
    return min(len(runtime._runtime_logs_raw), len(runtime._runtime_logs))


def sync_logs_encrypted(scene):
    """Encrypt new raw log entries and append to _runtime_logs"""
    start_idx = sync_index()
    for entry in runtime._runtime_logs_raw[start_idx:]:
        encrypted = encrypt_log_item(scene, entry)
        runtime._runtime_logs.append(encrypted)


def sync_logs_decrypted(scene):
    """Decrypt new encrypted log entries and append to _runtime_logs_raw"""
    start_idx = sync_index()
    for encrypted in runtime._runtime_logs[start_idx:]:
        decrypted = decrypt_log_item(scene, encrypted)
        runtime._runtime_logs_raw.append(decrypted)


# --------------------------------------------------
# LOGGING FUNCTION
# --------------------------------------------------


def add_log(
    action_type: str,
    object_name: str,
    object_type: str,
    action_details: dict = None,
    duration: float = 0.0,
):
    scene = bpy.context.scene

    # Determine previous hash
    if runtime._runtime_logs_raw:
        prev_hash = compute_entry_hash(runtime._runtime_logs_raw[-1])
    else:
        # Genesis hash
        prev_hash = generate_genesis_key(
            teacher_key=scene.teacher_key,
            student_id=scene.student_id,
        )

    entry: ActionLogEntry = {
        "t": round(time.time(), 3),
        "a": action_type,
        "o": object_name,
        "ot": object_type,
        "d": action_details or {},
        "dt": round(duration, 3),
        "s": get_scene_stats(scene),
        "ph": prev_hash,
    }

    runtime._runtime_logs_raw.append(entry)
    runtime.mark_dirty()


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
    if hasattr(runtime, "_runtime_logs") and len(runtime._runtime_logs) >= 1:
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
    if not hasattr(runtime, "_runtime_logs"):
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
    if not runtime._runtime_logs:
        load_logs_from_scene(scene)

    if not runtime._runtime_logs:
        raise RuntimeError("No log entries found; cannot validate genesis log")

    # Get the first log entry
    first_encrypted = runtime._runtime_logs[0]
    first_entry = decrypt_log_item(scene, first_encrypted)

    if "ph" not in first_entry:
        raise RuntimeError("First log entry missing 'ph' (genesis hash)")

    expected_genesis = generate_genesis_key(teacher_key, student_id)

    return first_entry["ph"] == expected_genesis


def save_logs_to_scene(scene):
    sync_logs_encrypted(scene)
    compressed = compress_logs(runtime._runtime_logs)
    scene[SCENE_LOGS] = compressed


def load_logs_from_scene(scene) -> list[str]:
    data = scene.get(SCENE_LOGS)
    if not data:
        return []

    logs = decompress_logs(data)
    runtime._runtime_logs.clear()
    runtime._runtime_logs.extend(logs)

    # Sync new decrypted logs
    sync_logs_decrypted(scene)
    return logs


# --------------------------------------------------
# DETECT GENERAL MESH CHANGES
# --------------------------------------------------


def detect_mesh_action(obj) -> str | None:
    """
    Detects mesh changes with minimal overhead.
    Returns a string describing the action or None.
    """

    now = time.time()
    name = obj.name

    # -------------------------------
    # 1. New object detection
    # -------------------------------
    if name not in runtime._known_objects:
        runtime._known_objects.add(name)
        if obj.type == "MESH":
            prim_type = obj.get("primitive_type", "Mesh")
            runtime._last_object_state[name] = _get_object_state(obj)
            return f"Added {prim_type}"

    # -------------------------------
    # 2. Modifier added
    # -------------------------------
    last_mods = runtime._last_modifiers.get(name)
    current_mods = {mod.name for mod in obj.modifiers}

    if last_mods is None:
        runtime._last_modifiers[name] = current_mods
    elif added_mods := current_mods - last_mods:
        runtime._last_modifiers[name] = current_mods
        return f"Added Modifier: {', '.join(sorted(added_mods))}"

    # -------------------------------
    # 3. Edit mode debounce
    # -------------------------------
    if obj.mode == "EDIT":
        last_edit = runtime._edit_debounce.get(name, 0)
        if now - last_edit > 1.0:
            runtime._edit_debounce[name] = now
            return "Edited Mesh"

    # -------------------------------
    # 4. Transform debounce
    # -------------------------------
    state = _get_object_state(obj)
    last_state = runtime._last_object_state.get(name)

    last_transform = runtime._transform_debounce.get(name, 0)
    if state != last_state and now - last_transform > 1:
        runtime._last_object_state[name] = state
        runtime._transform_debounce[name] = now
        return "Transformed Object"

    return None


def _get_object_state(obj):
    """Cache-friendly tuple state of object location/rotation/scale rounded to 0.1"""
    return (
        tuple(round(v, 1) for v in obj.location),
        tuple(round(v, 1) for v in obj.rotation_euler),
        tuple(round(v, 1) for v in obj.scale),
    )


def log_simple_action(obj):
    action = detect_mesh_action(obj)
    if not action:
        return
    add_log(action_type=action, object_name=obj.name, object_type=obj.type)


def get_scene_stats(scene) -> dict:
    now = time.time()
    last = getattr(runtime, "_last_stats_time", 0)

    if now - last < 1.0:
        return runtime._last_scene_stats

    stats_str = scene.statistics(bpy.context.view_layer)
    print("[DEBUG] Scene statistics string:", stats_str)

    # Allow commas in numbers
    verts_match = re.search(r"Verts:([\d,]+)", stats_str)
    faces_match = re.search(r"Faces:([\d,]+)", stats_str)
    objects_match = re.search(r"Objects:([\d,]+)", stats_str)

    if not verts_match or not faces_match or not objects_match:
        print("[DEBUG] Regex match failed for scene stats")
        verts = faces = objects = 0
    else:
        # Remove commas before converting to int
        verts = int(verts_match.group(1).replace(",", ""))
        faces = int(faces_match.group(1).replace(",", ""))
        objects = int(objects_match.group(1).replace(",", ""))

    stats = {"v": verts, "f": faces, "o": objects}

    runtime._last_scene_stats = stats
    runtime._last_stats_time = now
    return stats


def get_total_work_time(scene) -> int:
    """
    Returns the total work time in seconds (int) between the 2nd log entry and the last log entry.
    Returns 0 if there are no logs or only the genesis log exists.
    """
    logs = runtime._runtime_logs_raw
    if not logs or len(logs) < 2:
        return 0

    # Decrypt the 2nd item (after genesis) and last item
    start_item = logs[1]
    end_item = logs[-1]

    start_time = start_item.get("t", 0)
    end_time = end_item.get("t", 0)

    total_seconds = round(max(0, end_time - start_time))
    return int(total_seconds)


def get_working_period(scene) -> WorkingPeriod:
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
