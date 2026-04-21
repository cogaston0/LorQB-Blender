# C01 — LorQB Master Controller
#
# Architecture:
#   Master (this file)
#     └── LorQBController         orchestrates lieutenant lifecycle
#           ├── BlueToRedLieutenant    (C12)
#           ├── RedToGreenLieutenant   (C13)
#           ├── GreenToYellowLieutenant(C14)
#           └── YellowToBlueLieutenant (C15)
#
# Each lieutenant exposes: get_confidence → prepare → execute → verify → rollback
# Master selects, validates, runs, and handles failures per the failure taxonomy.
#
# Path resolution: SCRIPTS_ROOT is auto-detected from this file's location so
# the add-on works on any machine without editing hardcoded paths.

import bpy
import os

# ---------------------------------------------------------------------------
# Path resolution — works whether run from disk or Blender text-block
# ---------------------------------------------------------------------------

def _resolve_c_dir() -> str:
    """Return absolute path to the C_series folder."""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(here) == "C_series":
            return here
        candidate = os.path.join(here, "C_series")
        if os.path.isdir(candidate):
            return candidate
    except (NameError, TypeError):
        pass
    # Fallback: scan bpy.data.filepath (Blender's open .blend directory)
    blend_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else ""
    for root in (blend_dir, os.path.expanduser("~")):
        candidate = os.path.join(root, "C_series")
        if os.path.isdir(candidate):
            return candidate
    return ""


C_DIR = _resolve_c_dir()

# ---------------------------------------------------------------------------
# Import lieutenant infrastructure (inline-exec friendly — no package needed)
# ---------------------------------------------------------------------------

def _load_module(filename: str):
    """exec a module file into a fresh dict and return it."""
    path = os.path.join(C_DIR, filename)
    globs: dict = {"bpy": bpy, "__file__": path}
    with open(path, "r", encoding="utf-8") as f:
        exec(f.read(), globs)
    return globs


try:
    # Prefer package-style import when running as an add-on
    from .lieutenant_api import (
        FailureType, Failure, ConfidenceScore,
        PrepareResult, ExecuteResult, VerifyResult,
    )
    from .movement_registry import MOVEMENT_REGISTRY, LEVEL1_SEQUENCE, get_movement
    from .lieutenants import build_all

except ImportError:
    # Fallback for exec-from-disk (no package context)
    _api_mod  = _load_module("lieutenant_api.py")
    _reg_mod  = _load_module("movement_registry.py")

    # Patch .lieutenant_api and .movement_registry into _reg_mod so lieutenants
    # can resolve their relative imports at exec time
    import sys, types
    _pkg = types.ModuleType("lorqb_runtime")
    _pkg.lieutenant_api   = types.ModuleType("lorqb_runtime.lieutenant_api")
    _pkg.movement_registry = types.ModuleType("lorqb_runtime.movement_registry")
    vars(_pkg.lieutenant_api).update(_api_mod)
    vars(_pkg.movement_registry).update(_reg_mod)
    sys.modules.setdefault("lorqb_runtime", _pkg)
    sys.modules.setdefault("lorqb_runtime.lieutenant_api",   _pkg.lieutenant_api)
    sys.modules.setdefault("lorqb_runtime.movement_registry", _pkg.movement_registry)

    # Now exec lieutenants with the patched namespace
    _lt_path = os.path.join(C_DIR, "lieutenants.py")
    _lt_src  = open(_lt_path, "r", encoding="utf-8").read()
    _lt_src  = _lt_src.replace("from .lieutenant_api import",
                                "from lorqb_runtime.lieutenant_api import")
    _lt_src  = _lt_src.replace("from .movement_registry import",
                                "from lorqb_runtime.movement_registry import")
    _lt_globs: dict = {"bpy": bpy, "__file__": _lt_path}
    exec(_lt_src, _lt_globs)

    FailureType  = _api_mod["FailureType"]
    MOVEMENT_REGISTRY = _reg_mod["MOVEMENT_REGISTRY"]
    LEVEL1_SEQUENCE   = _reg_mod["LEVEL1_SEQUENCE"]
    get_movement      = _reg_mod["get_movement"]
    build_all         = _lt_globs["build_all"]


# ---------------------------------------------------------------------------
# LorQBController — Master orchestrator
# ---------------------------------------------------------------------------

