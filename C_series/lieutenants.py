# Concrete lieutenant implementations — one per Level-1 C-series movement.
#
# Each lieutenant wraps its corresponding C-script behind the five-method API:
#   get_confidence → prepare → execute → verify → (rollback on failure)
#
# Path injection:
#   Instantiate with lieutenants.build_all(c_dir), or set lt.c_dir manually,
#   where c_dir is the absolute path to the C_series folder.

import os
import bpy

from .lieutenant_api import (
    LieutenantBase,
    ConfidenceScore,
    PrepareResult, ExecuteResult, VerifyResult,
    Failure, FailureType,
)
from .movement_registry import MOVEMENT_REGISTRY, REQUIRED_SCENE_OBJECTS


# ---------------------------------------------------------------------------
# Shared base for the four Level-1 lieutenants
# ---------------------------------------------------------------------------

class _C_Lieutenant(LieutenantBase):
    """Shared machinery for lieutenants that wrap a single C-series script."""

    c_dir: str = ""  # injected by build_all() or set manually

    # Subclasses must override these two:
    _post_seats: tuple = ()       # Seat empty names expected after execute
    _post_latches: tuple = ()     # Constraint names expected on Ball after execute

    def _spec(self):
        return MOVEMENT_REGISTRY[self.movement_id]

    # --- get_confidence ---

    def get_confidence(self, context) -> ConfidenceScore:
        spec = self._spec()
        warnings = []

        # Factor 1: all required scene objects present (hard requirement — 0 or 1)
        obj_score, missing = self._score_objects(list(REQUIRED_SCENE_OBJECTS))
        if missing:
            warnings.append(f"Missing objects: {missing}")

        # Factor 2: active hinge at zero rotation
        hinge_score, hinge_warns = self._score_hinges_at_zero([spec.hinge_name])
        warnings.extend(hinge_warns)

        # Factor 3: Ball has no stale constraints
        ball_score, ball_warns = self._score_ball_clean()
        warnings.extend(ball_warns)

        # Weighted composite — objects-present is a hard gate
        value = obj_score * (0.5 * hinge_score + 0.5 * ball_score)

        return ConfidenceScore(
            movement_id=self.movement_id,
            value=round(value, 3),
            factors={
                "objects_present": obj_score,
                "hinge_at_zero":   hinge_score,
                "ball_clean":      ball_score,
            },
            warnings=warnings,
        )

    # --- prepare ---

    def prepare(self, context) -> PrepareResult:
        spec = self._spec()
        failures = []

        # Validate all required objects
        _, missing = self._require_objects(*REQUIRED_SCENE_OBJECTS)
        if missing:
            failures.append(Failure(
                FailureType.MISSING_OBJECT,
                f"Objects not found in scene: {missing}",
                affected_objects=missing,
                recoverable=False,
            ))
            return PrepareResult(success=False, failures=failures)

        # Check for timing conflicts — warn if scene frame is past our start
        current_frame = context.scene.frame_current
        if current_frame > spec.frame_start:
            failures.append(Failure(
                FailureType.TIMING_ERROR,
                (f"Scene is at frame {current_frame}, but {self.movement_id} "
                 f"starts at {spec.frame_start}. Reset before running."),
                recoverable=True,
            ))

        # Warn on stale constraints (collision risk if Ball latches to wrong seat)
        ball = bpy.data.objects.get("Ball")
        if ball and ball.constraints:
            failures.append(Failure(
                FailureType.STATE_MISMATCH,
                "Ball has existing constraints; canonical reset recommended.",
                affected_objects=["Ball"],
                recoverable=True,
            ))

        # Snapshot state for potential rollback
        snap_names = list(REQUIRED_SCENE_OBJECTS) + ["Seat_Blue", "Seat_Red",
                                                       "Seat_Green", "Seat_Yellow"]
        snapshot = self._snapshot(*snap_names)

        non_fatal = [f for f in failures if f.recoverable]
        hard_fail = [f for f in failures if not f.recoverable]

        if hard_fail:
            return PrepareResult(success=False, failures=failures, snapshot=snapshot)

        for f in non_fatal:
            print(f"[{self.movement_id}] prepare warning ({f.failure_type.value}): {f.message}")

        return PrepareResult(success=True, failures=non_fatal, snapshot=snapshot)

    # --- execute ---

    def execute(self, context) -> ExecuteResult:
        spec = self._spec()

        if not self.c_dir:
            return ExecuteResult(
                success=False,
                failures=[Failure(
                    FailureType.STATE_MISMATCH,
                    "c_dir not set on lieutenant — call build_all(c_dir) first.",
                )],
            )

        script_path = os.path.join(self.c_dir, spec.script_file)
        if not os.path.isfile(script_path):
            return ExecuteResult(
                success=False,
                failures=[Failure(
                    FailureType.MISSING_OBJECT,
                    f"Script not found: {script_path}",
                    recoverable=False,
                )],
            )

        ok = self._exec_script(script_path)
        if not ok:
            return ExecuteResult(
                success=False,
                failures=[Failure(
                    FailureType.CONSTRAINT_FAILURE,
                    f"Exception while executing {spec.script_file} — see console.",
                )],
            )

        # Approximate frames keyed: hinge goes start → mid → hold → swap → ret → end = 6 keys
        return ExecuteResult(success=True, frames_keyed=6)

    # --- verify ---

    def verify(self, context) -> VerifyResult:
        spec = self._spec()
        checks = {}
        failures = []

        # Check 1: expected seat empties exist
        for seat_name in self._post_seats:
            exists = bpy.data.objects.get(seat_name) is not None
            checks[f"seat_{seat_name}"] = exists
            if not exists:
                failures.append(Failure(
                    FailureType.VERIFICATION_FAILED,
                    f"{seat_name} empty not found after execute.",
                    affected_objects=[seat_name],
                ))

        # Check 2: Ball has expected latch constraints
        ball = bpy.data.objects.get("Ball")
        for latch_name in self._post_latches:
            found = ball is not None and ball.constraints.get(latch_name) is not None
            checks[f"latch_{latch_name}"] = found
            if not found:
                failures.append(Failure(
                    FailureType.CONSTRAINT_FAILURE,
                    f"Ball constraint '{latch_name}' missing after execute.",
                    affected_objects=["Ball"],
                ))

        # Check 3: active hinge has animation data
        hinge = bpy.data.objects.get(spec.hinge_name)
        has_anim = hinge is not None and hinge.animation_data is not None
        checks["hinge_animated"] = has_anim
        if not has_anim:
            failures.append(Failure(
                FailureType.VERIFICATION_FAILED,
                f"{spec.hinge_name} has no animation data after execute.",
                affected_objects=[spec.hinge_name],
            ))

        # Check 4: scene frame range matches spec
        fr_ok = (context.scene.frame_start == spec.frame_start and
                 context.scene.frame_end   == spec.frame_end)
        checks["frame_range"] = fr_ok
        if not fr_ok:
            failures.append(Failure(
                FailureType.TIMING_ERROR,
                (f"Frame range mismatch: expected [{spec.frame_start},{spec.frame_end}], "
                 f"got [{context.scene.frame_start},{context.scene.frame_end}]"),
            ))

        passed = len(failures) == 0
        return VerifyResult(passed=passed, checks=checks, failures=failures)

    # --- rollback ---

    def rollback(self, context) -> bool:
        self._reset_canonical()
        return True


