import bpy
import mathutils

print("\n=== PARENT ASSIGNMENT TEST ===")

hrg    = bpy.data.objects.get("Hinge_Red_Green")
green  = bpy.data.objects.get("Cube_Green")

if not hrg or not green:
    print("ERROR: Objects not found — run C10 first")
else:
    # Step 1: unparent green
    green.parent = None
    bpy.context.view_layer.update()
    print(f"After unparent  — green.parent: {green.parent}")

    # Step 2: try to set parent
    green.parent = hrg
    green.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    green.location = (-0.51, 0.51, 0.0)
    bpy.context.view_layer.update()
    print(f"After parent set — green.parent: {green.parent}")
    wp = green.matrix_world.translation
    print(f"Green world pos: ({wp.x:.3f}, {wp.y:.3f}, {wp.z:.3f})")
    print(f"Expected:        (-0.510,  0.000,  1.000)")

print("=== END TEST ===\n")
