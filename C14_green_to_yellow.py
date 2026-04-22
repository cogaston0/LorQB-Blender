# ============================================================================
# lorqb_green_to_yellow_C14.py  (Blender 5.0.1)
# C14 — Green → Yellow
# Frames 1 – 240 | Transfer at frame 120 → 121
# Chain: Blue — Red — Green — Yellow
# Hinge: Hinge_Green_Yellow (X-axis rotation, ROT_SIGN = -1.0)
# Ball rides Cube_Green (Latch_Green) → drops into Cube_Yellow (Latch_Yellow)
# Blue + Red + Hinge_Blue_Red + Hinge_Red_Green ride passively with Green.
# Only Hinge_Green_Yellow is keyed. No other hinges are touched.
# Architecture: matches C12/C13 reference standard
# ============================================================================

import bpy
import math
import mathutils

################################################################################
# SECTION 1: Constants
################################################################################
F_START = 1     # Start: Green at 0°, ball in Green
F_MID   = 60    # Mid:   Green at 90°
F_HOLD  = 120   # Hold:  Green at 180° — ball aligned above Yellow
F_SWAP  = 121   # Swap:  ball transfers from Latch_Green to Latch_Yellow
F_RET   = 180   # Return: Green at 90° on way back
F_END   = 240   # End:   Green at 0°, ball in Yellow

ROT_AXIS = 0        # X-axis index in rotation_euler
ROT_SIGN = -1.0     # Negative X rotation

# ---- Four-Seat Contract (Z=0.5 cube center; LORQB_BALL_STATE_STANDARD.md §4) ----
CANON_SEATS = {
    "Seat_Blue":   (mathutils.Vector(( 0.51,  0.51, 0.5)), "Cube_Blue"),
    "Seat_Red":    (mathutils.Vector(( 0.51, -0.51, 0.5)), "Cube_Red"),
    "Seat_Green":  (mathutils.Vector((-0.51, -0.51, 0.5)), "Cube_Green"),
    "Seat_Yellow": (mathutils.Vector((-0.51,  0.51, 0.5)), "Cube_Yellow"),
}

SEAT_GREEN_WORLD  = CANON_SEATS["Seat_Green"][0]
SEAT_YELLOW_WORLD = CANON_SEATS["Seat_Yellow"][0]

# Authoritative canonical cube + hinge world positions (from C10_scene_build.py).
# C10 uses ORIGIN_CURSOR to place each cube's origin at its hinge corner, so
# cube.location == hinge-corner world position (NOT visual center).
CANON_CUBES = {
    "Cube_Blue":   mathutils.Vector(( 0.51,  0.00, 1.0)),  # origin at Hinge_Blue_Red
    "Cube_Red":    mathutils.Vector(( 0.00, -0.51, 1.0)),  # origin at Hinge_Red_Green
    "Cube_Green":  mathutils.Vector((-0.51,  0.00, 1.0)),  # origin at Hinge_Green_Yellow
    "Cube_Yellow": mathutils.Vector((-0.51,  0.00, 1.0)),  # origin at Hinge_Green_Yellow
}
CANON_HINGES = {
    "Hinge_Blue_Red":     mathutils.Vector(( 0.51,  0.00, 1.0)),
    "Hinge_Red_Green":    mathutils.Vector(( 0.00, -0.51, 1.0)),
    "Hinge_Green_Yellow": mathutils.Vector((-0.51,  0.00, 1.0)),
}

################################################################################
# SECTION 1B: Four-Seat Contract helpers (shared block — identical in all scripts)
################################################################################
def ensure_four_seats():
    for seat_name, (world_vec, cube_name) in CANON_SEATS.items():
        stale = bpy.data.objects.get(seat_name)
        if stale:
            bpy.data.objects.remove(stale, do_unlink=True)
    bpy.context.view_layer.update()

    for seat_name, (world_vec, cube_name) in CANON_SEATS.items():
        cube = bpy.data.objects.get(cube_name)
        if cube is None:
            continue
        seat = bpy.data.objects.new(seat_name, None)
        seat.empty_display_type = 'SPHERE'
        seat.empty_display_size = 0.08
        bpy.context.scene.collection.objects.link(seat)
        seat.parent   = cube
        seat.location = cube.matrix_world.inverted() @ world_vec
    bpy.context.view_layer.update()

