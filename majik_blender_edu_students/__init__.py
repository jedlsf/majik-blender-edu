bl_info = {
    "name": "Majik Blender Edu (For Students)",
    "author": "Zelijah",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Properties > Scene",
    "description": "Majik Blender Edu is a submission integrity and student activity tracking addon for Blender designed to help educators verify a student's work.",
    "doc_url": "https://thezelijah.world/tools/education-majik-blender-edu",
    "category": "Education",
    "warning": "Requires 'cryptography' Python package for AES encryption",
}


import os
import bpy  # type: ignore
import sys

_ADDON_DIR = os.path.dirname(__file__)
_VENDOR_DIR = os.path.join(_ADDON_DIR, "_vendor")

if os.path.isdir(_VENDOR_DIR) and _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

from .core.crypto import is_crypto_available, install_crypto_wheel


def try_install_crypto():
    if not is_crypto_available():
        print("[ADDON] Cryptography not found, attempting install...")
        install_crypto_wheel()
    return None  # stop the timer


bpy.app.timers.register(try_install_crypto)

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

from .core.properties import register_properties, unregister_properties
from .core.handlers import on_file_load
from .operators import *
from .ui import *
from .core.logging import (
    on_depsgraph_update,
    register_logging_handlers,
    unregister_logging_handlers,
)


# ---------------------------------------
# Addon Preferences
# ---------------------------------------
class MAJIK_OT_addon_prefs(bpy.types.AddonPreferences):
    bl_idname = "majik_blender_edu_students"  # must match the folder/module name

    def draw(self, context):
        layout = self.layout
        layout.label(text="Majik Blender Edu – For Students Addon Preferences")

        if not is_crypto_available():
            layout.label(text="Cryptography package not installed!", icon="ERROR")
            layout.operator("main.prompt_install_crypto", icon="IMPORT")
        else:
            layout.label(text="All dependencies satisfied.", icon="CHECKMARK")


classes = [
    MAJIK_OT_addon_prefs,
    STUDENT_OT_start_stop,
    STUDENT_OT_monitor,
    STUDENT_PT_panel,
    STUDENT_OT_export_logs,
]


def register():
    register_properties()
    register_logging_handlers()
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.handlers.load_post.append(on_file_load)


def unregister():
    bpy.app.handlers.load_post.remove(on_file_load)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    unregister_logging_handlers()
    unregister_properties()
