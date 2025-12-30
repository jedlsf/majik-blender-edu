import bpy  # type: ignore

from .crypto import is_crypto_available

# --------------------------------------------------
# PROPERTIES
# --------------------------------------------------


def register_properties():
    bpy.types.Scene.teacher_key = bpy.props.StringProperty(
        name="Teacher Key", subtype="PASSWORD"
    )
    bpy.types.Scene.student_id = bpy.props.StringProperty(name="Student ID")
    bpy.types.Scene.submission_tab = bpy.props.EnumProperty(
        name="Mode",
        items=[("ENCRYPT", "Encrypt", ""), ("DECRYPT", "Decrypt", "")],
        default="ENCRYPT",
    )

    bpy.types.Scene.protect_geometry = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.locked_objects = bpy.props.CollectionProperty(
        type=bpy.types.PropertyGroup
    )
    bpy.types.Scene.locked_index = bpy.props.IntProperty(default=0)

    # <-- Set default based on crypto availability
    # default_mode = "AES" if is_crypto_available() else "XOR"
    bpy.types.Scene.security_mode = bpy.props.EnumProperty(
        name="Security Mode",
        items=[
            ("AES", "AES (Default)", "Use AES encryption with cryptography"),
            # ("XOR", "XOR (Basic)", "Use built-in XOR obfuscation"),
        ],
        default="AES",
    )


def unregister_properties():
    del bpy.types.Scene.teacher_key
    del bpy.types.Scene.student_id
    del bpy.types.Scene.submission_tab
    del bpy.types.Scene.protect_geometry
    del bpy.types.Scene.locked_objects
    del bpy.types.Scene.locked_index
    del bpy.types.Scene.security_mode
