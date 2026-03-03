\# LorQB - Lord of the Quantum Balls

\*\*Blender Version:\*\* 5.0.1  

\*\*Original Design:\*\* Jose R. Velazquez © 2014  

\*\*Developer:\*\* Carlos  

\*\*AI System:\*\* Rukmini Trio (Claude + ChatGPT + NotebookLM)



\## Project Structure

scripts/

&nbsp; construction/   -> Scene building scripts (stable, do not modify)

&nbsp; animation/      -> Per-sequence animation scripts (C12, C15, etc.)

&nbsp; diagnostic/     -> Debugging and state-check scripts

docs/

&nbsp; validation\_reports/  -> NotebookLM + ChatGPT verification outputs

&nbsp; sequence\_logs/       -> Per-sequence progress notes



\## Cube Chain Topology

Yellow — Green — Red — Blue (snake chain, hinged on top)



\## Level 1 Status

\- Goal: complete all sequences for Level 1 with modular, reorderable scripts.

\- Current focus: C15 (Yellow -> Blue).



\## Key Design Notes

\- Ball starts outside the cubes at the beginning of each turn.

\- Current dev order: Blue -> Red -> Green -> Yellow (temporary).

\- Future: shuffle can select any cube order; scripts must support any permutation.



\## Key Rules

\- Script-only operations (no manual Blender UI)

\- Commit after every confirmed working step



\## Python Scripts

| Script | Description |
|--------|-------------|
| C10\_scene\_build.py | Builds the initial LorQB scene: clears all objects, then creates four hollow colored cubes (Blue, Red, Green, Yellow) with circular holes, a ball inside Cube\_Blue, and three hinge pivot empties. |
| C12\_blue\_to\_red.py | Animates the Blue→Red sequence (frames 1–240): parents Cube\_Blue to Hinge\_Blue\_Red, rotates it 180° on the X-axis, and transfers the ball from Cube\_Blue to Cube\_Red at frame 120→121 using COPY\_TRANSFORMS constraints. |
| C13\_red\_to\_green.py | Animates the Red→Green sequence (frames 241–480): parents Cube\_Red to Hinge\_Red\_Green, rotates it 180° on the Y-axis, and transfers the ball from Cube\_Red to Cube\_Green at frame 360→361. |
| C14\_green\_to\_yellow.py | Animates the Green→Yellow sequence (frames 481–720): parents Cube\_Green to Hinge\_Green\_Yellow, rotates it 180° on the X-axis, and transfers the ball from Cube\_Green to Cube\_Yellow at frame 600→601. |
| C15\_yellow\_to\_blue.py | Keys Hinge\_Red\_Green with a 0°→180°→0° Y-axis rotation using CONSTANT interpolation for the Yellow→Blue transfer; currently implements the hinge-rotation block only. |
| lorQB\_Master\_Runnet | Python script (no .py extension) that registers a Blender N-panel ("LorQB Sequences") with operator buttons to run each animation sequence (C12–C15) individually. |



\## C15\_yellow\_to\_blue.py — Full Source

```python
# ============================================================================
# 5lorqb_yellow_to_blue_C15.py  (Blender 5.0.1)
# ----------------------------------------------------------------------------
# LorQB Level 1 — Sequence C15 (Yellow -> Blue)
# Hinge: Hinge_Red_Green
# Axis: Y
#
# This script matches the *structure* of your C12/C13/C14 scripts:
# - Creates a LorQB UI tab + button
# - Runs a single operator that builds the C15 hinge rotation keys
# - Forces CONSTANT interpolation via Blender 5 Action API
#
# NOTE: This is the **C15 hinge-rotation block only** (the same way C12 started).
# Ball/seat/latch transfer block gets added after the hinge snaps correctly.
# ============================================================================

import bpy
import math

# ----------------------------------------------------------------------------
# UI / IDs
# ----------------------------------------------------------------------------
ADDON_NAME   = "LorQB"
TAB_NAME     = "LorQB"
PANEL_LABEL  = "LorQB Animation"
PANEL_ID     = "LORQB_PT_animation_panel"
OP_ID        = "lorqb.c15_yellow_to_blue"
OP_LABEL     = "Run C15: Yellow -> Blue (Hinge_Red_Green)"

# ----------------------------------------------------------------------------
# REQUIRED OBJECT NAMES (MATCH YOUR FILE)
# ----------------------------------------------------------------------------
REQ = [
    "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
    "Ball",
    "Hinge_Red_Green", "Hinge_Green_Yellow", "Hinge_Blue_Red",
]

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def require_objects():
    missing = [n for n in REQ if bpy.data.objects.get(n) is None]
    if missing:
        raise RuntimeError("Missing objects: " + ", ".join(missing))

def clear_object_animation(obj: bpy.types.Object):
    if obj.animation_data:
        obj.animation_data_clear()

def force_constant_rotation_euler(obj: bpy.types.Object):
    """
    Blender 5.0.1 in your build:
    - Action has NO .fcurves
    - Use action.fcurve_ensure_for_datablock(..., index=)
    """
    ad = obj.animation_data
    if not ad or not ad.action:
        raise RuntimeError(f"No action found on {obj.name} after inserting keys.")

    act = ad.action

    # rotation_euler has 3 components: X=0, Y=1, Z=2
    for i in (0, 1, 2):
        fc = act.fcurve_ensure_for_datablock(obj, "rotation_euler", index=i)
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"

def key_hinge_red_green_C15():
    require_objects()

    hinge = bpy.data.objects["Hinge_Red_Green"]
    scene = bpy.context.scene

    # wipe prior animation so we don't "stack" rotations
    clear_object_animation(hinge)

    hinge.rotation_mode = "XYZ"

    # f1 = 0
    scene.frame_set(1)
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # f120 = 180 on Y
    scene.frame_set(120)
    hinge.rotation_euler = (0.0, math.radians(180.0), 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # f240 = 0
    scene.frame_set(240)
    hinge.rotation_euler = (0.0, 0.0, 0.0)
    hinge.keyframe_insert(data_path="rotation_euler")

    # force snap
    force_constant_rotation_euler(hinge)

    print("C15 OK: Hinge_Red_Green keyed (Y: 0 -> 180 -> 0) with CONSTANT interpolation.")

# ----------------------------------------------------------------------------
# OPERATOR + PANEL (THIS IS WHY YOU DIDN'T SEE A LorQB TAB BEFORE)
# ----------------------------------------------------------------------------
class LORQB_OT_c15_yellow_to_blue(bpy.types.Operator):
    bl_idname = OP_ID
    bl_label = OP_LABEL

    def execute(self, context):
        key_hinge_red_green_C15()
        return {'FINISHED'}

class LORQB_PT_animation_panel(bpy.types.Panel):
    bl_label = PANEL_LABEL
    bl_idname = PANEL_ID
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = TAB_NAME

    def draw(self, context):
        layout = self.layout
        layout.operator(OP_ID, text=OP_LABEL)

# ----------------------------------------------------------------------------
# REGISTER
# ----------------------------------------------------------------------------
classes = (
    LORQB_OT_c15_yellow_to_blue,
    LORQB_PT_animation_panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
```

