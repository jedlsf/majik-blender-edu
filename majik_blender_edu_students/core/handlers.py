

from .logging import load_logs_from_scene
from .timer import load_timer_from_scene
# --------------------------------------------------
# HANDLER
# --------------------------------------------------


def on_file_load(scene):
    load_logs_from_scene(scene)
    load_timer_from_scene(scene)
