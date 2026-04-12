# ============================================================================
# T02_yellow_to_red.py  (Blender 5.0.1)
# T2 — Yellow → Red (diagonal)
#
# Ball path:
#   Frame   1: Ball at Yellow bottom (Seat_Yellow_Start = ball world pos, no jump)
#   Frame   1–80:  Stage 1 — Hinge_Green_Yellow rotates 0°→180° (Yellow flips)
#   Frame  81–160: Stage 2 — Hinge_Red_Green rotates 0°→90° (Yellow over Red)
#   Frame 161:     Ball transfers from Seat_Yellow_Start to Seat_Red
#   Frame 162–200: Stage 3 — Hinge_Red_Green returns 90°→0° FIRST
#   Frame 201–240: Stage 4 — Hinge_Green_Yellow returns 180°→0° SECOND
# ============================================================================

import bpy
import math
import mathutils

###############################################################################
# SECTION 1: Constants
###############################################################################

F_START        = 1
F_S1_END       = 80    # Hinge_Green_Yellow reaches 180° — Yellow fully flipped
F_S2_END       = 160   # Hinge_Red_Green reaches 90° — Yellow over Red
F_SWAP         = 161   # Ball transfers from Seat_Yellow_Start to Seat_Red
F_RET1_END     = 200   # Hinge_Red_Green returns 90°→0° FIRST
F_RET2_END     = 240   # Hinge_Green_Yellow returns 180°→0° SECOND
F_END          = 240

ROT_SIGN_1     = +1.0  # TODO: Hinge_Green_Yellow — verify sign in Blender
ROT_SIGN_2     = +1.0  # TODO: Hinge_Red_Green   — verify sign in Blender

# Red bottom interior center
SEAT_RED_WORLD = mathutils.Vector((0.51, -0.51, 0.25))

# Seat_Yellow_Start is NOT hardcoded — built from ball.matrix_world at runtime
# This prevents the jump-on-arm.

###############################################################################
# SECTION 2: Full Scene Reset
###############################################################################

