# LorQB — Claude Code Prompts
Repository: cogaston0/LorQB-Blender
Branch: claude/analyze-project-architecture-IMcim

---

## PROMPT 1 — Fix lorQB_Master_Runnet (Runnet)

```
You are working on the LorQB-Blender project.
Repository: cogaston0/LorQB-Blender
File to fix: lorQB_Master_Runnet

CURRENT PROBLEM:
lorQB_Master_Runnet only has 4 buttons (C12, C13, C14, C15).
It needs to be updated to match C01_lorQB_Master_Runner.py exactly,
which has 9 buttons organized in 3 sections.

TARGET STATE — 9 buttons in 3 sections:

  Section "Setup":
    Button 1 → C10: Build Scene
               operator: lorqb.run_c10
               script:   C10_scene_build.py
               icon:     SCENE_DATA

  Section "C-Series (Main Loop)":
    Button 2 → C12: Blue → Red
               operator: lorqb.run_c12
               script:   C12_blue_to_red.py
               icon:     PLAY
    Button 3 → C13: Red → Green
               operator: lorqb.run_c13
               script:   C13_red_to_green.py
               icon:     PLAY
    Button 4 → C14: Green → Yellow
               operator: lorqb.run_c14
               script:   C14_green_to_yellow.py
               icon:     PLAY
    Button 5 → C15: Yellow → Blue
               operator: lorqb.run_c15
               script:   C15_yellow_to_blue.py
               icon:     PLAY

  Section "T-Series (Diagonal)":
    Button 6 → T01: Blue → Green
               operator: lorqb.run_t01
               script:   T01_blue_to_green.py
               icon:     PLAY
    Button 7 → T02: Yellow → Red
               operator: lorqb.run_t02
               script:   T02_yellow_to_red.py
               icon:     PLAY
    Button 8 → T03: Red → Yellow
               operator: lorqb.run_t03
               script:   T03_red_to_yellow.py
               icon:     PLAY
    Button 9 → T04: Green → Blue
               operator: lorqb.run_t04
               script:   T04_green_to_blue.py
               icon:     PLAY

RULES:
- SCRIPTS path stays: r"C:\rukmini_ai_loop\scripts"
- Each operator uses exec(open(SCRIPTS + r"\<filename>").read(), globs)
- globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
- Panel bl_idname:    LORQB_PT_master_panel
- Panel bl_category:  LorQB
- Panel bl_space_type: VIEW_3D
- Panel bl_region_type: UI
- Register/unregister loop at bottom (try/except pattern)
- Final print: "LorQB Master Panel registered — N-panel > LorQB tab."

Use C01_lorQB_Master_Runner.py as the reference — lorQB_Master_Runnet
must be a functionally identical copy.

After editing, commit and push to branch:
claude/analyze-project-architecture-IMcim
```

---

## PROMPT 2 — Fix C01_lorQB_Master_Runner.py (Runner) with GitHub access + consistency

```
You are working on the LorQB-Blender project.
Repository: cogaston0/LorQB-Blender  (you have GitHub access)
Branch: claude/analyze-project-architecture-IMcim
Primary file: C01_lorQB_Master_Runner.py

───────────────────────────────────────────────
TASK 1 — Verify C01_lorQB_Master_Runner.py
───────────────────────────────────────────────
Read C01_lorQB_Master_Runner.py from the repository.
Confirm it has exactly 9 buttons in 3 sections:

  Section "Setup":
    Button 1 → C10: Build Scene  (lorqb.run_c10, icon SCENE_DATA)

  Section "C-Series (Main Loop)":
    Button 2 → C12: Blue → Red       (lorqb.run_c12, icon PLAY)
    Button 3 → C13: Red → Green      (lorqb.run_c13, icon PLAY)
    Button 4 → C14: Green → Yellow   (lorqb.run_c14, icon PLAY)
    Button 5 → C15: Yellow → Blue    (lorqb.run_c15, icon PLAY)

  Section "T-Series (Diagonal)":
    Button 6 → T01: Blue → Green     (lorqb.run_t01, icon PLAY)
    Button 7 → T02: Yellow → Red     (lorqb.run_t02, icon PLAY)
    Button 8 → T03: Red → Yellow     (lorqb.run_t03, icon PLAY)
    Button 9 → T04: Green → Blue     (lorqb.run_t04, icon PLAY)

If any button is missing, add it.
If the sections are not labeled, add the labels.

───────────────────────────────────────────────
TASK 2 — Consistency fixes (same commit)
───────────────────────────────────────────────
In C01_lorQB_Master_Runner.py, verify:
- SCRIPTS = r"C:\rukmini_ai_loop\scripts"
- Each operator uses exec(open(SCRIPTS + r"\<file>").read(), globs)
- globs = {"bpy": _bpy, "_unregister_all_lorqb": lambda: None}
- Panel: bl_idname="LORQB_PT_master_panel", bl_category="LorQB"
- Register/unregister loop uses try/except at bottom
- Final print: "LorQB Master Panel registered — N-panel > LorQB tab."

───────────────────────────────────────────────
TASK 3 — Known issues to flag (do NOT auto-fix)
───────────────────────────────────────────────
Report only — do not modify these files:
1. T02_yellow_to_red.py — ROT_SIGN values are marked TODO,
   need Blender runtime verification before fixing
2. lorQB_Master_Runnet — redundant old file (no .py extension),
   confirm with user before deleting

───────────────────────────────────────────────
RULES
───────────────────────────────────────────────
- Only modify C01_lorQB_Master_Runner.py
- Commit with message: "C01: verify and finalize 9-button Master Panel"
- Push to branch: claude/analyze-project-architecture-IMcim
```

---

## CONSISTENCY REPORT SUMMARY

| Check | Status | Notes |
|---|---|---|
| SCRIPTS path | ✓ Consistent | All use `r"C:\rukmini_ai_loop\scripts"` |
| Reset function naming | ✓ Mostly consistent | C14 uses `reset_c14_state()` — intentional |
| globs dict pattern | ✓ Consistent | Identical across all files |
| bl_idname conventions | ✓ Consistent | All follow `lorqb.xxx` pattern |
| Frame ranges | ✓ Consistent | C-series sequential, T-series independent |
| Hinge keys & ROT_SIGN | ✓ Consistent | Correct by geometric design |
| File references in C01 | ✓ All match | All 9 referenced scripts exist |

### Issues Requiring Attention

| # | File | Issue | Action |
|---|---|---|---|
| 1 | `lorQB_Master_Runnet` | Redundant old file, no .py extension | Confirm with user before deleting |
| 2 | `T02_yellow_to_red.py` | ROT_SIGN values marked TODO | Verify in Blender before fixing |
| 3 | C12/C13 vs T-series vs C14/C15 | fcurves access pattern differs | Consider standardizing to try/except |
