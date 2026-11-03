"""
Porsche Motorsport Cockpit & Telemetry HUD Overlay Generator.
Generates:
1. 9,000 RPM Racing Tachometer with needle sweep and shift lights.
2. PDK Gear Indicator (1 - 7) and digital speed readout (KM/H).
3. Active DRS Badge (Closed: 860 kg Downforce <-> Active: Low Drag Overtake).
4. G-Force circle / accelerometer (pulling up to 1.84 G).
5. Nürburgring Nordschleife lap time (06:49.328) with sector delta.
6. 60-Year Heritage Evolution Banner (1974 930 Turbo -> 2024 992 GT3 RS).
7. Top & bottom telemetry brackets, corner reticles, and cyber-motorsport styling.
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class PorscheHUD:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._init_fonts()

    def _init_fonts(self):
        """Load crisp system fonts or fall back gracefully to default PIL font."""
        font_candidates = [
            ("segoeuib.ttf", "segoeui.ttf"),     # Windows Segoe UI Bold / Regular
            ("consola.ttf", "consolab.ttf"),    # Windows Consolas
            ("arialbd.ttf", "arial.ttf"),       # Arial Bold
            ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf")
        ]

        self.font_large = None
        self.font_med = None
        self.font_small = None
        self.font_mono = None

        # Scaling base relative to 1080p
        scale = max(0.55, min(1.35, self.height / 1080.0))
        size_large = int(32 * scale)
        size_med   = int(19 * scale)
        size_small = int(14 * scale)
        size_tiny  = int(11 * scale)

        for bold_c, reg_c in font_candidates:
            try:
                self.font_large = ImageFont.truetype(bold_c, size_large)
                self.font_med = ImageFont.truetype(bold_c, size_med)
                self.font_small = ImageFont.truetype(reg_c, size_small)
                self.font_mono = ImageFont.truetype(reg_c, size_tiny)
                break
            except Exception:
                continue

        if self.font_large is None:
            self.font_large = ImageFont.load_default()
            self.font_med = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_mono = ImageFont.load_default()

    def generate_hud_image(self, t, total_duration, throttle_pct=0.0, drs_active=False, morph_pct=1.0):
        """
        Render a full-resolution RGBA HUD image overlay.
        t: Current timestamp in seconds
        total_duration: Total video length (14.0s)
        throttle_pct: 0.0 to 1.0 (engine throttle)
        drs_active: Boolean or float (DRS wing flap state)
        morph_pct: 0.0 (1974 930 Turbo) to 1.0 (2024 992 GT3 RS)
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Scale helpers
        w, h = self.width, self.height
        is_vertical = (h > w)

        # Calculate dynamic driving telemetry based on timestamp t
        # Realistic acceleration curve:
        # 0s - 3s: Idle / Rev warmup in garage (morphing phase)
        # 3s - 7.5s: 1st -> 2nd -> 3rd gear pull, 4,500 to 8,200 RPM
        # 7.5s - 11s: 4th gear scream to 9,000 RPM (shift lights blink!)
        # 11s - 14s: 5th gear high-speed DRS blast, 296 KM/H
        if t < 3.0:
            rpm = 1200 + 1800 * math.sin(t * 4.0) ** 2
            gear = "N"
            speed_kmh = 0
            lat_g = 0.0
        elif t < 7.5:
            dt = t - 3.0
            gear = "2" if dt < 2.0 else "3"
            rpm = 5000 + 3800 * ((dt % 2.2) / 2.2)
            speed_kmh = int(60 + dt * 32.0)
            lat_g = 1.42 + 0.35 * math.sin(t * 3.5)
        elif t < 11.0:
            dt = t - 7.5
            gear = "4"
            rpm = 6500 + 2500 * (dt / 3.5)
            speed_kmh = int(200 + dt * 22.0)
            lat_g = 1.78 + 0.12 * math.cos(t * 2.5)
        else:
            dt = t - 11.0
            gear = "5"
            rpm = 8400 + 600 * math.sin(dt * 3.0)
            speed_kmh = min(296, int(275 + dt * 7.0))
            lat_g = 1.84

        # Override with manual throttle if provided
        if throttle_pct > 0.01:
            rpm = max(rpm, 1200 + throttle_pct * 7800)

        # ---------------------------------------------------------------------
        # 1. TOP HEADER & TELEMETRY RETICLES
        # ---------------------------------------------------------------------
        pad = int(min(w, h) * 0.035)

        if is_vertical:
            # Clean stacked layout for 9:16 mobile display
            title_main = "PORSCHE MOTORSPORT // WEISSACH"
            draw.text((pad, pad), title_main, fill=(240, 245, 255, 230), font=self.font_med)

            if morph_pct < 0.6:
                model_sub = "HERITAGE // 1974 930 TURBO (260 HP)"
                tag_color = (255, 180, 50, 240)
            else:
                model_sub = "CHASSIS // 992 GT3 RS (9000 RPM • 525 HP)"
                tag_color = (100, 230, 255, 240)
            draw.text((pad, pad + int(self.height * 0.024)), model_sub, fill=tag_color, font=self.font_small)

            nurb_line = "NÜRBURGRING: 06:49.328"
            delta_line = "DELTA: -0.42s"
            draw.text((pad, pad + int(self.height * 0.046)), nurb_line, fill=(255, 255, 255, 220), font=self.font_small)

            bbox_d = draw.textbbox((0, 0), delta_line, font=self.font_small)
            wd = bbox_d[2] - bbox_d[0]
            draw.text((w - pad - wd, pad + int(self.height * 0.046)), delta_line, fill=(50, 255, 120, 240), font=self.font_small)
        else:
            # Widescreen laptop display
            title_main = "PORSCHE MOTORSPORT // WEISSACH AERO LAB"
            draw.text((pad, pad), title_main, fill=(240, 245, 255, 230), font=self.font_med)

            if morph_pct < 0.6:
                model_sub = "HERITAGE // 1974 PORSCHE 930 TURBO (3.0L TURBO FLAT-6 • 260 HP)"
                tag_color = (255, 180, 50, 240)
            else:
                model_sub = "CHASSIS // 992 GT3 RS (4.0L NA FLAT-6 • 9000 RPM • 525 HP)"
                tag_color = (100, 230, 255, 240)
            draw.text((pad, pad + int(self.height * 0.032)), model_sub, fill=tag_color, font=self.font_small)

            nurburg_text = "NÜRBURGRING LAP: 06:49.328"
            delta_text = "SECTOR DELTA: -0.42s"
            bbox_nurb = draw.textbbox((0, 0), nurburg_text, font=self.font_small)
            w_nurb = bbox_nurb[2] - bbox_nurb[0]
            draw.text((w - pad - w_nurb, pad), nurburg_text, fill=(255, 255, 255, 220), font=self.font_small)

            bbox_delta = draw.textbbox((0, 0), delta_text, font=self.font_small)
            w_delta = bbox_delta[2] - bbox_delta[0]
            draw.text((w - pad - w_delta, pad + int(self.height * 0.028)), delta_text, fill=(50, 255, 120, 240), font=self.font_small)

        # Corner Viewfinder Brackets
        ret_len = int(min(w, h) * 0.045)
        b_col = (140, 180, 210, 160)
        # Top-Left
        draw.line([(pad - 5, pad - 5), (pad - 5 + ret_len, pad - 5)], fill=b_col, width=2)
        draw.line([(pad - 5, pad - 5), (pad - 5, pad - 5 + ret_len)], fill=b_col, width=2)
        # Top-Right
        draw.line([(w - pad + 5, pad - 5), (w - pad + 5 - ret_len, pad - 5)], fill=b_col, width=2)
        draw.line([(w - pad + 5, pad - 5), (w - pad + 5, pad - 5 + ret_len)], fill=b_col, width=2)
        # Bottom-Left
        draw.line([(pad - 5, h - pad + 5), (pad - 5 + ret_len, h - pad + 5)], fill=b_col, width=2)
        draw.line([(pad - 5, h - pad + 5), (pad - 5, h - pad + 5 - ret_len)], fill=b_col, width=2)
        # Bottom-Right
        draw.line([(w - pad + 5, h - pad + 5), (w - pad + 5 - ret_len, h - pad + 5)], fill=b_col, width=2)
        draw.line([(w - pad + 5, h - pad + 5), (w - pad + 5, h - pad + 5 - ret_len)], fill=b_col, width=2)

        # ---------------------------------------------------------------------
        # 2. PORSCHE 9,000 RPM RACING TACHOMETER (BOTTOM-CENTER OR BOTTOM-LEFT)
        # ---------------------------------------------------------------------
        # Positioning:
        if is_vertical:
            tacho_cx = w // 2
            tacho_cy = int(h * 0.81)
            tacho_r  = int(w * 0.31)
        else:
            tacho_cx = int(w * 0.18)
            tacho_cy = int(h * 0.72)
            tacho_r  = int(min(w, h) * 0.22)

        # Draw Tachometer Arc Dial
        # 0 to 9,000 RPM maps to 135° to 405° (sweep of 270°)
        start_angle = 135.0
        sweep_range = 270.0
        rpm_ratio = min(1.0, max(0.0, rpm / 9000.0))

        # Background Arc
        draw.arc([tacho_cx - tacho_r, tacho_cy - tacho_r, tacho_cx + tacho_r, tacho_cy + tacho_r],
                 start=start_angle, end=start_angle + sweep_range, fill=(40, 50, 65, 180), width=6)

        # Redline Arc (8,500 to 9,000 RPM)
        redline_start = start_angle + sweep_range * (8500.0 / 9000.0)
        draw.arc([tacho_cx - tacho_r, tacho_cy - tacho_r, tacho_cx + tacho_r, tacho_cy + tacho_r],
                 start=redline_start, end=start_angle + sweep_range, fill=(255, 50, 40, 240), width=7)

        # Active RPM Filled Glow Arc
        active_sweep = sweep_range * rpm_ratio
        arc_color = (255, 40, 40, 255) if rpm >= 8500 else (0, 210, 255, 230)
        draw.arc([tacho_cx - tacho_r, tacho_cy - tacho_r, tacho_cx + tacho_r, tacho_cy + tacho_r],
                 start=start_angle, end=start_angle + active_sweep, fill=arc_color, width=6)

        # Dial Tick Marks and Numbers (0 through 9)
        for i in range(10):
            tick_ang = math.radians(start_angle + sweep_range * (i / 9.0))
            cos_a = math.cos(tick_ang)
            sin_a = math.sin(tick_ang)

            p_in  = (tacho_cx + cos_a * (tacho_r - 12), tacho_cy + sin_a * (tacho_r - 12))
            p_out = (tacho_cx + cos_a * (tacho_r + 2),  tacho_cy + sin_a * (tacho_r + 2))
            t_col = (255, 60, 50, 240) if i >= 8 else (200, 215, 230, 200)
            draw.line([p_in, p_out], fill=t_col, width=2)

            # Number labels
            num_pos = (tacho_cx + cos_a * (tacho_r - 28) - 5, tacho_cy + sin_a * (tacho_r - 28) - 8)
            draw.text(num_pos, str(i), fill=t_col, font=self.font_small)

        # Needle Line
        needle_ang = math.radians(start_angle + active_sweep)
        n_x = tacho_cx + math.cos(needle_ang) * (tacho_r - 10)
        n_y = tacho_cy + math.sin(needle_ang) * (tacho_r - 10)
        draw.line([(tacho_cx, tacho_cy), (n_x, n_y)], fill=(255, 255, 255, 250), width=3)
        draw.ellipse([tacho_cx - 6, tacho_cy - 6, tacho_cx + 6, tacho_cy + 6], fill=(255, 50, 50, 255))

        # Center Gear Readout (Bold PDK Gear)
        gear_text = str(gear)
        bbox_g = draw.textbbox((0, 0), gear_text, font=self.font_large)
        gw = bbox_g[2] - bbox_g[0]
        gh = bbox_g[3] - bbox_g[1]
        draw.text((tacho_cx - gw // 2, tacho_cy - gh // 2 - 12), gear_text, fill=(255, 255, 255, 250), font=self.font_large)

        # Digital RPM Readout
        rpm_str = f"{int(rpm):,} RPM"
        bbox_rpm = draw.textbbox((0, 0), rpm_str, font=self.font_small)
        rw = bbox_rpm[2] - bbox_rpm[0]
        draw.text((tacho_cx - rw // 2, tacho_cy + int(tacho_r * 0.42)), rpm_str, fill=arc_color, font=self.font_small)

        # Digital Speed Readout (KM/H)
        speed_str = f"{speed_kmh} KM/H"
        bbox_sp = draw.textbbox((0, 0), speed_str, font=self.font_med)
        sw = bbox_sp[2] - bbox_sp[0]
        draw.text((tacho_cx - sw // 2, tacho_cy + int(tacho_r * 0.65)), speed_str, fill=(255, 255, 255, 240), font=self.font_med)

        # ---------------------------------------------------------------------
        # 3. FORMULA 1 / GT3 SHIFT LIGHT LED ARRAY
        # ---------------------------------------------------------------------
        # Placed directly above the tachometer
        num_leds = 8
        led_w = int(tacho_r * 0.16)
        led_h = int(tacho_r * 0.08)
        led_gap = int(tacho_r * 0.05)
        total_led_w = num_leds * led_w + (num_leds - 1) * led_gap
        led_start_x = tacho_cx - total_led_w // 2
        led_y = tacho_cy - tacho_r - int(tacho_r * 0.22)

        # Blinking logic when hitting 8800+ RPM
        is_blinking_red = (rpm >= 8800 and int(t * 16) % 2 == 0)

        for led_i in range(num_leds):
            lx = led_start_x + led_i * (led_w + led_gap)
            led_threshold = 6000 + (led_i / float(num_leds)) * 2800

            if rpm >= led_threshold:
                if led_i < 3:
                    l_color = (0, 220, 255, 255) # Cyan
                elif led_i < 6:
                    l_color = (255, 210, 20, 255) # Yellow/Green
                else:
                    l_color = (255, 30, 20, 255) if not is_blinking_red else (255, 255, 255, 255) # Blinking Red
            else:
                l_color = (30, 40, 50, 140) # Off / Dim

            draw.rectangle([lx, led_y, lx + led_w, led_y + led_h], fill=l_color)

        # ---------------------------------------------------------------------
        # 4. ACTIVE DRS STATUS BADGE & DOWNFORCE TELEMETRY
        # ---------------------------------------------------------------------
        # Positioned opposite to tachometer or top/bottom layout
        if is_vertical:
            drs_bx = pad
            drs_by = pad + int(h * 0.08)
            drs_bw = w - 2 * pad
            drs_bh = int(h * 0.065)
        else:
            drs_bx = int(w * 0.72)
            drs_by = int(h * 0.70)
            drs_bw = int(w * 0.24)
            drs_bh = int(h * 0.18)

        # Draw DRS Telemetry Card
        draw.rectangle([drs_bx, drs_by, drs_bx + drs_bw, drs_by + drs_bh],
                       fill=(10, 16, 26, 190), outline=(50, 80, 110, 180), width=1)

        is_drs_on = (drs_active or t >= 11.0)
        if is_drs_on:
            drs_title = "DRS // ACTIVE [OPEN]"
            drs_sub = "LOW DRAG OVERTAKE • FLAP: 34.0°"
            drs_accent = (50, 255, 120, 240) # Neon Green
        else:
            drs_title = "DRS // CLOSED [MAX DOWNFORCE]"
            drs_sub = "TOTAL DOWNFORCE: 860 KG @ 285 KM/H"
            drs_accent = (0, 200, 255, 230) # Neon Cyan

        draw.text((drs_bx + 14, drs_by + 10), drs_title, fill=drs_accent, font=self.font_med)
        draw.text((drs_bx + 14, drs_by + int(drs_bh * 0.48)), drs_sub, fill=(200, 220, 235, 200), font=self.font_small)

        # ---------------------------------------------------------------------
        # 5. G-FORCE METER / ACCELEROMETER
        # ---------------------------------------------------------------------
        if not is_vertical:
            g_cx = int(w * 0.50)
            g_cy = int(h * 0.82)
            g_r  = int(min(w, h) * 0.10)

            # Circular target radar
            draw.ellipse([g_cx - g_r, g_cy - g_r, g_cx + g_r, g_cy + g_r],
                         outline=(50, 70, 95, 160), width=1)
            draw.ellipse([g_cx - g_r//2, g_cy - g_r//2, g_cx + g_r//2, g_cy + g_r//2],
                         outline=(40, 55, 75, 130), width=1)
            draw.line([(g_cx - g_r, g_cy), (g_cx + g_r, g_cy)], fill=(40, 55, 75, 130), width=1)
            draw.line([(g_cx, g_cy - g_r), (g_cx, g_cy + g_r)], fill=(40, 55, 75, 130), width=1)

            # Dynamic G-ball
            g_dx = math.sin(t * 2.8) * (g_r * 0.72) * (lat_g / 2.0)
            g_dy = -math.cos(t * 2.8) * (g_r * 0.35)
            draw.ellipse([g_cx + g_dx - 5, g_cy + g_dy - 5, g_cx + g_dx + 5, g_cy + g_dy + 5],
                         fill=(0, 220, 255, 250))

            g_text = f"LATERAL: {lat_g:.2f} G"
            draw.text((g_cx - 45, g_cy + g_r + 8), g_text, fill=(200, 225, 245, 210), font=self.font_small)

        # ---------------------------------------------------------------------
        # 6. BOTTOM TELEMETRY FOOTER BAR
        # ---------------------------------------------------------------------
        footer_y = h - pad - 6
        cycle_pct = (t / max(0.1, total_duration)) * 100.0
        foot_left = f"SESSION TIME: {t:05.2f}s / {total_duration:04.1f}s ({cycle_pct:4.1f}%)"
        foot_right = "STATUS: 100% COMPILED // PORSCHE 911 GT3 RS"

        draw.text((pad, footer_y - 12), foot_left, fill=(130, 160, 185, 180), font=self.font_small)
        
        bbox_fr = draw.textbbox((0, 0), foot_right, font=self.font_small)
        w_fr = bbox_fr[2] - bbox_fr[0]
        draw.text((w - pad - w_fr, footer_y - 12), foot_right, fill=(130, 160, 185, 180), font=self.font_small)

        # Progress underline
        bar_len = w - 2 * pad
        draw.line([(pad, footer_y + 4), (pad + bar_len, footer_y + 4)], fill=(30, 45, 60, 160), width=2)
        draw.line([(pad, footer_y + 4), (pad + int(bar_len * (cycle_pct / 100.0)), footer_y + 4)],
                  fill=(0, 210, 255, 230), width=2)

        return img

    def draw_on_opencv_frame(self, frame_bgr, t, total_duration, throttle_pct=0.0, drs_active=False, morph_pct=1.0):
        """Alpha-composite the HUD image directly onto an OpenCV BGR video frame."""
        hud_pil = self.generate_hud_image(t, total_duration, throttle_pct, drs_active, morph_pct)
        hud_rgba = np.array(hud_pil)

        hud_rgb = hud_rgba[:, :, :3]
        hud_alpha = hud_rgba[:, :, 3] / 255.0

        # Convert RGB to BGR for OpenCV
        hud_bgr = hud_rgb[:, :, ::-1]

        alpha_3d = np.repeat(hud_alpha[:, :, np.newaxis], 3, axis=2)
        blended = (frame_bgr * (1.0 - alpha_3d) + hud_bgr * alpha_3d).astype(np.uint8)
        return blended
