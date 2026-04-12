import bpy

# Registration for the panel and operators
def register():
    bpy.utils.register_class(PanelHBR)
    bpy.utils.register_class(OperatorGreen)
    bpy.utils.register_class(OperatorHRG)
    bpy.utils.register_class(OperatorTransfer)
    bpy.utils.register_class(OperatorReturn)

# Panel Definition
class PanelHBR(bpy.types.Panel):
    bl_label = "HBR Panel"
    bl_idname = "PT_HBR"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HBR'

    def draw(self, context):
        layout = self.layout
        layout.operator(OperatorGreen.bl_idname)
        layout.operator(OperatorHRG.bl_idname)
        layout.operator(OperatorTransfer.bl_idname)
        layout.operator(OperatorReturn.bl_idname)

# Operator Definitions
class OperatorGreen(bpy.types.Operator):
    bl_idname = "object.green_operator"
    bl_label = "Green Operator"

    def execute(self, context):
        # Logic for Green 90° stage
        return {'FINISHED'}

class OperatorHRG(bpy.types.Operator):
    bl_idname = "object.hrg_operator"
    bl_label = "HRG Operator"

    def execute(self, context):
        # Logic for HRG 90° stage
        return {'FINISHED'}

class OperatorTransfer(bpy.types.Operator):
    bl_idname = "object.transfer_operator"
    bl_label = "Transfer Operator"

    def execute(self, context):
        # Logic for transfer at frame 161
        return {'FINISHED'}

class OperatorReturn(bpy.types.Operator):
    bl_idname = "object.return_operator"
    bl_label = "Return Operator"

    def execute(self, context):
        # Logic for return at frame 161
        return {'FINISHED'}

# Final registration call
if __name__ == "__main__":
    register()