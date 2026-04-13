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

SEQUENCE = [
    ("C12_blue_to_red.py",     "setup_blue_to_red"),
    ("C13_red_to_green.py",    "setup_red_to_green"),
    ("C14_green_to_yellow.py", "setup_green_to_yellow"),
    ("C15_yellow_to_blue.py",  "setup_yellow_to_blue"),
]

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
            path = os.path.join(SCRIPTS_DIR, filename)
            if not os.path.isfile(path):
                print(f"ERROR: File not found: {path}")
                self.report({'ERROR'}, f"File not found: {filename}")
                bpy.app.driver_namespace["lorqb_run_all"] = False
                return {'CANCELLED'}
            with open(path, "r") as f:
                lines = f.readlines()
            code = "".join(lines[:-1])
            ns = {"__file__": path, "bpy": bpy}
            exec(compile(code, path, "exec"), ns)
            try:
                ns[funcname]()
                print(f"=== {filename} complete ===")
            except Exception as e:
                print(f"=== ERROR in {filename}: {type(e).__name__}: {e} ===")
                traceback.print_exc()
        bpy.app.driver_namespace["lorqb_run_all"] = False
        print("=== ALL COMPLETE ===")
        return {'FINISHED'}

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

        # ── Run All ──
        layout.operator("lorqb.run_all", text="Run All C12 → C15", icon='PLAY')

        # ── C-Series ──
        layout.separator()
        layout.label(text="C-Series (Single Moves)")
        layout.operator("lorqb.blue_to_red",     text="C12: Blue → Red",     icon='FORWARD')
        layout.operator("lorqb.red_to_green",     text="C13: Red → Green",    icon='FORWARD')
        layout.operator("lorqb.green_to_yellow",  text="C14: Green → Yellow", icon='FORWARD')
        layout.operator("lorqb.yellow_to_blue",   text="C15: Yellow → Blue",  icon='FORWARD')

        # ── T-Series ──
        layout.separator()
        layout.label(text="T-Series (Diagonal Moves)")
        layout.operator("lorqb.run_t1", text="T01: Blue → Green",  icon='FORWARD')
        layout.operator("lorqb.run_t2", text="T02: Yellow → Red",  icon='FORWARD')
        layout.operator("lorqb.run_t3", text="T03: Red → Yellow",  icon='FORWARD')
        layout.operator("lorqb.run_t4", text="T04: Green → Blue",  icon='FORWARD')

_classes = [LORQB_OT_run_all, LORQB_PT_c01_panel]

###############################################################################
# SECTION 4: Register / Entry Point
###############################################################################

def register():
    for name in ["LORQB_OT_RunAll", "LORQB_PT_Panel",
                 "LORQB_OT_run_all", "LORQB_PT_c01_panel"]:
        cls = getattr(bpy.types, name, None)
        if cls:
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass
    for cls in _classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

register()