def validate_four_seats(label):
    print(f"--- FOUR-SEAT REPORT [{label}] ---")
    ok = True
    for seat_name in ("Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"):
        seat = bpy.data.objects.get(seat_name)
        if seat is None:
            print(f"  {seat_name}: <missing>  FAIL")
            ok = False
            continue
        w = seat.matrix_world.translation
        z_ok = abs(w.z - 0.5) <= 1e-3
        tag = "OK" if z_ok else "FAIL(Z)"
        if not z_ok:
            ok = False
        print(f"  {seat_name}: ({w.x:+.4f},{w.y:+.4f},{w.z:+.4f}) Z=0.5 {tag}")
    print(f"--- FOUR-SEAT [{label}] → {'PASS' if ok else 'FAIL'} ---")
    return ok

def hard_fail_missing_seats():
    missing = [n for n in CANON_SEATS if bpy.data.objects.get(n) is None]
    if missing:
        print("ABORT: missing canonical seats:", missing)
        return False
    return True

################################################################################
# SECTION 2: RESET — Full canonical reset of all 4 cubes + 3 hinges + ball
# (Option A / Main Agent correction pass: no partial reset; canonical base only)
################################################################################
def reset_c14_state():
    all_names = [
        "Ball",
        "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
        "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
    ]

    # Clear animation data on every active object.
    for name in all_names:
        obj = bpy.data.objects.get(name)
        if obj and obj.animation_data:
            obj.animation_data_clear()

    # Clear ball constraints.
    ball = bpy.data.objects.get("Ball")
    if ball:
        ball.constraints.clear()

    # Remove all 4 seats.
    for seat_name in ("Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"):
        seat = bpy.data.objects.get(seat_name)
        if seat:
            bpy.data.objects.remove(seat, do_unlink=True)

    bpy.context.view_layer.update()

    # Unparent every cube + hinge. Clear their constraints.
    for name in ("Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
                 "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.parent = None
            for con in list(obj.constraints):
                obj.constraints.remove(con)

    bpy.context.view_layer.update()

    # Restore all 4 cubes to canonical C10 positions, zero rotation.
    for name, loc in CANON_CUBES.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location       = (loc.x, loc.y, loc.z)
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)

    # Restore all 3 hinges to canonical C10 positions, zero rotation.
    for name, loc in CANON_HINGES.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location       = (loc.x, loc.y, loc.z)
            obj.rotation_mode  = 'XYZ'
            obj.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.view_layer.update()
    print("=== C14 reset: full canonical restore (4 cubes + 3 hinges) ===")

################################################################################
# SECTION 3: Helper — set interpolation on a specific keyframe by frame number
################################################################################
def set_last_keyframe_interpolation(obj, data_path, frame, interp='LINEAR'):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    fcurves = None
    try:
        fcurves = action.fcurves
    except AttributeError:
        pass
    if fcurves is None:
        try:
            fcurves = action.layers[0].strips[0].channelbag_for_slot(action.slots[0]).fcurves
        except Exception:
            pass
    if fcurves is None:
        try:
            fcurves = action.layers[0].strips[0].channelbags[0].fcurves
        except Exception:
            return
    for fc in fcurves:
        if fc.data_path == data_path or data_path in fc.data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = interp

################################################################################
# SECTION 4: Helper — key X-axis rotation with LINEAR interpolation
################################################################################
def key_rot_x(obj, frame, degrees):
    bpy.context.scene.frame_set(frame)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler[ROT_AXIS] = ROT_SIGN * math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=ROT_AXIS, frame=frame)
    set_last_keyframe_interpolation(obj, "rotation_euler", frame, 'LINEAR')

################################################################################
# SECTION 5: Helper — key constraint influence with CONSTANT interpolation
################################################################################
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

################################################################################
# SECTION 6: Helper — parent preserving world transform
################################################################################
def parent_preserve_world(child, new_parent):
    mw = child.matrix_world.copy()
    child.parent = new_parent
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()
    child.matrix_world = mw

def unparent_preserve_world(child):
    mw = child.matrix_world.copy()
    child.parent = None
    child.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    child.matrix_world = mw

