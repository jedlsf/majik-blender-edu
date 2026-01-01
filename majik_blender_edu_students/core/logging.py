import bpy  # type: ignore
import time
import json
import base64
import hashlib
import re

from ..core import runtime
from ..core.text.session_log_controller import SessionLogController
from .timer import save_timer_to_scene

from .constants import (
    SCENE_SIGNATURE_MODE,
)

from ..core.recovery import Recovery

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


IDLE_THRESHOLD = 60.0  # Seconds of inactivity before force-committing

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

    finalize_and_commit_log()

    if len(runtime._runtime_logs_raw) <= 0:
        print("[EXPORT DECRYPTED LOGS] Reloading logs")
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


# --------------------------------------------------
# LOGGING FUNCTION
# --------------------------------------------------


def add_log(
    action_type: str,
    object_name: str,
    object_type: str,
    action_details: dict = None,
    override_dt: float = None,  # Add this parameter
):
    scene = bpy.context.scene

    # Determine previous hash
    if runtime._runtime_logs_raw:
        prev_entry = runtime._runtime_logs_raw[-1]
        prev_hash = compute_entry_hash(prev_entry)
    else:
        prev_entry = None
        prev_hash = generate_genesis_key(
            teacher_key=scene.teacher_key,
            student_id=scene.student_id,
        )

    current_time = round(time.time(), 3)
    # Use the override_dt if provided (from aggregation),
    # otherwise calculate it normally.
    duration = (
        override_dt
        if override_dt is not None
        else calculate_duration(prev_entry, {"t": current_time})
    )

    entry: ActionLogEntry = {
        "t": current_time,
        "a": action_type,
        "o": object_name,
        "ot": object_type,
        "d": action_details or {},
        "dt": duration,
        "s": get_scene_stats(scene),
        "ph": prev_hash,
    }

    runtime._runtime_logs_raw.append(entry)
    runtime.mark_log_dirty()
    print(f"[Majik Log] [New Log] {action_type} -> {object_name} ({object_type})")
    # --- Recovery save ---
    try:
        recovery_instance = Recovery()
        recovery_instance.save(scene=scene, mode=get_security_mode(scene))
    except Exception as e:
        print(f"[Recovery] Failed to save logs: {e}")


def calculate_duration(
    previous_entry: ActionLogEntry | None, current_entry: ActionLogEntry | None
) -> float:
    """
    Calculate elapsed time in seconds between two log entries.
    Returns 0 if previous or current entry is missing, or timestamps are invalid.
    """
    if not previous_entry or not current_entry:
        return 0.0

    prev_time = previous_entry.get("t")
    curr_time = current_entry.get("t")

    if not isinstance(prev_time, (int, float)) or not isinstance(
        curr_time, (int, float)
    ):
        return 0.0

    diff = curr_time - prev_time
    return round(diff, 3) if diff > 0 else 0.0


def add_log_aggregated(action_type, object_name, object_type, action_details=None):
    """
    Guarantees that identical actions are merged into a single 'session'.
    If the context changes, the previous session is finalized immediately.
    """
    scene = bpy.context.scene
    current_time = round(time.time(), 3)

    pending = getattr(runtime, "_pending_log", None)

    if pending:
        # Calculate how long since the student last 'interacted' with this pending log
        # We'll use a new 'last_update' key in the pending dict
        last_update = pending.get("lu", pending["t"])
        idle_time = current_time - last_update

        # CHECK 1: Is the student continuing the EXACT same task?
        is_same_task = (
            pending["a"] == action_type
            and pending["o"] == object_name
            and pending["ot"] == object_type
        )

        # CHECK 2: Is the idle time too long? (Heartbeat check)
        if is_same_task and idle_time < IDLE_THRESHOLD:
            # Continue the session
            pending["d"] = action_details or {}
            pending["s"] = get_scene_stats(scene)
            pending["lu"] = current_time  # Update the 'Last Updated' timestamp
            return
        else:
            # Either task changed OR they were idle too long. Commit it.
            finalize_and_commit_log()
            print(f"[Majik Log] [Idle Commit] {pending['a']} -> {pending['o']} ({pending['ot']})")


    # 2. Start a NEW session
    runtime._pending_log = {
        "t": current_time,
        "lu": current_time,  # Last Update Time (for idle tracking)
        "a": action_type,
        "o": object_name,
        "ot": object_type,
        "d": action_details or {},
        "dt": 0.0,  # Will be calculated upon finalization
        "s": get_scene_stats(scene),
        "ph": None,
    }

    print(f"[Majik Log] [New Pending Log] {action_type} -> {object_name} ({object_type})")


