# ============================================================================
# B02_Sequence_Executor.py  (Blender 5.0.1)
# LorQB / Cubolita — Level 1 Sequence Executor
#
# Reads the B01 shuffle sequence, converts the 4-color row into 3 pairs,
# resolves each pair to a movement code via MOVE_MAP, and executes the plan.
#
# Does NOT touch cube/hinge/ball rig. Does NOT alter B01 objects.
# ============================================================================

import bpy
import json
from bpy.types import Operator, Panel

# ============================================================================
# SECTION 1: MOVE_MAP (Level 1, authoritative — Package version A)
# ============================================================================

MOVE_MAP = {
    # Adjacent — forward (C-series)
    ("Blue",   "Red"):    "C12",
    ("Red",    "Green"):  "C13",
    ("Green",  "Yellow"): "C14",
    ("Yellow", "Blue"):   "C15",

    # Adjacent — reverse
    ("Red",    "Blue"):   "C12_REV",
    ("Green",  "Red"):    "C13_REV",
    ("Yellow", "Green"):  "C14_REV",
    ("Blue",   "Yellow"): "C15_REV",

    # Diagonal — T-series (Level 1)
    ("Blue",   "Green"):  "T01",
    ("Green",  "Blue"):   "T01_REV",

    ("Yellow", "Red"):    "T02",
    ("Red",    "Yellow"): "T02_REV",
}

# ============================================================================
# SECTION 2: Runner resolver layer
#
# Execution priority for each move code:
#   1. Importable callable (FUNCTION_NAME_MAP) from loaded module
#   2. Registered Blender operator (OPERATOR_MAP)
#   3. Text datablock in bpy.data.texts (SCRIPT_FILE_MAP basename)
#   4. Script file on disk under SCRIPTS_DIR (SCRIPT_FILE_MAP)
#   5. Fail with exact "missing runner" error
#
# REVERSE VARIANTS:
#   No REV scripts or operators exist on disk (verified). C12_REV/C13_REV/
#   C14_REV/C15_REV/T01_REV/T02_REV will fail at runtime with a precise
#   "missing runner" error. Forward variants only are wired.
# ============================================================================

import os
import importlib.util
import runpy

SCRIPTS_DIR = r"c:\rukmini_ai_loop\scripts"

# --- 2a: file mapping ------------------------------------------------------
SCRIPT_FILE_MAP = {
    "C12":     "C12_blue_to_red.py",
    "C13":     "C13_red_to_green.py",
    "C14":     "C14_green_to_yellow.py",
    "C15":     "C15_yellow_to_blue.py",
    "T01":     "T01_blue_to_green.py",
    "T02":     "T02_yellow_to_red.py",
    # Reverse C variants
    "C12_REV": "C12_red_to_blue.py",
    "C13_REV": "C13_green_to_red.py",
    "C14_REV": "C14_yellow_to_green.py",
    "C15_REV": "C15_blue_to_yellow.py",
    # Reverse T variants — reuse locked T03/T04 scripts
    "T01_REV": "T04_green_to_blue.py",
    "T02_REV": "T03_red_to_yellow.py",
}

# --- 2b: operator mapping (verified bl_idname values) ---------------------
OPERATOR_MAP = {
    "C12":     "lorqb.blue_to_red",
    "C13":     "lorqb.red_to_green",
    "C14":     "lorqb.green_to_yellow",
    "C15":     "lorqb.yellow_to_blue",
    "T01":     "lorqb.run_t1",
    "T02":     "lorqb.run_t2",
    # Reverse C variants
    "C12_REV": "lorqb.red_to_blue",
    "C13_REV": "lorqb.green_to_red",
    "C14_REV": "lorqb.yellow_to_green",
    "C15_REV": "lorqb.blue_to_yellow",
    # Reverse T variants — reuse locked T03/T04 operators
    "T01_REV": "lorqb.run_t4",
    "T02_REV": "lorqb.run_t3",
}

# --- 2c: direct function-name mapping (optional) --------------------------
# No known module-level callables in the movement scripts; left empty.
FUNCTION_NAME_MAP = {
    # "C12": ("C12_blue_to_red", "run"),
}

MOVE_CODES = [
    "C12", "C13", "C14", "C15",
    "C12_REV", "C13_REV", "C14_REV", "C15_REV",
    "T01", "T01_REV",
    "T02", "T02_REV",
]


