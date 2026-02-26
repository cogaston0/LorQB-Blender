\# LorQB - Lord of the Quantum Balls

\*\*Blender Version:\*\* 5.0.1  

\*\*Original Design:\*\* Jose R. Velazquez © 2014  

\*\*Developer:\*\* Carlos  

\*\*AI System:\*\* Rukmini Trio (Claude + ChatGPT + NotebookLM)



\## Project Structure

scripts/

&nbsp; construction/   -> Scene building scripts (stable, do not modify)

&nbsp; animation/      -> Per-sequence animation scripts (C12, C15, etc.)

&nbsp; diagnostic/     -> Debugging and state-check scripts

docs/

&nbsp; validation\_reports/  -> NotebookLM + ChatGPT verification outputs

&nbsp; sequence\_logs/       -> Per-sequence progress notes



\## Cube Chain Topology

Yellow — Green — Red — Blue (snake chain, hinged on top)



\## Level 1 Status

\- Goal: complete all sequences for Level 1 with modular, reorderable scripts.

\- C12: Blue → Red (lorqb\_blue\_to\_red.py, frames 1–240) ✓

\- C13: Red → Green (lorqb\_red\_to\_green\_C13.py, frames 241–480) ✓

\- C16: Green → Yellow (scripts/animation/6lorqb\_green\_to\_yellow\_C16.py, frames 481–720) ✓

\- C15: Yellow → Blue (scripts/animation/5lorqb\_yellow\_to\_blue\_C15.py) — hinge block only; ball/seat/latch block pending.

\- Current focus: C15 complete ball transfer block.



\## Key Design Notes

\- Ball starts outside the cubes at the beginning of each turn.

\- Current dev order: Blue -> Red -> Green -> Yellow (temporary).

\- Future: shuffle can select any cube order; scripts must support any permutation.



\## Key Rules

\- Script-only operations (no manual Blender UI)

\- Commit after every confirmed working step

