# UTIL_load_all_scripts.py
# Run this ONCE in Blender's text editor (paste and Alt+P).
#
# What it does:
#   1. Loads all C and T scripts from disk (linked as external files)
#      → After this, Blender shows "Text is newer on disk — Reload" when files change.
#   2. Executes T01, T02, T03 to register their panels immediately.
#      → All three T panels appear in the LorQB N-panel tab right away.
#   3. C10–C15 are loaded but NOT auto-executed.
#      → Run each C script manually (Alt+P or its panel button) when needed.

import bpy
import os

SCRIPTS_DIR = r"C:\rukmini_ai_loop\scripts"

# Load + execute: T scripts coexist safely (each only unregisters its own class)
EXECUTE = [
    "T01_blue_to_green.py",
    "T02_yellow_to_red.py",
    "T03_red_to_yellow.py",
]

# Load only: C scripts use _unregister_all_lorqb() which removes all panels
LOAD_ONLY = [
    "C10_scene_build.py",
    "C12_blue_to_red.py",
    "C13_red_to_green.py",
    "C14_green_to_yellow.py",
    "C15_yellow_to_blue.py",
]

ALL_SCRIPTS = LOAD_ONLY + EXECUTE

print("\n=== Step 1: Loading scripts from disk ===")
for filename in ALL_SCRIPTS:
    filepath = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  MISSING: {filepath}")
        continue
    existing = bpy.data.texts.get(filename)
    if existing:
        bpy.data.texts.remove(existing)
    bpy.data.texts.load(filepath, internal=False)
    print(f"  Loaded:  {filename}")

print("\n=== Step 2: Registering T panels ===")
for filename in EXECUTE:
    filepath = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  MISSING: {filepath}")
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    exec(compile(code, filepath, 'exec'), {"__name__": "__main__"})
    print(f"  Registered: {filename}")

print("\n=== Done ===")
print("T01 / T02 / T03 panels active in LorQB N-panel tab.")
print("To activate a C script panel: open it in Text Editor → Alt+P.")
