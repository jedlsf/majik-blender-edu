import re
import time
import bpy  # type: ignore
from typing import Dict, TypedDict


class SceneStats(TypedDict):
    v: int  # Vertex Count
    f: int  # Face Count
    o: int  # Object Count


class SceneStatsManager:
    def __init__(self, scene=None):
        self._last_scene_stats: SceneStats = {"v": 0, "f": 0, "o": 0}
        self._last_stats_time: float = 0.0
        if scene:
            self._initialize_total_stats(scene)

    @staticmethod
    def is_edit_mode(stats_str: str) -> bool:
        """
        Returns True if the scene stats indicate a single object in edit mode.
        In edit mode, only one item appears before 'Verts'.
        """
        # Split by '|', trim spaces
        parts = [p.strip() for p in stats_str.split("|")]
        # Edit mode has only one item before the Verts/Faces info
        return len(parts) == 2  # Example: 'Cube | Verts:12/12'

    @staticmethod
    def is_armature_edit_mode(stats_str: str) -> bool:
        """
        Returns True if the scene stats indicate armature edit mode.
        Detects if 'Bones' keyword is present.
        """
        return "Bones" in stats_str

    @staticmethod
    def extract_denominator(stats_str: str, pattern: str) -> int:
        """
        Extracts denominator if format is 'num/den', else returns the number itself.
        """
        match = re.search(pattern, stats_str)
        if not match:
            return 0
        val = match.group(1).replace(",", "")
        if "/" in val:
            return int(val.split("/")[1])
        return int(val)

    def get_scene_stats(self, scene) -> SceneStats:
        """
        Returns a dictionary of scene stats: {'v': verts, 'f': faces, 'o': objects}.
        Uses cached stats if in edit mode or armature edit mode.
        """
        now = time.time()
        # Use cached stats if last update was less than 1 second ago
        if now - self._last_stats_time < 1.0:
            return self._last_scene_stats

        stats_str = scene.statistics(bpy.context.view_layer)

        # Check if we are in edit or armature edit mode
        if self.is_edit_mode(stats_str) or self.is_armature_edit_mode(stats_str):
            # Always return last stats in edit/armature mode
            return self._last_scene_stats

        # Otherwise, update stats
        verts = self.extract_denominator(stats_str, r"Verts:([\d/,]+)")
        faces = self.extract_denominator(stats_str, r"Faces:([\d/,]+)")
        objects = self.extract_denominator(stats_str, r"Objects:([\d/,]+)")

        self._last_scene_stats = {"v": verts, "f": faces, "o": objects}
        self._last_stats_time = now

        return self._last_scene_stats

    def _initialize_total_stats(self, scene):
        """
        Computes total vertices, faces, and objects including evaluated meshes.
        """
        now = time.time()
        depsgraph = bpy.context.evaluated_depsgraph_get()

        total_verts = 0
        total_faces = 0
        total_objects = 0

        for obj in scene.objects:
            if obj.type != "MESH":
                continue

            eval_obj = obj.evaluated_get(depsgraph)
            eval_mesh = eval_obj.to_mesh(
                preserve_all_data_layers=False, depsgraph=depsgraph
            )

            if eval_mesh:
                total_verts += len(eval_mesh.vertices)
                total_faces += len(eval_mesh.polygons)
                total_objects += 1
                eval_obj.to_mesh_clear()

        stats = {"v": total_verts, "f": total_faces, "o": total_objects}

        self._last_scene_stats = stats
        self._last_stats_time = now
