"""
================================================================================
  NOKIA 3310 SNAKE — 100% Hamiltonian AI & Retro Dot-Matrix Engine
  Episode 02 of Byte to Compiled (Nostalgic Viral Reel Series)
================================================================================
Usage:
  python generate_snake_animation.py            # Opens in FULL LAPTOP SCREEN
  python generate_snake_animation.py --windowed # Opens in a window
  python generate_snake_animation.py --export   # Render & export 14s MP4 video reel

Controls:
  M                : Toggle Manual Play / AI Autopilot
  Arrow Keys / WASD: Steer Snake (when in Manual Mode)
  1 / 2 / 3 / 4    : Speed multipliers (1x, 5x, 20x, Max)
  Spacebar         : Pause / Resume simulation
  F / F11          : Toggle Fullscreen / Windowed
  R                : Reset Game
  E                : Export 14s MP4 Reel Video
  ESC / Q          : Quit
================================================================================
"""

import sys
import os
import time
import math
import argparse
import numpy as np
import pygame
import cv2

# Local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from snake_ai import HamiltonianSnakeAI
from lcd_renderer import NokiaLCDRenderer

class NokiaSnakeApp:
    def __init__(self, width=None, height=None, fullscreen=True, is_headless=False, grid_w=20, grid_h=12):
        self.is_headless = is_headless
        self.fullscreen = fullscreen
        self.grid_w = grid_w
        self.grid_h = grid_h

        # Game & AI engine
        self.game = HamiltonianSnakeAI(width=grid_w, height=grid_h)
        self.renderer = NokiaLCDRenderer(grid_w=grid_w, grid_h=grid_h)

        # Simulation settings
        self.is_ai = True
        self.is_paused = False
        self.speed_level = 2 # 1: normal, 2: fast, 3: warp, 4: max
        self.speeds = {1: 8, 2: 24, 3: 70, 4: 200} # Steps per second

        # Display Setup
        if not self.is_headless:
            pygame.init()
            info = pygame.display.Info()
            self.desktop_w = info.current_w
            self.desktop_h = info.current_h
            if self.fullscreen:
                self.width = self.desktop_w
                self.height = self.desktop_h
                flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
            else:
                self.width = width if width else int(self.desktop_w * 0.8)
                self.height = height if height else int(self.desktop_h * 0.85)
                flags = pygame.RESIZABLE | pygame.DOUBLEBUF

            self.screen = pygame.display.set_mode((self.width, self.height), flags)
            pygame.display.set_caption("NOKIA 3310 SNAKE // 100% Hamiltonian Cycle AI")
        else:
            self.width = width if width else 720
            self.height = height if height else 1280
            self.screen = pygame.Surface((self.width, self.height))

        # Fonts for UI
        self.font_title = pygame.font.SysFont("Consolas", int(min(self.width, self.height) * 0.028), bold=True)
        self.font_sub = pygame.font.SysFont("Consolas", int(min(self.width, self.height) * 0.018), bold=True)
        self.font_tiny = pygame.font.SysFont("Consolas", int(min(self.width, self.height) * 0.014))

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
            self.width, self.height = self.desktop_w, self.desktop_h
            self.screen = pygame.display.set_mode((self.width, self.height), flags)
            print(f"[*] Switched to Fullscreen ({self.desktop_w}x{self.desktop_h})")
        else:
            w = int(self.desktop_w * 0.75)
            h = int(self.desktop_h * 0.8)
            flags = pygame.RESIZABLE | pygame.DOUBLEBUF
            self.width, self.height = w, h
            self.screen = pygame.display.set_mode((self.width, self.height), flags)
            print(f"[*] Switched to Windowed ({w}x{h})")

    def draw_dashboard_sidebars(self, surface):
        """Render cyberpunk retro telemetry panels on left and right sides in widescreen."""
        w, h = self.width, self.height
        is_widescreen = (w / float(h)) > 1.3

        if not is_widescreen:
            return

        c_accent = (140, 240, 255)
        c_green = (120, 255, 140)
        c_dim = (140, 160, 185)
        c_panel_bg = (16, 24, 36)

        # 1. Left Telemetry Panel (Algorithm & Stats)
        panel_w = int(w * 0.24)
        panel_h = int(h * 0.75)
        lx = int(w * 0.04)
        ly = (h - panel_h) // 2

        l_rect = pygame.Rect(lx, ly, panel_w, panel_h)
        pygame.draw.rect(surface, c_panel_bg, l_rect, border_radius=12)
        pygame.draw.rect(surface, (35, 50, 75), l_rect, width=2, border_radius=12)

        # Content
        pad = 20
        y_cursor = ly + pad
        surface.blit(self.font_title.render("SYSTEM TELEMETRY", True, c_accent), (lx + pad, y_cursor))
        y_cursor += 36

        fill_pct = (len(self.game.snake) / float(self.game.total_cells)) * 100.0
        stats = [
            ("ALGORITHM", "HAMILTONIAN CYCLE"),
            ("LOOKAHEAD", "TOPOLOGICAL SHORTCUTS"),
            ("BOARD SIZE", f"{self.grid_w} x {self.grid_h} ({self.game.total_cells} cells)"),
            ("SNAKE LENGTH", f"{len(self.game.snake)} / {self.game.total_cells}"),
            ("BOARD FILL", f"{fill_pct:5.1f}%"),
            ("SCORE", f"{self.game.score:05d}"),
            ("MODE", "AI AUTOPILOT" if self.is_ai else "MANUAL PLAY"),
            ("SIM SPEED", f"{self.speeds[self.speed_level]} steps/sec"),
        ]

        for label, val in stats:
            col = c_green if "FILL" in label or "ALGORITHM" in label else (240, 245, 255)
            surface.blit(self.font_tiny.render(label, True, c_dim), (lx + pad, y_cursor))
            surface.blit(self.font_sub.render(val, True, col), (lx + pad, y_cursor + 14))
            y_cursor += 42

        # 2. Right Telemetry Panel (Controls & Nostalgia)
        rx = w - panel_w - int(w * 0.04)
        r_rect = pygame.Rect(rx, ly, panel_w, panel_h)
        pygame.draw.rect(surface, c_panel_bg, r_rect, border_radius=12)
        pygame.draw.rect(surface, (35, 50, 75), r_rect, width=2, border_radius=12)

        y_cursor = ly + pad
        surface.blit(self.font_title.render("CONTROL MANUAL", True, c_accent), (rx + pad, y_cursor))
        y_cursor += 36

        controls = [
            ("KEY 'M'", "Toggle Manual / AI Autopilot"),
            ("ARROWS / WASD", "Steer Snake (in Manual Mode)"),
            ("KEYS 1 - 4", "Speed Multipliers (1x, 5x, 20x, Max)"),
            ("SPACEBAR", "Pause / Resume"),
            ("KEY 'F' / 'F11'", "Toggle Fullscreen / Windowed"),
            ("KEY 'R'", "Restart Simulation"),
            ("KEY 'E'", "Export 14s MP4 Reel Video"),
        ]

        for key_bind, desc in controls:
            surface.blit(self.font_sub.render(key_bind, True, c_green), (rx + pad, y_cursor))
            surface.blit(self.font_tiny.render(desc, True, c_dim), (rx + pad, y_cursor + 18))
            y_cursor += 40

        # Retro quote at bottom of right panel
        quote_rect = pygame.Rect(rx + pad, ly + panel_h - 65, panel_w - 2 * pad, 50)
        pygame.draw.rect(surface, (24, 34, 52), quote_rect, border_radius=6)
        surface.blit(self.font_tiny.render('"Indestructible hardware.', True, (255, 200, 120)), (rx + pad + 8, ly + panel_h - 58))
        surface.blit(self.font_tiny.render(' Unbeatable software."', True, (255, 200, 120)), (rx + pad + 8, ly + panel_h - 38))

    def run_interactive(self):
        """Run interactive 60 FPS viewer."""
        clock = pygame.time.Clock()
        running = True
        last_step_time = time.time()
        manual_dir = None

        print("\n" + "="*65)
        print("  NOKIA 3310 SNAKE — 100% Hamiltonian AI Simulation Active")
        print("="*65)
        print(f"  Screen Resolution : {self.width}x{self.height} {'[FULLSCREEN]' if self.fullscreen else '[WINDOWED]'}")
        print("  Controls:")
        print("    • 'M'            : Toggle Manual Control / AI Autopilot")
        print("    • Arrow Keys/WASD: Steer Snake (when in Manual Mode)")
        print("    • '1', '2', '3': Change Speed multiplier")
        print("    • Spacebar       : Pause / Resume")
        print("    • 'F' / 'F11'    : Toggle Fullscreen")
        print("    • 'R'            : Reset Game")
        print("    • 'E'            : Export 14s MP4 Reel Video")
        print("    • ESC / 'Q'      : Exit")
        print("="*65 + "\n")

        while running:
            dt = clock.tick(60) / 1000.0
            now = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    if not self.fullscreen:
                        self.width, self.height = event.w, event.h
                        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE | pygame.DOUBLEBUF)
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key in (pygame.K_f, pygame.K_F11):
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_m:
                        self.is_ai = not self.is_ai
                        print(f"[*] Mode switched: {'AI AUTOPILOT' if self.is_ai else 'MANUAL CONTROL'}")
                    elif event.key == pygame.K_r:
                        self.game.reset()
                        print("[*] Game reset.")
                    elif event.key in (pygame.K_1, pygame.K_KP1):
                        self.speed_level = 1
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        self.speed_level = 2
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        self.speed_level = 3
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        self.speed_level = 4
                    elif event.key == pygame.K_e:
                        pygame.quit()
                        self.export_video()
                        return

                    # Manual steering inputs
                    if not self.is_ai:
                        if event.key in (pygame.K_UP, pygame.K_w) and self.game.direction != (0, 1):
                            manual_dir = (0, -1)
                        elif event.key in (pygame.K_DOWN, pygame.K_s) and self.game.direction != (0, -1):
                            manual_dir = (0, 1)
                        elif event.key in (pygame.K_LEFT, pygame.K_a) and self.game.direction != (1, 0):
                            manual_dir = (-1, 0)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.game.direction != (-1, 0):
                            manual_dir = (1, 0)

            # Game Stepping based on Speed
            step_interval = 1.0 / self.speeds[self.speed_level]
            if not self.is_paused and (now - last_step_time) >= step_interval:
                if self.is_ai:
                    self.game.step()
                else:
                    if manual_dir:
                        self.game.direction = manual_dir
                    self.game.step(direction_override=self.game.direction)
                    manual_dir = None

                self.renderer.update_ghosting(self.game.snake_set, self.game.food, dt=step_interval)
                last_step_time = now

            # Rendering
            self.screen.fill((10, 14, 20))

            # Ambient LCD glow in center
            center_x = self.width // 2
            center_y = self.height // 2
            glow_surf = pygame.Surface((500, 500), pygame.SRCALPHA)
            fill_ratio = len(self.game.snake) / float(self.game.total_cells)
            glow_alpha = int(40 + 60 * fill_ratio)
            pygame.draw.circle(glow_surf, (142, 166, 102, glow_alpha), (250, 250), 220)
            self.screen.blit(glow_surf, (center_x - 250, center_y - 250))

            # Draw Phone & LCD
            phone_scale = min(self.height / 820.0, self.width / 820.0)
            self.renderer.draw_nokia_phone(self.screen, center_x, center_y, scale=phone_scale, game_state=self.game, is_ai=self.is_ai)

            # Draw sidebars in widescreen
            self.draw_dashboard_sidebars(self.screen)

            pygame.display.flip()

        pygame.quit()

    def export_video(self, output_filename="nokia_snake_reel.mp4", fps=30):
        """
        Export a high-definition 9:16 vertical video reel (720x1280)
        timed to 14.0 seconds for Instagram Reels.
        Guarantees 100% board fill with victory celebration.
        """
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
        export_w, export_h = 720, 1280
        total_duration = 14.0
        total_frames = int(total_duration * fps)

        print(f"\n[*] Initializing Nokia Reel Export -> {output_path}")
        print(f"[*] Resolution: {export_w}x{export_h} (9:16) | FPS: {fps} | Total Frames: {total_frames}")

        surface = pygame.Surface((export_w, export_h))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (export_w, export_h))

        if not writer.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            output_path = output_path.replace('.mp4', '.avi')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (export_w, export_h))

        # Reset game for pristine recording
        self.game.reset()

        font_hook = pygame.font.SysFont("Arial", 28, bold=True)
        font_subhook = pygame.font.SysFont("Arial", 18, bold=True)
        font_tele = pygame.font.SysFont("Consolas", 16, bold=True)

        start_time = time.time()
        max_cells = self.game.total_cells

        for frame_idx in range(total_frames):
            t = (frame_idx / float(total_frames)) * total_duration

            # Cinematic progression schedule:
            # 0.0s - 11.0s: Progress from length 3 to 100% (240 cells)
            # 11.0s - 14.0s: Victory celebration at 100% full
            if not self.game.is_won:
                if t < 11.0:
                    norm_t = min(1.0, t / 11.0)
                    target_len = min(max_cells, int(3 + (max_cells - 3) * (norm_t ** 1.35)))
                    steps_taken = 0
                    while len(self.game.snake) < target_len and not self.game.is_won and steps_taken < 150:
                        self.game.step()
                        steps_taken += 1
                else:
                    # Final push to 100% completion
                    steps_taken = 0
                    while not self.game.is_won and steps_taken < 300:
                        self.game.step()
                        steps_taken += 1

                self.renderer.update_ghosting(self.game.snake_set, self.game.food, dt=0.03)

            # Render frame
            surface.fill((8, 12, 18))

            center_x = export_w // 2
            center_y = int(export_h * 0.52)
            glow_surf = pygame.Surface((440, 440), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (142, 166, 102, 55), (220, 220), 200)
            surface.blit(glow_surf, (center_x - 220, center_y - 220))

            # Draw Nokia Phone
            self.renderer.draw_nokia_phone(surface, center_x, center_y, scale=1.35, game_state=self.game, is_ai=True)

            # 1. Top Hook Text Overlay
            if t < 3.8:
                # Opening hook
                txt1 = font_hook.render("POV: You let Python play Snake", True, (255, 255, 255))
                txt2 = font_subhook.render("on your dad's Nokia 3310...", True, (160, 255, 180))
                surface.blit(txt1, (center_x - txt1.get_width() // 2, 75))
                surface.blit(txt2, (center_x - txt2.get_width() // 2, 115))
            elif t >= 11.2:
                # Climax / Call to Action Hook
                txt1 = font_hook.render("100% BOARD FILLED!", True, (255, 230, 100))
                txt2 = font_subhook.render("Did anyone ever beat this legit?", True, (255, 255, 255))
                surface.blit(txt1, (center_x - txt1.get_width() // 2, 75))
                surface.blit(txt2, (center_x - txt2.get_width() // 2, 115))
            else:
                # Progression Title
                txt1 = font_hook.render("HAMILTONIAN CYCLE SOLVER", True, (180, 240, 255))
                txt2 = font_subhook.render("Zero collisions. Pure math.", True, (160, 200, 230))
                surface.blit(txt1, (center_x - txt1.get_width() // 2, 75))
                surface.blit(txt2, (center_x - txt2.get_width() // 2, 115))

            # 2. Bottom Telemetry Bar
            bar_y = int(export_h * 0.90)
            fill_pct = (len(self.game.snake) / float(self.game.total_cells)) * 100.0

            tele_txt = font_tele.render(f"BOARD DENSITY: {fill_pct:5.1f}%  |  SPEED: 250 FPS", True, (140, 220, 160))
            surface.blit(tele_txt, (center_x - tele_txt.get_width() // 2, bar_y))

            # Progress gauge line
            bar_w = 480
            bx0 = (export_w - bar_w) // 2
            pygame.draw.line(surface, (40, 55, 75), (bx0, bar_y + 30), (bx0 + bar_w, bar_y + 30), 4)
            fill_w = int(bar_w * (fill_pct / 100.0))
            if fill_w > 0:
                pygame.draw.line(surface, (142, 166, 102), (bx0, bar_y + 30), (bx0 + fill_w, bar_y + 30), 4)
                pygame.draw.circle(surface, (255, 255, 255), (bx0 + fill_w, bar_y + 30), 4)

            # Convert Pygame surface to OpenCV frame
            frame_rgb = pygame.surfarray.array3d(surface)
            frame_bgr = cv2.cvtColor(np.transpose(frame_rgb, (1, 0, 2)), cv2.COLOR_RGB2BGR)
            writer.write(frame_bgr)

            # Progress feedback
            if (frame_idx + 1) % 20 == 0 or frame_idx == total_frames - 1:
                pct = ((frame_idx + 1) / total_frames) * 100.0
                elapsed = time.time() - start_time
                fps_est = (frame_idx + 1) / max(0.01, elapsed)
                rem_sec = (total_frames - (frame_idx + 1)) / max(0.1, fps_est)
                print(f"\r  Rendering: [{frame_idx + 1:03d}/{total_frames}] {pct:5.1f}% | Speed: {fps_est:4.1f} fps | ETA: {rem_sec:4.1f}s", end="")

        writer.release()
        total_time = time.time() - start_time
        print(f"\n\n[+] Export Complete in {total_time:.1f}s!")
        print(f"[+] Reel Video saved successfully at:\n    {output_path}\n")

def main():
    parser = argparse.ArgumentParser(description="Nokia 3310 Snake — 100% Hamiltonian AI Simulation")
    parser.add_argument("--export", action="store_true", help="Render and export 14s MP4 reel video directly")
    parser.add_argument("--output", type=str, default="nokia_snake_reel.mp4", help="Output MP4 video filename")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second for video export (default: 30)")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode instead of fullscreen")
    args = parser.parse_args()

    if args.export:
        app = NokiaSnakeApp(is_headless=True)
        app.export_video(output_filename=args.output, fps=args.fps)
    else:
        app = NokiaSnakeApp(fullscreen=(not args.windowed), is_headless=False)
        app.run_interactive()

if __name__ == "__main__":
    main()
