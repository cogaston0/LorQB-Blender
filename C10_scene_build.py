# C10_scene_build.py  — v3  (Blender 5.0.1 — Reset to Base panel added)
import bpy

################################################################################
# SECTION 1: Clear scene helper
################################################################################
def clear_scene():
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    print("=== Scene cleared ===")

################################################################################
# SECTION 2: Function to create a hollow cube with circular openings
#
# Hole configuration (from original PDF dark bars):
#   Blue   (top-right):  2 holes — top + LEFT side  (faces Yellow across top row)
#   Yellow (top-left):   2 holes — top + RIGHT side (faces Blue across top row)
#   Red    (bottom-right): 1 hole — top only
#   Green  (bottom-left):  1 hole — top only
################################################################################
def create_hollow_cube(location, color, side_hole_direction=None):
    """
    side_hole_direction:
        None       = no side hole (Red, Green)
        'left'     = side hole on LEFT face  (Blue — faces Yellow)
        'right'    = side hole on RIGHT face (Yellow — faces Blue)
    """
    # Adjust location so cube bottom face sits on the ground
    location = (location[0], location[1], location[2] + 0.5)

    # --- Outer cube ---
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    outer_cube = bpy.context.object

    # --- Inner cube for hollow effect ---
    bpy.ops.mesh.primitive_cube_add(size=0.955, location=location)
    inner_cube = bpy.context.object

    bool_mod = outer_cube.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = inner_cube
    bpy.context.view_layer.objects.active = outer_cube
    bpy.ops.object.modifier_apply(modifier="Boolean")
    bpy.data.objects.remove(inner_cube)

    # --- Top hole ---
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.3, depth=0.6,
        location=(location[0], location[1], location[2] + 0.5)
    )
    top_cylinder = bpy.context.object
    # Top cylinder is vertical by default — no rotation needed

    bool_mod_top = outer_cube.modifiers.new(name="Boolean_Top_Hole", type='BOOLEAN')
    bool_mod_top.operation = 'DIFFERENCE'
    bool_mod_top.object = top_cylinder
    bpy.context.view_layer.objects.active = outer_cube
    bpy.ops.object.modifier_apply(modifier="Boolean_Top_Hole")
    bpy.data.objects.remove(top_cylinder)

    # --- Side hole (Blue and Yellow only) ---
    if side_hole_direction == 'left':
        # Blue: side hole on LEFT face (negative X side) — faces Yellow
        side_location = (location[0] - 0.5, location[1], location[2])
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.3, depth=0.6,
            location=side_location
        )
        side_cylinder = bpy.context.object
        side_cylinder.rotation_euler[1] = 1.5708  # Rotate 90° around Y — aligns along X axis

    elif side_hole_direction == 'right':
        # Yellow: side hole on RIGHT face (positive X side) — faces Blue
        side_location = (location[0] + 0.5, location[1], location[2])
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.3, depth=0.6,
            location=side_location
        )
        side_cylinder = bpy.context.object
        side_cylinder.rotation_euler[1] = 1.5708  # Rotate 90° around Y — aligns along X axis

    if side_hole_direction in ('left', 'right'):
        bool_mod_side = outer_cube.modifiers.new(name="Boolean_Side_Hole", type='BOOLEAN')
        bool_mod_side.operation = 'DIFFERENCE'
        bool_mod_side.object = side_cylinder
        bpy.context.view_layer.objects.active = outer_cube
        bpy.ops.object.modifier_apply(modifier="Boolean_Side_Hole")
        bpy.data.objects.remove(side_cylinder)

    # --- Material ---
    mat = bpy.data.materials.new(name=f"Mat_{outer_cube.name}")
    mat.use_nodes = True
    mat.diffuse_color = (*color, 0.35)  # Viewport display color with transparency
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Alpha"].default_value = 0.35
    mat.blend_method = 'HASHED'
    if hasattr(mat, "surface_render_method"):
        try:
            mat.surface_render_method = 'DITHERED'
        except Exception:
            pass
    if hasattr(mat, "shadow_method"):
        try:
            mat.shadow_method = 'NONE'
        except Exception:
            pass
    outer_cube.data.materials.append(mat)

    return outer_cube

