import json
from typing import Dict, Any


class GenesisSchema:
    @staticmethod
    def create() -> Dict[str, Any]:
        return {
            "schema_version": "1.0",
            "type": "GENESIS",
            "created_at": None,
            "addon_version": None,
            "blender_version": None,
        }

    @staticmethod
    def serialize(data: Dict[str, Any]) -> str:
        return json.dumps(data, indent=2, sort_keys=True)

    @staticmethod
    def validate(data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False

        required_keys = {
            "schema_version",
            "type",
            "created_at",
            "addon_version",
            "blender_version",
        }

        if set(data.keys()) != required_keys:
            return False

        if data.get("type") != "GENESIS":
            return False

        return True
