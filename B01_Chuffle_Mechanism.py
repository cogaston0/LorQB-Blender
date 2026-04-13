# ============================================================================
# B01_Chuffle_Mechanism.py  (Blender 5.0.1)
# LorQB / Cubolita — Level 1 Digital Shuffle Mechanism
#
# Self-contained. Does NOT touch cubes, hinges, ball, or any existing rig.
# Creates B01_* objects only. Idempotent — safe for repeated runs.
# ============================================================================

import bpy
import random
import json
from bpy.types import Operator, Panel
from bpy.props import StringProperty

# ============================================================================
# SECTION 1: Constants
# ============================================================================

B01_COLORS = ["Blue", "Red", "Yellow", "Green"]

COLOR_RGB = {
    "Blue":   (0.1, 0.3, 0.9, 1.0),
    "Red":    (0.9, 0.1, 0.1, 1.0),
    "Yellow": (0.95, 0.85, 0.1, 1.0),
    "Green":  (0.1, 0.8, 0.2, 1.0),
}

MAT_NAMES = {
    "Blue":     "MAT_B01_Blue",
    "Red":      "MAT_B01_Red",
    "Yellow":   "MAT_B01_Yellow",
    "Green":    "MAT_B01_Green",
    "Inactive": "MAT_B01_Inactive",
    "Complete": "MAT_B01_Complete",
    "Active":   "MAT_B01_Active",
}

SLOT_NAMES = [
    "B01_OrderSlot_1",
    "B01_OrderSlot_2",
    "B01_OrderSlot_3",
    "B01_OrderSlot_4",
]

ROOT_NAME      = "B01_OrderBar_ROOT"
MARKER_NAME    = "B01_ActiveMarker"
TIMER_NAME     = "B01_TimerText"
STATUS_NAME    = "B01_StatusText"
BTN_NEXT_NAME  = "B01_BTN_NextTurn"
BTN_RESET_NAME = "B01_BTN_Reset"
BTN_PRACTICE   = "B01_BTN_Practice"

# Layout: bar centered in front of Blue/Yellow row, at ground level
# Blue ~(0.51, 0.51), Yellow ~(-0.51, 0.51) — bar goes at Y=2.5
ROOT_X = 0.0
ROOT_Y = 2.5
ROOT_Z = 0.0
SLOT_WIDTH  = 0.8
SLOT_HEIGHT = 0.5
SLOT_DEPTH  = 0.15
SLOT_GAP    = 0.0
MARKER_Z_OFFSET = -0.05
TEXT_Y_OFFSET    = 0.8

# ============================================================================
# SECTION 2: Material helpers
# ============================================================================

def _get_or_create_mat(name, rgba):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = rgba
    return mat


def ensure_b01_materials():
    for color_key, mat_name in MAT_NAMES.items():
        if color_key in COLOR_RGB:
            _get_or_create_mat(mat_name, COLOR_RGB[color_key])
    _get_or_create_mat(MAT_NAMES["Inactive"], (0.6, 0.6, 0.6, 1.0))
    _get_or_create_mat(MAT_NAMES["Complete"], (0.25, 0.25, 0.25, 1.0))
    _get_or_create_mat(MAT_NAMES["Active"],   (1.0, 1.0, 1.0, 1.0))


# ============================================================================
# SECTION 3: Object helpers
# ============================================================================

def _get_or_create_empty(name, location, parent=None):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = 0.3
    if parent is not None:
        obj.parent = parent
    return obj


def _get_or_create_box(name, size, location, parent=None):
    obj = bpy.data.objects.get(name)
    if obj is None:
        mesh = bpy.data.meshes.new(name + "_mesh")
        bpy.ops.mesh.primitive_cube_add(size=1)
        temp = bpy.context.active_object
        mesh = temp.data
        mesh.name = name + "_mesh"
        temp.name = name
        obj = temp
        bpy.context.view_layer.objects.active = None
    obj.scale = size
    obj.location = location
    if parent is not None:
        obj.parent = parent
    return obj


def _get_or_create_text(name, body, location, parent=None, size=0.3):
    obj = bpy.data.objects.get(name)
    if obj is None:
        curve = bpy.data.curves.new(name + "_curve", type='FONT')
        obj = bpy.data.objects.new(name, curve)
        bpy.context.scene.collection.objects.link(obj)
    obj.data.body = body
    obj.data.size = size
    obj.data.align_x = 'CENTER'
    obj.location = location
    import math
    obj.rotation_euler = (math.radians(90), 0, math.radians(180))
    if parent is not None:
        obj.parent = parent
    return obj


def _assign_mat(obj, mat_name):
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        return
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat


# ============================================================================
# SECTION 4: Rig builder
# ============================================================================

def _delete_b01_objects():
    """Remove all existing B01 objects for a clean rebuild."""
    import re
    to_remove = [obj for obj in bpy.data.objects if obj.name.startswith("B01_")]
    for obj in to_remove:
        bpy.data.objects.remove(obj, do_unlink=True)


