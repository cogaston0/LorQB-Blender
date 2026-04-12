# LorQB - Lord of the Quantum Balls

**Blender Version:** 5.1.0 

**Original Design:** Jose R. Velazquez © 2014  

**Developer:** Carlos  

**AI System:** Rukmini Trio (Claude + ChatGPT + NotebookLM)

## Project Structure

C_series/

- C-series Python files (C01, C10, C12, C13, C14, C15)

T_series/

- T-series Python files (T01, T02, T03, T04)

Root support files:

- UTIL_load_all_scripts.py
- C17_Master_Runner.blend
- LorQB Video Game.pdf
- README.md

## Cube Chain Topology

Yellow — Green — Red — Blue (snake chain, hinged on top)

## Level 1 Status

- Goal: complete all sequences for Level 1 with modular, reorderable scripts.

- Current focus: C15 (Yellow -> Blue).

## Key Design Notes

- Ball starts outside the cubes at the beginning of each turn.

- Current dev order: Blue -> Red -> Green -> Yellow (temporary).

- Future: shuffle can select any cube order; scripts must support any permutation.

## Key Rules

- Script-only operations (no manual Blender UI)

- Commit after every confirmed working step
