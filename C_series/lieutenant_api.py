# Lieutenant API — base contract, failure taxonomy, and confidence scoring.
# Every movement lieutenant inherits LieutenantBase and implements all five methods.
# Master calls: get_confidence → prepare → execute → verify; rollback on any failure.

import bpy
from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Failure taxonomy
# ---------------------------------------------------------------------------

class FailureType(Enum):
    TIMING_ERROR        = "timing_error"        # frame sequence out of order
    COLLISION_RISK      = "collision_risk"       # objects would intersect mid-move
    STATE_MISMATCH      = "state_mismatch"       # scene not in expected canonical state
    CONSTRAINT_FAILURE  = "constraint_failure"   # constraint missing or unapplicable
    MISSING_OBJECT      = "missing_object"       # required Blender object not found
    VERIFICATION_FAILED = "verification_failed"  # post-execute state check failed


@dataclass
class Failure:
    failure_type: FailureType
    message: str
    affected_objects: list = field(default_factory=list)
    recoverable: bool = True  # True means rollback can fix it


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

@dataclass
class ConfidenceScore:
    movement_id: str
    value: float                                  # 0.0 (certain fail) → 1.0 (certain success)
    factors: dict = field(default_factory=dict)   # factor_name -> float contribution
    warnings: list = field(default_factory=list)

    def is_safe(self, threshold: float = 0.7) -> bool:
        return self.value >= threshold

    def summary(self) -> str:
        level = "SAFE" if self.is_safe() else "RISKY"
        warn_text = f" | warnings: {self.warnings}" if self.warnings else ""
        return f"[{level}] {self.movement_id}: {self.value:.2f}{warn_text}"


# ---------------------------------------------------------------------------
# Result containers for each API step
# ---------------------------------------------------------------------------

@dataclass
class PrepareResult:
    success: bool
    failures: list = field(default_factory=list)
    snapshot: dict = field(default_factory=dict)  # saved state for rollback


@dataclass
class ExecuteResult:
    success: bool
    failures: list = field(default_factory=list)
    frames_keyed: int = 0


@dataclass
class VerifyResult:
    passed: bool
    checks: dict = field(default_factory=dict)   # check_name -> bool
    failures: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Base lieutenant
# ---------------------------------------------------------------------------

class LieutenantBase:
    """Abstract base for all movement lieutenants.

    Subclasses must implement all five methods. The Master controller calls
    them in order: get_confidence → prepare → execute → verify. If any step
    returns failure the Master calls rollback before escalating.

    Each subclass must also set:
        movement_id  str  -- matches the key in MOVEMENT_REGISTRY
        label        str  -- human-readable label for UI / logs
    """

    movement_id: str = ""
    label: str = ""

    def prepare(self, context) -> PrepareResult:
        raise NotImplementedError(f"{type(self).__name__}.prepare not implemented")

    def execute(self, context) -> ExecuteResult:
        raise NotImplementedError(f"{type(self).__name__}.execute not implemented")

    def verify(self, context) -> VerifyResult:
        raise NotImplementedError(f"{type(self).__name__}.verify not implemented")

    def rollback(self, context) -> bool:
        raise NotImplementedError(f"{type(self).__name__}.rollback not implemented")

    def get_confidence(self, context) -> ConfidenceScore:
        raise NotImplementedError(f"{type(self).__name__}.get_confidence not implemented")

    # -----------------------------------------------------------------------
    # Shared helpers — available to all subclasses
    # -----------------------------------------------------------------------

    def _require_objects(self, *names) -> tuple:
        """Return (found_dict, missing_list)."""
        found, missing = {}, []
        for name in names:
            obj = bpy.data.objects.get(name)
            if obj:
                found[name] = obj
            else:
                missing.append(name)
        return found, missing

    def _score_objects(self, required: list) -> tuple:
        """Return (score 0.0|1.0, missing_names). Score 0.0 if any object absent."""
        _, missing = self._require_objects(*required)
        return (0.0 if missing else 1.0), missing

    def _score_hinges_at_zero(self, hinge_names: list) -> tuple:
        """Return (score 0.0–1.0, warning_strings). Degrades per off-zero hinge."""
        warnings, at_zero = [], 0
        for name in hinge_names:
            h = bpy.data.objects.get(name)
            if h:
                if all(abs(v) < 0.01 for v in h.rotation_euler):
                    at_zero += 1
                else:
                    warnings.append(f"{name} not at zero rotation ({list(h.rotation_euler):.2})")
        total = len(hinge_names)
        return (at_zero / total if total else 1.0), warnings

    def _score_ball_clean(self) -> tuple:
        """Return (score, warnings). 0.5 penalty if Ball has stale constraints."""
        ball = bpy.data.objects.get("Ball")
        if ball and ball.constraints:
            return 0.5, ["Ball has stale constraints from a prior run"]
        return 1.0, []

    def _snapshot(self, *names) -> dict:
        """Save world location + rotation of named objects for rollback."""
        snap = {}
        for name in names:
            obj = bpy.data.objects.get(name)
            if obj:
                snap[name] = {
                    "location": obj.location.copy(),
                    "rotation_euler": obj.rotation_euler.copy(),
                    "parent": obj.parent,
                }
        return snap

    def _reset_canonical(self):
        """Inline canonical reset — matches every C-script's reset_scene_to_canonical()."""
        all_names = [
            "Ball",
            "Cube_Blue", "Cube_Red", "Cube_Green", "Cube_Yellow",
            "Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow",
        ]
        for name in all_names:
            obj = bpy.data.objects.get(name)
            if obj and obj.animation_data:
                obj.animation_data_clear()

        ball = bpy.data.objects.get("Ball")
        if ball:
            ball.constraints.clear()

        for hinge_name in ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]:
            h = bpy.data.objects.get(hinge_name)
            if h:
                h.rotation_mode = 'XYZ'
                h.rotation_euler = (0.0, 0.0, 0.0)

        for seat_name in ["Seat_Blue", "Seat_Red", "Seat_Green", "Seat_Yellow"]:
            seat = bpy.data.objects.get(seat_name)
            if seat:
                bpy.data.objects.remove(seat, do_unlink=True)

        bpy.context.view_layer.update()
        print(f"[{self.movement_id}] rollback: scene reset to canonical state")

    def _exec_script(self, script_path: str) -> bool:
        """Execute a C-series script file in a fresh globals dict."""
        try:
            import bpy as _bpy
            globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
            with open(script_path, "r", encoding="utf-8") as f:
                exec(f.read(), globs)
            return True
        except Exception as exc:
            print(f"[{self.movement_id}] script execution error: {exc}")
            return False
