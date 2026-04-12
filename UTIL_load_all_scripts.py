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
C_DIR = os.path.join(SCRIPTS_DIR, "C_series")
T_DIR = os.path.join(SCRIPTS_DIR, "T_series")

# Load + execute: T scripts coexist safely (each only unregisters its own class)
EXECUTE = [
    ("T", "T01_blue_to_green.py"),
    ("T", "T02_yellow_to_red.py"),
    ("T", "T03_red_to_yellow.py"),
]

# Load only: C scripts use _unregister_all_lorqb() which removes all panels
LOAD_ONLY = [
    ("C", "C10_scene_build.py"),
    ("C", "C12_blue_to_red.py"),
    ("C", "C13_red_to_green.py"),
    ("C", "C14_green_to_yellow.py"),
    ("C", "C15_yellow_to_blue.py"),
]

ALL_SCRIPTS = LOAD_ONLY + EXECUTE

def script_path(group, filename):
    return os.path.join(C_DIR if group == "C" else T_DIR, filename)

print("\n=== Step 1: Loading scripts from disk ===")
for group, filename in ALL_SCRIPTS:
    filepath = script_path(group, filename)
    if not os.path.exists(filepath):
        print(f"  MISSING: {filepath}")
        continue
    existing = bpy.data.texts.get(filename)
    if existing:
        bpy.data.texts.remove(existing)
    bpy.data.texts.load(filepath, internal=False)
    print(f"  Loaded:  {filename}")

print("\n=== Step 2: Registering T panels ===")
for group, filename in EXECUTE:
    filepath = script_path(group, filename)
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
