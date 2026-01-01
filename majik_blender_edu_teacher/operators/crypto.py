import bpy  # type: ignore
import time
import hashlib

from ..core.logging import (
    load_logs_from_scene,
    save_logs_to_scene,
    create_genesis_log,
    generate_genesis_key,
    validate_genesis_log,
)


from ..core.crypto import (
    install_crypto_wheel,
    is_crypto_available,
    decrypt_metadata,
    encrypt_metadata,
)
from ..core.hash import compute_object_hash
from ..core.constants import (
    SCENE_TEACHER_DOUBLE_HASH,
    SCENE_ENCRYPTED_KEY,
    SCENE_SIGNATURE_VERSION,
    SCENE_STUDENT_ID_HASH,
    SCENE_SIGNATURE_MODE,
)

from ..core.text.session_log_controller import SessionLogController

from ..core import runtime

# --------------------------------------------------
# CRYPTO INSTALLER OPERATOR
# --------------------------------------------------


class SIGNATURE_OT_prompt_install_crypto(bpy.types.Operator):
    bl_idname = "main.prompt_install_crypto"
    bl_label = "Install Dependencies"
    bl_description = "Install cryptography for AES encryption"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        success = install_crypto_wheel(self.report)

        if success:
            self.report(
                {"INFO"},
                "Cryptography installed.",
            )
            return {"FINISHED"}

        self.report({"ERROR"}, "Cryptography installation failed. Check console.")
        return {"CANCELLED"}


# -------------------------------
# SIGNATURE_OT_encrypt (fixed)
# -------------------------------
class SIGNATURE_OT_encrypt(bpy.types.Operator):
    bl_idname = "main.encrypt"
    bl_label = "Encrypt & Apply Signature"
    bl_description = "Encrypt the submission and apply integrity signature"

    @classmethod
    def poll(cls, context):
        scene = context.scene

        logFile = SessionLogController.get_text_content()

        # Only allow encrypt if:
        # - XOR mode is selected
        # OR AES mode and cryptography is available
        return (
            bool(scene.teacher_key.strip())
            and not bool(logFile.strip())
            and bool(scene.student_id.strip())
            and (
                scene.security_mode == "XOR"
                or (scene.security_mode == "AES" and is_crypto_available())
            )
        )

    def execute(self, context):
        scene = context.scene

        if not scene.teacher_key.strip() or not scene.student_id.strip():
            self.report({"ERROR"}, "Teacher Key and Student ID are required")
            return {"CANCELLED"}

        timestamp = int(time.time())

        # Determine objects to protect
        if scene.protect_geometry:
            objects = [
                bpy.data.objects[item.name]
                for item in scene.locked_objects
                if item.name in bpy.data.objects
                and bpy.data.objects[item.name].type == "MESH"
            ]
        else:
            # Geometry protection disabled → do NOT hash meshes
            objects = []

        object_hashes = {
            o.name: compute_object_hash(o) for o in objects if compute_object_hash(o)
        }

        metadata = {
            "student_id": scene.student_id,
            "timestamp": timestamp,
            "object_hashes": object_hashes,
            "locked_objects": list(object_hashes.keys()),
        }

        hashed_student_id = hashlib.sha256(scene.student_id.encode()).hexdigest()
        scene[SCENE_STUDENT_ID_HASH] = hashed_student_id

        if scene.security_mode == "XOR":
            encryption_key = scene.teacher_key
        else:
            encryption_key = hashlib.sha256(scene.teacher_key.encode()).hexdigest()

        # Use the unified encrypt_metadata
        encrypted_metadata = encrypt_metadata(
            metadata,
            key=encryption_key,
            salt_bytes=hashed_student_id.encode("utf-8"),
            mode=scene.security_mode,
        )

        scene[SCENE_ENCRYPTED_KEY] = encrypted_metadata
        scene[SCENE_SIGNATURE_VERSION] = 1
        double_hash = hashlib.sha256(encryption_key.encode()).hexdigest()
        scene[SCENE_TEACHER_DOUBLE_HASH] = double_hash

        genesis_key = generate_genesis_key(scene.teacher_key, scene.student_id)
        create_genesis_log(scene, genesis_key)
        save_logs_to_scene(scene)

        scene.teacher_key = ""
        scene[SCENE_SIGNATURE_MODE] = scene.security_mode

        self.report(
            {"INFO"},
            f"Project encrypted ({scene.security_mode}), signature applied, logs initialized",
        )
        return {"FINISHED"}


