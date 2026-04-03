import bpy
import os

SCRIPTS = os.path.dirname(bpy.data.filepath)

class LORQB_OT_RunC10(bpy.types.Operator):
    bl_idname = "lorqb.run_c10"
    bl_label  = "Run C10: Build Scene"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "C10_scene_build.py")).read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC12(bpy.types.Operator):
    bl_idname = "lorqb.run_c12"
    bl_label  = "Run C12: Blue -> Red"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "C12_blue_to_red.py")).read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC13(bpy.types.Operator):
    bl_idname = "lorqb.run_c13"
    bl_label  = "Run C13: Red -> Green"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "C13_red_to_green.py")).read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC14(bpy.types.Operator):
    bl_idname = "lorqb.run_c14"
    bl_label  = "Run C14: Green -> Yellow"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "C14_green_to_yellow.py")).read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC15(bpy.types.Operator):
    bl_idname = "lorqb.run_c15"
    bl_label  = "Run C15: Yellow -> Blue"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "C15_yellow_to_blue.py")).read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunT01(bpy.types.Operator):
    bl_idname = "lorqb.run_t01_master"
    bl_label  = "Run T01: Blue → Green"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "T01_blue_to_green.py")).read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunT02(bpy.types.Operator):
    bl_idname = "lorqb.run_t02_master"
    bl_label  = "Run T02: Yellow → Red"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "T02_yellow_to_red.py")).read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunT03(bpy.types.Operator):
    bl_idname = "lorqb.run_t03_master"
    bl_label  = "Run T03: Red → Yellow"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "T03_red_to_yellow.py")).read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunT04(bpy.types.Operator):
    bl_idname = "lorqb.run_t04_master"
    bl_label  = "Run T04: Green → Blue"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(os.path.join(SCRIPTS, "T04_green_to_blue.py")).read(), globs)
        return {'FINISHED'}

class LORQB_PT_MasterPanel(bpy.types.Panel):
    bl_label       = "LorQB Sequences"
    bl_idname      = "LORQB_PT_master_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Scene:")
        layout.operator("lorqb.run_c10", icon='SCENE_DATA')
        layout.separator()
        layout.label(text="C-Series (Sequential Rotations):")
        layout.operator("lorqb.run_c12", icon='PLAY')
        layout.operator("lorqb.run_c13", icon='PLAY')
        layout.operator("lorqb.run_c14", icon='PLAY')
        layout.operator("lorqb.run_c15", icon='PLAY')
        layout.separator()
        layout.label(text="T-Series (Diagonal Transfers):")
        layout.operator("lorqb.run_t01_master", icon='PLAY')
        layout.operator("lorqb.run_t02_master", icon='PLAY')
        layout.operator("lorqb.run_t03_master", icon='PLAY')
        layout.operator("lorqb.run_t04_master", icon='PLAY')

classes = [
    LORQB_OT_RunC10,
    LORQB_OT_RunC12,
    LORQB_OT_RunC13,
    LORQB_OT_RunC14,
    LORQB_OT_RunC15,
    LORQB_OT_RunT01,
    LORQB_OT_RunT02,
    LORQB_OT_RunT03,
    LORQB_OT_RunT04,
    LORQB_PT_MasterPanel,
]

for cls in classes:
    try:
        bpy.utils.unregister_class(cls)
    except Exception:
        pass
    bpy.utils.register_class(cls)

print("LorQB Master Panel registered — N-panel > LorQB tab.")