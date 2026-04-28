# B01_shuffle_display.py  (Blender 5.0.1)
# LorQB / Cubolita — B01 Shuffle Display Mechanism
#
# Pure UI/data layer:
#   - Generates a random 4-color sequence (no adjacent repeats)
#   - Displays the sequence as 4 numbered colored slots in the N-panel
#   - Provides a single SHUFFLE button to regenerate
#
# Color labels are rendered as custom preview icons so the letters
# themselves appear in the cube's color (Blender label text cannot be
# tinted, so we draw the glyphs into a pixel buffer and register it
# as an icon via bpy.utils.previews).
#
# Does NOT touch any cube, hinge, or ball object.
# Does NOT clear animation data.
# Safe to run at any time.
# ============================================================================

import bpy
import os
import random
import struct
import zlib
import tempfile
from bpy.types import Operator, Panel
from bpy.props import StringProperty
from bpy.utils import previews as _previews


# ============================================================================
# Constants
# ============================================================================

COLOR_MAP = {
    "blue":   (0.20, 0.40, 1.00, 1.0),
    "red":    (1.00, 0.15, 0.15, 1.0),
    "green":  (0.20, 0.90, 0.25, 1.0),
    "yellow": (1.00, 0.95, 0.10, 1.0),
}
COLORS = ["blue", "red", "green", "yellow"]

DEFAULT_SEQUENCE = ",".join(COLORS)
SCENE_PROP_NAME = "lorqb_sequence"
MAX_SHUFFLE_TRIES = 20

COLOR_ABBREV = {
    "blue":   "BLU",
    "red":    "RED",
    "green":  "GRN",
    "yellow": "YEL",
}

FONT_SCALE = 5          # pixel-replication factor for the 5x7 bitmap (glyphs become 25x35)
ICON_W, ICON_H = 88, 40

# Module-level preview collection (created in register())
_preview_collection = None


# ============================================================================
# Tiny 5x7 bitmap font — only the glyphs we need: B L U R E D G N Y
# Each glyph is 7 rows of 5-bit values (MSB = leftmost pixel).
# ============================================================================