################################################################################
# SECTION 3: Build full scene
################################################################################
def build_scene():
    clear_scene()

    locations = [
        (-0.51, -0.51, 0),  # Bottom-left  (Green)
        ( 0.51, -0.51, 0),  # Bottom-right (Red)
        (-0.51,  0.51, 0),  # Top-left     (Yellow)
        ( 0.51,  0.51, 0)   # Top-right    (Blue)
    ]

    blue_color   = (0.0, 0.0, 1.0)  # Blue   — top-right
    yellow_color = (1.0, 1.0, 0.0)  # Yellow — top-left
    green_color  = (0.0, 1.0, 0.0)  # Green  — bottom-left
    red_color    = (1.0, 0.0, 0.0)  # Red    — bottom-right

    cubes = {}
    for location in locations:
        if location[0] > 0 and location[1] > 0:       # Blue — top-right
            cubes['blue'] = create_hollow_cube(location, blue_color, side_hole_direction='left')
            cubes['blue'].name = "Cube_Blue"
        elif location[0] < 0 and location[1] > 0:     # Yellow — top-left
            cubes['yellow'] = create_hollow_cube(location, yellow_color, side_hole_direction='right')
            cubes['yellow'].name = "Cube_Yellow"
        elif location[0] < 0 and location[1] < 0:     # Green — bottom-left
            cubes['green'] = create_hollow_cube(location, green_color, side_hole_direction=None)
            cubes['green'].name = "Cube_Green"
        elif location[0] > 0 and location[1] < 0:     # Red — bottom-right
            cubes['red'] = create_hollow_cube(location, red_color, side_hole_direction=None)
            cubes['red'].name = "Cube_Red"

    # ── Ball ────────────────────────────────────────────────────────────────
    if 'blue' in cubes:
        cube            = cubes['blue']
        cube_dimensions = cube.dimensions
        cube_location   = cube.location
        ball_radius     = 0.25

        bottom_center = (
            cube_location.x,
            cube_location.y,
            cube_location.z - (cube_dimensions.z / 2) + ball_radius * 0.99
        )
        bpy.ops.mesh.primitive_uv_sphere_add(radius=ball_radius, location=bottom_center)
        ball = bpy.context.object
        ball.name = "Ball"

    # ── Hinges ──────────────────────────────────────────────────────────────
    def _create_hinge_visual(location, axis, name, hinge_empty,
                             cube_pos, cube_neg):
        # Real door-hinge geometry:
        #   - horizontal pin (cylinder) parented to the hinge empty (rotates with it)
        #   - two flat leaves, each parented to its respective cube
        # `cube_pos` is the cube on the +offset side, `cube_neg` on the -offset side.
        pin_radius   = 0.025
        pin_length   = 0.5      # along the seam
        leaf_long    = 0.5      # match pin length exactly so leaves align with pin
        leaf_wide    = 0.12     # extends out onto a cube's top face
        leaf_thick   = 0.015    # thin — lies flat on the cube top

        # Shared white material for pin + leaves
        mat_name = name + "_Mat"
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(name=mat_name)
            mat.diffuse_color = (1.0, 1.0, 1.0, 1.0)

        # ── Pin: 4 short knuckle segments along the hinge axis with gaps ────
        n_knuckles = 4
        seg_len = (pin_length / n_knuckles) * 0.95  # 95% segment, 5% gap
        gap     = (pin_length - n_knuckles * seg_len) / (n_knuckles - 1)

        for i in range(n_knuckles):
            # Center of segment i along the pin span (centered on `location`)
            t = -pin_length / 2 + seg_len / 2 + i * (seg_len + gap)
            if axis == 'X':
                seg_loc = (location[0] + t, location[1], location[2])
            else:                                # 'Y'
                seg_loc = (location[0], location[1] + t, location[2])

            bpy.ops.mesh.primitive_cylinder_add(radius=pin_radius, depth=seg_len,
                                                location=seg_loc)
            seg = bpy.context.object
            seg.name = f"{name}_Pin_{i+1}"
            # Default cylinder runs along Z. Rotate to match the hinge axis.
            if axis == 'X':
                seg.rotation_euler[1] = 1.5708
            else:
                seg.rotation_euler[0] = 1.5708
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            seg.data.materials.append(mat)

            bpy.context.view_layer.update()
            mw = seg.matrix_world.copy()
            seg.parent = hinge_empty
            seg.matrix_parent_inverse = hinge_empty.matrix_world.inverted()
            seg.matrix_world = mw

        # ── Two leaves: each parented to its own cube ───────────────────────
        # Z-lift so leaves sit on top of cube faces (cube tops at Z=1).
        z_lift = leaf_thick / 2  # bottom of leaf flush with cube top
        if axis == 'Y':
            # Pin along Y; leaves extend ±X. cube_pos at +X, cube_neg at -X.
            leaf_size = (leaf_wide, leaf_long, leaf_thick)
            leaf_specs = [
                (( leaf_wide / 2, 0, z_lift), cube_pos),
                ((-leaf_wide / 2, 0, z_lift), cube_neg),
            ]
        else:                              # 'X'
            # Pin along X; leaves extend ±Y. cube_pos at +Y, cube_neg at -Y.
            leaf_size = (leaf_long, leaf_wide, leaf_thick)
            leaf_specs = [
                ((0,  leaf_wide / 2, z_lift), cube_pos),
                ((0, -leaf_wide / 2, z_lift), cube_neg),
            ]

        for i, (off, cube_owner) in enumerate(leaf_specs):
            leaf_loc = (location[0] + off[0], location[1] + off[1], location[2] + off[2])
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=leaf_loc)
            leaf = bpy.context.object
            leaf.name = f"{name}_Leaf_{i+1}"
            leaf.scale = leaf_size
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            # Leaf takes the color of the cube it's mounted on.
            cube_mat = (cube_owner.data.materials[0]
                        if cube_owner.data.materials else None)
            if cube_mat is not None:
                leaf.data.materials.append(cube_mat)
            else:
                leaf.data.materials.append(mat)
            bpy.context.view_layer.update()
            mw_leaf = leaf.matrix_world.copy()
            leaf.parent = cube_owner
            leaf.matrix_parent_inverse = cube_owner.matrix_world.inverted()
            leaf.matrix_world = mw_leaf

    # Hinge axis = direction the pin runs (parallel to the shared cube edge).
    # cube_pos / cube_neg = which cube each leaf attaches to.
    # axis='X': pin along X, leaves extend ±Y → cube_pos at +Y, cube_neg at -Y.
    # axis='Y': pin along Y, leaves extend ±X → cube_pos at +X, cube_neg at -X.
    #   HBR at (+0.51, 0, 1): axis X. +Y = Blue, -Y = Red.
    #   HRG at (0, -0.51, 1): axis Y. +X = Red,  -X = Green.
    #   HGY at (-0.51, 0, 1): axis X. +Y = Yellow, -Y = Green.
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.51, 0, 1), scale=(0.1, 0.1, 0.1))
    hinge_1 = bpy.context.object
    hinge_1.name = "Hinge_Blue_Red"
    _create_hinge_visual((0.51, 0, 1), 'X', "Hinge_Blue_Red", hinge_1,
                         cubes['blue'], cubes['red'])

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, -0.51, 1), scale=(0.1, 0.1, 0.1))
    hinge_2 = bpy.context.object
    hinge_2.name = "Hinge_Red_Green"
    _create_hinge_visual((0, -0.51, 1), 'Y', "Hinge_Red_Green", hinge_2,
                         cubes['red'], cubes['green'])

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-0.51, 0, 1), scale=(0.1, 0.1, 0.1))
    hinge_3 = bpy.context.object
    hinge_3.name = "Hinge_Green_Yellow"
    _create_hinge_visual((-0.51, 0, 1), 'X', "Hinge_Green_Yellow", hinge_3,
                         cubes['yellow'], cubes['green'])

    # ── Cube pivots → hinge locations ───────────────────────────────────────
    bpy.context.view_layer.objects.active = cubes['blue']
    cubes['blue'].select_set(True)
    bpy.context.scene.cursor.location = (0.51, 0, 1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    cubes['blue'].select_set(False)

    bpy.context.view_layer.objects.active = cubes['red']
    cubes['red'].select_set(True)
    bpy.context.scene.cursor.location = (0, -0.51, 1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    cubes['red'].select_set(False)

    bpy.context.view_layer.objects.active = cubes['green']
    cubes['green'].select_set(True)
    bpy.context.scene.cursor.location = (-0.51, 0, 1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    cubes['green'].select_set(False)

    bpy.context.view_layer.objects.active = cubes['yellow']
    cubes['yellow'].select_set(True)
    bpy.context.scene.cursor.location = (-0.51, 0, 1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    cubes['yellow'].select_set(False)

    # ── Seats ───────────────────────────────────────────────────────────────
    seat_config = {
        'blue':   ( 0.51,  0.51, 0.07),
        'red':    ( 0.51, -0.51, 0.07),
        'green':  (-0.51, -0.51, 0.07),
        'yellow': (-0.51,  0.51, 0.07),
    }

    seats = {}
    for color_key, seat_loc in seat_config.items():
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=seat_loc, scale=(0.05, 0.05, 0.05))
        seat = bpy.context.object
        seat.name = f"Seat_{color_key.capitalize()}"
        seat.location.x = seat_loc[0]
        seat.location.y = seat_loc[1]
        seat.location.z = seat_loc[2]
        seats[color_key] = seat

    print("Seat empties created:")
    for key, seat in seats.items():
        print(f"  {seat.name} @ {tuple(round(v, 4) for v in seat.location)}")

    # ── System Rotator (permanent pivot — never delete, never recreate in T04) ──
    sr = bpy.data.objects.get("System_Rotator")
    if sr is None:
        sr = bpy.data.objects.new("System_Rotator", None)
        sr.empty_display_type = 'PLAIN_AXES'
        bpy.context.scene.collection.objects.link(sr)
    sr.location = (0, 0, 1)
    sr.rotation_euler = (0, 0, 0)
    print(f"  {sr.name} @ {tuple(round(v, 4) for v in sr.location)}")

    # ── Force viewport shading to show material colors ───────────────────────
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type       = 'SOLID'
                    space.shading.color_type = 'MATERIAL'

    print("=== LorQB Scene Setup Complete ===")
    print("Chain (clockwise): Blue — Red — Green — Yellow")
    print("Blue   (top-right):  2 holes — top + LEFT  side (faces Yellow)")
    print("Yellow (top-left):   2 holes — top + RIGHT side (faces Blue)")
    print("Red    (bottom-right): 1 hole — top only")
    print("Green  (bottom-left):  1 hole — top only")
    print("Hinges:")
    print("  Hinge_Blue_Red     @ ( 0.51,  0,    1) — right edge")
    print("  Hinge_Red_Green    @ ( 0,    -0.51, 1) — bottom edge")
    print("  Hinge_Green_Yellow @ (-0.51,  0,    1) — left edge")
    print("Cube pivots set correctly to their respective hinges.")

################################################################################
# SECTION 4: UI Panel
################################################################################
class LORQB_OT_reset_c10(bpy.types.Operator):
    bl_idname      = "lorqb.reset_c10"
    bl_label       = "Reset to Base"
    bl_description = "Clear and rebuild the canonical base layout"

    def execute(self, context):
        build_scene()
        self.report({'INFO'}, "Reset to base complete")
        return {'FINISHED'}


class LORQB_OT_build_c10(bpy.types.Operator):
    bl_idname      = "lorqb.build_c10"
    bl_label       = "Build Scene (C10)"
    bl_description = "Clear and rebuild the full LorQB scene"

    def execute(self, context):
        build_scene()
        self.report({'INFO'}, "Scene built")
        return {'FINISHED'}


class LORQB_PT_c10_panel(bpy.types.Panel):
    bl_label       = "LorQB — C10"
    bl_idname      = "LORQB_PT_c10_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout
        layout.operator("lorqb.reset_c10", text="Reset to Base", icon='LOOP_BACK')
        layout.separator()
        layout.operator("lorqb.build_c10", text="Build Scene (C10)", icon='SCENE_DATA')


_classes = [LORQB_OT_reset_c10, LORQB_OT_build_c10, LORQB_PT_c10_panel]

################################################################################
# SECTION 5: Register / Entry Point
################################################################################
def register():
    for cls in _classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

register()
build_scene()
