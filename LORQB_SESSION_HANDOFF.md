# LorQB Blender — Session Handoff Report
**Date:** 2026-02-27
**Project:** LorQB (Lord of the Quantum Balls)
**Developer:** Carlos Olivencia (cogaston0)
**GitHub:** https://github.com/cogaston0/LorQB-Blender
**Branch:** refactor/seats-uniformity
**Blender Version:** 5.0.1

---

## PASTE THIS INTO CLAUDE INSTRUCTIONS AT START OF NEW SESSION:

**Rukmini Blender Project Rules (follow strictly)**

1. **One step only.** Give exactly 1 action per reply. End with: **"Confirmed?"**
2. **No explanations, no options, no theory.** Only the step.
3. **Always assume Blender version: 5.0.1.0.**
4. When troubleshooting, ask for only 1 screenshot at a time.
5. Never change multiple things at once.
6. For any step involving keys, always include: frame number + exact value.
7. Goal: ball transfers cleanly Blue → Red → Green → Yellow → Blue with no jumping.

CRITICAL SCRIPT-ONLY RULE:
All scene modifications must be implemented exclusively through Python scripts.
No manual Blender UI operations allowed.

---

## 1. WHAT THIS PROJECT IS

LorQB is a 3D educational physics puzzle game in Blender 5.0.1.
A ball transfers between 4 hollow transparent cubes connected by hinges.
Original design by Jose R. Velazquez (2014).

**Chain topology (NEVER changes):**
```
Blue — Red — Green — Yellow
```

**3 Hinges:**
- `Hinge_Blue_Red`     @ ( 0.51,  0,    1) — right edge
- `Hinge_Red_Green`    @ ( 0,    -0.51, 1) — bottom edge
- `Hinge_Green_Yellow` @ (-0.51,  0,    1) — left edge

**Cube hole configuration:**
- Blue   (top-right):    2 holes — top + LEFT side
- Yellow (top-left):     2 holes — top + RIGHT side
- Red    (bottom-right): 1 hole — top only
- Green  (bottom-left):  1 hole — top only

**Ball transfer cycle:**
```
Blue → Red → Green → Yellow → Blue (repeating)
```

**Cube world positions:**
- Yellow: (-0.51, 0.0, 1.0)  dimensions: 1x1x1
- Blue:   ( 0.51, 0.0, 1.0)  dimensions: 1x1x1
- Ball radius: 0.25
- Seat Z = cube_z - 0.5 + 0.25 = cube_z - 0.25

---

## 2. ANIMATION SEQUENCES

| Seq | Transfer       | Hinge Used         | Frames   | Status                        |
|-----|----------------|--------------------|----------|-------------------------------|
| C12 | Blue → Red     | Hinge_Blue_Red     | 1–240    | ⚠️ Needs rewrite with CHILD_OF |
| C13 | Red → Green    | Hinge_Red_Green    | 241–480  | ⚠️ Needs upgrade to CHILD_OF  |
| C14 | Green → Yellow | Hinge_Green_Yellow | 481–720  | ⚠️ Needs rewrite with CHILD_OF |
| C15 | Yellow → Blue  | Hinge_Red_Green    | 720–960  | 🔄 Chain collapse bug          |

**Why C15 uses Hinge_Red_Green (same as C13):**
Hinge_Red_Green sits at the middle of the chain. When it rotates 180°,
the entire Green+Yellow sub-chain swings over Red+Blue, placing Yellow
directly above Blue so the ball drops in.

---

## 3. THE CRITICAL DECISION — SEATS FOR ALL SCRIPTS

**ALL 4 scripts must use the CHILD_OF + Seat Empty system.**

### How the seat system works:
1. Two Empty objects created as seat markers inside each cube pair
2. Ball gets two CHILD_OF constraints — one per seat
3. Influence keyframes switch at transfer frame (CONSTANT interpolation)
4. `inverse_matrix` captured at correct world position before switching

### Required helper functions in every script:

```python
def force_constant(obj, data_fragment):
    """Blender 5.0.1 Layered Actions — force CONSTANT interpolation."""
    ad = obj.animation_data
    if not ad or not ad.action: return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for fc in channelbag.fcurves:
                    if data_fragment in fc.data_path:
                        for kp in fc.keyframe_points:
                            kp.interpolation = 'CONSTANT'

def ensure_child_of(obj, name, target):
    """Get or create CHILD_OF constraint."""
    con = obj.constraints.get(name)
    if not con:
        con = obj.constraints.new(type='CHILD_OF')
        con.name = name
    con.target = target
    return con
```