def finalize_and_commit_log():
    """
    Calculates the final duration of the buffered action and
    officially adds it to the cryptographically hashed log.
    """
    pending = getattr(runtime, "_pending_log", None)
    if not pending:
        return

    # Calculate how long this specific action lasted
    # This turns 50 'Edited Mesh' events into ONE entry with a 30s duration
    last_active = pending.get("lu", pending["t"])
    duration = round(last_active - pending["t"], 3)

    # Use the existing add_log to handle the hashing and list insertion
    add_log(
        action_type=pending["a"],
        object_name=pending["o"],
        object_type=pending["ot"],
        action_details=pending["d"],
        override_dt=max(0.0, duration),
    )

    runtime._pending_log = None


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
        print("[VALIDATE GENESIS LOG] Reloading logs")
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

    # Print raw logs
    for log in runtime._runtime_logs_raw:
        print(log)

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
        if now - last_edit > 0.3:
            runtime._edit_debounce[name] = now
            return "Edited Mesh"

    # -------------------------------
    # 4. Transform debounce
    # -------------------------------
    state = _get_object_state(obj)
    last_state = runtime._last_object_state.get(name)

    last_transform = runtime._transform_debounce.get(name, 0)
    if state != last_state and now - last_transform > 0.3:
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
    add_log_aggregated(action_type=action, object_name=obj.name, object_type=obj.type)


# --------------------------------------------------
# DEPSGRAPH MONITOR
# --------------------------------------------------
def on_depsgraph_update(scene, depsgraph):
    """Optimized depsgraph update handler for logging mesh, curve, and armature changes."""
    if bpy.app.background or runtime._timer_start is None:
        return

    updated_objs: set[bpy.types.Object] = set()

    # Collect all relevant updated objects
    for update in depsgraph.updates:
        obj = getattr(update, "id", None)
        if isinstance(obj, bpy.types.Object) and obj.type in {
            "MESH",
            "CURVE",
            "ARMATURE",
        }:
            updated_objs.add(obj)

    now = time.time()

    # Log actions for each updated object only once
    for obj in updated_objs:
        action = detect_mesh_action(obj)  # detect once
        if action:
            print(f"[Depsgraph Monitor] {action} on {obj.name}")
            add_log_aggregated(
                action_type=action,
                object_name=obj.name,
                object_type=obj.type,
            )

    # Autosave timer + logs every N seconds
    if now - runtime._last_autosave_time >= runtime.AUTOSAVE_INTERVAL:
        save_timer_to_scene(scene)
        runtime._last_autosave_time = now


# --------------------------------------------------
# OPERATOR POST HANDLER
# --------------------------------------------------
def handle_object_update(obj):
    log_simple_action(obj)
    operator_post_handler()


def operator_post_handler():
    if runtime._timer_start is None:
        return

    context = bpy.context
    obj = context.active_object
    if not obj or obj.type != "MESH":
        return

    op = getattr(context.window_manager, "operators", None)
    if not op:
        return

    last_op = op[-1] if op else None
    if last_op and last_op.bl_idname.startswith("MESH_OT"):
        details = {
            prop.identifier: getattr(last_op.properties, prop.identifier)
            for prop in last_op.properties.bl_rna.properties
            if not prop.is_readonly
        }

        add_log_aggregated(
            action_type=f"Operator: {last_op.bl_idname}",
            object_name=obj.name,
            object_type=obj.type,
            action_details=details,
        )


