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

\- Current focus: C15 (Yellow -> Blue).



\## Key Design Notes

\- Ball starts outside the cubes at the beginning of each turn.

\- Current dev order: Blue -> Red -> Green -> Yellow (temporary).

\- Future: shuffle can select any cube order; scripts must support any permutation.



\## Key Rules

\- Script-only operations (no manual Blender UI)

\- Commit after every confirmed working step



\## Python Scripts

| Script | Description |
|--------|-------------|
| C10\_scene\_build.py | Builds the initial LorQB scene: clears all objects, then creates four hollow colored cubes (Blue, Red, Green, Yellow) with circular holes, a ball inside Cube\_Blue, and three hinge pivot empties. |
| C12\_blue\_to\_red.py | Animates the Blue→Red sequence (frames 1–240): parents Cube\_Blue to Hinge\_Blue\_Red, rotates it 180° on the X-axis, and transfers the ball from Cube\_Blue to Cube\_Red at frame 120→121 using COPY\_TRANSFORMS constraints. |
| C13\_red\_to\_green.py | Animates the Red→Green sequence (frames 241–480): parents Cube\_Red to Hinge\_Red\_Green, rotates it 180° on the Y-axis, and transfers the ball from Cube\_Red to Cube\_Green at frame 360→361. |
| C14\_green\_to\_yellow.py | Animates the Green→Yellow sequence (frames 481–720): parents Cube\_Green to Hinge\_Green\_Yellow, rotates it 180° on the X-axis, and transfers the ball from Cube\_Green to Cube\_Yellow at frame 600→601. |
| C15\_yellow\_to\_blue.py | Keys Hinge\_Red\_Green with a 0°→180°→0° Y-axis rotation using CONSTANT interpolation for the Yellow→Blue transfer; currently implements the hinge-rotation block only. |
| lorQB\_Master\_Runnet | Python script (no .py extension) that registers a Blender N-panel ("LorQB Sequences") with operator buttons to run each animation sequence (C12–C15) individually. |

