import bpy # type: ignore
import json
import random
import string
from bpy_extras.io_utils import ExportHelper, ImportHelper  # type: ignore



# --------------------------------------------------
# KEY MANAGEMENT
# --------------------------------------------------


class SIGNATURE_OT_generate_key(bpy.types.Operator):
    bl_idname = "main.generate_key"
    bl_label = "Generate Key"
    bl_description = "Automatically generate a secure random teacher key"

    def execute(self, context):
        context.scene.teacher_key = "".join(
            random.choices(string.ascii_letters + string.digits, k=32)
        )
        return {"FINISHED"}


class SIGNATURE_OT_export_key(bpy.types.Operator, ExportHelper):
    bl_idname = "main.export_key"
    bl_label = "Download Key"
    filename_ext = ".json"
    bl_description = "Download the current Teacher Key as a JSON file"

    @classmethod
    def poll(cls, context):
        return bool(context.scene.teacher_key.strip())

    def execute(self, context):
        with open(self.filepath, "w") as f:
            json.dump({"teacher_key": context.scene.teacher_key}, f)
        return {"FINISHED"}


class SIGNATURE_OT_import_key(bpy.types.Operator, ImportHelper):
    bl_idname = "main.import_key"
    bl_label = "Import Key"
    filename_ext = ".json"
    bl_description = "Import a Teacher Key from a JSON file"

    def execute(self, context):
        with open(self.filepath, "r") as f:
            context.scene.teacher_key = json.load(f)["teacher_key"]
        return {"FINISHED"}
