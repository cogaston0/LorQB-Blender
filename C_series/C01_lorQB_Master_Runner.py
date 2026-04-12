import bpy
import os

SCRIPTS_ROOT = r"C:\rukmini_ai_loop\scripts"
C_DIR = os.path.join(SCRIPTS_ROOT, "C_series")

def run_c_script(filename):
    import bpy as _bpy
    globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
    with open(os.path.join(C_DIR, filename), "r", encoding="utf-8") as f:
        exec(f.read(), globs)

class LORQB_OT_RunC12(bpy.types.Operator):
    bl_idname = "lorqb.run_c12"
    bl_label  = "Run C12: Blue -> Red"
    def execute(self, context):
        run_c_script("C12_blue_to_red.py")
        return {'FINISHED'}

class LORQB_OT_RunC13(bpy.types.Operator):
    bl_idname = "lorqb.run_c13"
    bl_label  = "Run C13: Red -> Green"
    def execute(self, context):
        run_c_script("C13_red_to_green.py")
        return {'FINISHED'}

class LORQB_OT_RunC14(bpy.types.Operator):
    bl_idname = "lorqb.run_c14"
    bl_label  = "Run C14: Green -> Yellow"
    def execute(self, context):
        run_c_script("C14_green_to_yellow.py")
        return {'FINISHED'}

class LORQB_OT_RunC15(bpy.types.Operator):
    bl_idname = "lorqb.run_c15"
    bl_label  = "Run C15: Yellow -> Blue"
    def execute(self, context):
        run_c_script("C15_yellow_to_blue.py")
        return {'FINISHED'}

class LORQB_PT_MasterPanel(bpy.types.Panel):
    bl_label       = "LorQB Sequences"
    bl_idname      = "LORQB_PT_master_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Run Sequences Individually:")
        layout.separator()
        layout.operator("lorqb.run_c12", icon='PLAY')
        layout.operator("lorqb.run_c13", icon='PLAY')
        layout.operator("lorqb.run_c14", icon='PLAY')
        layout.operator("lorqb.run_c15", icon='PLAY')

classes = [
    LORQB_OT_RunC12,
    LORQB_OT_RunC13,
    LORQB_OT_RunC14,
    LORQB_OT_RunC15,
    LORQB_PT_MasterPanel,
]

for cls in classes:
    try:
        bpy.utils.unregister_class(cls)
    except Exception:
        pass
    bpy.utils.register_class(cls)

print("LorQB Master Panel registered — N-panel > LorQB tab.")
