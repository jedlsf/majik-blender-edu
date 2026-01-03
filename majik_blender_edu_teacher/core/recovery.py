# recovery.py
import os
import bpy  # type: ignore
from typing import List, Optional, Dict, Any

from ..core import runtime
from ..core.crypto import encrypt_metadata, decrypt_metadata


class Recovery:
    """
    Handles external encrypted recovery logs for Majik Blender sessions.
    Uses AES (Fernet) or XOR fallback based on availability.
    """

    def __init__(self, filename: Optional[str] = None):
        if filename:
            self.filename = filename
        else:
            project_path = bpy.data.filepath
            if project_path:  # If the Blender project has been saved
                project_dir = os.path.dirname(project_path)
                project_name = os.path.splitext(os.path.basename(project_path))[0]
                self.filename = os.path.join(
                    project_dir, f"{project_name}_recovery.mjkb"
                )
            else:  # Fallback to home folder
                self.filename = os.path.join(
                    os.path.expanduser("~"), "majik_recovery_log.mjkb"
                )
        self.salt_bytes = None  # Will be derived from student_id

    def _derive_salt(self, scene: bpy.types.Scene) -> bytes:
        """
        Derive a salt for encryption/decryption from student_id
        """
        if not hasattr(scene, "student_id"):
            raise RuntimeError("Scene missing student_id for recovery encryption")
        return scene.student_id.encode("utf-8")

    def save(self, scene: bpy.types.Scene, mode: str = "AES") -> None:
        """
        Save the current runtime logs to an encrypted external file.
        """
        if not hasattr(runtime, "_runtime_logs_raw") or not runtime._runtime_logs_raw:
            return

        logs: List[Dict[str, Any]] = runtime._runtime_logs_raw.copy()
        self.salt_bytes = self._derive_salt(scene)

        encrypted = encrypt_metadata(
            metadata=logs,
            key=scene.teacher_key,
            salt_bytes=self.salt_bytes,
            mode=mode,
        )

        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(encrypted)

        print(f"[Recovery] Logs saved to {self.filename} ({len(logs)} entries)")

    def restore(
        self, scene: bpy.types.Scene, mode: str = "AES"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Restore runtime logs from the external encrypted recovery file.
        Returns the log list if successful, else None.
        """
        if not os.path.exists(self.filename):
            print("[Recovery] No recovery file found")
            return None

        self.salt_bytes = self._derive_salt(scene)

        with open(self.filename, "r", encoding="utf-8") as f:
            encrypted = f.read()

        try:
            logs = decrypt_metadata(
                encrypted_metadata=encrypted,
                key=scene.teacher_key,
                salt_bytes=self.salt_bytes,
                mode=mode,
            )
            current_len = len(getattr(runtime, "_runtime_logs_raw", []))
            recovered_len = len(logs)

            if recovered_len <= current_len:
                print(
                    f"[Recovery] Recovery skipped (current logs have {current_len} entries, recovery has {recovered_len})"
                )
                return None

            runtime._runtime_logs_raw = logs
            print(f"[Recovery] Restored {recovered_len} log entries from recovery file")

            # Delete recovery after successful restoration
            self.delete()

            return logs

        except Exception as e:
            print(f"[Recovery] Failed to restore logs: {e}")
            return None

    def delete(self) -> None:
        """
        Delete the recovery file.
        """
        if os.path.exists(self.filename):
            os.remove(self.filename)
            print(f"[Recovery] Recovery file {self.filename} deleted")
