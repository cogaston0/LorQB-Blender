###############################################################################
# FILE: lorqb_master_runner.py
# PURPOSE: Blender 5.0.1 N-Panel runner for C12-C15 cycle scripts.
#          Uses compile()+exec() only. NO area-type switching — that caused
#          the crash. The execution context difference between exec() and
#          native Run Script is diagnosed via Section 2 verbose output rather
#          than by manipulating Blender internals at runtime.
# INSTALL: Paste into Blender Text Editor and click "Run Script".
# SCRIPTS DIR: C:\rukmini_ai_loop\scripts
###############################################################################

import bpy
import os
import traceback

###############################################################################
# SECTION 1: Configuration
# Central place to update the scripts directory and filename map.
# If a script is renamed, only this section needs to change.
###############################################################################

SCRIPTS_DIR = r"C:\rukmini_ai_loop\scripts"

SCRIPT_MAP = {
    "C12": "C12_blue_to_red.py",
    "C13": "C13_red_to_green.py",
    "C14": "C14_green_to_yellow.py",
    "C15": "C15_yellow_to_blue.py",
}

###############################################################################
# SECTION 2: Core Runner Function — compile()+exec() with verbose diagnostics
#
# WHY exec() IS SAFE HERE:
#   The area-type hijacking approach crashed Blender 5.0.1. We are back to
#   compile()+exec() which is stable. C15 already confirmed this path works.
#   If C12-C14 do not move, the problem is inside those scripts (likely a
#   bpy.ops call that needs a different context override), not in the runner.
#
# DIAGNOSTICS ADDED:
#   After exec() completes, this function checks the scene for expected
#   animation data on the hinge objects and prints the result. This lets us
#   confirm whether the script ran its keyframe logic or silently skipped it.
###############################################################################