def ensure_b01_rig():
    ensure_b01_materials()
    _delete_b01_objects()

    root = _get_or_create_empty(ROOT_NAME, (ROOT_X, ROOT_Y, ROOT_Z))

    total_width = 4 * SLOT_WIDTH
    start_x = -total_width / 2 + SLOT_WIDTH / 2

    for i, slot_name in enumerate(SLOT_NAMES):
        x = start_x + i * SLOT_WIDTH
        slot = _get_or_create_box(
            slot_name,
            (SLOT_WIDTH, SLOT_HEIGHT, SLOT_DEPTH),
            (x, 0, 0),
            parent=root,
        )
        _assign_mat(slot, MAT_NAMES["Inactive"])

    # Active marker — thin flat plane below slots
    marker = _get_or_create_box(
        MARKER_NAME,
        (SLOT_WIDTH / 2 + 0.05, 0.05, 0.02),
        (start_x, 0, MARKER_Z_OFFSET - SLOT_HEIGHT / 2),
        parent=root,
    )
    _assign_mat(marker, MAT_NAMES["Active"])

    # Text objects — placed below slots (positive Y = further from cubes)
    _get_or_create_text(
        STATUS_NAME, "Ready",
        (0, TEXT_Y_OFFSET, 0),
        parent=root, size=0.3,
    )
    _get_or_create_text(
        TIMER_NAME, "00:00",
        (0, TEXT_Y_OFFSET + 0.5, 0),
        parent=root, size=0.25,
    )

    # Button empties (optional visual anchors)
    btn_y = -1.0
    _get_or_create_empty(BTN_NEXT_NAME,  (start_x, btn_y, 0), parent=root)
    _get_or_create_empty(BTN_RESET_NAME, (start_x + 1.5, btn_y, 0), parent=root)
    _get_or_create_empty(BTN_PRACTICE,   (start_x + 3.0, btn_y, 0), parent=root)


# ============================================================================
# SECTION 5: State management
# ============================================================================

def _scene():
    return bpy.context.scene


def reset_shuffle_state():
    s = _scene()
    s["b01_sequence"]      = json.dumps([])
    s["b01_current_index"] = 0
    s["b01_mode"]          = "idle"
    s["b01_timer_running"] = False
    s["b01_turn_complete"] = False


def new_turn_shuffle():
    ensure_b01_rig()
    seq = list(B01_COLORS)
    random.shuffle(seq)
    s = _scene()
    s["b01_sequence"]      = json.dumps(seq)
    s["b01_current_index"] = 0
    s["b01_mode"]          = "playing"
    s["b01_timer_running"] = True
    s["b01_turn_complete"] = False
    update_order_bar_visuals()
    set_status_text("Target: " + seq[0])


def get_current_target():
    s = _scene()
    seq = json.loads(s.get("b01_sequence", "[]"))
    idx = s.get("b01_current_index", 0)
    if idx < len(seq):
        return seq[idx]
    return None


def is_sequence_complete():
    s = _scene()
    seq = json.loads(s.get("b01_sequence", "[]"))
    idx = s.get("b01_current_index", 0)
    return len(seq) > 0 and idx >= len(seq)


def mark_current_complete_and_advance():
    s = _scene()
    seq = json.loads(s.get("b01_sequence", "[]"))
    idx = s.get("b01_current_index", 0)
    if idx >= len(seq):
        return

    # Mark current slot complete
    slot = bpy.data.objects.get(SLOT_NAMES[idx])
    if slot:
        _assign_mat(slot, MAT_NAMES["Complete"])

    idx += 1
    s["b01_current_index"] = idx

    if idx >= len(seq):
        s["b01_turn_complete"] = True
        s["b01_timer_running"] = False
        s["b01_mode"] = "complete"
        set_status_text("COMPLETE")
        # Hide marker
        marker = bpy.data.objects.get(MARKER_NAME)
        if marker:
            marker.hide_viewport = True
    else:
        update_order_bar_visuals()
        set_status_text("Target: " + seq[idx])


# ============================================================================
# SECTION 6: Visual update
# ============================================================================

def update_order_bar_visuals():
    s = _scene()
    seq = json.loads(s.get("b01_sequence", "[]"))
    idx = s.get("b01_current_index", 0)

    total_width = 4 * SLOT_WIDTH
    start_x = -total_width / 2 + SLOT_WIDTH / 2

    for i, slot_name in enumerate(SLOT_NAMES):
        slot = bpy.data.objects.get(slot_name)
        if slot is None:
            continue
        if i < len(seq):
            color_key = seq[i]
            if i < idx:
                _assign_mat(slot, MAT_NAMES["Complete"])
            elif i == idx:
                _assign_mat(slot, MAT_NAMES.get(color_key, "MAT_B01_Inactive"))
            else:
                _assign_mat(slot, MAT_NAMES.get(color_key, "MAT_B01_Inactive"))
        else:
            _assign_mat(slot, MAT_NAMES["Inactive"])

    # Move marker under active slot
    marker = bpy.data.objects.get(MARKER_NAME)
    if marker and idx < len(seq):
        marker.hide_viewport = False
        x = start_x + idx * SLOT_WIDTH
        marker.location.x = x


