


import bpy # type: ignore
from bpy.types import Text # type: ignore
from typing import Optional


class TextData:
    """
    Utility helpers for bpy.data.texts (BlendDataTexts).
    """

    # ---------------------------------------------------------------------
    # CREATE NEW TEXT
    # ---------------------------------------------------------------------
    @staticmethod
    def create_text(name: str) -> Text:
        print("[TextData] create_text() called")
        print(f"[TextData] Requested name: {name}")

        if not name or not isinstance(name, str):
            raise ValueError("Text name must be a non-empty string")

        if name in bpy.data.texts:
            raise ValueError(f"Text '{name}' already exists")

        print("[TextData] Creating new text datablock...")
        text = bpy.data.texts.new(name=name)

        print(f"[TextData] Text created: {text.name}")
        print("[TextData] Text is internal and will be saved with the .blend")

        return text

    # ---------------------------------------------------------------------
    # LOAD TEXT FROM FILE
    # ---------------------------------------------------------------------
    @staticmethod
    def load_text(
        filepath: str,
        *,
        internal: bool = True
    ) -> Text:
        print("[TextData] load_text() called")
        print(f"[TextData] Filepath: {filepath}")
        print(f"[TextData] Internal: {internal}")

        if not filepath or not isinstance(filepath, str):
            raise ValueError("Filepath must be a valid string")

        print("[TextData] Loading text from file...")
        text = bpy.data.texts.load(filepath, internal=internal)

        print(f"[TextData] Text loaded: {text.name}")

        if internal:
            print("[TextData] Text embedded in .blend (WILL be saved)")
        else:
            print("[TextData] Text linked externally (path reference only)")

        return text

    # ---------------------------------------------------------------------
    # REMOVE TEXT
    # ---------------------------------------------------------------------
    @staticmethod
    def remove_text(
        text: Text,
        *,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True
    ) -> None:
        print("[TextData] remove_text() called")

        if not isinstance(text, Text):
            raise TypeError("Expected bpy.types.Text")

        print(f"[TextData] Removing text: {text.name}")
        print(f"[TextData] do_unlink={do_unlink}")
        print(f"[TextData] do_id_user={do_id_user}")
        print(f"[TextData] do_ui_user={do_ui_user}")

        bpy.data.texts.remove(
            text,
            do_unlink=do_unlink,
            do_id_user=do_id_user,
            do_ui_user=do_ui_user,
        )

        print("[TextData] Text removed successfully")

    # ---------------------------------------------------------------------
    # GET TEXT BY NAME
    # ---------------------------------------------------------------------
    @staticmethod
    def get_text(name: str) -> Optional[Text]:
        print("[TextData] get_text() called")
        print(f"[TextData] Name: {name}")

        text = bpy.data.texts.get(name)

        if text:
            print(f"[TextData] Text found: {text.name}")
        else:
            print("[TextData] Text not found")

        return text

    # ---------------------------------------------------------------------
    # WRITE CONTENT TO TEXT
    # ---------------------------------------------------------------------
    @staticmethod
    def write_text(text: Text, content: str, *, clear: bool = True) -> None:
        print("[TextData] write_text() called")

        if not isinstance(text, Text):
            raise TypeError("Expected bpy.types.Text")

        if not isinstance(content, str):
            raise TypeError("Content must be a string")

        print(f"[TextData] Writing to text: {text.name}")
        print(f"[TextData] Clear first: {clear}")

        if clear:
            print("[TextData] Clearing existing content...")
            text.clear()

        print("[TextData] Writing content...")
        text.write(content)

        print("[TextData] Write completed")

    # ---------------------------------------------------------------------
    # READ CONTENT FROM TEXT
    # ---------------------------------------------------------------------
    @staticmethod
    def read_text(text: Text) -> str:
        print("[TextData] read_text() called")

        if not isinstance(text, Text):
            raise TypeError("Expected bpy.types.Text")

        print(f"[TextData] Reading from text: {text.name}")

        content = text.as_string()

        print("[TextData] Read completed")
        print(f"[TextData] Character count: {len(content)}")

        return content

    # ---------------------------------------------------------------------
    # ENSURE TEXT EXISTS (CREATE IF MISSING)
    # ---------------------------------------------------------------------
    @staticmethod
    def ensure_text(name: str) -> Text:
        print("[TextData] ensure_text() called")
        print(f"[TextData] Name: {name}")

        text = bpy.data.texts.get(name)

        if text:
            print("[TextData] Text already exists")
            return text

        print("[TextData] Text does not exist, creating...")
        return TextData.create_text(name)
