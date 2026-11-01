"""
Neuro-Imaging HUD (Heads-Up Display) overlay for Synaptic Connectome.
Includes live real-time EEG brainwave oscilloscope, cortical telemetry,
stage indicators, and sci-fi neural diagnostics.
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class NeuroHUD:
    def __init__(self, width=1536, height=864):
        self.width = width
        self.height = height
        self._load_fonts()

    def _load_fonts(self):
        font_names = [
            "Consolas", "consolab.ttf", "consola.ttf",
            "Courier New", "cour.ttf", "Arial", "arial.ttf"
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
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        progress = min(1.0, max(0.0, current_time / total_duration))
        w = self.width
        h = self.height
        is_widescreen = (w / float(h)) > 1.2

        # Color palette
        c_cyan_glow = (60, 225, 255, 240)
        c_violet_glow = (185, 110, 255, 240)
        c_gold_glow = (255, 215, 90, 240)
        c_white = (245, 250, 255, 240)
        c_dim = (160, 190, 220, 150)
        c_bar_bg = (40, 60, 85, 110)

        margin_x = int(w * 0.05) if is_widescreen else int(w * 0.08)
        top_y = int(h * 0.05)
        right_x = w - margin_x

        # 1. Header (Top HUD)
        draw.text((margin_x, top_y), "SYNAPTIC CONNECTOME", font=self.font_title, fill=c_white)
        draw.text((margin_x, top_y + int(h * 0.038)), "ATLAS: HUMAN BRAIN CORTICAL MAPPING // BRODMANN 1-52", font=self.font_small, fill=c_dim)

        line_y = top_y + int(h * 0.065)
        draw.line([(margin_x, line_y), (right_x, line_y)], fill=(100, 140, 180, 80), width=1)
        num_ticks = 20 if is_widescreen else 12
        for tick in range(num_ticks):
            tx = int(margin_x + tick * ((right_x - margin_x) / float(num_ticks - 1)))
            draw.line([(tx, line_y - 3), (tx, line_y + 3)], fill=(140, 180, 220, 130), width=1)

        # 2. Live Oscillating EEG Waveform (Top Right)
        eeg_w = int(w * 0.22) if is_widescreen else int(w * 0.35)
        eeg_h = int(h * 0.045)
        eeg_x = right_x - eeg_w
        eeg_y = top_y + int(h * 0.008)

        # EEG background box
        draw.rectangle([(eeg_x, eeg_y), (eeg_x + eeg_w, eeg_y + eeg_h)], outline=(80, 130, 180, 90), width=1)
        draw.text((eeg_x + 5, eeg_y - 12), "EEG TELEMETRY [GAMMA 42Hz]", font=self.font_small, fill=c_cyan_glow)

        # Draw dynamic EEG wave
        pts = []
        for xi in range(0, eeg_w, 2):
            norm_x = xi / float(eeg_w)
            # Superposition of brainwave frequencies
            wave = math.sin(norm_x * 24.0 - current_time * 8.0) * 0.4 + \
                   math.sin(norm_x * 50.0 - current_time * 16.0) * 0.25 + \
                   math.sin(norm_x * 12.0 + current_time * 4.0) * 0.2
            if current_time > 7.0: # High frequency bursts during action potentials
                wave += math.sin(norm_x * 110.0 - current_time * 28.0) * 0.15
            py = int(eeg_y + (eeg_h * 0.5) + wave * (eeg_h * 0.38))
            pts.append((eeg_x + xi, py))

        if len(pts) > 1:
            draw.line(pts, fill=c_cyan_glow, width=1)

        # 3. Stage Progression (Bottom HUD)
        if current_time < 3.5:
            stage_num = "STAGE 01"
            stage_desc = "CYTOARCHITECTURE & SOMA HUBS"
            stage_color = c_cyan_glow
        elif current_time < 7.5:
            stage_num = "STAGE 02"
            stage_desc = "AXONAL ARBORIZATION & MYELIN PATHWAYS"
            stage_color = c_violet_glow
        else:
            stage_num = "STAGE 03"
            stage_desc = "ACTION POTENTIALS & SYNAPTIC FIRING (ACTIVE)"
            stage_color = c_gold_glow

        bottom_y = int(h * 0.88)
        draw.text((margin_x, bottom_y), f"{stage_num} // {stage_desc}", font=self.font_sub, fill=stage_color)

        # Progress bar
        bar_x0 = margin_x
        bar_x1 = right_x
        bar_y = bottom_y + int(h * 0.038)
        bar_h = 3

        draw.line([(bar_x0, bar_y), (bar_x1, bar_y)], fill=c_bar_bg, width=bar_h)
        fill_x = int(bar_x0 + (bar_x1 - bar_x0) * progress)
        if fill_x > bar_x0:
            draw.line([(bar_x0, bar_y), (fill_x, bar_y)], fill=stage_color, width=bar_h)
            draw.ellipse([(fill_x - 3, bar_y - 3), (fill_x + 3, bar_y + 3)], fill=c_white)

        pct_text = f"{int(progress * 100):02d}% COMPILED"
        draw.text((margin_x, bar_y + int(h * 0.015)), pct_text, font=self.font_small, fill=c_dim)
        draw.text((right_x - int(w * 0.18) if is_widescreen else int(w * 0.65), bar_y + int(h * 0.015)), "CONNECTOME ENGINE v3.4", font=self.font_small, fill=c_dim)

        # 4. Corner tech brackets
        bracket_len = int(min(w, h) * 0.04)
        margin = int(min(w, h) * 0.035)
        bracket_color = (110, 150, 190, 120)

        draw.line([(margin, margin), (margin + bracket_len, margin)], fill=bracket_color, width=2)
        draw.line([(margin, margin), (margin, margin + bracket_len)], fill=bracket_color, width=2)

        draw.line([(w - margin, margin), (w - margin - bracket_len, margin)], fill=bracket_color, width=2)
        draw.line([(w - margin, margin), (w - margin, margin + bracket_len)], fill=bracket_color, width=2)

        draw.line([(margin, h - margin), (margin + bracket_len, h - margin)], fill=bracket_color, width=2)
        draw.line([(margin, h - margin), (margin, h - margin - bracket_len)], fill=bracket_color, width=2)

        draw.line([(w - margin, h - margin), (w - margin - bracket_len, h - margin)], fill=bracket_color, width=2)
        draw.line([(w - margin, h - margin), (w - margin, margin - bracket_len)], fill=bracket_color, width=2)

        return img
