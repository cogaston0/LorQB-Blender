# ============================================================================
# C01_lorQB_Master_Runner.py  (Blender 5.0.1)
# C01 — Master Runner: C12 → C15
#
# Executes the full C-series sequence in order:
#   C12: Blue → Red
#   C13: Red → Green
#   C14: Green → Yellow
#   C15: Yellow → Blue
# ============================================================================

import bpy
import os
import traceback

###############################################################################
# SECTION 1: Constants
###############################################################################

SCRIPTS_DIR = r"C:\rukmini_ai_loop\scripts"

# Per-file panels registered by individual C/T scripts on exec.
# The Master Runner strips these after each run so only the C01 panel shows.
CHILD_PANELS = [
    "LORQB_PT_c12_panel", "LORQB_PT_c13_panel",
    "LORQB_PT_c14_panel", "LORQB_PT_c15_panel",
    "LORQB_PT_t1_panel",  "LORQB_PT_t2_panel",
    "LORQB_PT_t3_panel",  "LORQB_PT_t4_panel",
]

def _strip_child_panels():
    for name in CHILD_PANELS:
        cls = getattr(bpy.types, name, None)
        if cls is not None:
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass

SEQUENCE = [
    ("C12_blue_to_red.py",     "setup_blue_to_red"),
    ("C13_red_to_green.py",    "setup_red_to_green"),
    ("C14_green_to_yellow.py", "setup_green_to_yellow"),
    ("C15_yellow_to_blue.py",  "setup_yellow_to_blue"),
]

T_SEQUENCE = [
    ("T01_blue_to_green.py",  "setup_blue_to_green"),
    ("T02_yellow_to_red.py",  "setup_yellow_to_red"),
    ("T03_red_to_yellow.py",  "setup_red_to_yellow"),
    ("T04_green_to_blue.py",  "setup_green_to_blue"),
]

def _exec_and_call(filename, funcname):
    path = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.isfile(path):
        print(f"ERROR: File not found: {path}")
        return False, f"File not found: {filename}"
    with open(path, "r") as f:
        lines = f.readlines()
    code = "".join(lines[:-1])
    ns = {"__file__": path, "bpy": bpy}
    try:
        exec(compile(code, path, "exec"), ns)
    except Exception as e:
        print(f"=== EXEC ERROR in {filename}: {type(e).__name__}: {e} ===")
        traceback.print_exc()
        _strip_child_panels()
        return False, f"exec error: {e}"
    fn = ns.get(funcname)
    if fn is None:
        msg = f"{filename} does not expose {funcname}()"
        print(f"=== ERROR: {msg} ===")
        _strip_child_panels()
        return False, msg
    try:
        fn()
        print(f"=== {filename} complete ===")
        _strip_child_panels()
        return True, None
    except Exception as e:
        print(f"=== ERROR in {filename}: {type(e).__name__}: {e} ===")
        traceback.print_exc()
        _strip_child_panels()
        return False, f"{type(e).__name__}: {e}"

###############################################################################
# SECTION 2: Operator
###############################################################################

class LORQB_OT_run_all(bpy.types.Operator):
    bl_idname      = "lorqb.run_all"
    bl_label       = "Run All C12 → C15"
    bl_description = "Execute the full C-series sequence"
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.app.driver_namespace["lorqb_run_all"] = True
        for filename, funcname in SEQUENCE:
            ok, err = _exec_and_call(filename, funcname)
            if not ok:
                self.report({'ERROR'}, f"{filename}: {err}")
        bpy.app.driver_namespace["lorqb_run_all"] = False
        print("=== ALL COMPLETE ===")
        return {'FINISHED'}


class LORQB_OT_run_all_t(bpy.types.Operator):
    bl_idname      = "lorqb.run_all_t"
    bl_label       = "Run All T01 → T04"
    bl_description = "Execute the full T-series sequence"
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.app.driver_namespace["lorqb_run_all"] = True
        for filename, funcname in T_SEQUENCE:
            ok, err = _exec_and_call(filename, funcname)
            if not ok:
                self.report({'ERROR'}, f"{filename}: {err}")
        bpy.app.driver_namespace["lorqb_run_all"] = False
        print("=== ALL T COMPLETE ===")
        return {'FINISHED'}


def _set_active_btn(idname):
    bpy.app.driver_namespace["lorqb_active_btn"] = idname
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    except Exception:
        pass


def _make_master_op(cls_suffix, idname, label, filename, funcname, start_banner):
    class _Op(bpy.types.Operator):
        bl_idname      = idname
        bl_label       = label
        bl_description = f"Run {filename}"
        bl_options     = {'REGISTER', 'UNDO'}

        def execute(self, context):
            _set_active_btn(idname)
            print(f"=== {start_banner} ===")
            ok, err = _exec_and_call(filename, funcname)
            if not ok:
                self.report({'ERROR'}, f"{filename}: {err}")
                return {'CANCELLED'}
            return {'FINISHED'}
    _Op.__name__ = f"LORQB_OT_{cls_suffix}"
    _Op.__qualname__ = _Op.__name__
    return _Op


LORQB_OT_master_c12 = _make_master_op("master_c12", "lorqb.master_c12",
    "C12: Blue -> Red",     "C12_blue_to_red.py",     "setup_blue_to_red",     "C12 Start")
