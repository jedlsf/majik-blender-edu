import bpy  # type: ignore

# --------------------------------------------------
# PROPERTIES
# --------------------------------------------------


# --------------------------------------------------
# LOCKED OBJECT ITEM (for CollectionProperty)
# --------------------------------------------------
class LockedObjectItem(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Object Name")


# Track whether we registered it
_registered = False


def register_properties():

    # Register the class if not already registered
    global _registered
    if not _registered:
        bpy.utils.register_class(LockedObjectItem)
        _registered = True

    bpy.types.Scene.user_mode = bpy.props.EnumProperty(
        name="User Mode",
        items=[("TEACHER", "Teacher", ""), ("STUDENT", "Student", "")],
        default="TEACHER",
    )

    bpy.types.Scene.teacher_key = bpy.props.StringProperty(
        name="Teacher Key", subtype="PASSWORD"
    )
    bpy.types.Scene.student_id = bpy.props.StringProperty(
        name="Student ID",
        description="Assigned student identifier",
        maxlen=100,
        default="",
    )

    bpy.types.Scene.submission_tab = bpy.props.EnumProperty(
        name="Mode",
        items=[("ENCRYPT", "Encrypt", ""), ("DECRYPT", "Decrypt", "")],
        default="ENCRYPT",
    )

    bpy.types.Scene.protect_geometry = bpy.props.BoolProperty(default=False)

    # Locked objects collection
    bpy.types.Scene.locked_objects = bpy.props.CollectionProperty(type=LockedObjectItem)
    bpy.types.Scene.locked_index = bpy.props.IntProperty(default=0)

    bpy.types.Scene.security_mode = bpy.props.EnumProperty(
        name="Security Mode",
        items=[
            ("AES", "AES (Default)", "Use AES encryption with cryptography"),
            # ("XOR", "XOR (Basic)", "Use built-in XOR obfuscation"),
        ],
        default="AES",
    )


def unregister_properties():
    global _registered

    # Delete scene props
    for prop in [
        "security_mode",
        "locked_index",
        "locked_objects",
        "protect_geometry",
        "submission_tab",
        "student_id",
        "teacher_key",
        "user_mode",
    ]:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)

    # Unregister the class only if it was registered
    if _registered:
        bpy.utils.unregister_class(LockedObjectItem)
        _registered = False
