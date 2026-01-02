
from .runtime import clear_runtime
from .logging import load_logs_from_scene
from .timer import load_timer_from_scene

def on_file_load(scene):
    scene.teacher_key = ""
    clear_runtime()
    load_logs_from_scene(scene)
    load_timer_from_scene(scene)