################################################################################
# SECTION 6B: Hole alignment validation at F_HOLD
# At F_HOLD the hinge is at 180° on X with ROT_SIGN=-1.0.
# Green's world translation must equal Yellow's canonical translation
# offset by (0, 0, 1.0) — i.e. Green sits directly above Yellow, holes aligned.
################################################################################
def validate_alignment_at_hold(tol=1e-3):
    sg = bpy.data.objects.get("Seat_Green")
    sy = bpy.data.objects.get("Seat_Yellow")
    if sg is None or sy is None:
        print("[ALIGN] FAIL: Seat_Green or Seat_Yellow missing")
        return False
    gw = sg.matrix_world.translation
    yw = sy.matrix_world.translation
    dx = abs(gw.x - yw.x)
    dy = abs(gw.y - yw.y)
    dxy = (dx * dx + dy * dy) ** 0.5
    above = gw.z > yw.z
    ok = (dxy <= tol) and above
    status = "PASS" if ok else "FAIL"
    print(f"[ALIGN @ F_HOLD] Seat_Green=({gw.x:+.4f},{gw.y:+.4f},{gw.z:+.4f}) Seat_Yellow=({yw.x:+.4f},{yw.y:+.4f},{yw.z:+.4f}) ΔXY={dxy:.5f} above={above} → {status}")
    return ok

def validate_canonical_restore(tol=1e-3):
    ok = True
    for name, target in list(CANON_CUBES.items()) + list(CANON_HINGES.items()):
        obj = bpy.data.objects.get(name)
        if obj is None:
            print(f"[RESTORE] {name}: <missing>  FAIL")
            ok = False
            continue
        w = obj.matrix_world.translation
        d = (w - target).length
        status = "OK" if d <= tol else "FAIL"
        if d > tol:
            ok = False
        print(f"[RESTORE] {name}: Δ={d:.5f} {status}")
    return ok

################################################################################
# SECTION 7: Main C14 setup function
################################################################################
def setup_green_to_yellow():
    print("=== C14 Start: Green → Yellow ===")

    reset_c14_state()

    green  = bpy.data.objects.get("Cube_Green")
    yellow = bpy.data.objects.get("Cube_Yellow")
    ball   = bpy.data.objects.get("Ball")
    hinge  = bpy.data.objects.get("Hinge_Green_Yellow")

    missing = [n for n, o in [
        ("Cube_Green",         green),
        ("Cube_Yellow",        yellow),
        ("Ball",               ball),
        ("Hinge_Green_Yellow", hinge),
    ] if o is None]

    if missing:
        print("ERROR: Missing objects:", missing)
        return False

    bpy.context.scene.frame_set(F_START)
    hinge.rotation_mode = 'XYZ'
    hinge.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

    # --- STEP A: Build ALL 4 canonical seats BEFORE any reparenting ---
    # Seats are computed from each cube's canonical world matrix.
    ensure_four_seats()
    if not validate_four_seats("after ensure_four_seats"):
        print("ABORT: four-seat validation failed at build time.")
        return False
    if not hard_fail_missing_seats():
        return False

    seat_green  = bpy.data.objects.get("Seat_Green")
    seat_yellow = bpy.data.objects.get("Seat_Yellow")

    # --- STEP B: Create ball latches (COPY_TRANSFORMS) ---
    latch_green = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_green.name = "Latch_Green"
    latch_green.target = seat_green
    print("Latch_Green created.")

    latch_yellow = ball.constraints.new(type='COPY_TRANSFORMS')
    latch_yellow.name = "Latch_Yellow"
    latch_yellow.target = seat_yellow
    print("Latch_Yellow created.")

    # --- STEP C: Explicit ball snap to Seat_Green at F=1 ---
    # VB Fix Action 1: snap ball to Seat_Green at frame 1.
    # Latch_Green becomes authoritative on first evaluation, but we set the
    # ball's own location to the seat's world pos as a belt-and-braces guarantee.
    bpy.context.scene.frame_set(F_START)
    ball.location = seat_green.matrix_world.translation.copy()
    bpy.context.view_layer.update()
    print(f"Ball snapped to Seat_Green: {ball.matrix_world.translation[:]}")

    # --- STEP D: Passive-ride chain (known-good C14 pattern) ---
    # Only Green rides HGY. Red rides Green passively. Blue anchored to HBR
    # which does NOT rotate — Blue stays still at base.
    # Tree: HGY → Green → Red   ||   HBR → Blue
    blue = bpy.data.objects.get("Cube_Blue")
    red  = bpy.data.objects.get("Cube_Red")
    hbr  = bpy.data.objects.get("Hinge_Blue_Red")
    if blue and hbr:
        parent_preserve_world(blue, hbr)
    if red and green:
        parent_preserve_world(red, green)
    parent_preserve_world(green, hinge)
    bpy.context.view_layer.update()
    print("Parented: HGY→Green→Red (ride); HBR→Blue (still).")

    # --- STEP E: Key only Hinge_Green_Yellow — Blue/Red/HBR/HRG not touched ---
    key_rot_x(hinge, F_START,   0)
    key_rot_x(hinge, F_MID,    90)
    key_rot_x(hinge, F_HOLD,  180)
    key_rot_x(hinge, F_SWAP,  180)
    key_rot_x(hinge, F_RET,    90)
    key_rot_x(hinge, F_END,     0)
    print("Hinge_Green_Yellow rotation keyed — LINEAR.")

    # --- STEP F: Latch influence sequence (CONSTANT interpolation) ---
    key_influence(ball, "Latch_Green",  F_START, 1.0)
    key_influence(ball, "Latch_Yellow", F_START, 0.0)
    key_influence(ball, "Latch_Green",  F_HOLD,  1.0)
    key_influence(ball, "Latch_Yellow", F_HOLD,  0.0)
    key_influence(ball, "Latch_Green",  F_SWAP,  0.0)
    key_influence(ball, "Latch_Yellow", F_SWAP,  1.0)
    key_influence(ball, "Latch_Green",  F_END,   0.0)
    key_influence(ball, "Latch_Yellow", F_END,   1.0)
    print("Ball influences keyed — CONSTANT.")

    bpy.context.scene.frame_start = F_START
    bpy.context.scene.frame_end   = F_END

    # --- STEP G: Validate hole alignment at F_HOLD ---
    bpy.context.scene.frame_set(F_HOLD)
    bpy.context.view_layer.update()
    align_ok = validate_alignment_at_hold()

    # --- STEP H: Advance to F_END and validate canonical restore ---
    # Parent relationship persists (matches C12/C13 reference standard).
    # Hinge returns to 0° via keyframe → Green returns to canonical pose via parent.
    bpy.context.scene.frame_set(F_END)
    bpy.context.view_layer.update()

    restore_ok = validate_canonical_restore()

    # Back to F=1 for playback start.
    bpy.context.scene.frame_set(F_START)
    bpy.context.view_layer.update()

    validate_four_seats("C14 final")

    print("=== C14 Complete: Green → Yellow ===")
    print(f"Frames {F_START}–{F_END} | Transfer at frame {F_HOLD}→{F_SWAP}")
    print(f"ROT_SIGN: {ROT_SIGN} | Axis: X | Hinge: Hinge_Green_Yellow")
    print(f"Alignment @ F_HOLD: {'PASS' if align_ok else 'FAIL'}")
    print(f"Canonical restore @ F_END: {'PASS' if restore_ok else 'FAIL'}")
    return align_ok and restore_ok

