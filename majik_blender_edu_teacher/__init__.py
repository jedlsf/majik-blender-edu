bl_info = {
    "name": "Majik Blender Edu",
    "author": "Zelijah",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Properties > Scene",
    "description": "Majik Blender Edu is a submission integrity and student activity tracking addon for Blender designed to help educators verify a student's work.",
    "doc_url": "https://thezelijah.world/tools/education-majik-blender-edu",
    "category": "Education",
}


import bpy  # type: ignore

from .core.crypto import install_crypto_wheel, is_crypto_installed


def try_install_crypto():
    if not is_crypto_installed():
        print("[ADDON] Cryptography not yet installed, attempting install...")
        install_crypto_wheel()
    return None  # stop the timer


def restore_logs_on_start():

    from .core.recovery import Recovery
    from .core.constants import SCENE_SIGNATURE_MODE

    if runtime._runtime_logs_raw:
        return  # Already loaded
    scene = bpy.context.scene

    if scene is None:
        print("[Recovery] No active scene; skipping log restore")
        return

    try:
        secMode = scene.get(SCENE_SIGNATURE_MODE, "AES")
        recovery_instance = Recovery()
        restored = recovery_instance.restore(scene=scene, mode=secMode)
        if restored:
            print(f"[Recovery] Restored {len(restored)} logs from previous session")
        else:
            # No recovery file, start fresh
            print("[Recovery] No previous logs found")
    except Exception as e:
        print(f"[Recovery] Failed to restore logs: {e}")


def safe_restore_logs():
    try:
        restore_logs_on_start()
    except Exception as e:
        print(f"[Recovery] Could not restore logs yet: {e}")
    return None  # timers need this


bpy.app.timers.register(try_install_crypto)
bpy.app.timers.register(safe_restore_logs)

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

from .core.properties import register_properties, unregister_properties
from .core.handlers import on_file_load
from .operators import *
from .ui import *

from .core.logging import register_logging_handlers, unregister_logging_handlers

from .core import runtime


# ---------------------------------------
# Addon Preferences
# ---------------------------------------
class MAJIK_OT_addon_prefs(bpy.types.AddonPreferences):
    bl_idname = "majik_blender_edu_teacher"

    # default_user_mode = bpy.props.EnumProperty(
    #     name="Default User Mode",
    #     description="Default mode when opening a new file",
    #     items=[
    #         ("TEACHER", "Teacher", "Instructor mode"),
    #         ("STUDENT", "Student", "Student mode"),
    #     ],
    #     default="TEACHER",
    # )

    # lock_user_mode = bpy.props.BoolProperty(
    #     name="Lock User Mode",
    #     description="Prevent changing user mode inside the scene",
    #     default=False,
    # )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Majik Blender Edu – Global Settings")
        # layout.prop(self, "default_user_mode")
        # layout.prop(self, "lock_user_mode")


classes = [
    MAJIK_OT_addon_prefs,
    SIGNATURE_OT_encrypt,
    SIGNATURE_OT_decrypt,
    SIGNATURE_OT_export_logs,
    SIGNATURE_OT_reset_submission,
    SIGNATURE_OT_generate_key,
    SIGNATURE_OT_export_key,
    SIGNATURE_OT_import_key,
    MAJIK_PT_mode_selector,
    LOCKED_OBJECTS_UL_list,
    LOCKED_OBJECTS_OT_add,
    LOCKED_OBJECTS_OT_remove,
    LOCKED_OBJECTS_OT_clear,
    TEACHER_PT_panel,
    STUDENT_OT_start_stop,
    STUDENT_OT_monitor,
    STUDENT_PT_panel,
    STUDENT_OT_export_logs,
]

# --------------------------------------------------
# REGISTER
# --------------------------------------------------


def register():
    # Ensure runtime logs exist
    if not hasattr(runtime, "_runtime_logs_raw"):
        runtime._runtime_logs_raw = []

    register_properties()
    register_logging_handlers()

    for cls in classes:
        bpy.utils.register_class(cls)

    if on_file_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_file_load)


def unregister():
    bpy.app.handlers.load_post.remove(on_file_load)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    unregister_logging_handlers()
    unregister_properties()
