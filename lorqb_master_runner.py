# ============================================================================
# lorqb_master_runner.py  (Blender 5.0.1)
# LorQB Master Runner — launches individual Cx animation scripts from one panel
# Load this script in Blender's Text Editor and run it to register the panel.
# Update SCRIPTS to point to the folder containing the Cx script files.
# ============================================================================

import bpy

# *** UPDATE THIS PATH to the folder on your machine that contains C12–C15 scripts ***
SCRIPTS = r"C:\rukmini_ai_loop\scripts"

class LORQB_OT_RunC12(bpy.types.Operator):
    bl_idname = "lorqb.run_c12"
    bl_label  = "Run C12: Blue -> Red"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C12_blue_to_red.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC13(bpy.types.Operator):
    bl_idname = "lorqb.run_c13"
    bl_label  = "Run C13: Red -> Green"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C13_red_to_green.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC14(bpy.types.Operator):
    bl_idname = "lorqb.run_c14"
    bl_label  = "Run C14: Green -> Yellow"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C14_green_to_yellow.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC15(bpy.types.Operator):
    bl_idname = "lorqb.run_c15"
    bl_label  = "Run C15: Yellow -> Blue"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C15_yellow_to_blue.py").read(), globs)
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