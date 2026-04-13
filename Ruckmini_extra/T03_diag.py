import bpy

names = [
    "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
    "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
    "Ball",
]

print("\n=== T03 DIAGNOSTIC ===")
for name in names:
    obj = bpy.data.objects.get(name)
    if obj is None:
        print(f"  MISSING: {name}")
        continue
    wp = obj.matrix_world.translation
    lp = obj.location
    parent = obj.parent.name if obj.parent else "NONE"
    mpi_is_identity = obj.matrix_parent_inverse == __import__('mathutils').Matrix.Identity(4)
    print(f"  {name}")
    print(f"    parent        : {parent}")
    print(f"    world pos     : ({wp.x:.3f}, {wp.y:.3f}, {wp.z:.3f})")
    print(f"    local loc     : ({lp.x:.3f}, {lp.y:.3f}, {lp.z:.3f})")
    print(f"    mpi=identity  : {mpi_is_identity}")
print("=== END DIAGNOSTIC ===\n")