def run_script(cycle_key):
    filename = SCRIPT_MAP.get(cycle_key)
    if not filename:
        print(f"[LorQB] ERROR: Unknown cycle key '{cycle_key}'")
        return False

    filepath = os.path.join(SCRIPTS_DIR, filename)

    print(f"[LorQB] ── Running {cycle_key} ──────────────────────────────────")
    print(f"[LorQB] Path : {filepath}")

    # Verify the file exists before attempting to open it
    if not os.path.exists(filepath):
        print(f"[LorQB] ERROR: File not found: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        # compile() gives line-accurate SyntaxError messages
        code = compile(source, filepath, "exec")

        # Isolated namespace prevents variable bleed between scripts
        global_ns = {"__file__": filepath, "__name__": "__main__"}
        exec(code, global_ns)

        print(f"[LorQB] {cycle_key} exec() completed without exception.")

        # --- Post-run diagnostic: check hinges for animation data ---
        _diagnose_after_run(cycle_key)

        return True

    except SyntaxError as e:
        print(f"[LorQB] SYNTAX ERROR in {filename}:")
        print(f"  Line {e.lineno}: {e.msg}")
        print(f"  Text: {e.text}")
        return False

    except Exception:
        print(f"[LorQB] RUNTIME ERROR in {filename}:")
        traceback.print_exc()
        return False


###############################################################################
# SECTION 3: Post-Run Diagnostic Helper
# After each script runs, inspect the scene to confirm whether keyframes were
# actually written. Reports hinge animation data and ball constraint state so
# we know if the script logic fired or was silently skipped.
###############################################################################

def _diagnose_after_run(cycle_key):
    print(f"[LorQB] -- Post-run diagnostic for {cycle_key} --")

    hinge_names = ["Hinge_Blue_Red", "Hinge_Red_Green", "Hinge_Green_Yellow"]
    for hname in hinge_names:
        obj = bpy.data.objects.get(hname)
        if not obj:
            print(f"[LorQB]   {hname}: NOT FOUND in scene")
            continue
        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            # Blender 5.0.1 fcurve access path
            try:
                fcurves = action.layers[0].strips[0].channelbags[0].fcurves
                print(f"[LorQB]   {hname}: action='{action.name}' "
                      f"fcurves={len(list(fcurves))}")
            except Exception:
                print(f"[LorQB]   {hname}: action='{action.name}' "
                      f"(could not read fcurves)")
        else:
            print(f"[LorQB]   {hname}: NO animation data")

    ball = bpy.data.objects.get("Ball")
    if ball:
        constraints = ball.constraints
        if constraints:
            for c in constraints:
                print(f"[LorQB]   Ball constraint: '{c.name}' "
                      f"type={c.type} influence={c.influence:.2f}")
        else:
            print("[LorQB]   Ball: no constraints")
    else:
        print("[LorQB]   Ball: NOT FOUND in scene")

    print(f"[LorQB] -- End diagnostic --")


###############################################################################
# SECTION 4: Run-All Helper
# Executes C12 -> C13 -> C14 -> C15 in sequence.
# Stops immediately on the first failure and reports which cycle failed.
###############################################################################

def run_all_cycles():
    print("[LorQB] == Running ALL cycles C12 -> C13 -> C14 -> C15 =========")
    for key in ("C12", "C13", "C14", "C15"):
        ok = run_script(key)
        if not ok:
            print(f"[LorQB] !! Stopped at {key} due to error.")
            return False
    print("[LorQB] == All cycles complete ==================================")
    return True


###############################################################################
# SECTION 5: Operators
# One operator per cycle plus Run-All and Ping.
# Each prints a confirmation to System Console on press so you can confirm
# the button registration fired before any script logic runs.
###############################################################################

class LORQB_OT_ping(bpy.types.Operator):
    """
    Ping — press first to confirm the addon is live and all files exist.
    Output goes to System Console (Window > Toggle System Console).
    """
    bl_idname      = "lorqb.ping"
    bl_label       = "Ping / Check Paths"
    bl_description = "Print script paths to System Console for verification"

    def execute(self, context):
        print("[LorQB] == PING ==============================================")
        print(f"[LorQB] Scripts dir exists : {os.path.exists(SCRIPTS_DIR)}")
        print(f"[LorQB] Scripts dir path   : {SCRIPTS_DIR}")
        for key, fname in SCRIPT_MAP.items():
            fp     = os.path.join(SCRIPTS_DIR, fname)
            status = "FOUND" if os.path.exists(fp) else "MISSING"
            print(f"[LorQB]   {key}: {fname}  [{status}]")
        print("[LorQB] =====================================================")
        self.report({"INFO"}, "Ping done - check System Console.")
        return {"FINISHED"}


class LORQB_OT_run_c12(bpy.types.Operator):
    """Run C12: Blue cube rotates, ball transfers into Red cube."""
    bl_idname      = "lorqb.run_c12"
    bl_label       = "C12  Blue -> Red"
    bl_description = "Execute C12: Blue to Red ball transfer"

    def execute(self, context):
        print("[LorQB] Button pressed: C12")
        ok = run_script("C12")
        self.report({"INFO"} if ok else {"ERROR"},
                    "C12 done." if ok else "C12 FAILED - check System Console.")
        return {"FINISHED"}


class LORQB_OT_run_c13(bpy.types.Operator):
    """Run C13: Red cube rotates, ball transfers into Green cube."""
    bl_idname      = "lorqb.run_c13"
    bl_label       = "C13  Red -> Green"
    bl_description = "Execute C13: Red to Green ball transfer"

    def execute(self, context):
        print("[LorQB] Button pressed: C13")
        ok = run_script("C13")
        self.report({"INFO"} if ok else {"ERROR"},
                    "C13 done." if ok else "C13 FAILED - check System Console.")
        return {"FINISHED"}


class LORQB_OT_run_c14(bpy.types.Operator):
    """Run C14: Green cube rotates, ball transfers into Yellow cube."""
    bl_idname      = "lorqb.run_c14"
    bl_label       = "C14  Green -> Yellow"
    bl_description = "Execute C14: Green to Yellow ball transfer"

    def execute(self, context):
        print("[LorQB] Button pressed: C14")
        ok = run_script("C14")
        self.report({"INFO"} if ok else {"ERROR"},
                    "C14 done." if ok else "C14 FAILED - check System Console.")
        return {"FINISHED"}


class LORQB_OT_run_c15(bpy.types.Operator):
    """Run C15: Yellow cube rotates, ball transfers into Blue cube."""
    bl_idname      = "lorqb.run_c15"
    bl_label       = "C15  Yellow -> Blue"
    bl_description = "Execute C15: Yellow to Blue ball transfer"

    def execute(self, context):
        print("[LorQB] Button pressed: C15")
        ok = run_script("C15")
        self.report({"INFO"} if ok else {"ERROR"},
                    "C15 done." if ok else "C15 FAILED - check System Console.")
        return {"FINISHED"}


class LORQB_OT_run_all(bpy.types.Operator):
    """Run the full sequence: C12 -> C13 -> C14 -> C15."""
    bl_idname      = "lorqb.run_all"
    bl_label       = "Run ALL  C12 -> C15"
    bl_description = "Execute all four cycles in sequence"

    def execute(self, context):
        print("[LorQB] Button pressed: RUN ALL")
        ok = run_all_cycles()
        self.report({"INFO"} if ok else {"ERROR"},
                    "All cycles done." if ok else "FAILED - check System Console.")
        return {"FINISHED"}


###############################################################################
# SECTION 6: N-Panel UI
# Draws the LorQB tab in the 3D Viewport sidebar (press N to open).
# Layout: Diagnostic first, then individual cycles, then full sequence.
###############################################################################

class LORQB_PT_panel(bpy.types.Panel):
    bl_label       = "LorQB Runner"
    bl_idname      = "LORQB_PT_panel"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "LorQB"

    def draw(self, context):
        layout = self.layout

        # ── Diagnostic ───────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Diagnostic", icon="INFO")
        box.operator("lorqb.ping", icon="CONSOLE")

        layout.separator()

        # ── Individual Cycles ─────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Individual Cycles", icon="PLAY")
        box.operator("lorqb.run_c12", icon="MESH_CUBE")
        box.operator("lorqb.run_c13", icon="MESH_CUBE")
        box.operator("lorqb.run_c14", icon="MESH_CUBE")
        box.operator("lorqb.run_c15", icon="MESH_CUBE")

        layout.separator()

        # ── Full Sequence ─────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Full Sequence", icon="FF")
        row = box.row()
        row.scale_y = 1.6
        row.operator("lorqb.run_all", icon="PLAY")


###############################################################################
# SECTION 7: Registration
# All classes registered on Run Script; unregistered in reverse on reload
# or addon disable to avoid leftover operator/panel conflicts.
###############################################################################

CLASSES = (
    LORQB_OT_ping,
    LORQB_OT_run_c12,
    LORQB_OT_run_c13,
    LORQB_OT_run_c14,
    LORQB_OT_run_c15,
    LORQB_OT_run_all,
    LORQB_PT_panel,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    print("[LorQB] Master Runner registered. Open N-panel > LorQB tab.")


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    print("[LorQB] Master Runner unregistered.")


###############################################################################
# SECTION 8: Entry Point
# Runs register() when executed directly from the Blender Text Editor.
###############################################################################

if __name__ == "__main__":
    register()