# -------------------------------
# SIGNATURE_OT_decrypt (fixed)
# -------------------------------
class SIGNATURE_OT_decrypt(bpy.types.Operator):
    bl_idname = "main.decrypt"
    bl_label = "Decrypt & Validate"
    bl_description = "Decrypt the submission and validate integrity"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        mode = scene.get(SCENE_SIGNATURE_MODE, "XOR")

        return (
            bool(scene.teacher_key.strip())
            and SCENE_ENCRYPTED_KEY in scene
            and (mode == "XOR" or (mode == "AES" and is_crypto_available()))
        )

    def execute(self, context):
        scene = context.scene

        if SCENE_ENCRYPTED_KEY not in scene:
            self.report({"ERROR"}, "No encrypted submission found")
            return {"CANCELLED"}

        mode = scene.get(SCENE_SIGNATURE_MODE, "XOR")
        decryption_key = hashlib.sha256(scene.teacher_key.encode()).hexdigest()

        if mode == "XOR":
            decryption_key = scene.teacher_key
        else:
            decryption_key = hashlib.sha256(scene.teacher_key.encode()).hexdigest()

        salt_bytes = scene[SCENE_STUDENT_ID_HASH].encode("utf-8")

        try:
            metadata = decrypt_metadata(
                encrypted_metadata=scene[SCENE_ENCRYPTED_KEY],
                key=decryption_key,
                salt_bytes=salt_bytes,
                mode=mode,
            )
        except Exception:
            self.report({"ERROR"}, "Invalid Teacher Key or decryption failed")
            return {"CANCELLED"}

        runtime._runtime_metadata = metadata

        locked = set(metadata.get("locked_objects", []))

        # Verify hashes
        tampered = any(
            name not in bpy.data.objects
            or compute_object_hash(bpy.data.objects[name]) != stored_hash
            for name, stored_hash in metadata["object_hashes"].items()
            if name in locked
        )

        runtime._is_tampered = tampered

        # Decrypt logs
        load_logs_from_scene(scene)
        genesis_log_is_valid = validate_genesis_log(
            scene, teacher_key=scene.teacher_key, student_id=scene.student_id
        )

        log_status_message = "VALID" if genesis_log_is_valid else "INVALID (Tampered)"
        status = "VALID – Untampered" if not tampered else "TAMPERED"
        self.report(
            {"INFO"},
            f"{status} | Log Chain: {log_status_message} | Student: {metadata['student_id']}",
        )
        return {"FINISHED"}


# --------------------------------------------------
# RESET OPERATOR (NEW)
# --------------------------------------------------


class SIGNATURE_OT_reset_submission(bpy.types.Operator):
    bl_idname = "main.reset_submission"
    bl_label = "Reset Key"
    bl_description = "Completely remove encryption and logs"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):

        scene = context.scene

        scene.pop(SCENE_ENCRYPTED_KEY, None)
        scene.pop(SCENE_SIGNATURE_VERSION, None)
        scene.pop(SCENE_STUDENT_ID_HASH, None)
        scene.pop(SCENE_TEACHER_DOUBLE_HASH, None)
        scene.pop(SCENE_SIGNATURE_MODE, None)
        SessionLogController.clear_logs()
        runtime._runtime_metadata = None
        runtime.clear_runtime()

        scene.locked_objects.clear()
        scene.locked_index = 0

        scene.teacher_key = ""

        self.report({"INFO"}, "Submission reset successfully")
        return {"FINISHED"}
