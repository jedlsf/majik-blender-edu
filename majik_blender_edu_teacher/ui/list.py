import bpy  # type: ignore


# --------------------------------------------------
# UI LIST
# --------------------------------------------------


class LOCKED_OBJECTS_UL_list(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=item.name, icon="MESH_CUBE")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="")
