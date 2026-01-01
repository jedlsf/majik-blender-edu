import bpy  # type: ignore


from ..core.constants import SCENE_TEACHER_DOUBLE_HASH

from ..core.timer import load_timer_from_scene, get_timer_label

from ..core.crypto import is_crypto_available

from ..core import runtime

from ..core.logging import get_total_work_time

from ..core.text.session_log_controller import SessionLogController

# --------------------------------------------------
# PANEL
# --------------------------------------------------


class STUDENT_PT_panel(bpy.types.Panel):
    bl_label = "Majik Blender Edu – Student"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        load_timer_from_scene(scene)

        layout.prop(scene, "student_id", text="Student ID")

        logFile = SessionLogController.get_text_content()

        enabled = (
            bool(logFile.strip())
            and SCENE_TEACHER_DOUBLE_HASH in scene
            and bool(scene.student_id.strip())
        )

        mode = scene.get("_signature_mode", "XOR")

        # ERROR CASE: AES mode but crypto is missing
        if mode == "AES" and not is_crypto_available():
            layout.label(
                text="This project is encrypted with AES and its dependencies are missing.",
                icon="ERROR",
            )
            layout.operator("main.prompt_install_crypto", icon="IMPORT")

        # NORMAL CASE: AES + crypto OK OR not AES
        else:
            if enabled:
                row = layout.row()
                row.enabled = enabled
                buttonLabel = get_timer_label()
                icon = "PAUSE" if runtime._timer_start else "PLAY"
                row.operator("main.start_stop", text=buttonLabel, icon=icon)
            else:
                box = layout.box()
                box.label(
                    text="Please set a Student ID and ensure the file is prepared by the teacher.",
                    icon="ERROR",
                )

        layout.separator()
        layout.label(text=f"Total Work Time: {get_total_work_time():.1f} seconds")

        export_row = layout.row()
        export_row.enabled = enabled
        export_row.operator("main.export_encrypted_logs", icon="EXPORT")
