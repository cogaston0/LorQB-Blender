# ============================================================================
# T04_anim_probe.py  (Blender 5.0.1)
# Run AFTER T04_no_detachment.py has been loaded.
# Checks world positions of Blue, Red, Green at every 20 frames.
# Paste the full console output back to Claude.
# ============================================================================

import bpy

scene = bpy.context.scene

blue  = bpy.data.objects.get("Cube_Blue")
red   = bpy.data.objects.get("Cube_Red")
green = bpy.data.objects.get("Cube_Green")
hbr   = bpy.data.objects.get("Hinge_Blue_Red")
hrg   = bpy.data.objects.get("Hinge_Red_Green")

if not all([blue, red, green, hbr, hrg]):
    print("ERROR: missing objects")
else:
    print("\n" + "="*70)
    print("T04 ANIMATION PROBE — world positions at every 20 frames")
    print(f"{'F':>4}  {'Blue XYZ':>26}  {'Red XYZ':>26}  {'BR dist':>8}  {'RG dist':>8}  {'HRG rot Z':>10}")
    print("="*70)

    base_br = None
    base_rg = None

    for f in range(1, 241, 20):
        scene.frame_set(f)
        bpy.context.view_layer.update()

        bw = blue.matrix_world.translation
        rw = red.matrix_world.translation
        gw = green.matrix_world.translation

        d_br = (bw - rw).length
        d_rg = (rw - gw).length

        if base_br is None:
            base_br = d_br
            base_rg = d_rg

        flag_br = " DETACH!" if abs(d_br - base_br) > 1e-3 else ""
        flag_rg = " DETACH!" if abs(d_rg - base_rg) > 1e-3 else ""

        hrg_rz = hrg.rotation_euler[2]

        print(f"{f:>4}  "
              f"({bw.x:+.3f},{bw.y:+.3f},{bw.z:+.3f})  "
              f"({rw.x:+.3f},{rw.y:+.3f},{rw.z:+.3f})  "
              f"{d_br:>8.4f}{flag_br}  "
              f"{d_rg:>8.4f}{flag_rg}  "
              f"{hrg_rz:>+10.4f}")

    print("="*70)
    print(f"Base distances — BR: {base_br:.6f}  RG: {base_rg:.6f}")
    print("DETACH! = center distance changed from base (face gap opened)")
    print("="*70 + "\n")

    scene.frame_set(1)
