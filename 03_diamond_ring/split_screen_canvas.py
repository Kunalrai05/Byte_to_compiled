"""
Split-Screen Compositor for 9:16 Vertical Video Reel.
Combines:
- Top 55%: Glowing 3D ASCII Diamond Ring with starburst glints and telemetry.
- Bottom 45%: VS Code editor with line numbers, code syntax highlighting & blinking cursor.
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ascii_diamond import ASCIIDiamondRenderer
from code_editor_view import CodeEditorView


class SplitScreenCanvas:
    def __init__(self, width=720, height=1280):
        self.width = width
        self.height = height
        
        # Split ratio: 55% for top 3D ASCII viewport, 45% for bottom code editor
        self.top_h = int(height * 0.55)
        self.bot_h = height - self.top_h
        
        # ASCII Grid Resolution (approx 76 cols x 52 rows fits perfectly in top panel)
        self.cols = 76
        self.rows = 52
        self.ascii_renderer = ASCIIDiamondRenderer(cols=self.cols, rows=self.rows)
        self.editor_view = CodeEditorView(width=self.width, height=self.bot_h)
        
        self._init_fonts()

    def _init_fonts(self):
        """Initialize fonts for ASCII characters and telemetry HUD."""
        mono_candidates = [
            ("consola.ttf", "consolab.ttf"),
            ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf"),
            ("cour.ttf", "courbd.ttf"),
            ("arial.ttf", "arialbd.ttf")
        ]
        
        scale = self.width / 720.0
        char_font_size = max(9, int(13 * scale))
        hud_font_size = max(9, int(12.5 * scale))
        
        self.font_ascii = None
        self.font_hud = None
        self.font_hud_bold = None

        for reg_c, bold_c in mono_candidates:
            try:
                self.font_ascii = ImageFont.truetype(reg_c, char_font_size)
                self.font_hud = ImageFont.truetype(reg_c, hud_font_size)
                self.font_hud_bold = ImageFont.truetype(bold_c, hud_font_size)
                break
            except Exception:
                continue

        if self.font_ascii is None:
            self.font_ascii = ImageFont.load_default()
            self.font_hud = ImageFont.load_default()
            self.font_hud_bold = ImageFont.load_default()

    def render_composite_frame(self, t):
        """
        Render a full-resolution 9:16 vertical video frame.
        Returns: PIL Image (RGBA)
        """
        composite = Image.new("RGBA", (self.width, self.height), (3, 3, 5, 255))
        draw = ImageDraw.Draw(composite)

        # ---------------------------------------------------------------------
        # 1. TOP PANE: 3D ASCII DIAMOND RING
        # ---------------------------------------------------------------------
        char_mat, bright_mat, glint_mat, stats = self.ascii_renderer.render_frame(t)

        cell_w = self.width / float(self.cols)
        cell_h = (self.top_h - 70) / float(self.rows) # Reserve margins for top & bottom telemetry
        offset_y = 28 # Top margin

        # Draw ASCII characters with luminance-based silver/diamond glow
        for r in range(self.rows):
            for c in range(self.cols):
                ch = char_mat[r][c]
                if ch == " ":
                    continue

                b = bright_mat[r, c]
                is_glint = glint_mat[r, c]

                # Position character
                x_pos = int(c * cell_w + cell_w * 0.15)
                y_pos = int(offset_y + r * cell_h)

                if is_glint:
                    # Intense Dazzling Diamond Sparkle (Bright White + Cyan Bloom)
                    draw.text((x_pos, y_pos), ch, fill=(255, 255, 255, 255), font=self.font_ascii)
                else:
                    # Metallic platinum / diamond gradient
                    val = int(min(255, max(40, b * 255.0)))
                    c_rgb = (val, val, min(255, int(val * 1.08)), 240)
                    draw.text((x_pos, y_pos), ch, fill=c_rgb, font=self.font_ascii)

        # ---------------------------------------------------------------------
        # 2. TELEMETRY OVERLAYS ON TOP PANE (Exact match to reference reel)
        # ---------------------------------------------------------------------
        # Top-Right Timestamp: "• f 08.07s"
        time_str = f"• f {t:05.2f}s"
        bbox_tr = draw.textbbox((0, 0), time_str, font=self.font_hud)
        w_tr = bbox_tr[2] - bbox_tr[0]
        # Red / coral dot
        dot_x = self.width - 24 - w_tr
        top_y = 16
        draw.text((dot_x, top_y), "•", fill=(248, 113, 113, 240), font=self.font_hud)
        draw.text((dot_x + 12, top_y), f"f {t:05.2f}s", fill=(215, 220, 230, 220), font=self.font_hud)

        # Bottom of Top Pane (Telemetry Info Bar above the code editor)
        # Left side:
        # @kunalrai · 2026
        # rotation 056.00°   glints 272
        # letters 1,366
        # $ py art.py
        info_y = self.top_h - 68
        line1 = "@kunalrai · 2026"
        line2 = f"rotation {stats['rotation_deg']:06.2f}°   glints {stats['glint_count']}"
        line3 = f"letters {stats['letter_count']:,}"
        line4 = "$ py art.py"

        hud_dim = (140, 145, 155, 190)
        hud_bright = (225, 230, 240, 230)

        draw.text((22, info_y), line1, fill=hud_dim, font=self.font_hud)
        draw.text((22, info_y + 15), line2, fill=hud_dim, font=self.font_hud)
        draw.text((22, info_y + 30), line3, fill=hud_dim, font=self.font_hud)
        draw.text((22, info_y + 45), line4, fill=hud_bright, font=self.font_hud_bold)

        # Right side:
        # running - 30 fps
        fps_str = "running - 30 fps"
        bbox_fps = draw.textbbox((0, 0), fps_str, font=self.font_hud)
        w_fps = bbox_fps[2] - bbox_fps[0]
        draw.text((self.width - 22 - w_fps, info_y + 45), fps_str, fill=hud_dim, font=self.font_hud)

        # ---------------------------------------------------------------------
        # 3. BOTTOM PANE: VS CODE CODE EDITOR
        # ---------------------------------------------------------------------
        # Cycle active highlighted line smoothly over time (e.g. lines 79, 81, 84, 88)
        cycle_lines = [77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 91, 92, 93]
        line_idx = int((t * 0.8)) % len(cycle_lines)
        active_line = cycle_lines[line_idx]

        editor_img = self.editor_view.render_editor(t, active_line=active_line)
        composite.paste(editor_img, (0, self.top_h))

        return composite
