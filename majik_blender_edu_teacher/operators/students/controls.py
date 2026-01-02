import bpy  # type: ignore
from bpy_extras.io_utils import ExportHelper  # type: ignore

import json

from ...core.constants import SCENE_TEACHER_DOUBLE_HASH

from ...core.timer import start_timer, stop_timer, load_timer_from_scene

from ...core.logging import (
    export_encrypted_logs,
    get_security_mode,
    load_logs_from_scene,
    operator_monitor,
    log_session_start,
    log_session_stop,
    get_total_work_time,
    get_working_period,
)

from .overlay import register_overlay, unregister_overlay

from ...core import runtime

from ...core.text.session_log_controller import SessionLogController

# --------------------------------------------------
# OPERATORS
# --------------------------------------------------
class STUDENT_OT_monitor(bpy.types.Operator):
    bl_idname = "main.monitor"
    bl_label = "Student Monitor"
    _timer = None

    def modal(self, context, event):
        if event.type == "TIMER":
            operator_monitor(context.scene)
        return {"PASS_THROUGH"}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        self._timer = None
        runtime._monitor_running = False
        return {"CANCELLED"}


class STUDENT_OT_start_stop(bpy.types.Operator):
    bl_idname = "main.start_stop"
    bl_label = "Start / Stop Session"
    bl_description = "Start or stop the logging session"

    @classmethod
    def poll(cls, context):
        scene = context.scene

        return bool(scene.student_id.strip()) and SCENE_TEACHER_DOUBLE_HASH in scene

    def execute(self, context):
        scene = context.scene

        if not scene.student_id.strip():
            self.report({"ERROR"}, "Student ID required")
            return {"CANCELLED"}

        logFile = SessionLogController.get_text_content()

        if (
            SCENE_TEACHER_DOUBLE_HASH not in scene
            or not logFile.strip()
        ):
            self.report({"ERROR"}, "Encrypted submission not found")
            return {"CANCELLED"}

        print("[STUDENT OT START STOP] Reloading logs and timer")
        # Load persisted data once
        load_timer_from_scene(scene)

        if runtime._timer_start is None:
            start_timer(scene)
            log_session_start("Session Timer Started")
            self.report({"INFO"}, "Session started")

            # Show overlay
            register_overlay()

            # Start modal safely using timer handler
            if not hasattr(runtime, "_monitor_running") or not runtime._monitor_running:
                bpy.app.timers.register(
                    lambda: bpy.ops.main.monitor("INVOKE_DEFAULT"),
                    first_interval=0.1,
                )
                runtime._monitor_running = True

        else:
            stop_timer(scene)
            log_session_stop("Session Timer Stopped")
            self.report({"INFO"}, "Session stopped and saved")
            # Hide overlay
            unregister_overlay()

        return {"FINISHED"}


class STUDENT_OT_export_logs(bpy.types.Operator, ExportHelper):
    bl_idname = "main.export_encrypted_logs"
    bl_label = "Download Encrypted Logs (JSON)"
    filename_ext = ".json"

    def execute(self, context):
        scene = context.scene

        rawLog = export_encrypted_logs(scene)

        if not rawLog:
            self.report({"WARNING"}, "No encrypted logs available to export")
            return {"CANCELLED"}

        load_timer_from_scene(scene)

        if runtime._timer_start:
            try:
                stop_timer(scene)
            except Exception as e:
                self.report({"WARNING"}, f"Failed to stop timer: {e}")

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "logs": rawLog,
                        "total_working_time": get_total_work_time(),
                        "period": get_working_period(),
                        "mode": get_security_mode(scene),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export encrypted logs: {e}")
            return {"CANCELLED"}

        self.report({"INFO"}, "Encrypted logs exported")
        return {"FINISHED"}