_FONT_5x7 = {
    'B': [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    'L': [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    'U': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    'E': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    'D': [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    'G': [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110],
    'N': [0b10001, 0b11001, 0b10101, 0b10101, 0b10011, 0b10001, 0b10001],
    'Y': [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    ' ': [0, 0, 0, 0, 0, 0, 0],
}

GLYPH_W, GLYPH_H = 5, 7
GLYPH_GAP = 1


# ============================================================================
# Shuffle logic
# ============================================================================

def _has_adjacent_repeats(seq):
    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            return True
    return False


def generate_sequence():
    """Return a random permutation of COLORS with no adjacent repeats."""
    seq = COLORS[:]
    for _ in range(MAX_SHUFFLE_TRIES):
        random.shuffle(seq)
        if not _has_adjacent_repeats(seq):
            return seq
    return seq


# ============================================================================
# Pixel-buffer text rendering + PNG writer
# ============================================================================

def _render_text_pixels(text, rgba, w=ICON_W, h=ICON_H, scale=FONT_SCALE):
    """Render text into an RGBA byte buffer (top-down rows), scaled by integer replication."""
    pixels = bytearray(w * h * 4)  # zero-initialised = transparent black

    sgw = GLYPH_W * scale
    sgh = GLYPH_H * scale
    sgap = GLYPH_GAP * scale

    text_w = len(text) * sgw + (len(text) - 1) * sgap
    x0 = max((w - text_w) // 2, 0)
    y0 = max((h - sgh) // 2, 0)

    cr = int(round(rgba[0] * 255))
    cg = int(round(rgba[1] * 255))
    cb = int(round(rgba[2] * 255))

    for ci, ch in enumerate(text):
        glyph = _FONT_5x7.get(ch.upper())
        if glyph is None:
            continue
        gx = x0 + ci * (sgw + sgap)
        for ry, row_bits in enumerate(glyph):
            for bx in range(GLYPH_W):
                if not ((row_bits >> (GLYPH_W - 1 - bx)) & 1):
                    continue
                # Fill an (scale x scale) block per source pixel
                for dy in range(scale):
                    py = y0 + ry * scale + dy
                    if py < 0 or py >= h:
                        continue
                    for dx in range(scale):
                        px = gx + bx * scale + dx
                        if px < 0 or px >= w:
                            continue
                        idx = (py * w + px) * 4
                        pixels[idx + 0] = cr
                        pixels[idx + 1] = cg
                        pixels[idx + 2] = cb
                        pixels[idx + 3] = 255
    return pixels


def _write_png(path, pixels, w=ICON_W, h=ICON_H):
    """Write an RGBA byte buffer as a PNG file (no PIL dependency)."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)

    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)  # filter byte: None
        raw.extend(pixels[y * stride:(y + 1) * stride])
    idat = zlib.compress(bytes(raw), 9)

    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


def _build_color_icons():
    """Generate a colored-letter PNG per color and load it as a preview icon."""
    global _preview_collection
    if _preview_collection is not None:
        try:
            _previews.remove(_preview_collection)
        except Exception:
            pass

    pcoll = _previews.new()
    tmp_dir = os.path.join(tempfile.gettempdir(), "lorqb_b01_icons")
    os.makedirs(tmp_dir, exist_ok=True)

    for color in COLORS:
        text = COLOR_ABBREV[color]
        rgba = COLOR_MAP[color]
        pixels = _render_text_pixels(text, rgba)
        path = os.path.join(tmp_dir, "lorqb_b01_" + color + ".png")
        _write_png(path, pixels)
        pcoll.load(color, path, 'IMAGE')

    _preview_collection = pcoll


# ============================================================================
# Operator
# ============================================================================

class LORQB_OT_B01Shuffle(Operator):
    bl_idname = "lorqb.b01_shuffle"
    bl_label = "Shuffle"
    bl_description = "Generate a new random 4-color sequence"

    def execute(self, context):
        seq = generate_sequence()
        context.scene.lorqb_sequence = ",".join(seq)
        print("=== B01 Shuffle: " + " → ".join(seq) + " ===")
        return {'FINISHED'}


# ============================================================================
# Panel
# ============================================================================

class LORQB_PT_b01_panel(Panel):
    bl_label = "LorQB — Shuffle"
    bl_idname = "LORQB_PT_b01_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LorQB"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        raw = scene.lorqb_sequence if hasattr(scene, "lorqb_sequence") else DEFAULT_SEQUENCE
        seq = [c.strip() for c in raw.split(",") if c.strip()]

        row = layout.row(align=True)
        for i, color in enumerate(seq):
            col = row.column(align=True)
            col.alignment = 'CENTER'
            col.scale_y = 0.85

            if _preview_collection is not None and color in _preview_collection:
                icon_id = _preview_collection[color].icon_id
                col.template_icon(icon_value=icon_id, scale=1.7)
            else:
                col.label(text=COLOR_ABBREV.get(color, color.upper()[:3]))

        layout.separator()
        layout.operator("lorqb.b01_shuffle", text="Shuffle", icon='FILE_REFRESH')


# ============================================================================
# Registration
# ============================================================================

_classes = (
    LORQB_OT_B01Shuffle,
    LORQB_PT_b01_panel,
)


def _unregister_all_lorqb():
    """Remove any stale instances of these classes before re-registering."""
    for cls in _classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


def register():
    global _preview_collection
    _unregister_all_lorqb()

    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.lorqb_sequence = StringProperty(
        name="LorQB Sequence",
        default=DEFAULT_SEQUENCE,
    )

    _build_color_icons()

    seq = generate_sequence()
    try:
        bpy.context.scene.lorqb_sequence = ",".join(seq)
    except AttributeError:
        pass

    print("=== B01 Shuffle Display Ready ===")
    print("Default sequence: " + " → ".join(seq))
    print("3D View → N-panel → LorQB → Shuffle section")


def unregister():
    global _preview_collection

    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    if hasattr(bpy.types.Scene, "lorqb_sequence"):
        try:
            del bpy.types.Scene.lorqb_sequence
        except Exception:
            pass

    if _preview_collection is not None:
        try:
            _previews.remove(_preview_collection)
        except Exception:
            pass
        _preview_collection = None


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
