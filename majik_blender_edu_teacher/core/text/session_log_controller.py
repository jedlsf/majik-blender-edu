import hashlib
import bpy  # type: ignore

import json
import zlib
import base64
from typing import Any, Dict, List, Optional, TypedDict

from .text_data import TextData
from ...core.crypto import fernet_key_from_string

from cryptography.fernet import Fernet
from ...core.constants import (
    SCENE_STUDENT_ID_HASH,
    SCENE_TEACHER_DOUBLE_HASH,
)


# -------------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------------
SESSION_LOG_TEXT_NAME = "__MAJIK_SESSION_LOG__"


class SceneStats(TypedDict):
    v: int  # Vertex Count
    f: int  # Face Count
    o: int  # Object Count


class ActionLogEntry(TypedDict):
    t: float  # timestamp
    a: str  # action_type
    o: str  # object_name
    ot: str  # object_type
    d: Dict[str, Any]  # action_details
    dt: float  # duration
    s: SceneStats  # scene_stats
    ph: str  # previous hash or genesis hash


def get_student_id_hash(scene) -> str:
    if SCENE_STUDENT_ID_HASH not in scene:
        raise RuntimeError("Student ID hash missing from scene")
    return scene[SCENE_STUDENT_ID_HASH]


def get_teacher_double_hash(scene) -> str:
    if SCENE_TEACHER_DOUBLE_HASH not in scene:
        raise RuntimeError("Teacher integrity key missing from scene")
    return scene[SCENE_TEACHER_DOUBLE_HASH]


# -------------------------------------------------------------------
# CONTROLLER
# -------------------------------------------------------------------
class SessionLogController:
    """
    Controller for managing session logs in Blender via a Text datablock.
    Follows the architecture:
    _runtime_logs_raw (List[ActionLogEntry]) → json.dumps → zlib.compress → encrypt → base64 → Text
    """

    # -------------------------------------------------------------------
    # ENSURE SESSION TEXT EXISTS
    # -------------------------------------------------------------------
    @staticmethod
    def ensure_session_text(force_recreate: bool = False) -> bpy.types.Text:
        print("[SessionLogController] ensure_session_text() called")
        print(f"[SessionLogController] force_recreate={force_recreate}")

        text = TextData.get_text(SESSION_LOG_TEXT_NAME)

        if text and not force_recreate:
            print("[SessionLogController] Session log text already exists")
            return text

        if text and force_recreate:
            print("[SessionLogController] Removing existing session log text")
            TextData.remove_text(text)

        print("[SessionLogController] Creating new session log text")
        text = TextData.create_text(SESSION_LOG_TEXT_NAME)
        TextData.write_text(text, "", clear=True)
        print("[SessionLogController] Session log text created successfully")
        return text

    # -------------------------------------------------------------------
    # SAVE RAW LOGS TO TEXT
    # -------------------------------------------------------------------
    @staticmethod
    def save_logs_to_text(
        raw_logs: List[ActionLogEntry], *, scene: Optional[bpy.types.Scene] = None
    ) -> None:
        """
        Save _runtime_logs_raw to Text datablock following the flow:
        json.dumps → zlib.compress → encrypt → base64 → write to Text
        """
        print("[SessionLogController] save_logs_to_text() called")
        if scene is None:
            scene = bpy.context.scene

        print(f"[SessionLogController] Total logs to save: {len(raw_logs)}")

        # Step 1: Serialize JSON
        serialized = json.dumps(raw_logs, separators=(",", ":"), ensure_ascii=False)
        print(
            f"[SessionLogController] Serialized logs size: {len(serialized.encode('utf-8'))} bytes"
        )

        # Step 2: Compress
        compressed = zlib.compress(serialized.encode("utf-8"), level=5)
        print(f"[SessionLogController] Compressed size: {len(compressed)} bytes")

        # Step 3: Encrypt
        salt_bytes = get_student_id_hash(scene).encode("utf-8")
        key = get_teacher_double_hash(scene)

        aes_key = fernet_key_from_string(key, salt_bytes)
        cipher = Fernet(aes_key)
        encrypted = cipher.encrypt(compressed)

        print(f"[SessionLogController] Encrypted size: {len(encrypted)} bytes")

        # Step 4: Base64 encode
        b64_encoded = base64.b64encode(encrypted).decode("utf-8")
        print(f"[SessionLogController] Base64 size: {len(b64_encoded)} chars")

        # Step 5: Write to Text datablock
        text = SessionLogController.ensure_session_text()
        TextData.write_text(text, b64_encoded, clear=True)
        print("[SessionLogController] Logs successfully saved to Text datablock")

    # -------------------------------------------------------------------
    # LOAD LOGS FROM TEXT
    # -------------------------------------------------------------------
    @staticmethod
    def load_logs_from_text(
        *, scene: Optional[bpy.types.Scene] = None
    ) -> List[ActionLogEntry]:
        """
        Load logs from Text datablock and reverse the flow:
        read → base64 decode → decrypt → decompress → json.loads
        """
        print("[SessionLogController] load_logs_from_text() called")
        if scene is None:
            scene = bpy.context.scene

        text = TextData.get_text(SESSION_LOG_TEXT_NAME)
        if not text:
            print("[SessionLogController] No session log text found")
            return []

        # Step 1: Read Text
        b64_encoded = TextData.read_text(text)
        print(
            f"[SessionLogController] Read {len(b64_encoded)} chars from Text datablock"
        )

        if not b64_encoded:
            print("[SessionLogController] Text datablock is empty")
            return []

        try:
            # Step 2: Base64 decode
            encrypted = base64.b64decode(b64_encoded)
            print(f"[SessionLogController] Base64 decoded size: {len(encrypted)} bytes")

            # Step 3: Decrypt
            salt_bytes = get_student_id_hash(scene).encode("utf-8")
            key = get_teacher_double_hash(scene)

            aes_key = fernet_key_from_string(key, salt_bytes)
            cipher = Fernet(aes_key)
            compressed = cipher.decrypt(encrypted)

            print(f"[SessionLogController] Decrypted size: {len(compressed)} bytes")

            # Step 4: Decompress
            serialized = zlib.decompress(compressed).decode("utf-8")
            print(
                f"[SessionLogController] Decompressed size: {len(serialized.encode('utf-8'))} bytes"
            )

            # Step 5: Deserialize JSON
            raw_logs = json.loads(serialized)
            print(f"[SessionLogController] Loaded {len(raw_logs)} logs successfully")

        except Exception as e:
            print(f"[SessionLogController][ERROR] Failed to load logs: {e}")
            return []

        return raw_logs

    # -------------------------------------------------------------------
    # CLEAR LOGS
    # -------------------------------------------------------------------
    @staticmethod
    def clear_logs() -> None:
        print("[SessionLogController] clear_logs() called")
        text = TextData.get_text(SESSION_LOG_TEXT_NAME)
        if text:
            TextData.write_text(text, "", clear=True)
            print("[SessionLogController] Session logs cleared")
        else:
            print("[SessionLogController] No session log text to clear")

    @staticmethod
    def get_text_content() -> str:
        """
        Get the raw session log Text datablock content as a string.
        """
        text_block = TextData.get_text(SESSION_LOG_TEXT_NAME)
        if text_block:
            return text_block.as_string()
        return ""
