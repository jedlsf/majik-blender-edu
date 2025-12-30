
import bpy # type: ignore


# --------------------------------------------------
# LOCKED OBJECTS OPERATORS
# --------------------------------------------------


class LOCKED_OBJECTS_OT_add(bpy.types.Operator):
    bl_idname = "locked_objects.add"
    bl_label = "Add Selected Object"
    bl_description = "Add currently selected mesh objects to the locked objects list"

    def execute(self, context):
        scene = context.scene
        selected_objs = [o for o in context.selected_objects if o.type == "MESH"]

        for obj in selected_objs:
            if not any(item.name == obj.name for item in scene.locked_objects):
                item = scene.locked_objects.add()
                item.name = obj.name

        return {"FINISHED"}


class LOCKED_OBJECTS_OT_remove(bpy.types.Operator):
    bl_idname = "locked_objects.remove"
    bl_label = "Remove Selected"
    bl_description = "Remove the selected object from the locked objects list"

    def execute(self, context):
        scene = context.scene
        idx = scene.locked_index
        if 0 <= idx < len(scene.locked_objects):
            scene.locked_objects.remove(idx)
            scene.locked_index = max(0, idx - 1)
        return {"FINISHED"}


class LOCKED_OBJECTS_OT_clear(bpy.types.Operator):
    bl_idname = "locked_objects.clear"
    bl_label = "Clear List"
    bl_description = "Remove all objects from the locked objects list"

    def execute(self, context):
        scene = context.scene
        scene.locked_objects.clear()
        scene.locked_index = 0
        return {"FINISHED"}