# ---------------------------------------------------------------------------
# Concrete lieutenants
# ---------------------------------------------------------------------------

class BlueToRedLieutenant(_C_Lieutenant):
    movement_id  = "C12_blue_to_red"
    label        = "Blue → Red"
    _post_seats  = ("Seat_Blue", "Seat_Red")
    _post_latches = ("Latch_Blue", "Latch_Red")


class RedToGreenLieutenant(_C_Lieutenant):
    movement_id  = "C13_red_to_green"
    label        = "Red → Green"
    _post_seats  = ("Seat_Red", "Seat_Green")
    _post_latches = ("Latch_Red", "Latch_Green")


class GreenToYellowLieutenant(_C_Lieutenant):
    movement_id  = "C14_green_to_yellow"
    label        = "Green → Yellow"
    _post_seats  = ("Seat_Green", "Seat_Yellow")
    _post_latches = ("Latch_Green", "Latch_Yellow")


class YellowToBlueLieutenant(_C_Lieutenant):
    """C15 uses different constraint names (C15_Yellow / C15_Blue)
    and reuses Hinge_Red_Green to swing Green+Yellow as a compound unit."""
    movement_id  = "C15_yellow_to_blue"
    label        = "Yellow → Blue"
    _post_seats  = ("Seat_Yellow", "Seat_Blue")
    _post_latches = ("C15_Yellow", "C15_Blue")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_ALL_CLASSES = (
    BlueToRedLieutenant,
    RedToGreenLieutenant,
    GreenToYellowLieutenant,
    YellowToBlueLieutenant,
)


def build_all(c_dir: str) -> dict:
    """Instantiate all lieutenants with the given C_series directory path.

    Returns dict keyed by movement_id.
    """
    result = {}
    for cls in _ALL_CLASSES:
        lt = cls()
        lt.c_dir = c_dir
        result[lt.movement_id] = lt
    return result