class LorQBController:
    """Runs lieutenant lifecycle for one movement or a full sequence.

    Instantiate once; lieutenants are built lazily on first access.
    """

    def __init__(self, c_dir: str):
        self._c_dir = c_dir
        self._lieutenants: dict = {}  # movement_id -> lieutenant instance

    @property
    def lieutenants(self) -> dict:
        if not self._lieutenants:
            self._lieutenants = build_all(self._c_dir)
        return self._lieutenants

    # --- Single movement ---

    def run_movement(self, context, movement_id: str) -> bool:
        lt = self.lieutenants.get(movement_id)
        if lt is None:
            print(f"[Master] Unknown movement_id: {movement_id}")
            return False

        spec = get_movement(movement_id)
        print(f"\n{'='*60}")
        print(f"[Master] Starting: {lt.label} ({movement_id})")

        # 1. Confidence check
        confidence = lt.get_confidence(context)
        print(f"[Master] {confidence.summary()}")
        if not confidence.is_safe():
            # Check for a safer alternate
            for alt_id in (spec.alternate_ids if spec else ()):
                alt_conf = self.lieutenants[alt_id].get_confidence(context)
                if alt_conf.is_safe():
                    print(f"[Master] Low confidence — substituting safer alternate: {alt_id}")
                    return self.run_movement(context, alt_id)
            print(f"[Master] WARNING: Confidence {confidence.value:.2f} below threshold; proceeding anyway.")

        # 2. Prepare
        prep = lt.prepare(context)
        if not prep.success:
            for f in prep.failures:
                print(f"[Master] PREPARE FAILED ({f.failure_type.value}): {f.message}")
            return False

        # 3. Execute
        result = lt.execute(context)
        if not result.success:
            for f in result.failures:
                print(f"[Master] EXECUTE FAILED ({f.failure_type.value}): {f.message}")
            print(f"[Master] Rolling back...")
            lt.rollback(context)
            return False

        # 4. Verify
        verify = lt.verify(context)
        if not verify.passed:
            for f in verify.failures:
                print(f"[Master] VERIFY FAILED ({f.failure_type.value}): {f.message}")
            print(f"[Master] Rolling back after failed verification...")
            lt.rollback(context)
            return False

        checks_summary = ", ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in verify.checks.items())
        print(f"[Master] {lt.label} complete. Checks: {checks_summary}")
        return True

    # --- Full Level-1 sequence ---

    def run_level1_sequence(self, context) -> bool:
        print("\n" + "="*60)
        print("[Master] Running full Level-1 sequence...")
        for movement_id in LEVEL1_SEQUENCE:
            ok = self.run_movement(context, movement_id)
            if not ok:
                print(f"[Master] Sequence aborted at {movement_id}.")
                return False
        print("[Master] Level-1 sequence complete.")
        return True

    # --- Confidence report ---

    def print_confidence_report(self, context):
        print("\n--- LorQB Confidence Report ---")
        for movement_id in LEVEL1_SEQUENCE:
            lt = self.lieutenants.get(movement_id)
            if lt:
                score = lt.get_confidence(context)
                print(f"  {score.summary()}")
        print("-------------------------------\n")


# Singleton controller — recreated each time the script is exec'd
_controller = LorQBController(C_DIR)


# ---------------------------------------------------------------------------
# Blender Operators
# ---------------------------------------------------------------------------

class LORQB_OT_RunMovement(bpy.types.Operator):
    """Run a single movement by its registry ID."""
    bl_idname  = "lorqb.run_movement"
    bl_label   = "Run Movement"
    bl_options = {'REGISTER', 'UNDO'}

    movement_id: bpy.props.StringProperty(name="Movement ID", default="")

    def execute(self, context):
        ok = _controller.run_movement(context, self.movement_id)
        if ok:
            spec = get_movement(self.movement_id)
            self.report({'INFO'}, f"{spec.label if spec else self.movement_id} complete")
        else:
            self.report({'ERROR'}, f"{self.movement_id} failed — see console")
        return {'FINISHED'}


class LORQB_OT_RunLevel1(bpy.types.Operator):
    """Run the full Level-1 sequence (C12 → C13 → C14 → C15)."""
    bl_idname  = "lorqb.run_level1"
    bl_label   = "Run Level-1 Sequence"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ok = _controller.run_level1_sequence(context)
        if ok:
            self.report({'INFO'}, "Level-1 sequence complete")
        else:
            self.report({'ERROR'}, "Level-1 sequence failed — see console")
        return {'FINISHED'}


class LORQB_OT_ConfidenceReport(bpy.types.Operator):
    """Print per-movement confidence scores to the system console."""
    bl_idname = "lorqb.confidence_report"
    bl_label  = "Confidence Report"

    def execute(self, context):
        _controller.print_confidence_report(context)
        self.report({'INFO'}, "Confidence report printed to console")
        return {'FINISHED'}


class LORQB_OT_ResetScene(bpy.types.Operator):
    """Reset scene to canonical state (delegates to any lieutenant's rollback)."""
    bl_idname  = "lorqb.reset_scene"
    bl_label   = "Reset Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        lt = list(_controller.lieutenants.values())[0]
        lt.rollback(context)
        self.report({'INFO'}, "Scene reset to canonical state")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# UI Panel
# ---------------------------------------------------------------------------

class LORQB_PT_MasterPanel(bpy.types.Panel):
    bl_label       = "LorQB Master"
    bl_idname      = "LORQB_PT_master_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LorQB'

    def draw(self, context):
        layout = self.layout

        # Full sequence button
        row = layout.row()
        row.scale_y = 1.4
        row.operator("lorqb.run_level1", icon='PLAY')
        layout.separator()

        # Individual movements
        layout.label(text="Individual Movements:")
        for movement_id in LEVEL1_SEQUENCE:
            spec = get_movement(movement_id)
            if spec:
                op = layout.operator("lorqb.run_movement", text=spec.label, icon='FORWARD')
                op.movement_id = movement_id

        layout.separator()
        layout.operator("lorqb.confidence_report", icon='INFO')
        layout.operator("lorqb.reset_scene",       icon='LOOP_BACK')


# ---------------------------------------------------------------------------
# Register / Unregister
# ---------------------------------------------------------------------------

_CLASSES = [
    LORQB_OT_RunMovement,
    LORQB_OT_RunLevel1,
    LORQB_OT_ConfidenceReport,
    LORQB_OT_ResetScene,
    LORQB_PT_MasterPanel,
]


def _unregister_lorqb():
    for name in dir(bpy.types):
        cls = getattr(bpy.types, name, None)
        if cls and "lorqb" in getattr(cls, "bl_idname", "").lower():
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass


def register():
    _unregister_lorqb()
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    print("\n" + "="*60)
    print("LorQB Master Controller registered.")
    print(f"C_DIR resolved to: {C_DIR or '(not found — check path)'}")
    print("3D View → N-panel → LorQB")
    print("="*60 + "\n")


def unregister():
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