def set_status_text(text):
    obj = bpy.data.objects.get(STATUS_NAME)
    if obj:
        obj.data.body = text


def set_timer_text(text):
    obj = bpy.data.objects.get(TIMER_NAME)
    if obj:
        obj.data.body = text


# ============================================================================
# SECTION 7: Operators
# ============================================================================

class LORQB_OT_b01_build_shuffle_ui(Operator):
    bl_idname = "lorqb.b01_build_shuffle_ui"
    bl_label = "Build / Refresh B01"
    bl_description = "Create or refresh the B01 shuffle UI rig"

    def execute(self, context):
        ensure_b01_rig()
        reset_shuffle_state()
        update_order_bar_visuals()
        set_status_text("Ready")
        return {'FINISHED'}


class LORQB_OT_b01_next_turn(Operator):
    bl_idname = "lorqb.b01_next_turn"
    bl_label = "New Shuffle"
    bl_description = "Generate a new random color sequence"

    def execute(self, context):
        new_turn_shuffle()
        return {'FINISHED'}


class LORQB_OT_b01_reset_shuffle(Operator):
    bl_idname = "lorqb.b01_reset_shuffle"
    bl_label = "Reset"
    bl_description = "Reset the shuffle state and visuals"

    def execute(self, context):
        reset_shuffle_state()
        ensure_b01_rig()
        update_order_bar_visuals()
        set_status_text("Ready")
        marker = bpy.data.objects.get(MARKER_NAME)
        if marker:
            marker.hide_viewport = True
        return {'FINISHED'}


class LORQB_OT_b01_advance_step(Operator):
    bl_idname = "lorqb.b01_advance_step"
    bl_label = "Advance Step"
    bl_description = "Mark current target complete and advance"

    def execute(self, context):
        s = context.scene
        if s.get("b01_turn_complete", False):
            self.report({'INFO'}, "Sequence already complete")
            return {'CANCELLED'}
        seq = json.loads(s.get("b01_sequence", "[]"))
        if len(seq) == 0:
            self.report({'INFO'}, "No active sequence — shuffle first")
            return {'CANCELLED'}
        mark_current_complete_and_advance()
        return {'FINISHED'}


class LORQB_OT_b01_show_target(Operator):
    bl_idname = "lorqb.b01_show_target"
    bl_label = "Show Current Target"
    bl_description = "Display the current target color"

    def execute(self, context):
        target = get_current_target()
        if target:
            self.report({'INFO'}, "Current target: " + target)
        else:
            self.report({'INFO'}, "No active target")
        return {'FINISHED'}


# ============================================================================
# SECTION 8: N-Panel
# ============================================================================

class LORQB_PT_b01_panel(Panel):
    bl_label = "LorQB — B01"
    bl_idname = "LORQB_PT_b01_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LorQB — B01"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        # Buttons
        layout.operator("lorqb.b01_build_shuffle_ui", icon='MESH_CUBE')
        layout.operator("lorqb.b01_next_turn", icon='FILE_REFRESH')
        layout.operator("lorqb.b01_reset_shuffle", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.b01_advance_step", icon='FORWARD')
        layout.operator("lorqb.b01_show_target", icon='VIEWZOOM')

        # State display
        layout.separator()
        box = layout.box()
        seq = json.loads(s.get("b01_sequence", "[]"))
        idx = s.get("b01_current_index", 0)
        complete = s.get("b01_turn_complete", False)

        box.label(text="Sequence: " + (", ".join(seq) if seq else "—"))
        box.label(text="Index: " + str(idx))

        target = get_current_target()
        box.label(text="Target: " + (target if target else "—"))
        box.label(text="Complete: " + ("YES" if complete else "No"))


# ============================================================================
# SECTION 9: Registration
# ============================================================================

_classes = (
    LORQB_OT_b01_build_shuffle_ui,
    LORQB_OT_b01_next_turn,
    LORQB_OT_b01_reset_shuffle,
    LORQB_OT_b01_advance_step,
    LORQB_OT_b01_show_target,
    LORQB_PT_b01_panel,
)


def register():
    for cls in _classes:
        # Unregister first to avoid duplicate errors on repeated runs
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


# ============================================================================
# SECTION 10: Auto-run when executed from Text Editor
# ============================================================================

if __name__ == "__main__":
    register()
    ensure_b01_rig()
    reset_shuffle_state()
    update_order_bar_visuals()
    set_status_text("Ready")
    print("B01_Chuffle_Mechanism registered.")
    print("B01 rig built at X=%.1f Z=%.1f" % (ROOT_X, ROOT_Z))
