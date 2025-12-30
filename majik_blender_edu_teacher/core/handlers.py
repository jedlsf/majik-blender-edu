import bpy  # type: ignore
from .runtime import clear_runtime


def on_file_load(_):
    for scene in bpy.data.scenes:
        scene.teacher_key = ""
    clear_runtime()
