# ============================================================================
# T01_blue_to_green.py  (Blender 5.1.0)
# T1 — Blue → Green (diagonal)
#
# Ball path:
#   Frame   1:       Ball at Blue bottom (Seat_Blue_Start = ball world pos, no jump)
#   Frame   1– 80:  Stage 1 — Hinge_Blue_Red rotates 0°→180° (Blue flips over Red)
#   Frame  81–160:  Stage 2 — Hinge_Red_Green rotates 0°→90°  (Blue+Red over Green)
#   Frame 161:       Ball transfers from Seat_Blue_Start to Seat_Green
#   Frame 162–200:  Stage 3 — Hinge_Red_Green returns 90°→0° FIRST
#   Frame 201–240:  Stage 4 — Hinge_Blue_Red returns 180°→0° SECOND
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START        = 1
F_S1_END       = 80    # Hinge_Blue_Red reaches 180° — Blue fully flipped over Red
F_S2_END       = 160   # Hinge_Red_Green reaches 90° — Blue+Red over Green
F_SWAP         = 161   # Ball transfers from Seat_Blue_Start to Seat_Green
F_RET1_END     = 200   # Hinge_Red_Green returns 90°→0° FIRST
F_RET2_END     = 240   # Hinge_Blue_Red returns 180°→0° SECOND
F_END          = 240

ROT_SIGN_1     = +1.0  # TODO: Hinge_Blue_Red  — verify direction in Blender
ROT_SIGN_2     = +1.0  # Hinge_Red_Green — positive direction swings Red+Blue over Green

# Green bottom interior center
SEAT_GREEN_WORLD = mathutils.Vector((-0.51, -0.51, 0.25))

# Seat_Blue_Start is NOT hardcoded — built from ball.matrix_world at runtime
# This prevents the jump-on-arm.

###############################################################################
# SECTION 2: Full Scene Reset
###############################################################################

def reset_scene_to_canonical():
    if bpy.app.driver_namespace.get("lorqb_run_all", False):
        print("=== T1 Reset skipped (Run ALL mode) ===")
        return

    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
        "Seat_Blue_Start",
        "Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow",
    ]
    for name in all_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    for hinge_name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
        hinge = bpy.data.objects.get(hinge_name)
        if hinge:
            hinge.rotation_mode = 'XYZ'
            hinge.rotation_euler = (0.0, 0.0, 0.0)

    for seat_name in ["Seat_Blue_Start",
                      "Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    bpy.context.view_layer.update()
    print("=== Scene reset to canonical state ===")

###############################################################################
# SECTION 3: Helpers
###############################################################################

def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    try:
        fcurves = action.layers[0].strips[0].channelbags[0].fcurves
    except Exception:
        return
    for fc in fcurves:
        if fc.data_path == data_path or data_path in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp

def key_rot(obj, axis, sign, frame, degrees, interp='LINEAR'):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[axis] = sign * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=frame)
    set_last_keyframe_interpolation(obj, "rotation_euler", frame, interp)

def key_influence(obj, constraint_name, frame, value):
    bpy.context.scene.frame_set(frame)
    con = obj.constraints.get(constraint_name)
    if not con:
        print(f"WARNING: Constraint '{constraint_name}' not found on {obj.name}")
        return
    con.influence = value
    data_path = f'constraints["{constraint_name}"].influence'
    obj.keyframe_insert(data_path=data_path, frame=frame)
    set_last_keyframe_interpolation(obj, data_path, frame, 'CONSTANT')

def parent_preserve_world(child, new_parent):
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

###############################################################################
# SECTION 4: Main T1 Animation Logic
###############################################################################

