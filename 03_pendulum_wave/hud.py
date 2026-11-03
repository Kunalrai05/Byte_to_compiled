"""
Physics Telemetry HUD (Heads-Up Display) overlay for Harmonic Pendulum Wave.
Adapts dynamically to both widescreen laptop desktop (16:9) and vertical reels (9:16).
Generates technical typography, stage progression indicators,
real-time wave pattern classification, and frequency telemetry.
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pendulum_geometry

class PendulumHUD:
    def __init__(self, width=1536, height=864):
        self.width = width
        self.height = height
        self._load_fonts()

    def _load_fonts(self):
        """Load clean monospaced or modern sans-serif fonts."""
        font_names = [
            "C:\\Windows\\Fonts\\YuGothM.ttc",
            "C:\\Windows\\Fonts\\msgothic.ttc",
            "C:\\Windows\\Fonts\\consolab.ttf",
            "C:\\Windows\\Fonts\\consola.ttf",
            "Consolas", "Courier New", "cour.ttf", "Arial", "arial.ttf"
        ]
        self.font_title = None
        self.font_sub = None
        self.font_small = None

        base_dim = min(self.width, self.height)
        size_title = max(14, int(base_dim * 0.038))
        size_sub = max(11, int(base_dim * 0.024))
        size_small = max(9, int(base_dim * 0.018))

        for name in font_names:
            try:
                self.font_title = ImageFont.truetype(name, size_title)
                self.font_sub = ImageFont.truetype(name, size_sub)
                self.font_small = ImageFont.truetype(name, size_small)
                break
            except Exception:
                continue

        if self.font_title is None:
            self.font_title = ImageFont.load_default()
            self.font_sub = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def render_overlay(self, current_time, total_duration=14.0):
        """
        Render transparent RGBA HUD overlay image for the given timestamp.
        Returns: PIL Image (RGBA)
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        progress = min(1.0, max(0.0, current_time / total_duration))
        w = self.width
        h = self.height
        is_widescreen = (w / float(h)) > 1.2

        # Aesthetic color palette
        c_cyan_glow  = (140, 240, 255, 230)
        c_white      = (248, 250, 255, 240)
        c_dim        = (175, 200, 225, 160)
        c_bar_bg     = (40, 60, 85, 110)

        pattern_name, pattern_color = pendulum_geometry.get_wave_pattern_info(current_time, total_duration)

        # 1. Header (Top HUD)
        margin_x = int(w * 0.05) if is_widescreen else int(w * 0.08)
        top_y = int(h * 0.05)

        draw.text((margin_x, top_y), "HARMONIC PENDULUM WAVE // 調和振り子", font=self.font_title, fill=c_white)
        draw.text((margin_x, top_y + int(h * 0.038)), "KINETIC HARMONICS // FREQUENCY DISPERSION & COHERENCE", font=self.font_small, fill=c_dim)

        # Technical tick marks across top
        line_y = top_y + int(h * 0.065)
        right_x = w - margin_x
        draw.line([(margin_x, line_y), (right_x, line_y)], fill=(140, 170, 210, 80), width=1)
        num_ticks = 20 if is_widescreen else 12
        for tick in range(num_ticks):
            tx = int(margin_x + tick * ((right_x - margin_x) / float(num_ticks - 1)))
            draw.line([(tx, line_y - 3), (tx, line_y + 3)], fill=(160, 210, 240, 140), width=1)

        # Top-right telemetry
        phase_deg = (current_time / total_duration) * 360.0
        if is_widescreen:
            telemetry = f"HARMONICS: N = 24  //  CYCLE: T = 14.0s  //  PHASE: {phase_deg:.1f}°"
            telem_y = top_y + int(h * 0.012)
        else:
            telemetry = f"HARMONICS: N = 24  //  T = 14.0s  //  φ: {phase_deg:.0f}°"
            telem_y = line_y + int(h * 0.010)

        try:
            bbox_t = draw.textbbox((0, 0), telemetry, font=self.font_small)
            telem_w = bbox_t[2] - bbox_t[0]
            telem_x = right_x - telem_w
        except Exception:
            telem_x = right_x - int(w * 0.38)
        draw.text((telem_x, telem_y), telemetry, font=self.font_small, fill=c_cyan_glow)

        # 2. Stage progression (Bottom HUD)
        bottom_y = int(h * 0.88)
        draw.text((margin_x, bottom_y), f"PATTERN // {pattern_name}", font=self.font_sub, fill=pattern_color)

        # Progress bar
        bar_x0 = margin_x
        bar_x1 = right_x
        bar_y = bottom_y + int(h * 0.038)
        bar_h = 3

        draw.line([(bar_x0, bar_y), (bar_x1, bar_y)], fill=c_bar_bg, width=bar_h)
        fill_x = int(bar_x0 + (bar_x1 - bar_x0) * progress)
        if fill_x > bar_x0:
            draw.line([(bar_x0, bar_y), (fill_x, bar_y)], fill=pattern_color, width=bar_h)
            draw.ellipse([(fill_x - 3, bar_y - 3), (fill_x + 3, bar_y + 3)], fill=c_white)

        # Sub-status
        pct_text = f"{int(progress * 100):02d}% CYCLE COMPILED"
        draw.text((margin_x, bar_y + int(h * 0.015)), pct_text, font=self.font_small, fill=c_dim)

        stats_text = "f_min: 1.14 Hz  //  f_max: 2.79 Hz  //  RESONANCE: 100%"
        try:
            bbox_s = draw.textbbox((0, 0), stats_text, font=self.font_small)
            stats_w = bbox_s[2] - bbox_s[0]
            stats_x = right_x - stats_w
        except Exception:
            stats_x = right_x - int(w * 0.35)
        draw.text((stats_x, bar_y + int(h * 0.015)), stats_text, font=self.font_small, fill=c_dim)

        # 3. Corner tech brackets
        bracket_len = int(min(w, h) * 0.04)
        margin = int(min(w, h) * 0.035)
        bracket_color = (140, 190, 230, 130)

        # Top-left
        draw.line([(margin, margin), (margin + bracket_len, margin)], fill=bracket_color, width=2)
        draw.line([(margin, margin), (margin, margin + bracket_len)], fill=bracket_color, width=2)

        # Top-right
        draw.line([(w - margin, margin), (w - margin - bracket_len, margin)], fill=bracket_color, width=2)
        draw.line([(w - margin, margin), (w - margin, margin + bracket_len)], fill=bracket_color, width=2)

        # Bottom-left
        draw.line([(margin, h - margin), (margin + bracket_len, h - margin)], fill=bracket_color, width=2)
        draw.line([(margin, h - margin), (margin, margin - bracket_len)], fill=bracket_color, width=2)

        # Bottom-right
        draw.line([(w - margin, h - margin), (w - margin - bracket_len, h - margin)], fill=bracket_color, width=2)
        draw.line([(w - margin, h - margin), (w - margin, margin - bracket_len)], fill=bracket_color, width=2)

        return img

    def draw_on_opencv_frame(self, frame_bgr, current_time, total_duration=14.0):
        """Alpha composite HUD onto an OpenCV BGR frame (numpy uint8)."""
        overlay = self.render_overlay(current_time, total_duration)
        overlay_np = np.array(overlay)

        alpha = overlay_np[:, :, 3:4].astype(np.float32) / 255.0
        overlay_bgr = overlay_np[:, :, [2, 1, 0]].astype(np.float32)

        base = frame_bgr.astype(np.float32)
        blended = (1.0 - alpha) * base + alpha * overlay_bgr
        return np.clip(blended, 0, 255).astype(np.uint8)
