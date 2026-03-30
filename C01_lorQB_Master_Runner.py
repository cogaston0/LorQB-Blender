import bpy

SCRIPTS = r"C:\rukmini_ai_loop\scripts"

# ── Setup ────────────────────────────────────────────────────────────────────

class LORQB_OT_RunC10(bpy.types.Operator):
    bl_idname = "lorqb.run_c10"
    bl_label  = "C10: Build Scene"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C10_scene_build.py").read(), globs)
        return {'FINISHED'}

# ── C-Series ─────────────────────────────────────────────────────────────────

class LORQB_OT_RunC12(bpy.types.Operator):
    bl_idname = "lorqb.run_c12"
    bl_label  = "C12: Blue → Red"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C12_blue_to_red.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC13(bpy.types.Operator):
    bl_idname = "lorqb.run_c13"
    bl_label  = "C13: Red → Green"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C13_red_to_green.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC14(bpy.types.Operator):
    bl_idname = "lorqb.run_c14"
    bl_label  = "C14: Green → Yellow"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C14_green_to_yellow.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunC15(bpy.types.Operator):
    bl_idname = "lorqb.run_c15"
    bl_label  = "C15: Yellow → Blue"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\C15_yellow_to_blue.py").read(), globs)
        return {'FINISHED'}

# ── T-Series ─────────────────────────────────────────────────────────────────

class LORQB_OT_RunT01(bpy.types.Operator):
    bl_idname = "lorqb.run_t01"
    bl_label  = "T01: Blue → Green"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\T01_blue_to_green.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunT02(bpy.types.Operator):
    bl_idname = "lorqb.run_t02"
    bl_label  = "T02: Yellow → Red"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\T02_yellow_to_red.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunT03(bpy.types.Operator):
    bl_idname = "lorqb.run_t03"
    bl_label  = "T03: Red → Yellow"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\T03_red_to_yellow.py").read(), globs)
        return {'FINISHED'}

class LORQB_OT_RunT04(bpy.types.Operator):
    bl_idname = "lorqb.run_t04"
    bl_label  = "T04: Green → Blue"
    def execute(self, context):
        import bpy as _bpy
        globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
        exec(open(SCRIPTS + r"\T04_green_to_blue.py").read(), globs)
        return {'FINISHED'}

# ── Panel ─────────────────────────────────────────────────────────────────────

class LORQB_PT_MasterPanel(bpy.types.Panel):
    bl_label       = "LorQB Sequences"
    bl_idname      = "LORQB_PT_master_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout

        layout.label(text="Setup:")
        layout.operator("lorqb.run_c10", icon='SCENE_DATA')
        layout.separator()

        layout.label(text="C-Series (Main Loop):")
        layout.operator("lorqb.run_c12", icon='PLAY')
        layout.operator("lorqb.run_c13", icon='PLAY')
        layout.operator("lorqb.run_c14", icon='PLAY')
        layout.operator("lorqb.run_c15", icon='PLAY')
        layout.separator()

        layout.label(text="T-Series (Diagonal):")
        layout.operator("lorqb.run_t01", icon='PLAY')
        layout.operator("lorqb.run_t02", icon='PLAY')
        layout.operator("lorqb.run_t03", icon='PLAY')
        layout.operator("lorqb.run_t04", icon='PLAY')

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