def run_animation():
    print("=== T1 Start: Blue → Green ===")

    reset_scene_to_canonical()

    blue    = bpy.data.objects.get("Cube_Blue")
    red     = bpy.data.objects.get("Cube_Red")
    green   = bpy.data.objects.get("Cube_Green")
    ball    = bpy.data.objects.get("Ball")
    hinge_br = bpy.data.objects.get("Hinge_Blue_Red")
    hinge_rg = bpy.data.objects.get("Hinge_Red_Green")

    missing = [n for n, o in [
        ("Cube_Blue",       blue),
        ("Cube_Red",        red),
        ("Cube_Green",      green),
        ("Ball",            ball),
        ("Hinge_Blue_Red",  hinge_br),
        ("Hinge_Red_Green", hinge_rg),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge_br.rotation_euler = (0, 0, 0)
    hinge_rg.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # ── Hierarchy ──────────────────────────────────────────────────────────
    # Blue → Hinge_Blue_Red → Red → Hinge_Red_Green
    # Green has NO parent — stays fixed (destination cube)
    parent_preserve_world(blue,     hinge_br)
    parent_preserve_world(hinge_br, red)
    parent_preserve_world(red,      hinge_rg)
    print("Hierarchy set: Blue→HBR→Red→HRG  (Green unparented)")

    # ── Remove rigid body from ball ────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    bpy.context.view_layer.update()

    # ── Move ball to Blue's bottom interior center ────────────────────────
    # Ball starts inside Blue by default (C10_scene_build). Ensure position.
    ball.location = mathutils.Vector((0.51, 0.51, 0.25))
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()
    print("Ball positioned at Blue bottom interior center (0.51, 0.51, 0.25).")

    # ── Seat_Blue_Start ───────────────────────────────────────────────────
    # Built from ball's ACTUAL world position — no jump on arm.
    # Ball rides this seat through Stage 1 and Stage 2, then transfers
    # directly to Seat_Green at F_SWAP.
    ball_world        = ball.matrix_world.translation.copy()
    seat_start_local  = blue.matrix_world.inverted() @ ball_world
    seat_blue_start   = bpy.data.objects.new("Seat_Blue_Start", None)
    seat_blue_start.empty_display_type = 'SPHERE'
    seat_blue_start.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_blue_start)
    seat_blue_start.parent   = blue
    seat_blue_start.location = seat_start_local
    print(f"Seat_Blue_Start at ball world pos {ball_world} (no jump).")

    # ── Seat_Green ────────────────────────────────────────────────────────
    # Bottom interior center of Green. Ball lands here at F_SWAP.
    seat_green_local  = green.matrix_world.inverted() @ SEAT_GREEN_WORLD
    seat_green        = bpy.data.objects.new("Seat_Green", None)
    seat_green.empty_display_type = 'SPHERE'
    seat_green.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_green)
    seat_green.parent   = green
    seat_green.location = seat_green_local
    print(f"Seat_Green at world {SEAT_GREEN_WORLD} (bottom center of Green).")

    bpy.context.view_layer.update()

    # ── Constraints ────────────────────────────────────────────────────────
    latch_start = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_start.name   = "Latch_Blue_Start"
    latch_start.target = seat_blue_start

    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name   = "Latch_Green"
    latch_green.target = seat_green
    print("Latch_Blue_Start and Latch_Green created.")

    # ── Hinge keyframes ────────────────────────────────────────────────────

    # Hinge_Blue_Red (X-axis):
    #   Stage 1:  0°→180°  (frames  1– 80) — Blue flips over Red
    #   Hold:    180°       (frames 80–200) — waits for HRG to retract
    #   Stage 4: 180°→0°   (frames 201–240)
    key_rot(hinge_br, 0, ROT_SIGN_1, F_START,      0)
    key_rot(hinge_br, 0, ROT_SIGN_1, F_S1_END,   180)
    key_rot(hinge_br, 0, ROT_SIGN_1, F_S2_END,   180)
    key_rot(hinge_br, 0, ROT_SIGN_1, F_SWAP,     180)
    key_rot(hinge_br, 0, ROT_SIGN_1, F_RET1_END, 180)
    key_rot(hinge_br, 0, ROT_SIGN_1, F_RET2_END,   0)

    # Hinge_Red_Green (Y-axis):
    #   Stage 2:  0°→90°   (frames  81–160) — Blue+Red swings over Green
    #   Hold:     90°       (frames 160–161)
    #   Stage 3:  90°→0°   (frames 162–200) — retracts FIRST
    #   Hold:      0°       (frames 200–240)
    key_rot(hinge_rg, 1, ROT_SIGN_2, F_START,      0)
    key_rot(hinge_rg, 1, ROT_SIGN_2, F_S1_END,     0)
    key_rot(hinge_rg, 1, ROT_SIGN_2, F_S2_END,    90)
    key_rot(hinge_rg, 1, ROT_SIGN_2, F_SWAP,      90)
    key_rot(hinge_rg, 1, ROT_SIGN_2, F_RET1_END,   0)
    key_rot(hinge_rg, 1, ROT_SIGN_2, F_RET2_END,   0)

    print("Hinge keyframes set.")

    # ── Ball constraint influences ─────────────────────────────────────────
    #
    # Latch_Blue_Start: ON  frames 1–160, OFF from 161 onward
    # Latch_Green:      OFF frames 1–160, ON  from 161 onward
    #
    # All use CONSTANT interpolation — switches are intentional, not jumps.

    # Latch_Blue_Start
    key_influence(ball, "Latch_Blue_Start", F_START,       1.0)
    key_influence(ball, "Latch_Blue_Start", F_S2_END,      1.0)  # still on through Stage 2
    key_influence(ball, "Latch_Blue_Start", F_SWAP,        0.0)  # off at 161
    key_influence(ball, "Latch_Blue_Start", F_END,         0.0)

    # Latch_Green
    key_influence(ball, "Latch_Green",      F_START,       0.0)
    key_influence(ball, "Latch_Green",      F_S2_END,      0.0)  # still off through Stage 2
    key_influence(ball, "Latch_Green",      F_SWAP,        1.0)  # on at 161
    key_influence(ball, "Latch_Green",      F_END,         1.0)

    print("Influences keyed — Blue_Start→Green at frame 161.")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== T1 Complete: Blue → Green ===")
    return True

###############################################################################
# SECTION 5: N-Panel UI
###############################################################################

class LORQB_OT_run_t1(bpy.types.Operator):
    bl_idname      = "lorqb.run_t1"
    bl_label       = "Run T1: Blue → Green"
    bl_description = "Arm T1 animation: Blue transfers ball to Green"

    def execute(self, context):
        result = run_animation()
        if result:
            self.report({'INFO'}, "T1 armed — press Play to run")
        else:
            self.report({'ERROR'}, "T1 failed — check console for missing objects")
        return {'FINISHED'}


class LORQB_PT_t1_panel(bpy.types.Panel):
    bl_label       = "LorQB — T1"
    bl_idname      = "LORQB_PT_t1_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.label(text="T1: Blue → Green")
        layout.operator("lorqb.run_t1", icon='PLAY')


_classes = [LORQB_OT_run_t1, LORQB_PT_t1_panel]

def register():
    for cls in _classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

###############################################################################
# SECTION 6: Entry Point
###############################################################################

register()
