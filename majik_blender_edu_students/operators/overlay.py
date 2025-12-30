import bpy  # type: ignore
import gpu  # type: ignore
from gpu_extras.batch import batch_for_shader  # type: ignore

from ..core import runtime

# Use the shader name confirmed by your Blender 5.0 error log
SHADER_NAME = "POLYLINE_UNIFORM_COLOR"
shader = gpu.shader.from_builtin(SHADER_NAME)
_handler = None

_cached_batch = None
_last_size = (0, 0)

def draw_indicator_callback():

   # Only draw if your addon's logic says the session is active
    if runtime._timer_start is None:
        return

    global _cached_batch, _last_size
    region = bpy.context.region
    w, h = float(region.width), float(region.height)

    # 2. Update geometry only if viewport size changes
    if _cached_batch is None or _last_size != (w, h):
        padding = 35.0
        # vec3 pos as per your documentation (x, y, 0)
        vertices = [
            (padding, padding, 0),
            (w - padding, padding, 0),
            (w - padding, h - padding, 0),
            (padding, h - padding, 0),
        ]
        _cached_batch = batch_for_shader(shader, "LINE_LOOP", {"pos": vertices})
        _last_size = (w, h)

    # 3. Setup GPU state
    gpu.state.blend_set("ALPHA")
    
    # 4. Bind shader and set uniforms (using your build's uniform_float)
    shader.bind()
    shader.uniform_float("viewportSize", (w, h))
    shader.uniform_float("lineWidth", 4.0)
    shader.uniform_float("color", (0.93, 0.2, 0.0, 1.0)) # Red

    # 5. Handle the Matrix (The Blender 5.0 Built-in way)
    # Since we are in POST_PIXEL, Blender has already loaded a 
    # projection matrix that matches the pixel dimensions of the region.
    # We just need to make sure the ModelView matrix is identity.
    gpu.matrix.push()
    gpu.matrix.load_identity()
    
    _cached_batch.draw(shader)
    
    gpu.matrix.pop()

    # 6. Cleanup
    gpu.state.blend_set("NONE")

def register_overlay():
    global _handler
    if _handler is not None: return
    _handler = bpy.types.SpaceView3D.draw_handler_add(
        draw_indicator_callback, (), "WINDOW", "POST_PIXEL"
    )
    tag_redraw_viewports()

def unregister_overlay():
    global _handler, _cached_batch
    if _handler:
        bpy.types.SpaceView3D.draw_handler_remove(_handler, "WINDOW")
        _handler = None
        _cached_batch = None
    tag_redraw_viewports()

def tag_redraw_viewports():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()