def _resolve_function(code):
    entry = FUNCTION_NAME_MAP.get(code)
    if not entry:
        return None
    module_name, func_name = entry
    try:
        path = os.path.join(SCRIPTS_DIR, SCRIPT_FILE_MAP.get(code, "") or "")
        if not path or not os.path.isfile(path):
            return None
        spec = importlib.util.spec_from_file_location(module_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        func = getattr(mod, func_name, None)
        return func if callable(func) else None
    except Exception:
        return None


def _resolve_operator(code):
    op_id = OPERATOR_MAP.get(code)
    if not op_id:
        return None
    # op_id format: "lorqb.blue_to_red" → bpy.ops.lorqb.blue_to_red
    try:
        ns, name = op_id.split(".", 1)
        op_ns = getattr(bpy.ops, ns, None)
        if op_ns is None:
            return None
        op = getattr(op_ns, name, None)
        if op is None:
            return None
        # Check if the operator is actually registered
        poll_id = f"{ns}.{name}".upper().replace(".", "_OT_")
        if poll_id not in dir(bpy.types) and not hasattr(bpy.types, f"{ns.upper()}_OT_{name}"):
            # Best-effort check; still allow attempt
            pass
        return op
    except Exception:
        return None


def _resolve_text_datablock(code):
    fname = SCRIPT_FILE_MAP.get(code)
    if not fname:
        return None
    return bpy.data.texts.get(fname)


def _resolve_disk_file(code):
    fname = SCRIPT_FILE_MAP.get(code)
    if not fname:
        return None
    path = os.path.join(SCRIPTS_DIR, fname)
    return path if os.path.isfile(path) else None


def _make_runner(code):
    def _run():
        # 1. Function
        fn = _resolve_function(code)
        if fn is not None:
            fn()
            print(f"[B02] {code}: executed via function")
            return True

        # 2. Operator
        op = _resolve_operator(code)
        if op is not None:
            try:
                op()
                print(f"[B02] {code}: executed via operator {OPERATOR_MAP[code]}")
                return True
            except Exception as e:
                raise RuntimeError(
                    f"Operator {OPERATOR_MAP[code]} call failed for {code}: {e}"
                )

        # 3. Text datablock
        text = _resolve_text_datablock(code)
        if text is not None:
            try:
                ctx = {"__name__": "__main__", "__file__": text.name}
                exec(text.as_string(), ctx)
                print(f"[B02] {code}: executed via text datablock {text.name}")
                return True
            except Exception as e:
                raise RuntimeError(
                    f"Text datablock execution failed for {code}: {e}"
                )

        # 4. Disk file
        path = _resolve_disk_file(code)
        if path is not None:
            try:
                runpy.run_path(path, run_name="__main__")
                print(f"[B02] {code}: executed via disk file {path}")
                return True
            except Exception as e:
                raise RuntimeError(
                    f"Disk execution failed for {code} ({path}): {e}"
                )

        # 5. Fail
        raise RuntimeError(
            f"Missing runner for {code}: no function, operator, text datablock, "
            f"or disk file available (SCRIPT_FILE_MAP={SCRIPT_FILE_MAP.get(code)}, "
            f"OPERATOR_MAP={OPERATOR_MAP.get(code)})"
        )

    return _run


RUNNERS = {code: _make_runner(code) for code in MOVE_CODES}


# --- 2d: wiring status table (printed at register) ------------------------
def _print_runner_status_table():
    print("[B02] Runner wiring status:")
    print("      CODE       EXEC          SOURCE                              REV?")
    print("      ---------- ------------- ----------------------------------- ----")
    for code in MOVE_CODES:
        fname = SCRIPT_FILE_MAP.get(code)
        op_id = OPERATOR_MAP.get(code)
        fn_entry = FUNCTION_NAME_MAP.get(code)
        is_rev = code.endswith("_REV")
        rev_mark = "REV" if is_rev else "FWD"

        if fn_entry:
            exec_kind = "function"
            source = f"{fn_entry[0]}.{fn_entry[1]}"
        elif op_id:
            exec_kind = "operator"
            source = op_id
        elif fname:
            path = os.path.join(SCRIPTS_DIR, fname)
            if os.path.isfile(path):
                exec_kind = "disk/text"
                source = fname
            else:
                exec_kind = "MISSING"
                source = f"(file not found: {fname})"
        else:
            exec_kind = "MISSING"
            source = "(no mapping — will fail at runtime)"
        print(f"      {code:<10} {exec_kind:<13} {source:<35} {rev_mark}")

# ============================================================================
# SECTION 3: Plan builder
# ============================================================================

def build_pairs_from_sequence(sequence):
    if not sequence or len(sequence) != 4:
        raise ValueError("Level 1 sequence must contain exactly 4 colors.")
    return [
        (sequence[0], sequence[1]),
        (sequence[1], sequence[2]),
        (sequence[2], sequence[3]),
    ]


def resolve_plan_from_pairs(pairs):
    plan = []
    missing = []
    for pair in pairs:
        code = MOVE_MAP.get(pair)
        if code is None:
            missing.append(pair)
        else:
            plan.append(code)
    if missing:
        raise KeyError(f"Missing MOVE_MAP entries for: {missing}")
    return plan


def build_execution_plan(sequence):
    pairs = build_pairs_from_sequence(sequence)
    plan = resolve_plan_from_pairs(pairs)
    return pairs, plan

# ============================================================================
# SECTION 4: State helpers
# ============================================================================

def _scene():
    return bpy.context.scene


def _get_b01_sequence():
    s = _scene()
    raw = s.get("b01_sequence", "[]")
    try:
        return json.loads(raw)
    except Exception:
        return []


def reset_executor_state():
    s = _scene()
    s["b02_pairs"]       = json.dumps([])
    s["b02_plan"]        = json.dumps([])
    s["b02_step_index"]  = 0
    s["b02_running"]     = False
    s["b02_complete"]    = False
    s["b02_last_move"]   = ""
    s["b02_last_error"]  = ""


def store_plan(pairs, plan):
    s = _scene()
    s["b02_pairs"]      = json.dumps(pairs)
    s["b02_plan"]       = json.dumps(plan)
    s["b02_step_index"] = 0
    s["b02_running"]    = False
    s["b02_complete"]   = False
    s["b02_last_move"]  = ""
    s["b02_last_error"] = ""


def get_plan():
    return json.loads(_scene().get("b02_plan", "[]"))


def get_pairs():
    return json.loads(_scene().get("b02_pairs", "[]"))

# ============================================================================
# SECTION 5: Execution
# ============================================================================

def _validate_plan(plan):
    missing = [code for code in plan if code not in RUNNERS]
    return missing


def run_single_move(code):
    runner = RUNNERS.get(code)
    if runner is None:
        raise KeyError(f"No runner registered for {code}")
    return runner()


def advance_one_step():
    s = _scene()
    plan = get_plan()
    idx = s.get("b02_step_index", 0)

    if idx >= len(plan):
        s["b02_complete"] = True
        s["b02_running"]  = False
        return False

    code = plan[idx]
    try:
        run_single_move(code)
        s["b02_last_move"]  = code
        s["b02_last_error"] = ""
    except Exception as e:
        s["b02_last_error"] = str(e)
        s["b02_running"]    = False
        return False

    idx += 1
    s["b02_step_index"] = idx

    if idx >= len(plan):
        s["b02_complete"] = True
        s["b02_running"]  = False

    return True

# ============================================================================
# SECTION 6: Operators
# ============================================================================

class LORQB_OT_b02_build_plan(Operator):
    bl_idname = "lorqb.b02_build_plan"
    bl_label = "Build Execution Plan"
    bl_description = "Read B01 sequence and build the move plan"

    def execute(self, context):
        seq = _get_b01_sequence()
        if len(seq) != 4:
            self.report({'ERROR'}, "B01 sequence invalid — run New Shuffle first")
            return {'CANCELLED'}
        try:
            pairs, plan = build_execution_plan(seq)
        except (ValueError, KeyError) as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        missing = _validate_plan(plan)
        if missing:
            self.report({'ERROR'}, f"Missing runners: {missing}")
            return {'CANCELLED'}
        store_plan(pairs, plan)
        self.report({'INFO'}, f"Plan: {plan}")
        return {'FINISHED'}


class LORQB_OT_b02_run_full(Operator):
    bl_idname = "lorqb.b02_run_full"
    bl_label = "Run Shuffled Sequence"
    bl_description = "Execute the full plan in order"

    def execute(self, context):
        s = context.scene
        plan = get_plan()
        if not plan:
            self.report({'ERROR'}, "No plan — Build Execution Plan first")
            return {'CANCELLED'}
        if s.get("b02_complete", False):
            self.report({'INFO'}, "Plan already complete — Reset Executor")
            return {'CANCELLED'}

        s["b02_running"] = True
        while not s.get("b02_complete", False):
            ok = advance_one_step()
            if not ok and not s.get("b02_complete", False):
                self.report({'ERROR'}, s.get("b02_last_error", "step failed"))
                return {'CANCELLED'}
        s["b02_running"] = False
        self.report({'INFO'}, "Sequence complete")
        return {'FINISHED'}


class LORQB_OT_b02_run_next(Operator):
    bl_idname = "lorqb.b02_run_next"
    bl_label = "Run Next Planned Move"
    bl_description = "Execute only the next move in the plan"

    def execute(self, context):
        s = context.scene
        plan = get_plan()
        if not plan:
            self.report({'ERROR'}, "No plan — Build Execution Plan first")
            return {'CANCELLED'}
        if s.get("b02_complete", False):
            self.report({'INFO'}, "Plan already complete")
            return {'CANCELLED'}
        if s.get("b02_running", False):
            self.report({'INFO'}, "Already running")
            return {'CANCELLED'}
        s["b02_running"] = True
        ok = advance_one_step()
        s["b02_running"] = False
        if not ok and not s.get("b02_complete", False):
            self.report({'ERROR'}, s.get("b02_last_error", "step failed"))
            return {'CANCELLED'}
        self.report({'INFO'}, f"Ran: {s.get('b02_last_move', '')}")
        return {'FINISHED'}


class LORQB_OT_b02_reset(Operator):
    bl_idname = "lorqb.b02_reset"
    bl_label = "Reset Executor"
    bl_description = "Clear plan and executor state"

    def execute(self, context):
        reset_executor_state()
        self.report({'INFO'}, "Executor reset")
        return {'FINISHED'}


class LORQB_OT_b02_show_plan(Operator):
    bl_idname = "lorqb.b02_show_plan"
    bl_label = "Show Plan"
    bl_description = "Print the current plan to the console"

    def execute(self, context):
        pairs = get_pairs()
        plan = get_plan()
        print("[B02] Pairs:", pairs)
        print("[B02] Plan :", plan)
        self.report({'INFO'}, f"Plan: {plan if plan else '—'}")
        return {'FINISHED'}

# ============================================================================
# SECTION 7: Panel
# ============================================================================

class LORQB_PT_b02_panel(Panel):
    bl_label = "LorQB — B02 Executor"
    bl_idname = "LORQB_PT_b02_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LorQB — B02"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        layout.operator("lorqb.b02_build_plan", icon='PRESET')
        layout.operator("lorqb.b02_run_full", icon='PLAY')
        layout.operator("lorqb.b02_run_next", icon='FORWARD')
        layout.separator()
        layout.operator("lorqb.b02_show_plan", icon='VIEWZOOM')
        layout.operator("lorqb.b02_reset", icon='LOOP_BACK')

        layout.separator()
        box = layout.box()
        seq = _get_b01_sequence()
        pairs = get_pairs()
        plan = get_plan()
        idx = s.get("b02_step_index", 0)
        running = s.get("b02_running", False)
        complete = s.get("b02_complete", False)
        last = s.get("b02_last_move", "")
        err = s.get("b02_last_error", "")

        box.label(text="B01 Sequence: " + (", ".join(seq) if seq else "—"))
        box.label(text="Pairs: " + (str(pairs) if pairs else "—"))
        box.label(text="Plan: " + (", ".join(plan) if plan else "—"))
        box.label(text=f"Step: {idx} / {len(plan)}")
        box.label(text="Running: " + ("YES" if running else "No"))
        box.label(text="Complete: " + ("YES" if complete else "No"))
        box.label(text="Last Move: " + (last if last else "—"))
        if err:
            box.label(text="Error: " + err, icon='ERROR')

# ============================================================================
# SECTION 8: Registration
# ============================================================================

_classes = (
    LORQB_OT_b02_build_plan,
    LORQB_OT_b02_run_full,
    LORQB_OT_b02_run_next,
    LORQB_OT_b02_reset,
    LORQB_OT_b02_show_plan,
    LORQB_PT_b02_panel,
)


def register():
    for cls in _classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

# ============================================================================
# SECTION 9: Auto-run
# ============================================================================

if __name__ == "__main__":
    register()
    reset_executor_state()
    _print_runner_status_table()
    print("B02_Sequence_Executor registered.")
