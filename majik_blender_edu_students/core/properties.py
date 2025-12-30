import bpy  # type: ignore


# --------------------------------------------------
# PROPERTIES
# --------------------------------------------------


def register_properties():
    bpy.types.Scene.student_id = bpy.props.StringProperty(
        name="Student ID",
        description="Assigned student identifier",
        maxlen=100,
        default="",
    )


def unregister_properties():
    if hasattr(bpy.types.Scene, "student_id"):
        del bpy.types.Scene.student_id

