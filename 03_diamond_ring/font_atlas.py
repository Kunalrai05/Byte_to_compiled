"""
Font Atlas Generator for the Binary / Coded Word Matrix Diamond Ring.
Episode 03: Byte to Compiled.

Generates a 512x512 texture atlas containing monospaced glyphs:
1. ASCII Luminance Density Ramp: ' ', '.', ':', '-', '=', '+', '*', '#', '%', '@'
2. Binary Digits & Nibbles: '0', '1', '00', '11', '01', '10', '101', '010'
3. Code Symbols: '{', '}', '[', ']', '(', ')', '<', '>', ';', ':', '/', '|', '&', '!', '?', '$'
4. Coded Words & Keywords: 'def', 'var', 'val', 'vec', 'mat', 'rot', 'rad', 'sin', 'cos', 'gem',
   'void', 'for', 'hex', '0x1', '0xF', 'ring'
5. Machine / System Tokens: 'byte', 'math', 'code', 'true', 'null', '1010', '0101', '1100', '0011',
   '1111', '0000', 'loop', 'call', 'ret', 'link', 'node'
"""

import os
from PIL import Image, ImageDraw, ImageFont


def build_font_atlas(tile_w=32, tile_h=32, cols=16, rows=16):
    """
    Constructs a 512x512 grayscale texture atlas of monospaced coded glyphs.
    Returns:
        atlas_bytes (bytes): Raw grayscale (L) pixel bytes.
        atlas_size (tuple): (width, height)
    """
    atlas_w = cols * tile_w
    atlas_h = rows * tile_h

    img = Image.new('L', (atlas_w, atlas_h), color=0)
    draw = ImageDraw.Draw(img)

    # Search for standard crisp monospace fonts on Windows
    font_candidates = [
        'C:/Windows/Fonts/consola.ttf',      # Consolas (VS Code standard)
        'C:/Windows/Fonts/cour.ttf',         # Courier New
        'C:/Windows/Fonts/lucon.ttf',        # Lucida Console
    ]
    font_path = None
    for cand in font_candidates:
        if os.path.exists(cand):
            font_path = cand
            break

    try:
        if font_path:
            font_main = ImageFont.truetype(font_path, 25)
            font_mid = ImageFont.truetype(font_path, 19)
            font_small = ImageFont.truetype(font_path, 14)
        else:
            font_main = font_mid = font_small = ImageFont.load_default()
    except Exception:
        font_main = font_mid = font_small = ImageFont.load_default()

    glyph_map = {
        # Row 0: ASCII Density Ramp (0-9)
        0: ' ', 1: '.', 2: ':', 3: '-', 4: '=', 5: '+', 6: '*', 7: '#', 8: '%', 9: '@',

        # Row 1: Binary Digits & Pairs (16-23)
        16: '0', 17: '1', 18: '00', 19: '11', 20: '01', 21: '10', 22: '101', 23: '010',

        # Row 2: Code Brackets & Operators (32-47)
        32: '{', 33: '}', 34: '[', 35: ']', 36: '(', 37: ')', 38: '<', 39: '>',
        40: ';', 41: ':', 42: '/', 43: '|', 44: '&', 45: '!', 46: '?', 47: '$',

        # Row 3: Programming Keywords & Geometry Tokens (48-63)
        48: 'def', 49: 'var', 50: 'val', 51: 'vec', 52: 'mat', 53: 'rot', 54: 'rad', 55: 'sin',
        56: 'cos', 57: 'gem', 58: 'void', 59: 'for', 60: 'hex', 61: '0x1', 62: '0xF', 63: 'ring',

        # Row 4: Machine Bytes & Logic Tokens (64-79)
        64: 'byte', 65: 'math', 66: 'code', 67: 'true', 68: 'null', 69: '1010', 70: '0101', 71: '1100',
        72: '0011', 73: '1111', 74: '0000', 75: 'loop', 76: 'call', 77: 'ret', 78: 'link', 79: 'node'
    }

    for idx, tok in glyph_map.items():
        c = idx % cols
        r = idx // cols
        x0 = c * tile_w
        y0 = r * tile_h

        if len(tok) == 1:
            f = font_main
        elif len(tok) == 2:
            f = font_mid
        else:
            f = font_small

        bbox = draw.textbbox((0, 0), tok, font=f)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = x0 + (tile_w - tw) // 2
        ty = y0 + (tile_h - th) // 2 - bbox[1]
        draw.text((tx, ty), tok, fill=255, font=f)

    return img.tobytes(), (atlas_w, atlas_h)