################################################################################
# SECTION 8: Blender UI Panel and Operator
################################################################################
class LORQB_OT_ResetC14(bpy.types.Operator):
    bl_idname  = "lorqb.reset_c14"
    bl_label   = "Reset to Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_c14_state()
        self.report({'INFO'}, "Reset to base complete")
        return {'FINISHED'}

class LORQB_PT_C14Panel(bpy.types.Panel):
    bl_label       = "LorQB C14: Green → Yellow"
    bl_idname      = "LORQB_PT_c14_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c14", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.green_to_yellow", text="Run C14: Green → Yellow", icon='PLAY')

class LORQB_OT_GreenToYellow(bpy.types.Operator):
    bl_idname  = "lorqb.green_to_yellow"
    bl_label   = "Green to Yellow C14"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success = setup_green_to_yellow()
        if success:
            self.report({'INFO'}, "C14 complete: Green → Yellow")
        else:
            self.report({'ERROR'}, "C14 failed — check console")
        return {'FINISHED'}

################################################################################
# SECTION 9: Register / Unregister
################################################################################
def _unregister_all_lorqb():
    to_remove = []
    for name in dir(bpy.types):
        cls = getattr(bpy.types, name, None)
        if cls is None:
            continue
        bl_idname = getattr(cls, "bl_idname", "") or ""
        if "lorqb" in bl_idname.lower():
            to_remove.append(cls)
    for cls in to_remove:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

def register():
    _unregister_all_lorqb()
    bpy.utils.register_class(LORQB_OT_ResetC14)
    bpy.utils.register_class(LORQB_PT_C14Panel)
    bpy.utils.register_class(LORQB_OT_GreenToYellow)
    print("\n" + "=" * 50)
    print("✓ LorQB C14 Panel Ready.")
    print("3D View → N-panel → LorQB → 'Run C14: Green → Yellow'")
    print("=" * 50 + "\n")

def unregister():
    try:
        bpy.utils.unregister_class(LORQB_OT_GreenToYellow)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_PT_C14Panel)
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(LORQB_OT_ResetC14)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()