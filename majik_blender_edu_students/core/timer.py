import json
from ..core import runtime
import time
from .constants import SCENE_ACTIVE_TIMER

# --------------------------------------------------
# TIMER
# --------------------------------------------------


def start_timer(scene):
    """Resume timer without resetting elapsed time"""
    if runtime._timer_start is None:
        runtime._timer_start = time.time()
        save_timer_to_scene(scene)


def stop_timer(scene):
    """Pause timer and finalize elapsed time"""
    if runtime._timer_start is not None:
        runtime._timer_elapsed += time.time() - runtime._timer_start

        runtime._timer_elapsed = max(0.0, runtime._timer_elapsed)
        runtime._timer_start = None
        save_timer_to_scene(scene)


def get_total_time() -> float:
    """Get total elapsed time, including running session"""
    elapsed = runtime._timer_elapsed
    if runtime._timer_start is not None:
        elapsed += time.time() - runtime._timer_start
    return elapsed


def get_timer_label():
    if runtime._timer_start is None:
        if runtime._timer_elapsed > 0:
            return "Resume"
        return "Start"
    return "Pause"


def load_timer_from_scene(scene):
    data = scene.get(SCENE_ACTIVE_TIMER)
    if not data:
        return

    try:
        parsed = json.loads(data)
    except Exception:
        return

    runtime._timer_elapsed = max(0.0, float(parsed.get("elapsed", 0.0)))
    runtime._timer_start = time.time() if parsed.get("running") else None


def save_timer_to_scene(scene):
    scene[SCENE_ACTIVE_TIMER] = json.dumps(
        {
            "elapsed": runtime._timer_elapsed,
            "running": runtime._timer_start is not None,
        }
    )
