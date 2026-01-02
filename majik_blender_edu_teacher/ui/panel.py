import bpy  # type: ignore

from ..core import *

from ..core import runtime

from ..core.constants import SCENE_TEACHER_DOUBLE_HASH

from ..core.timer import load_timer_from_scene, get_timer_label


from ..core.logging import get_total_work_time

from ..core.text.session_log_controller import SessionLogController


# --------------------------------------------------
# USER MODE PANEL
# --------------------------------------------------


class MAJIK_PT_mode_selector(bpy.types.Panel):
    bl_label = "Majik Blender Edu (Mode Selector)"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return hasattr(context.scene, "user_mode")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "user_mode", expand=True)


# --------------------------------------------------
# TEACHER PANEL
# --------------------------------------------------


class TEACHER_PT_panel(bpy.types.Panel):
    bl_label = "Majik Blender Edu – Teacher"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return (
            hasattr(context.scene, "user_mode") and context.scene.user_mode == "TEACHER"
        )

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "submission_tab", expand=True)

        if scene.submission_tab == "ENCRYPT":
            layout.label(text="Encryption / Signing", icon="LOCKED")

            layout.prop(scene, "teacher_key", text="Teacher Key")
            layout.prop(scene, "student_id", text="Student ID")
            layout.prop(
                scene, "protect_geometry", text="Protect Selected Geometry Only"
            )

            if scene.protect_geometry:
                layout.template_list(
                    "LOCKED_OBJECTS_UL_list",
                    "",
                    scene,
                    "locked_objects",
                    scene,
                    "locked_index",
                )
                row = layout.row(align=True)
                row.operator("locked_objects.add", icon="ADD")
                row.operator("locked_objects.remove", icon="REMOVE")
                row.operator("locked_objects.clear", icon="TRASH")

            row = layout.row(align=True)
            row.operator("main.generate_key")
            row.operator("main.export_key")
            row.operator("main.import_key")

            layout.prop(scene, "security_mode", text="Security Mode")

            layout.operator("main.encrypt", icon="CHECKMARK")

        else:
            layout.label(text="Decryption / Review", icon="UNLOCKED")

            if SCENE_ENCRYPTED_KEY in scene:
                box = layout.box()
                box.label(text="This project is encrypted.", icon="LOCKED")
                box.label(text="Enter the Teacher Key to decrypt and review.")

                layout.prop(scene, "teacher_key", text="Teacher Key")

                importRow = layout.row()
                importRow.operator("main.import_key")

                row = layout.row()
                row.operator("main.decrypt", icon="KEY_HLT")

            else:
                box = layout.box()
                box.label(text="This project is NOT encrypted.", icon="ERROR")
                box.label(text="No submission signature was found.")
                box.label(text="This file cannot be verified.")
                return

            # Decrypted metadata view
            if runtime._runtime_metadata:
                layout.separator()
                layout.label(
                    text=f"Student ID: {runtime._runtime_metadata['student_id']}",
                    icon="USER",
                )
                layout.label(
                    text=f"Timestamp: {timestamp_to_readable(runtime._runtime_metadata['timestamp'])}",
                    icon="TIME",
                )

                layout.separator()
                layout.label(text="Action Logs", icon="TEXT")
                layout.operator("main.export_logs", icon="EXPORT")

                # NEW: Reset button with confirmation
                layout.separator()
                layout.operator("main.reset_submission", icon="TRASH")


# --------------------------------------------------
# STUDENT PANEL
# --------------------------------------------------


class STUDENT_PT_panel(bpy.types.Panel):
    bl_label = "Majik Blender Edu – Student"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return (
            hasattr(context.scene, "user_mode") and context.scene.user_mode == "STUDENT"
        )

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
        layout.label(text=f"Total Logs: {len(runtime._runtime_logs_raw)} entries")

        export_row = layout.row()
        export_row.enabled = enabled
        export_row.operator("main.export_encrypted_logs", icon="EXPORT")
