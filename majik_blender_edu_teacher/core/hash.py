
import bpy  # type: ignore
from datetime import datetime
import json
import hashlib


def timestamp_to_readable(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%B %d, %Y | %I:%M %p")


def compute_object_hash(obj: bpy.types.Object) -> str | None:
    if obj.type != "MESH":
        return None

    mesh = obj.data
    payload = json.dumps(
        {
            "vertices": [tuple(v.co) for v in mesh.vertices],
            "edges": [tuple(e.vertices) for e in mesh.edges],
            "polygons": [tuple(p.vertices) for p in mesh.polygons],
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


