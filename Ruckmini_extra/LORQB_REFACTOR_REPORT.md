# LorQB Blender — Refactor Report & Development Plan
**Date:** 2026-02-27  
**Author:** Carlos Olivencia (cogaston0)  
**Repo:** https://github.com/cogaston0/LorQB-Blender  
**Prepared by:** Claude (Anthropic) acting as lead coordinator

---

## 1. PROJECT OVERVIEW

LorQB is a 3D educational physics puzzle game built in Blender 5.0.1.  
A ball transfers between 4 hollow transparent cubes connected by hinges in a snake chain.

**Chain topology (fixed, never changes):**
```
Blue — Red — Green — Yellow
```
Connected by 3 hinges:
- `Hinge_Blue_Red`     @ ( 0.51,  0,    1) — right edge
- `Hinge_Red_Green`    @ ( 0,    -0.51, 1) — bottom edge  
- `Hinge_Green_Yellow` @ (-0.51,  0,    1) — left edge

**Ball transfer cycle:**
```
Blue → Red → Green → Yellow → Blue (repeating)
```

**Cube hole configuration:**
- Blue   (top-right):    2 holes — top + LEFT side
- Yellow (top-left):     2 holes — top + RIGHT side
- Red    (bottom-right): 1 hole — top only
- Green  (bottom-left):  1 hole — top only

---

## 2. ANIMATION SEQUENCES

| Seq | Transfer    | Hinge Used        | Frames   | Status              |
|-----|-------------|-------------------|----------|---------------------|
| C12 | Blue → Red  | Hinge_Blue_Red    | 1–240    | ⚠️ Needs rewrite    |
| C13 | Red → Green | Hinge_Red_Green   | 241–480  | ✅ Gold standard    |
| C14 | Green → Yellow | Hinge_Green_Yellow | 481–720 | ⚠️ Needs rewrite |
| C15 | Yellow → Blue  | Hinge_Red_Green   | 720–960  | 🔄 In progress      |

**Why C15 uses Hinge_Red_Green (same as C13):**  
Hinge_Red_Green sits at the middle of the chain. When it rotates 180°, the entire  
Green+Yellow sub-chain swings over the Red+Blue sub-chain, placing Yellow directly  
above Blue so the ball drops in. The same hinge serves both C13 and C15 because  
it is the pivot point between the two halves of the chain.

---

## 3. CRITICAL DECISION: SEATS FOR ALL SCRIPTS

**Decision made:** All 4 animation scripts (C12, C13, C14, C15) must use the  
**Seat-Based CHILD_OF constraint system** for ball transfers.

**Reason:** Uniformity, no parenting conflicts, no ball jumping when scrubbing timeline.

### The Seat System (C13 is the gold standard):
1. Two **Empty objects** are created as seat markers inside each cube pair
2. Ball gets two **CHILD_OF constraints** — one per seat
3. **Influence keyframes** switch at transfer frame (CONSTANT interpolation)
4. `inverse_matrix` is captured at the correct world position before switching

### What each script currently uses:
- **C12** (`lorqb_blue_to_red.py`): Direct parenting — `ball.parent = cube` ❌
- **C13** (`lorqb_red_to_green_C13.py`): COPY_TRANSFORMS + seats ✅ (needs upgrade to CHILD_OF)
- **C14** (`lorqb_green_flip_cycle.py`): Direct parenting — `ball.parent = cube` ❌
- **C15** (`lorqb_yellow_to_blue_C15.py`): CHILD_OF + seats ✅ (in progress)

---

## 4. TECHNICAL STANDARDS (all scripts must follow)

```python
# Blender 5.0.1 Layered Actions — force CONSTANT interpolation
def force_constant(obj, data_fragment):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for fc in channelbag.fcurves:
                    if data_fragment in fc.data_path:
                        for kp in fc.keyframe_points:
                            kp.interpolation = 'CONSTANT'

# CHILD_OF constraint helper
def ensure_child_of(obj, name, target):
    con = obj.constraints.get(name)
    if not con:
        con = obj.constraints.new(type='CHILD_OF')
        con.name = name
    con.target = target
    return con
```

**Hinge rotation axis:**
- All hinges rotate on **Y-axis** (`rotation_euler[1]`)
- Use `math.radians()` — never raw radian values

**Frame constants (required in every script):**
```python
F_START, F_MID, F_TRANSFER, F_TRANSFER_1, F_RET, F_END
```

**Independence rule:**  
Every script must place the ball at its correct starting position by itself.  
No script may rely on a previous script having run first.

**Cube/Ball world positions:**
```python
Yellow: (-0.51, 0.0, 1.0)  dimensions: 1x1x1
Blue:   ( 0.51, 0.0, 1.0)  dimensions: 1x1x1
Red:    ( 0.51, 0.0, 0.0)  dimensions: 1x1x1  (estimated)
Green:  (-0.51, 0.0, 0.0)  dimensions: 1x1x1  (estimated)
Ball radius: 0.25
Seat Z = cube_z - 0.5 + 0.25 = cube_z - 0.25
```

---

## 5. CURRENT PROBLEM WITH C15

Ball is visible inside Yellow at frame 720 ✅  
But chain layout collapses when script runs ❌  

**Root cause suspected:**  
`CHILD_OF` constraints on Green and Yellow cubes conflict with  
existing pivot/parent setup from `lorqb_with_pivots.py`.  
The `inverse_matrix` calculation needs to account for the  
existing world transform of each cube after scene construction.

**Next debugging step:**  
Verify what `lorqb_with_pivots.py` sets as parents for Green and Yellow  
before applying C15 constraints.

---

## 6. FILES IN REPOSITORY

| File | Purpose | Action Needed |
|------|---------|---------------|
| `lorqb_with_pivots.py` | Scene construction | ✅ Keep as-is |
| `lorqb_blue_to_red.py` | C12 animation | ⚠️ Rewrite with CHILD_OF + seats |
| `lorqb_red_to_green_C13.py` | C13 animation | ⚠️ Upgrade COPY_TRANSFORMS → CHILD_OF |
| `lorqb_green_flip_cycle.py` | C14 animation | ⚠️ Rewrite with CHILD_OF + seats |
| `lorqb_yellow_to_blue_C15.py` | C15 animation | 🔄 Fix chain collapse bug |
| `scripts/` | Empty folder | 📁 Organize scripts here |

---

## 7. RECOMMENDED GITHUB ACTIONS

### Step 1 — Create a development branch
```bash
cd LorQB-Blender
git checkout -b refactor/seats-uniformity
```

### Step 2 — Create GitHub Issue to track this work
Title: `Refactor: Implement CHILD_OF seat system uniformly across C12–C15`

### Step 3 — Commit order
1. Fix C15 chain collapse bug → commit: `fix: C15 chain collapse on CHILD_OF setup`
2. Rewrite C12 with seats → commit: `refactor: C12 Blue→Red rewrite with CHILD_OF seats`
3. Upgrade C13 COPY_TRANSFORMS → CHILD_OF → commit: `refactor: C13 upgrade to CHILD_OF`
4. Rewrite C14 with seats → commit: `refactor: C14 Green→Yellow rewrite with CHILD_OF seats`
5. Final integration test → commit: `test: full cycle B→R→G→Y→B verified`

### Step 4 — Merge to main
```bash
git checkout main
git merge refactor/seats-uniformity
git push origin main
```
