"""
================================================================================
  GARGANTUA // SUPERMASSIVE ROTATING KERR BLACK HOLE
  General Relativistic Raymarching Simulation & Accretion Disk Physics
  Episode 03 of Byte to Compiled (Aesthetic Creative Coding Series)
================================================================================
Usage:
  python generate_black_hole_animation.py            # Launches in FULL LAPTOP SCREEN
  python generate_black_hole_animation.py --windowed # Opens in a window
  python generate_black_hole_animation.py --export   # Render & export 14s MP4 video reel

Controls:
  Left Mouse Drag  : Orbit 3D camera around Gargantua
  Right Mouse Drag : Pan camera target
  Mouse Scroll     : Zoom in / out
  Spacebar         : Pause / Resume animation
  H                : Toggle HUD Telemetry on / off (Pure Cinematic View)
  F / F11          : Toggle Fullscreen / Windowed
  W                : Toggle Visual Modes (Cinematic Hybrid / Spacetime Grid / Photorealistic)
  R                : Reset animation & camera
  E                : Start direct MP4 Video Reel Export
  ESC / Q          : Quit
================================================================================
"""

import sys
import os
import time
import math
import argparse
import numpy as np
import cv2
import pygame
import moderngl

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from math_utils import (
    perspective_matrix,
    look_at_matrix,
    smoothstep
)
import shaders
from hud import AstrophysicsHUD