def log_import_post(context):
    if runtime._timer_start is None:
        return

    op = (
        bpy.context.window_manager.operators[-1]
        if bpy.context.window_manager.operators
        else None
    )

    for obj in context.objects:
        if obj.library is not None:
            method = "link"
        elif op and op.bl_idname == "WM_OT_append":
            method = "append"
        elif op and op.bl_idname.startswith("IMPORT_SCENE_"):
            method = "import"
        else:
            method = "unknown"

        add_log_aggregated(
            action_type="Asset Added",
            object_name=obj.name,
            object_type=obj.type,
            action_details={
                "method": method,
                "source_file": context.filepath,
                "linked": obj.library is not None,
                "library": obj.library.filepath if obj.library else None,
                "collection": (
                    obj.users_collection[0].name if obj.users_collection else None
                ),
            },
        )


def log_session_event(
    *,
    started: bool,
    reason: str = "",
):
    """
    Log a session (timer) start or stop event.
    This is a chain-critical audit entry.
    """

    action = "Session Started" if started else "Session Stopped"

    add_log(
        action_type=action,
        object_name="__SESSION__",
        object_type="SYSTEM",
        action_details={
            "started": started,
            "reason": reason,
            "timer_running": runtime._timer_start is not None,
        },
    )

    runtime._session_active = started
    print(f"[Session Log] {action} | Active: {started}")


def log_session_start(reason: str = "user_start"):
    if runtime.is_session_active():
        return  # prevent duplicate starts

    log_session_event(
        started=True,
        reason=reason,
    )


def log_session_stop(reason: str = "user_stop"):
    if not runtime.is_session_active():
        return  # prevent duplicate stops
    finalize_and_commit_log()
    log_session_event(
        started=False,
        reason=reason,
    )
    scene = bpy.context.scene
    save_logs_to_scene(scene)
    save_timer_to_scene(scene)


def get_scene_stats(scene) -> SceneStats:
    now = time.time()
    last = getattr(runtime, "_last_stats_time", 0)

    if now - last < 1.0:
        return runtime._last_scene_stats

    stats_str = scene.statistics(bpy.context.view_layer)

    def extract_denominator(pattern: str) -> int:
        """
        Extracts the denominator if format is 'num/den', else returns the number itself.
        """
        match = re.search(pattern, stats_str)
        if not match:
            return 0
        val = match.group(1).replace(",", "")
        if "/" in val:
            return int(val.split("/")[1])
        return int(val)

    verts = extract_denominator(r"Verts:([\d/,]+)")
    faces = extract_denominator(r"Faces:([\d/,]+)")
    objects = extract_denominator(r"Objects:([\d/,]+)")

    stats = {"v": verts, "f": faces, "o": objects}

    runtime._last_scene_stats = stats
    runtime._last_stats_time = now
    return stats


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


# --------------------------------------------------
# AUTOSAVE + SIMPLE MONITOR
# --------------------------------------------------


def operator_monitor(scene):
    if runtime._timer_start is None:
        return

    obj = bpy.context.active_object
    if obj and obj.type in {"MESH", "CURVE", "ARMATURE"}:
        log_simple_action(obj)

    now = time.time()
    # --- IDLE CHECK ---
    pending = getattr(runtime, "_pending_log", None)
    if pending:
        last_update = pending.get("lu", pending["t"])
        if (now - last_update) > IDLE_THRESHOLD:
            print(f"[Majik] Idle timeout reached for {pending['a']}. Committing.")
            finalize_and_commit_log()

    if now - runtime._last_autosave_time >= runtime.AUTOSAVE_INTERVAL:
        save_timer_to_scene(scene)
        runtime._last_autosave_time = now


def on_save_pre(filepath: str):
    scene = bpy.context.scene
    finalize_and_commit_log()
    add_log(
        action_type="File Saved",
        object_name="__SYSTEM__",
        object_type="SYSTEM",
        action_details={"filepath": filepath},
    )
    save_logs_to_scene(scene)
    save_timer_to_scene(scene)
    print(f"[Majik] Logs and timer saved before saving {filepath}")


# --------------------------------------------------
# REGISTER / UNREGISTER
# --------------------------------------------------


def register_logging_handlers():
    if on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
    if log_import_post not in bpy.app.handlers.blend_import_post:
        bpy.app.handlers.blend_import_post.append(log_import_post)
    if on_save_pre not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(on_save_pre)


def unregister_logging_handlers():
    if on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    if log_import_post in bpy.app.handlers.blend_import_post:
        bpy.app.handlers.blend_import_post.remove(log_import_post)
    if on_save_pre in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(on_save_pre)
