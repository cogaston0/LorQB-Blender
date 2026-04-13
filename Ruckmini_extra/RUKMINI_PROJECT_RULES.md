# Rukmini Blender Project Rules
# Paste entire contents of this file into Claude Instructions box at start of every session.

---

**Rukmini Blender Project Rules (follow strictly)**

1. **One step only.** Give exactly **1 action** per reply. End with: **"Confirmed?"**
2. **No explanations, no options, no theory.** Only the step.
3. **Always assume Blender version: 5.0.1.0.**
4. When troubleshooting, ask for **only 1 screenshot** at a time, and specify exactly which panel/view (example: "Constraints tab for the Ball").
5. Never change multiple things at once. If a step fails, give a **single alternate step** (still only 1).
6. Default debugging order (use this order unless I say otherwise):
   a) Ball **keyframes** (clear unwanted L/R/S)
   b) **Constraints** (Child Of influence keys + Set Inverse)
   c) **Parenting / hierarchy** (Outliner + Relations)
   d) **NLA/Actions** (strip/action conflicts)
   e) **Rigid Body state** (Animated vs Dynamic timing)
7. For any step involving keys, always include: **frame number + exact value** (example: "Frame 120: Influence = 0, I-key").
8. Goal: ball transfers cleanly **Blue → Red → Green → Yellow → Blue** with **no jumping** when scrubbing or returning to frame 1.

---

CRITICAL SCRIPT-ONLY RULE:
All scene modifications, animations, and fixes must be implemented exclusively through Python scripts. No manual Blender UI operations allowed (no Alt+G, Alt+R, manual keyframes, constraint editing, parenting in Outliner, etc.).

When debugging:
- Identify the issue
- Tell me which script file to modify
- Tell me the exact line number(s) to change
- Provide the replacement code for that line

Example correct response:
"In lorqb_green_flip_cycle.py, line 23, change:
ball.parent = green_cube
to:
ball.parent = None"

Never say: "Select the Ball and press Alt+G" or "Manually clear the keyframes."

---

## HOW TO START EACH SESSION

1. Paste these rules into Claude Instructions box
2. Then send this message to Claude:

```
Read this file first before doing anything:
https://raw.githubusercontent.com/cogaston0/LorQB-Blender/refactor/seats-uniformity/LORQB_SESSION_HANDOFF.md
```

Claude will fetch the full project context from GitHub and continue where we left off.

---

## QUICK REFERENCE

**Repo:** https://github.com/cogaston0/LorQB-Blender
**Working branch:** refactor/seats-uniformity
**Blender version:** 5.0.1
**Scene construction script:** lorqb_with_pivots.py

**Chain:** Blue — Red — Green — Yellow
**Ball cycle:** Blue → Red → Green → Yellow → Blue
**3 Hinges:** Hinge_Blue_Red | Hinge_Red_Green | Hinge_Green_Yellow

**Animation sequences:**
- C12: Blue → Red   | Hinge_Blue_Red     | Frames 1–240
- C13: Red → Green  | Hinge_Red_Green    | Frames 241–480
- C14: Green → Yellow | Hinge_Green_Yellow | Frames 481–720
- C15: Yellow → Blue | Hinge_Red_Green   | Frames 720–960

**Key decision:** ALL scripts use CHILD_OF + Seat Empty system.
C15 is the gold standard template.
C12, C13, C14 need to be rewritten to match C15.
Current bug: C15 chain collapses — fix this first.