class BlackHoleRenderer:
    def __init__(self, width=None, height=None, fullscreen=True, is_headless=False):
        self.is_headless = is_headless
        self.fullscreen = fullscreen
        self.total_duration = 14.0 # Seconds for full compilation cycle

        if not self.is_headless:
            pygame.init()
            info = pygame.display.Info()
            self.desktop_w = info.current_w
            self.desktop_h = info.current_h
            if self.fullscreen:
                self.width = self.desktop_w
                self.height = self.desktop_h
            else:
                self.width = width if width else int(self.desktop_w * 0.8)
                self.height = height if height else int(self.desktop_h * 0.85)
        else:
            self.width = width if width else 720
            self.height = height if height else 1280

        # Camera orbital parameters
        self.cam_distance = 22.0
        self.cam_yaw = 0.40
        self.cam_pitch = 0.28
        self.cam_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.auto_rotate = True

        # Render modes
        self.visual_mode = 0 # 0: Cinematic Hybrid, 1: Spacetime Grid, 2: Photorealistic
        self.show_hud = True
        self.anim_time = 0.0
        self.is_paused = False

        # Initialize graphics
        self._init_gl()
        self._init_hud()

    def _init_gl(self):
        """Initialize ModernGL context, shaders, and framebuffers."""
        if self.is_headless:
            self.ctx = moderngl.create_context(standalone=True)
            self.fbo = self.ctx.simple_framebuffer((self.width, self.height))
            self.fbo.use()
        else:
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
            pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
            pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

            flags = pygame.OPENGL | pygame.DOUBLEBUF
            if self.fullscreen:
                flags |= pygame.FULLSCREEN
            else:
                flags |= pygame.RESIZABLE

            self.screen = pygame.display.set_mode((self.width, self.height), flags)
            pygame.display.set_caption("GARGANTUA // Supermassive Kerr Black Hole Simulation")
            self.ctx = moderngl.create_context()

        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        # 1. Relativistic Black Hole Raymarching program
        self.bh_prog = self.ctx.program(
            vertex_shader=shaders.QUAD_VERTEX_SHADER,
            fragment_shader=shaders.BLACK_HOLE_FRAGMENT_SHADER
        )

        # Screen quad buffer
        quad_vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
             1.0,  1.0,  1.0, 1.0,
            -1.0, -1.0,  0.0, 0.0,
             1.0,  1.0,  1.0, 1.0,
            -1.0,  1.0,  0.0, 1.0,
        ], dtype=np.float32)

        self.screen_quad_vbo = self.ctx.buffer(quad_vertices.tobytes())
        self.bh_vao = self.ctx.vertex_array(
            self.bh_prog,
            [(self.screen_quad_vbo, '2f 2f', 'in_position', 'in_uv')]
        )

        # HUD shader and texture (UV flipped vertically for PIL image format)
        hud_quad_vertices = np.array([
            -1.0, -1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 1.0,
             1.0,  1.0,  1.0, 0.0,
            -1.0, -1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 0.0,
        ], dtype=np.float32)

        self.hud_quad_vbo = self.ctx.buffer(hud_quad_vertices.tobytes())
        self.hud_prog = self.ctx.program(
            vertex_shader=shaders.HUD_VERTEX_SHADER,
            fragment_shader=shaders.HUD_FRAGMENT_SHADER
        )
        self.hud_vao = self.ctx.vertex_array(
            self.hud_prog,
            [(self.hud_quad_vbo, '2f 2f', 'in_position', 'in_uv')]
        )
        self.hud_texture = self.ctx.texture((self.width, self.height), 4)

    def _init_hud(self):
        """Initialize astrophysics telemetry HUD generator."""
        self.hud = AstrophysicsHUD(self.width, self.height)

    def resize(self, new_w, new_h):
        """Handle screen resize or fullscreen toggle."""
        self.width = max(100, new_w)
        self.height = max(100, new_h)
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.hud = AstrophysicsHUD(self.width, self.height)
        self.hud_texture.release()
        self.hud_texture = self.ctx.texture((self.width, self.height), 4)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode smoothly."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN
            self.screen = pygame.display.set_mode((self.desktop_w, self.desktop_h), flags)
            self.resize(self.desktop_w, self.desktop_h)
            print(f"[*] Switched to Fullscreen ({self.desktop_w}x{self.desktop_h})")
        else:
            w = int(self.desktop_w * 0.75)
            h = int(self.desktop_h * 0.8)
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
            self.screen = pygame.display.set_mode((w, h), flags)
            self.resize(w, h)
            print(f"[*] Switched to Windowed ({w}x{h})")

    def compute_camera(self, t):
        """Calculate camera position and target at timestamp t."""
        if self.auto_rotate:
            cam_d = self.cam_distance - min(7.5, t * 0.55)
            yaw = self.cam_yaw + t * 0.12
            pitch = self.cam_pitch + 0.05 * math.sin(t * 0.25)
        else:
            cam_d = self.cam_distance
            yaw = self.cam_yaw
            pitch = self.cam_pitch

        cam_x = cam_d * math.cos(pitch) * math.sin(yaw)
        cam_y = cam_d * math.sin(pitch)
        cam_z = cam_d * math.cos(pitch) * math.cos(yaw)
        return (cam_x, cam_y, cam_z)

    def render_frame(self, t):
        """Render a single complete frame at time t."""
        cam_pos = self.compute_camera(t)

        self.bh_prog['u_time'].value = float(t)
        self.bh_prog['u_resolution'].value = (float(self.width), float(self.height))
        self.bh_prog['u_cam_pos'].value = cam_pos
        self.bh_prog['u_cam_target'].value = tuple(self.cam_target)
        if 'u_spin' in self.bh_prog:
            self.bh_prog['u_spin'].value = 0.998
        if 'u_mode' in self.bh_prog:
            self.bh_prog['u_mode'].value = int(self.visual_mode)
        if 'u_fov_scale' in self.bh_prog:
            aspect = self.width / float(self.height)
            self.bh_prog['u_fov_scale'].value = 0.90 if aspect < 1.0 else 1.35

        self.bh_vao.render(moderngl.TRIANGLES)

        # Render Telemetry HUD Overlay
        if self.show_hud:
            hud_img = self.hud.render_overlay(t, self.total_duration)
            self.hud_texture.write(hud_img.tobytes())
            self.hud_texture.use(location=0)
            self.hud_prog['u_hud_texture'].value = 0
            self.hud_vao.render(moderngl.TRIANGLES)

    def run_interactive(self):
        """Run real-time interactive 60 FPS viewer window."""
        clock = pygame.time.Clock()
        dragging_left = False
        dragging_right = False
        last_mouse_pos = (0, 0)

        print("\n" + "="*68)
        print("  GARGANTUA // Relativistic Kerr Black Hole Active")
        print("="*68)
        print(f"  Display Mode : {'FULLSCREEN' if self.fullscreen else 'WINDOWED'} ({self.width}x{self.height})")
        print("  Controls:")
        print("    Left Drag   : Orbit camera around black hole")
        print("    Right Drag  : Pan camera target")
        print("    Scroll Wheel: Zoom in / out")
        print("    Spacebar    : Pause / Resume animation")
        print("    H           : Toggle HUD Telemetry on / off")
        print("    F / F11     : Toggle Fullscreen / Windowed")
        print("    W           : Cycle Visual Modes (Hybrid / Spacetime Grid / Photorealistic)")
        print("    R           : Restart animation from t = 0")
        print("    E           : Export 14s MP4 video reel")
        print("    ESC / Q     : Quit")
        print("="*68 + "\n")

        running = True
        last_real_time = time.time()

        while running:
            dt = clock.tick(60) / 1000.0
            now = time.time()

            if not self.is_paused:
                self.anim_time += dt
                if self.anim_time > self.total_duration:
                    self.anim_time = 0.0 # Seamless infinite compilation loop

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                        print(f"[*] Animation {'Paused' if self.is_paused else 'Resumed'} at t = {self.anim_time:.2f}s")
                    elif event.key == pygame.K_h:
                        self.show_hud = not self.show_hud
                        print(f"[*] HUD Telemetry: {'ON' if self.show_hud else 'OFF (Pure Cinematic View)'}")
                    elif event.key in (pygame.K_f, pygame.K_F11):
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_w:
                        self.visual_mode = (self.visual_mode + 1) % 3
                        modes = ["Cinematic Hybrid Mix", "Spacetime Curvature Grid", "Pure Photorealistic Shaded"]
                        print(f"[*] Visual Mode: {modes[self.visual_mode]}")
                    elif event.key == pygame.K_r:
                        self.anim_time = 0.0
                        self.cam_distance = 22.0
                        self.cam_yaw = 0.40
                        self.cam_pitch = 0.28
                        print("[*] Animation & Camera Reset to t = 0.0s")
                    elif event.key == pygame.K_e:
                        print("\n[!] Triggering MP4 Video Reel Export...")
                        self.export_video_reel()
                        print("[+] Interactive window resumed.\n")

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        dragging_left = True
                        self.auto_rotate = False
                        last_mouse_pos = event.pos
                    elif event.button == 3:
                        dragging_right = True
                        last_mouse_pos = event.pos
                    elif event.button == 4: # Scroll Up
                        self.cam_distance = max(4.0, self.cam_distance - 0.8)
                    elif event.button == 5: # Scroll Down
                        self.cam_distance = min(40.0, self.cam_distance + 0.8)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        dragging_left = False
                    elif event.button == 3:
                        dragging_right = False

                elif event.type == pygame.MOUSEMOTION:
                    dx = event.pos[0] - last_mouse_pos[0]
                    dy = event.pos[1] - last_mouse_pos[1]
                    last_mouse_pos = event.pos

                    if dragging_left:
                        self.cam_yaw -= dx * 0.006
                        self.cam_pitch = np.clip(self.cam_pitch + dy * 0.006, -0.65, 0.85)
                    elif dragging_right:
                        self.cam_target[0] += dx * 0.015
                        self.cam_target[1] -= dy * 0.015

                elif event.type == pygame.VIDEORESIZE:
                    if not self.fullscreen:
                        self.resize(event.w, event.h)

            self.render_frame(self.anim_time)
            pygame.display.flip()

        pygame.quit()

    def export_video_reel(self, output_path=None, fps=30, width=720, height=1280):
        """Headless high-fidelity 9:16 vertical MP4 video reel exporter."""
        if output_path is None:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gargantua_reel.mp4")

        total_frames = int(self.total_duration * fps)
        print(f"\n[*] Initializing Gargantua Reel Export -> {output_path}")
        print(f"[*] Resolution: {width}x{height} | FPS: {fps} | Total Frames: {total_frames}")

        # Create headless ModernGL context
        export_ctx = moderngl.create_context(standalone=True)
        export_fbo = export_ctx.simple_framebuffer((width, height))
        export_fbo.use()

        bh_prog = export_ctx.program(
            vertex_shader=shaders.QUAD_VERTEX_SHADER,
            fragment_shader=shaders.BLACK_HOLE_FRAGMENT_SHADER
        )

        quad_vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0, -1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 1.0,
        ], dtype=np.float32)

        vbo = export_ctx.buffer(quad_vertices.tobytes())
        vao = export_ctx.vertex_array(bh_prog, [(vbo, '2f 2f', 'in_position', 'in_uv')])

        hud = AstrophysicsHUD(width, height)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        t_start = time.time()
        for frame_idx in range(total_frames):
            t = (frame_idx / float(fps))

            cam_d = 22.0 - min(7.5, t * 0.55)
            yaw = 0.40 + t * 0.12
            pitch = 0.28 + 0.05 * math.sin(t * 0.25)
            cam_x = cam_d * math.cos(pitch) * math.sin(yaw)
            cam_y = cam_d * math.sin(pitch)
            cam_z = cam_d * math.cos(pitch) * math.cos(yaw)

            bh_prog['u_time'].value = float(t)
            bh_prog['u_resolution'].value = (float(width), float(height))
            bh_prog['u_cam_pos'].value = (cam_x, cam_y, cam_z)
            bh_prog['u_cam_target'].value = (0.0, 0.0, 0.0)
            if 'u_spin' in bh_prog:
                bh_prog['u_spin'].value = 0.998
            if 'u_mode' in bh_prog:
                bh_prog['u_mode'].value = 0
            if 'u_fov_scale' in bh_prog:
                bh_prog['u_fov_scale'].value = 0.90

            export_fbo.clear(0.0, 0.0, 0.0, 1.0)
            vao.render(moderngl.TRIANGLES)

            raw_bytes = export_fbo.read(components=3)
            frame_np = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, width, 3))
            frame_np = np.flipud(frame_np)
            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)

            # Composite HUD overlay
            frame_with_hud = hud.draw_on_opencv_frame(frame_bgr, t, self.total_duration)
            writer.write(frame_with_hud)

            if (frame_idx + 1) % 15 == 0 or frame_idx == total_frames - 1:
                elapsed = time.time() - t_start
                rate = (frame_idx + 1) / max(0.001, elapsed)
                remaining = (total_frames - (frame_idx + 1)) / max(0.001, rate)
                pct = ((frame_idx + 1) / total_frames) * 100.0
                print(f"  Rendering: [{frame_idx+1:03d}/{total_frames:03d}] {pct:5.1f}% | Speed: {rate:4.1f} fps | ETA: {remaining:4.1f}s", end='\r')

        writer.release()
        export_fbo.release()
        vbo.release()
        print(f"\n[+] Export Complete in {time.time() - t_start:.1f}s!")
        print(f"[+] Reel Video saved successfully at:\n    {output_path}\n")

def main():
    parser = argparse.ArgumentParser(description="Gargantua Black Hole Relativistic Raymarching Simulation")
    parser.add_argument("--export", action="store_true", help="Render and export 14s MP4 video reel")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode instead of fullscreen")
    parser.add_argument("--res", type=str, default="720x1280", help="Resolution for export, e.g. 720x1280 or 1080x1920")
    args = parser.parse_args()

    if args.export:
        try:
            w, h = map(int, args.res.split('x'))
        except Exception:
            w, h = 720, 1280
        renderer = BlackHoleRenderer(width=w, height=h, fullscreen=False, is_headless=True)
        renderer.export_video_reel(width=w, height=h)
    else:
        fullscreen = not args.windowed
        renderer = BlackHoleRenderer(fullscreen=fullscreen, is_headless=False)
        renderer.run_interactive()

if __name__ == "__main__":
    main()