def reset_scene_to_canonical():
    if bpy.app.driver_namespace.get("lorqb_run_all", False):
        print("=== T2 Reset skipped (Run ALL mode) ===")
        return

    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
        "Seat_Yellow_Start",
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

    for seat_name in ["Seat_Yellow_Start",
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
# SECTION 4: Main T2 Animation Logic
###############################################################################

def run_animation():
    print("=== T2 Start: Yellow → Red ===")

    reset_scene_to_canonical()

    yellow = bpy.data.objects.get("Cube_Yellow")
    green  = bpy.data.objects.get("Cube_Green")
    red    = bpy.data.objects.get("Cube_Red")
    ball   = bpy.data.objects.get("Ball")
    hinge1 = bpy.data.objects.get("Hinge_Green_Yellow")
    hinge2 = bpy.data.objects.get("Hinge_Red_Green")

    missing = [n for n, o in [
        ("Cube_Yellow",        yellow),
        ("Cube_Green",         green),
        ("Cube_Red",           red),
        ("Ball",               ball),
        ("Hinge_Green_Yellow", hinge1),
        ("Hinge_Red_Green",    hinge2),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge1.rotation_euler = (0, 0, 0)
    hinge2.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # ── Hierarchy ──────────────────────────────────────────────────────────
    # Yellow → Hinge_Green_Yellow → Green → Hinge_Red_Green
    # Red has NO parent — stays fixed throughout
    parent_preserve_world(yellow, hinge1)
    parent_preserve_world(hinge1, green)
    parent_preserve_world(green,  hinge2)
    print("Hierarchy set: Yellow→H1→Green→H2  (Red unparented)")

    # ── Remove rigid body from ball ────────────────────────────────────────
    if ball.rigid_body:
        bpy.context.view_layer.objects.active = ball
        try:
            bpy.ops.rigidbody.object_remove()
        except Exception:
            pass

    bpy.context.view_layer.update()

    # ── Move ball to Yellow's bottom interior center ─────────────────────
    # Ball starts inside Blue by default (C10_scene_build). Reposition it
    # to Yellow before capturing Seat_Yellow_Start.
    ball.location = mathutils.Vector((-0.51, 0.51, 0.25))
    ball.keyframe_insert(data_path="location", frame=F_START)
    bpy.context.view_layer.update()
    print("Ball moved to Yellow bottom interior center (-0.51, 0.51, 0.25).")

    # ── Seat_Yellow_Start ─────────────────────────────────────────────────
    # Built from ball's ACTUAL world position — no jump on arm.
    # Ball rides this seat through Stage 1 and Stage 2, then transfers
    # directly to Seat_Red at F_SWAP.
    ball_world           = ball.matrix_world.translation.copy()
    seat_start_local     = yellow.matrix_world.inverted() @ ball_world
    seat_yellow_start    = bpy.data.objects.new("Seat_Yellow_Start", None)
    seat_yellow_start.empty_display_type = 'SPHERE'
    seat_yellow_start.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_yellow_start)
    seat_yellow_start.parent   = yellow
    seat_yellow_start.location = seat_start_local
    print(f"Seat_Yellow_Start at ball world pos {ball_world} (no jump).")

    # ── Seat_Red ──────────────────────────────────────────────────────────
    # Bottom interior center of Red. Ball lands here at F_SWAP.
    seat_red_local       = red.matrix_world.inverted() @ SEAT_RED_WORLD
    seat_red             = bpy.data.objects.new("Seat_Red", None)
    seat_red.empty_display_type = 'SPHERE'
    seat_red.empty_display_size = 0.08
    bpy.context.scene.collection.objects.link(seat_red)
    seat_red.parent   = red
    seat_red.location = seat_red_local
    print(f"Seat_Red at world {SEAT_RED_WORLD} (bottom center of Red).")

    bpy.context.view_layer.update()

    # ── Constraints ────────────────────────────────────────────────────────
    latch_start = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_start.name   = "Latch_Yellow_Start"
    latch_start.target = seat_yellow_start

    latch_red = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_red.name   = "Latch_Red"
    latch_red.target = seat_red
    print("Latch_Yellow_Start and Latch_Red created.")

    # ── Hinge keyframes ────────────────────────────────────────────────────

    # Hinge_Green_Yellow (X-axis):
    #   Stage 1:  0°→180°  (frames  1–80)
    #   Hold:    180°       (frames 80–200) — waits for H2 to retract
    #   Stage 4: 180°→0°   (frames 201–240)
    key_rot(hinge1, 0, ROT_SIGN_1, F_START,      0)   # TODO: axis 0 = X — verify
    key_rot(hinge1, 0, ROT_SIGN_1, F_S1_END,   180)
    key_rot(hinge1, 0, ROT_SIGN_1, F_S2_END,   180)
    key_rot(hinge1, 0, ROT_SIGN_1, F_SWAP,     180)
    key_rot(hinge1, 0, ROT_SIGN_1, F_RET1_END, 180)
    key_rot(hinge1, 0, ROT_SIGN_1, F_RET2_END,   0)

    # Hinge_Red_Green (Y-axis):
    #   Stage 2:  0°→90°   (frames  81–160)
    #   Hold:     90°       (frames 160–161)
    #   Stage 3:  90°→0°   (frames 162–200) — retracts FIRST
    #   Hold:      0°       (frames 200–240)
    key_rot(hinge2, 1, ROT_SIGN_2, F_START,      0)   # TODO: axis 1 = Y — verify
    key_rot(hinge2, 1, ROT_SIGN_2, F_S1_END,     0)
    key_rot(hinge2, 1, ROT_SIGN_2, F_S2_END,    90)
    key_rot(hinge2, 1, ROT_SIGN_2, F_SWAP,      90)
    key_rot(hinge2, 1, ROT_SIGN_2, F_RET1_END,   0)
    key_rot(hinge2, 1, ROT_SIGN_2, F_RET2_END,   0)

    print("Hinge keyframes set.")

    # ── Ball constraint influences ─────────────────────────────────────────
    #
    # Latch_Yellow_Start: ON  frames 1–160, OFF from 161 onward
    # Latch_Red:          OFF frames 1–160, ON  from 161 onward
    #
    # All use CONSTANT interpolation — switches are intentional, not jumps.

    # Latch_Yellow_Start
    key_influence(ball, "Latch_Yellow_Start", F_START,       1.0)
    key_influence(ball, "Latch_Yellow_Start", F_S2_END,      1.0)  # still on through Stage 2
    key_influence(ball, "Latch_Yellow_Start", F_SWAP,        0.0)  # off at 161
    key_influence(ball, "Latch_Yellow_Start", F_END,         0.0)

    # Latch_Red
    key_influence(ball, "Latch_Red",          F_START,       0.0)
    key_influence(ball, "Latch_Red",          F_S2_END,      0.0)  # still off through Stage 2
    key_influence(ball, "Latch_Red",          F_SWAP,        1.0)  # on at 161
    key_influence(ball, "Latch_Red",          F_END,         1.0)

    print("Influences keyed — Yellow_Start→Red at frame 161.")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END
    bpy.context.scene.frame_set(F_START)

    print("=== T2 Complete: Yellow → Red ===")
    return True

###############################################################################
# SECTION 5: N-Panel UI
###############################################################################

class LORQB_OT_reset_t2(bpy.types.Operator):
    bl_idname      = "lorqb.reset_t2"
    bl_label       = "Reset to Base"
    bl_description = "Reset all objects to canonical state"

    def execute(self, context):
        reset_scene_to_canonical()
        self.report({'INFO'}, "T2 reset to base")
        return {'FINISHED'}


class LORQB_OT_run_t2(bpy.types.Operator):
    bl_idname      = "lorqb.run_t2"
    bl_label       = "Run T2: Yellow → Red"
    bl_description = "Arm T2 animation: Yellow transfers ball to Red"

    def execute(self, context):
        result = run_animation()
        if result:
            self.report({'INFO'}, "T2 armed — press Play to run")
        else:
            self.report({'ERROR'}, "T2 failed — check console for missing objects")
        return {'FINISHED'}


class LORQB_PT_t2_panel(bpy.types.Panel):
    bl_label       = "LorQB — T2"
    bl_idname      = "LORQB_PT_t2_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_t2", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.run_t2", text="Run T2: Yellow → Red", icon='PLAY')


_classes = [LORQB_OT_reset_t2, LORQB_OT_run_t2, LORQB_PT_t2_panel]

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
