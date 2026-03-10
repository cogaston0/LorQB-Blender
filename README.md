\# LorQB - Lord of the Quantum Balls

\*\*Blender Version:\*\* 5.0.1  

\*\*Original Design:\*\* Jose R. Velazquez © 2014  

\*\*Developer:\*\* Carlos  

\*\*AI System:\*\* Rukmini Trio (Claude + ChatGPT + NotebookLM)



\## Project Structure

scripts/

&nbsp; construction/   -> Scene building scripts (stable, do not modify)
&nbsp;&nbsp;&nbsp; lorqb_with_pivots.py          -> Creates hollow cubes, ball, and hinge pivots

&nbsp; animation/      -> Per-sequence animation scripts (C12, C15, etc.)
&nbsp;&nbsp;&nbsp; lorqb_blue_to_red.py          -> Blue → Red (hinge rotation, ball transfer)
&nbsp;&nbsp;&nbsp; lorqb_green_flip_cycle.py     -> Green flip cycle (Green → Yellow)
&nbsp;&nbsp;&nbsp; lorqb_red_to_green_C13.py     -> C13: Red → Green (frames 241–480)
&nbsp;&nbsp;&nbsp; 5lorqb_yellow_to_blue_C15.py  -> C15: Yellow → Blue (hinge rotation)

&nbsp; diagnostic/     -> Debugging and state-check scripts

docs/

&nbsp; validation\_reports/  -> NotebookLM + ChatGPT verification outputs

&nbsp; sequence\_logs/       -> Per-sequence progress notes



\## Cube Chain Topology

Yellow — Green — Red — Blue (snake chain, hinged on top)



\## Level 1 Status

\- Goal: complete all sequences for Level 1 with modular, reorderable scripts.

\- Current focus: C15 (Yellow -> Blue).



\## Key Design Notes

\- Ball starts outside the cubes at the beginning of each turn.

\- Current dev order: Blue -> Red -> Green -> Yellow (temporary).

\- Future: shuffle can select any cube order; scripts must support any permutation.



\## Key Rules

\- Script-only operations (no manual Blender UI)

\- Commit after every confirmed working step

