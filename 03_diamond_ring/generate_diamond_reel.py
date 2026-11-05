"""
Interactive Viewer & Direct 9:16 MP4 Video Reel Exporter for the 3D ASCII Diamond Ring.
Episode 03 of Byte to Compiled.
Features:
- Dual-pane split-screen: Shimmering 3D ASCII Diamond Ring on top + VS Code on bottom.
- 60 FPS real-time interactive viewer with keyboard/mouse controls.
- Headless 9:16 vertical MP4 video export for Instagram Reels and YouTube Shorts.
"""

import sys
import os
import time
import argparse
import numpy as np
import cv2
import pygame

from split_screen_canvas import SplitScreenCanvas


class DiamondRingReelEngine:
    def __init__(self, width=720, height=1280, is_headless=False):
        self.width = width
        self.height = height
        self.is_headless = is_headless
        self.total_duration = 12.0  # 12.0s = exactly 1 full rotation cycle for perfect loop

        self.canvas = SplitScreenCanvas(width=self.width, height=self.height)

        # Interactive state
        self.is_paused = False
        self.sim_time = 0.0
        self.rotation_manual_offset = 0.0
        self.fullscreen = False

        if not self.is_headless:
            self._init_window()

    def _init_window(self):
        """Initialize Pygame interactive window."""
        pygame.init()
        pygame.display.set_caption("Episode 03: Diamond Engagement Ring // ASCII Generative Art")

        display_info = pygame.display.Info()
        self.desktop_w = display_info.current_w
        self.desktop_h = display_info.current_h

        # Window size: Keep 9:16 vertical preview scaled to fit laptop height comfortably
        preview_h = min(820, int(self.desktop_h * 0.90))
        preview_w = int(preview_h * (9.0 / 16.0))
        self.win_w = preview_w
        self.win_h = preview_h

        self.screen = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

    def run_interactive(self):
        """Run 60 FPS interactive preview on desktop/laptop."""
        running = True
        t_prev = time.time()

        print("\n=======================================================")
        print("  EPISODE 03: 3D DIAMOND RING (ASCII GENERATIVE ART)")
        print("=======================================================")
        print("  Controls:")
        print("  * Spacebar    : Pause / Resume rotation")
        print("  * Left / Right: Manual rotation angle")
        print("  * 'F' / 'F11' : Toggle Fullscreen")
        print("  * 'E' Key     : Export direct 9:16 MP4 video reel")
        print("  * 'R' Key     : Restart animation from 0.0s")
        print("  * 'ESC' / 'Q' : Quit")
        print("=======================================================\n")

        while running:
            t_curr = time.time()
            dt = t_curr - t_prev
            t_prev = t_curr

            if not self.is_paused:
                self.sim_time += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.win_w = event.w
                    self.win_h = event.h
                    self.screen = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_r:
                        self.sim_time = 0.0
                    elif event.key in [pygame.K_f, pygame.K_F11]:
                        self.fullscreen = not self.fullscreen
                        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
                        self.screen = pygame.display.set_mode((self.desktop_w, self.desktop_h) if self.fullscreen else (self.win_w, self.win_h), flags)
                    elif event.key == pygame.K_e:
                        print("\n[*] Starting Direct 9:16 MP4 Reel Video Export...")
                        self.export_video_reel()
                        t_prev = time.time()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.rotation_manual_offset -= dt * 1.5
            if keys[pygame.K_RIGHT]:
                self.rotation_manual_offset += dt * 1.5

            effective_t = (self.sim_time + self.rotation_manual_offset) % self.total_duration

            # Render split-screen canvas
            frame_pil = self.canvas.render_composite_frame(effective_t)
            # Convert to Pygame surface
            raw_str = frame_pil.tobytes("raw", "RGBA")
            pygame_surface = pygame.image.fromstring(raw_str, (self.width, self.height), "RGBA")

            # Scale to current window size
            scaled_surf = pygame.transform.smoothscale(pygame_surface, (self.screen.get_width(), self.screen.get_height()))
            self.screen.blit(scaled_surf, (0, 0))
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()

    def export_video_reel(self, width=720, height=1280, output_path=None, fps=30):
        """
        Headless export of the 12-second 9:16 vertical video reel for Instagram and YouTube.
        """
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), "diamond_ring_reel.mp4")

        total_frames = int(self.total_duration * fps)
        print(f"\n=======================================================")
        print(f"[*] Exporting 9:16 Vertical Video Reel ({width}x{height})")
        print(f"[*] Frames: {total_frames} | Duration: {self.total_duration}s | FPS: {fps}")
        print(f"[*] Output: {output_path}")
        print(f"=======================================================\n")

        # Initialize export canvas
        canvas = SplitScreenCanvas(width=width, height=height)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        t_start = time.time()

        for frame_idx in range(total_frames):
            t = (frame_idx / float(fps)) % self.total_duration

            # Composite frame (PIL RGBA)
            frame_pil = canvas.render_composite_frame(t)
            frame_np = np.array(frame_pil.convert("RGB"))

            # Convert RGB to BGR for OpenCV
            frame_bgr = frame_np[:, :, ::-1]
            writer.write(frame_bgr)

            if (frame_idx + 1) % 15 == 0 or frame_idx == total_frames - 1:
                elapsed = time.time() - t_start
                rate = (frame_idx + 1) / max(0.001, elapsed)
                remaining = (total_frames - (frame_idx + 1)) / max(0.001, rate)
                pct = ((frame_idx + 1) / total_frames) * 100.0
                print(f"  Rendering: [{frame_idx+1:03d}/{total_frames:03d}] {pct:5.1f}% | Speed: {rate:4.1f} fps | ETA: {remaining:4.1f}s", end='\r')

        writer.release()
        print(f"\n[+] Export Complete in {time.time() - t_start:.1f}s!")
        print(f"[+] Video Reel saved successfully at:\n    {output_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Episode 03: 3D Diamond Ring ASCII Generative Art")
    parser.add_argument("--export", action="store_true", help="Render and export 12s MP4 video reel")
    parser.add_argument("--res", type=str, default="720x1280", help="Resolution for export, e.g. 720x1280 or 1080x1920")
    args = parser.parse_args()

    if args.export:
        try:
            w, h = map(int, args.res.split('x'))
        except Exception:
            w, h = 720, 1280
        engine = DiamondRingReelEngine(width=w, height=h, is_headless=True)
        engine.export_video_reel(width=w, height=h)
    else:
        engine = DiamondRingReelEngine(width=720, height=1280, is_headless=False)
        engine.run_interactive()


if __name__ == "__main__":
    main()
