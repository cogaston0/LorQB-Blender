# Movement registry — single source of truth for every LorQB movement.
# Maps movement_id -> MovementSpec describing the script, skills, geometry, and timing.

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MovementSpec:
    movement_id: str        # registry key, matches lieutenant_class.movement_id
    label: str              # human-readable (used in UI and logs)
    script_file: str        # filename inside C_series/
    required_skills: tuple  # skill tags this movement exercises

    # geometry
    hinge_name: str
    rot_axis: str           # "X", "Y", or "Z"
    rot_sign: float         # +1.0 or -1.0
    source_cube: str
    target_cube: str

    # timing
    frame_start: int
    frame_end: int
    transfer_frame: int     # frame where ball latch switches (F_HOLD → F_SWAP)

    # fallback — safer alternate movement_ids Master may substitute on low confidence
    alternate_ids: tuple = field(default=())


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

MOVEMENT_REGISTRY: dict = {

    "C12_blue_to_red": MovementSpec(
        movement_id    = "C12_blue_to_red",
        label          = "Blue → Red",
        script_file    = "C12_blue_to_red.py",
        required_skills= ("hinge_x_rotation", "constraint_transfer", "seat_creation"),
        hinge_name     = "Hinge_Blue_Red",
        rot_axis       = "X",
        rot_sign       = +1.0,
        source_cube    = "Cube_Blue",
        target_cube    = "Cube_Red",
        frame_start    = 1,
        frame_end      = 240,
        transfer_frame = 120,
    ),

    "C13_red_to_green": MovementSpec(
        movement_id    = "C13_red_to_green",
        label          = "Red → Green",
        script_file    = "C13_red_to_green.py",
        required_skills= ("hinge_y_rotation", "constraint_transfer", "seat_creation"),
        hinge_name     = "Hinge_Red_Green",
        rot_axis       = "Y",
        rot_sign       = -1.0,
        source_cube    = "Cube_Red",
        target_cube    = "Cube_Green",
        frame_start    = 241,
        frame_end      = 480,
        transfer_frame = 360,
    ),

    "C14_green_to_yellow": MovementSpec(
        movement_id    = "C14_green_to_yellow",
        label          = "Green → Yellow",
        script_file    = "C14_green_to_yellow.py",
        required_skills= ("hinge_x_rotation", "constraint_transfer", "seat_creation",
                          "passive_rider"),
        hinge_name     = "Hinge_Green_Yellow",
        rot_axis       = "X",
        rot_sign       = +1.0,
        source_cube    = "Cube_Green",
        target_cube    = "Cube_Yellow",
        frame_start    = 481,
        frame_end      = 720,
        transfer_frame = 600,
    ),

    "C15_yellow_to_blue": MovementSpec(
        movement_id    = "C15_yellow_to_blue",
        label          = "Yellow → Blue",
        script_file    = "C15_yellow_to_blue.py",
        required_skills= ("hinge_y_rotation", "constraint_transfer", "seat_creation",
                          "passive_rider", "compound_swing"),
        hinge_name     = "Hinge_Red_Green",  # Green+Yellow swing as one unit
        rot_axis       = "Y",
        rot_sign       = +1.0,
        source_cube    = "Cube_Yellow",
        target_cube    = "Cube_Blue",
        frame_start    = 720,
        frame_end      = 960,
        transfer_frame = 840,
    ),
}

# Canonical Level 1 execution order
LEVEL1_SEQUENCE = (
    "C12_blue_to_red",
    "C13_red_to_green",
    "C14_green_to_yellow",
    "C15_yellow_to_blue",
)

# All scene objects every movement depends on
REQUIRED_SCENE_OBJECTS = (
    "Ball",
    "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
    "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_movement(movement_id: str):
    """Return MovementSpec or None."""
    return MOVEMENT_REGISTRY.get(movement_id)


def movements_with_skill(skill: str) -> list:
    """Return all MovementSpecs that list the given skill."""
    return [m for m in MOVEMENT_REGISTRY.values() if skill in m.required_skills]


def skill_inventory() -> set:
    """Return the union of all required_skills across all movements."""
    skills = set()
    for spec in MOVEMENT_REGISTRY.values():
        skills.update(spec.required_skills)
    return skills
