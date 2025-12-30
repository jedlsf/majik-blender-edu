import json
import bpy  # type: ignore

from bpy_extras.io_utils import ExportHelper  # type: ignore

from ..core.logging import export_decrypted_logs



class SIGNATURE_OT_export_logs(bpy.types.Operator, ExportHelper):
    bl_idname = "main.export_logs"
    bl_label = "Download Action Logs (JSON)"
    filename_ext = ".json"
    bl_description = "Download the current action logs as a JSON file"

    def execute(self, context):
        scene = context.scene
        exportData = export_decrypted_logs(scene)

        if not exportData["data"]:
            self.report({"WARNING"}, "No logs available to export")
            return {"CANCELLED"}

        if exportData["status"] == "tampered":
            self.report(
                {"WARNING"}, "Logs integrity check failed! Some logs may be tampered."
            )

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(exportData, f, indent=2)
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export logs: {e}")
            return {"CANCELLED"}

        self.report({"INFO"}, "Action logs exported")
        return {"FINISHED"}
