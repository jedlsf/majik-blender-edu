import bpy  # type: ignore

from ..core import *

from ..core import runtime

# --------------------------------------------------
# PANEL
# --------------------------------------------------


class SIGNATURE_PT_panel(bpy.types.Panel):
    bl_label = "Majik Blender Edu – Teacher"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

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

            # If AES is selected but missing, show install button
            if scene.security_mode == "AES":
                if is_crypto_available():
                    layout.label(text="AES successfully installed.", icon="CHECKMARK")
                else:
                    layout.label(text="AES not available.", icon="ERROR")
                    layout.operator("main.prompt_install_crypto", icon="IMPORT")

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