LORQB_OT_master_c13 = _make_master_op("master_c13", "lorqb.master_c13",
    "C13: Red -> Green",    "C13_red_to_green.py",    "setup_red_to_green",    "C13 Start")
LORQB_OT_master_c14 = _make_master_op("master_c14", "lorqb.master_c14",
    "C14: Green -> Yellow", "C14_green_to_yellow.py", "setup_green_to_yellow", "C14 Start")
LORQB_OT_master_c15 = _make_master_op("master_c15", "lorqb.master_c15",
    "C15: Yellow -> Blue",  "C15_yellow_to_blue.py",  "setup_yellow_to_blue",  "C15 Start")
LORQB_OT_master_t1  = _make_master_op("master_t1",  "lorqb.master_t1",
    "T01: Blue -> Green",   "T01_blue_to_green.py",   "setup_blue_to_green",   "T01 Start")
LORQB_OT_master_t2  = _make_master_op("master_t2",  "lorqb.master_t2",
    "T02: Yellow -> Red",   "T02_yellow_to_red.py",   "setup_yellow_to_red",   "T02 Start")
LORQB_OT_master_t3  = _make_master_op("master_t3",  "lorqb.master_t3",
    "T03: Red -> Yellow",   "T03_red_to_yellow.py",   "setup_red_to_yellow",   "T03 Start")
LORQB_OT_master_t4  = _make_master_op("master_t4",  "lorqb.master_t4",
    "T04: Green -> Blue",   "T04_green_to_blue.py",   "setup_green_to_blue",   "T04 Start")

###############################################################################
# SECTION 3: UI Panel
###############################################################################

class LORQB_PT_c01_panel(bpy.types.Panel):
    bl_label       = "LorQB — C01"
    bl_idname      = "LORQB_PT_c01_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        active = bpy.app.driver_namespace.get("lorqb_active_btn", None)

        def btn(parent, op_id, text):
            # Active button = normal emboss. Inactive = flattened so active one "pops".
            row = parent.row()
            row.emboss = 'NORMAL' if op_id == active else 'NONE'
            row.operator(op_id, text=text, icon='FORWARD')

        # -- Run All --
        layout.operator("lorqb.run_all",   text="Run All C12 -> C15", icon='PLAY')
        layout.operator("lorqb.run_all_t", text="Run All T01 -> T04", icon='PLAY')

        # -- C-Series --
        layout.separator()
        layout.label(text="C-Series (Single Moves)")
        btn(layout, "lorqb.master_c12", "C12: Blue -> Red")
        btn(layout, "lorqb.master_c13", "C13: Red -> Green")
        btn(layout, "lorqb.master_c14", "C14: Green -> Yellow")
        btn(layout, "lorqb.master_c15", "C15: Yellow -> Blue")

        # -- T-Series --
        layout.separator()
        layout.label(text="T-Series (Diagonal Moves)")
        btn(layout, "lorqb.master_t1", "T01: Blue -> Green")
        btn(layout, "lorqb.master_t2", "T02: Yellow -> Red")
        btn(layout, "lorqb.master_t3", "T03: Red -> Yellow")
        btn(layout, "lorqb.master_t4", "T04: Green -> Blue")

_classes = [
    LORQB_OT_run_all, LORQB_OT_run_all_t,
    LORQB_OT_master_c12, LORQB_OT_master_c13, LORQB_OT_master_c14, LORQB_OT_master_c15,
    LORQB_OT_master_t1,  LORQB_OT_master_t2,  LORQB_OT_master_t3,  LORQB_OT_master_t4,
    LORQB_PT_c01_panel,
]

###############################################################################
# SECTION 4: Register / Entry Point
###############################################################################

def _safe_unregister_by_name(names):
    for name in names:
        cls = getattr(bpy.types, name, None)
        if cls is not None:
            try:
                bpy.utils.unregister_class(cls)
            except Exception as e:
                print(f"[C01] unregister warn ({name}): {e}")

def register():
    _safe_unregister_by_name([
        "LORQB_OT_RunAll", "LORQB_PT_Panel",
        "LORQB_OT_run_all", "LORQB_OT_run_all_t", "LORQB_PT_c01_panel",
        "LORQB_OT_master_c12", "LORQB_OT_master_c13",
        "LORQB_OT_master_c14", "LORQB_OT_master_c15",
        "LORQB_OT_master_t1",  "LORQB_OT_master_t2",
        "LORQB_OT_master_t3",  "LORQB_OT_master_t4",
    ])
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"[C01] register failed for {cls.__name__}: {e}")
            try:
                existing = getattr(bpy.types, cls.__name__, None)
                if existing is not None:
                    bpy.utils.unregister_class(existing)
                bpy.utils.register_class(cls)
                print(f"[C01] register recovered for {cls.__name__}")
            except Exception as e2:
                print(f"[C01] register recovery failed for {cls.__name__}: {e2}")
    panel_cls = getattr(bpy.types, "LORQB_PT_c01_panel", None)
    op_cls    = getattr(bpy.types, "LORQB_OT_run_all",   None)
    print(f"[C01] panel registered: {panel_cls is not None}")
    print(f"[C01] operator registered: {op_cls is not None}")
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    except Exception:
        pass

def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    register()
else:
    register()
