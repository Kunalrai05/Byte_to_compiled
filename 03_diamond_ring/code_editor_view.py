"""
VS Code Dark Editor Overlay for the Lower Panel of the 9:16 Reel.
Renders syntax-highlighted Python code with line numbers, active line highlight,
and animated blinking cursor matching the aesthetic of viral creative coding reels.
"""

import math
from PIL import Image, ImageDraw, ImageFont


CODE_LINES = [
    (75, ""),
    (76, ""),
    (77, "def prongs():"),
    (78, "    P, N = [], []"),
    (79, "    for i in range(4):"),
    (80, "        a = TAU * (i + 0.5) / 4"),
    (81, "        base = np.array([0.08 * np.cos(a), R_BAND + 0.02, 0.08 * np.sin(a)])"),
    (82, "        tip = np.array([(GIRDLE_R + 0.015) * np.cos(a), TABLE_Y - 0.03, 0.0])"),
    (83, "        u, phi = [x.ravel() for x in np.meshgrid(np.linspace(0, 1, 40), np.linspace(0, TAU, 16))]"),
    (84, "        d = (tip - base) / np.linalg.norm(tip - base)"),
    (85, "        s = np.cross(d, [0, 0, 1.0]); s /= np.linalg.norm(s)"),
    (86, "        w = np.cross(s, d)"),
    (87, "        n = np.cos(phi)[:, None] * s + np.sin(phi)[:, None] * w"),
    (88, "        P.append(base + u[:, None] * (tip - base) + n * 0.022), N.append(n)"),
    (89, "    return np.concatenate(P), np.concatenate(N)"),
    (90, ""),
    (91, "BAND_P, BAND_N = band()"),
    (92, "GEM_P, GEM_N, GEM_M = diamond()"),
    (93, "PRONG_P, PRONG_N = prongs()"),
    (94, "")
]


# VS Code Dark+ Color Palette
C_BG       = (12, 12, 14, 255)       # Editor canvas background
C_GUTTER   = (85, 85, 95, 230)       # Line numbers
C_KEYWORD  = (210, 130, 200, 255)    # def, for, in, return (purple/magenta)
C_FUNC     = (225, 220, 150, 255)    # prongs, band, diamond (yellow)
C_VAR      = (160, 215, 250, 255)    # P, N, a, base, tip, d, s, w, n (light blue)
C_BUILTIN  = (80, 205, 195, 255)     # np, range, concatenate, meshgrid (cyan)
C_NUMBER   = (180, 205, 165, 255)    # 0.08, 4, 1, 40 (light green/mint)
C_PUNCT    = (215, 215, 220, 240)    # (), [], =, +, *, :, ,
C_HIGHLIGHT= (58, 28, 45, 210)       # Active line highlight band (muted wine/pink)
C_CURSOR   = (255, 160, 200, 255)    # Blinking cursor


class CodeEditorView:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._init_fonts()

    def _init_fonts(self):
        """Load crisp monospace programming font."""
        mono_candidates = [
            ("consola.ttf", "consolab.ttf"),
            ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf"),
            ("cour.ttf", "courbd.ttf"),
            ("arial.ttf", "arialbd.ttf")
        ]
        
        scale = self.height / 1280.0
        font_size = max(11, int(15.5 * scale))
        
        self.font_code = None
        for reg_c, _ in mono_candidates:
            try:
                self.font_code = ImageFont.truetype(reg_c, font_size)
                break
            except Exception:
                continue
                
        if self.font_code is None:
            self.font_code = ImageFont.load_default()

    def tokenize_line(self, text):
        """
        Split a python code line into syntax-highlighted colored tokens.
        """
        import re
        tokens = []
        pattern = r'(\bdef\b|\bfor\b|\bin\b|\breturn\b|\bnp\b|\brange\b|\bconcatenate\b|\bmeshgrid\b|\barray\b|\bcross\b|\blinalg\b|\bnorm\b|\bappend\b|\bravel\b|\blinspace\b|\bcos\b|\bsin\b|\bTAU\b|\bR_BAND\b|\bGIRDLE_R\b|\bTABLE_Y\b|\d+\.\d+|\d+|[a-zA-Z_][a-zA-Z0-9_]*|[.,()\[\]=+\-/*;:]|\s+)'
        parts = re.findall(pattern, text)
        
        keywords = {"def", "for", "in", "return"}
        builtins = {"np", "range", "concatenate", "meshgrid", "array", "cross", "linalg", "norm", "append", "ravel", "linspace", "cos", "sin"}
        constants = {"TAU", "R_BAND", "GIRDLE_R", "TABLE_Y"}
        funcs = {"prongs", "band", "diamond"}
        
        for p in parts:
            if p in keywords:
                tokens.append((p, C_KEYWORD))
            elif p in funcs:
                tokens.append((p, C_FUNC))
            elif p in builtins:
                tokens.append((p, C_BUILTIN))
            elif p in constants:
                tokens.append((p, C_NUMBER))
            elif re.match(r'^\d+(\.\d+)?$', p):
                tokens.append((p, C_NUMBER))
            elif re.match(r'^[(),\[\]=+\-/*;:]$', p):
                tokens.append((p, C_PUNCT))
            elif p.strip():
                tokens.append((p, C_VAR))
            else:
                tokens.append((p, (0, 0, 0, 0))) # Whitespace
                
        return tokens

    def render_editor(self, t, active_line=79):
        """
        Render the VS Code editor lower pane onto a PIL RGBA Image.
        """
        img = Image.new("RGBA", (self.width, self.height), C_BG)
        draw = ImageDraw.Draw(img)

        # Subtle top border line separating ASCII view from Code Editor
        draw.line([(0, 0), (self.width, 0)], fill=(45, 45, 55, 240), width=1)

        scale = self.height / 560.0
        line_height = int(22.5 * scale)
        start_y = int(16 * scale)
        gutter_width = int(48 * (self.width / 720.0))
        code_start_x = gutter_width + int(12 * (self.width / 720.0))

        # Gutter dividing line
        draw.line([(gutter_width - 6, 0), (gutter_width - 6, self.height)],
                  fill=(28, 28, 35, 200), width=1)

        cursor_blink = (int(t * 2.5) % 2 == 0)

        for idx, (line_num, line_text) in enumerate(CODE_LINES):
            y = start_y + idx * line_height
            if y > self.height - 10:
                break

            # Active line highlight band
            if line_num == active_line:
                draw.rectangle([0, y - 2, self.width, y + line_height - 2], fill=C_HIGHLIGHT)
                # Gutter line indicator
                draw.rectangle([0, y - 2, 3, y + line_height - 2], fill=(230, 100, 160, 255))

            # Draw Line Number
            line_str = f"{line_num:2d}"
            l_col = (220, 220, 235, 250) if line_num == active_line else C_GUTTER
            draw.text((12, y), line_str, fill=l_col, font=self.font_code)

            # Draw Syntax Highlighted Code
            tokens = self.tokenize_line(line_text)
            curr_x = code_start_x
            for tok_text, tok_color in tokens:
                draw.text((curr_x, y), tok_text, fill=tok_color, font=self.font_code)
                bbox = draw.textbbox((curr_x, y), tok_text, font=self.font_code)
                curr_x = bbox[2]

            # Draw Cursor on Active Line
            if line_num == active_line and cursor_blink:
                cursor_x = curr_x + 3
                draw.rectangle([cursor_x, y + 2, cursor_x + 8, y + line_height - 5], fill=C_CURSOR)

        return img