### Technical standards:
- Hinge rotation: **Y-axis** (`rotation_euler[1]`) using `math.radians()`
- Frame constants: F_START, F_MID, F_TRANSFER, F_TRANSFER_1, F_RET, F_END
- Every script is **independent** — places ball at correct start position itself
- Cube movement: via **CHILD_OF constraints only** — NO direct parenting

---

## 4. CURRENT C15 STATUS AND BUG

**File:** `lorqb_yellow_to_blue_C15.py` (on branch refactor/seats-uniformity)

**What works:**
- Ball IS placed inside Yellow at frame 720 ✅
- CHILD_OF constraints created on ball ✅
- Hinge keyed on Y-axis ✅

**What is broken:**
- Chain layout collapses when script runs ❌
- Green and Yellow cubes fall out of position

**Root cause:**
C15 adds CHILD_OF constraints on Green and Yellow cubes targeting
Hinge_Red_Green and Green respectively. These conflict with the
existing pivot/parent setup from `lorqb_with_pivots.py`.

**Next debugging step:**
Run this diagnostic in Blender after running lorqb_with_pivots.py:

```python
import bpy
for name in ["Cube_Blue","Cube_Red","Cube_Green","Cube_Yellow",
             "Hinge_Blue_Red","Hinge_Red_Green","Hinge_Green_Yellow"]:
    obj = bpy.data.objects.get(name)
    if obj:
        print(f"{name}: parent={obj.parent}, constraints={[c.name for c in obj.constraints]}")
```

This will show exactly what lorqb_with_pivots.py sets up so C15
constraints can be written to work WITH the existing setup.

---

## 5. WHAT EACH CURRENT SCRIPT USES

### C12 (lorqb_blue_to_red.py) — NEEDS REWRITE
- Direct parenting: `ball.parent = blue_cube` then `ball.parent = red_cube`
- No seats, no CHILD_OF
- Uses X-axis rotation
- Transfer at frame 121

### C13 (lorqb_red_to_green_C13.py) — NEEDS UPGRADE
- Uses COPY_TRANSFORMS constraints (not CHILD_OF)
- Has seat empties (Seat_Red, Seat_Green) ✅
- Uses Y-axis rotation ✅
- Has parent_preserve_world helper ✅
- Missing force_constant for Blender 5.0.1 ❌
- Requires manual Graph Editor interpolation fix ❌

### C14 (lorqb_green_flip_cycle.py) — NEEDS REWRITE
- Direct parenting: `ball.parent = green_cube` then `ball.parent = yellow_cube`
- No seats, no CHILD_OF
- Uses X-axis rotation (wrong)
- Wrong frame range (1-240, should be 481-720)

### C15 (lorqb_yellow_to_blue_C15.py) — IN PROGRESS
- Uses CHILD_OF ✅
- Uses seat empties ✅
- Uses Y-axis rotation ✅
- Has force_constant ✅
- Chain collapse bug ❌

---

## 6. WORK ORDER

1. **Fix C15 chain collapse** — run diagnostic, identify conflict with lorqb_with_pivots.py
2. **Rewrite C12** using C15 as template
3. **Upgrade C13** COPY_TRANSFORMS → CHILD_OF
4. **Rewrite C14** using C15 as template
5. **Integration test** — run all 4 in sequence, verify full cycle

---

## 7. GITHUB WORKFLOW

```bash
# Clone repo
git clone https://github.com/cogaston0/LorQB-Blender.git
cd LorQB-Blender

# Switch to working branch
git checkout refactor/seats-uniformity

# After making changes
git add <filename>
git commit -m "fix: description of change"
git push origin refactor/seats-uniformity
```

**Pull Request:** https://github.com/cogaston0/LorQB-Blender/pull/new/refactor/seats-uniformity

---

## 8. KEY RULES CARLOS FOLLOWS

- Script-only operations — NO manual Blender UI
- One step per reply ending with "Confirmed?"
- Complete script replacements over partial fixes
- Diagnostic scripts to verify object states before making changes
- Delete all objects and recreate scene when issues become complex
- Cross-reference with ChatGPT and NotebookLM for validation

---

## END OF HANDOFF REPORT
