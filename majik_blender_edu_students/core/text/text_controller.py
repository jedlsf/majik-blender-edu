import json
import bpy  # type: ignore
from typing import Dict, Any, Optional

from .text_data import TextData
from .text_schemas import GenesisSchema


GENESIS_TEXT_NAME = "__MAJIK_GENESIS__"


class GenesisController:
    """
    Controller responsible for managing the Genesis text datablock.

    This is the ONLY place where the Genesis schema may be:
    - created
    - written
    - validated
    """

    # ------------------------------------------------------------------
    # ENSURE GENESIS EXISTS
    # ------------------------------------------------------------------
    @staticmethod
    def ensure_genesis(
        *,
        addon_version: Optional[str] = None,
        blender_version: Optional[str] = None,
        force_recreate: bool = False,
    ):
        print("[GenesisController] ensure_genesis() called")
        print(f"[GenesisController] force_recreate={force_recreate}")

        text = TextData.get_text(GENESIS_TEXT_NAME)

        if text and not force_recreate:
            print("[GenesisController] Genesis text already exists")
            return text

        if text and force_recreate:
            print("[GenesisController] Removing existing Genesis text")
            TextData.remove_text(text)

        print("[GenesisController] Creating new Genesis schema")
        data = GenesisSchema.create()

        print("[GenesisController] Populating runtime fields")
        data["created_at"] = bpy.app.timers.time()
        data["addon_version"] = addon_version
        data["blender_version"] = blender_version or bpy.app.version_string

        print("[GenesisController] Serializing Genesis schema")
        serialized = GenesisSchema.serialize(data)

        print("[GenesisController] Creating Genesis text datablock")
        text = TextData.create_text(GENESIS_TEXT_NAME)

        print("[GenesisController] Writing Genesis content")
        TextData.write_text(text, serialized, clear=True)

        print("[GenesisController] Genesis text created successfully")
        return text

    # ------------------------------------------------------------------
    # READ GENESIS
    # ------------------------------------------------------------------
    @staticmethod
    def read_genesis() -> Dict[str, Any]:
        print("[GenesisController] read_genesis() called")

        text = TextData.get_text(GENESIS_TEXT_NAME)

        if not text:
            raise RuntimeError("Genesis text does not exist")

        print("[GenesisController] Reading Genesis content")
        raw = TextData.read_text(text)

        try:
            data = json.loads(raw)
        except Exception as e:
            print("[GenesisController][ERROR] Invalid JSON")
            raise RuntimeError("Genesis text contains invalid JSON") from e

        print("[GenesisController] Genesis JSON parsed successfully")
        return data

    # ------------------------------------------------------------------
    # VALIDATE GENESIS
    # ------------------------------------------------------------------
    @staticmethod
    def validate_genesis() -> bool:
        print("[GenesisController] validate_genesis() called")

        try:
            data = GenesisController.read_genesis()
        except Exception as e:
            print(f"[GenesisController][ERROR] {e}")
            return False

        print("[GenesisController] Validating Genesis schema")
        valid = GenesisSchema.validate(data)

        print(f"[GenesisController] Validation result: {valid}")
        return valid

    # ------------------------------------------------------------------
    # GET OR CREATE (SAFE ENTRY POINT)
    # ------------------------------------------------------------------
    @staticmethod
    def get_or_create_genesis(
        *,
        addon_version: Optional[str] = None,
        blender_version: Optional[str] = None,
    ):
        print("[GenesisController] get_or_create_genesis() called")

        if GenesisController.validate_genesis():
            print("[GenesisController] Existing Genesis is valid")
            return TextData.get_text(GENESIS_TEXT_NAME)

        print("[GenesisController] Genesis missing or invalid, recreating")
        return GenesisController.ensure_genesis(
            addon_version=addon_version,
            blender_version=blender_version,
            force_recreate=True,
        )
