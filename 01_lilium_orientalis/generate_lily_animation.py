"""
================================================================================
  LILIUM ORIENTALIS — Procedural Botanical Compilation & Animation
  Designed for High-Engagement Aesthetic Tech & Coding Reels
================================================================================
Usage:
  python generate_lily_animation.py            # Opens in FULL LAPTOP SCREEN
  python generate_lily_animation.py --windowed # Opens in a window
  python generate_lily_animation.py --export   # Render & export 14s MP4 video reel

Controls:
  Left Mouse Drag  : Orbit 3D camera
  Right Mouse Drag : Pan camera
  Mouse Scroll     : Zoom in / out
  Spacebar         : Pause / Resume animation
  F / F11          : Toggle Fullscreen / Windowed
  W                : Toggle Wireframe / Shaded / Cinematic Mix
  R                : Reset animation & camera
  E                : Start MP4 Video Export
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

# Add local path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from math_utils import (
    perspective_matrix,
    look_at_matrix,
    rotation_matrix_y,
    smoothstep
)
import botanical_geometry
import shaders
from hud import BotanicalHUD

class LilyRenderer:
    def __init__(self, width=None, height=None, fullscreen=True, is_headless=False):
        self.is_headless = is_headless
        self.fullscreen = fullscreen
        self.total_duration = 14.0 # Seconds for full 3-stage compilation

        # Initialize Pygame & detect full laptop screen
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

        # Camera parameters
        self.cam_distance = 4.6
        self.cam_yaw = 0.0
        self.cam_pitch = 6.0
        self.cam_target = np.array([0.0, 0.35, 0.20], dtype=np.float32)
        self.auto_rotate = True

        # Render modes
        self.wireframe_mode = 0 # 0: Cinematic mix, 1: Wireframe only, 2: Shaded only
        self.anim_time = 0.0
        self.is_paused = False

        # Initialize graphics
        self._init_gl()
        self._init_geometry()
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
            pygame.display.set_caption("LILIUM ORIENTALIS // Procedural Botanical Specimen")
            self.ctx = moderngl.create_context()

        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        # 1. Botanical mesh shader
        self.botanical_prog = self.ctx.program(
            vertex_shader=shaders.BOTANICAL_VERTEX_SHADER,
            fragment_shader=shaders.BOTANICAL_FRAGMENT_SHADER
        )

        # 2. Pollen particle shader
        self.particle_prog = self.ctx.program(
            vertex_shader=shaders.PARTICLE_VERTEX_SHADER,
            fragment_shader=shaders.PARTICLE_FRAGMENT_SHADER
        )

        # 3. HUD Screen Quad Shader
        self.hud_prog = self.ctx.program(
            vertex_shader=shaders.HUD_VERTEX_SHADER,
            fragment_shader=shaders.HUD_FRAGMENT_SHADER
        )

        # Full-screen quad geometry for HUD overlay
        quad_vertices = np.array([
            -1.0, -1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 1.0,
             1.0,  1.0,  1.0, 0.0,
            -1.0, -1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 0.0,
        ], dtype=np.float32)

        self.hud_vbo = self.ctx.buffer(quad_vertices.tobytes())
        self.hud_vao = self.ctx.vertex_array(
            self.hud_prog,
            [(self.hud_vbo, '2f 2f', 'in_position', 'in_uv')]
        )
        self.hud_texture = self.ctx.texture((self.width, self.height), 4)

    def _init_geometry(self):
        """Generate procedural specimen geometry and upload to GPU VBOs."""
        print("[*] Generating 3D parametric surfaces for Lilium Orientalis...")
        vdata, particles = botanical_geometry.generate_full_botanical_specimen()

        self.vdata = vdata
        self.mesh_vbo = self.ctx.buffer(vdata.tobytes())
        self.mesh_vao = self.ctx.vertex_array(
            self.botanical_prog,
            [(self.mesh_vbo, '3f 3f 3f 3f 2f 4f 3f',
              'in_position', 'in_normal', 'in_color', 'in_bary', 'in_uv', 'in_timing', 'in_mat')]
        )
        self.vertex_count = len(vdata)
        print(f"[+] Loaded {self.vertex_count:,} botanical surface vertices into GPU memory.")

        # Particle VBO
        particle_data = []
        for p in particles:
            pos, phase, speed, radius = p
            particle_data.extend([pos[0], pos[1], pos[2], phase, speed, radius])
        p_arr = np.array(particle_data, dtype=np.float32)

        self.p_vbo = self.ctx.buffer(p_arr.tobytes())
        self.p_vao = self.ctx.vertex_array(
            self.particle_prog,
            [(self.p_vbo, '3f 1f 1f 1f', 'in_position', 'in_phase', 'in_speed', 'in_radius')]
        )
        self.particle_count = len(particles)
        print(f"[+] Created {self.particle_count} ambient 3D pollen bokeh particles.")

    def _init_hud(self):
        """Initialize the sci-fi botanical telemetry HUD generator."""
        self.hud = BotanicalHUD(self.width, self.height)

    def resize(self, new_w, new_h):
        """Handle screen resize or fullscreen toggle."""
        self.width = max(100, new_w)
        self.height = max(100, new_h)
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.hud = BotanicalHUD(self.width, self.height)
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

    def compute_matrices(self, t):
        """Calculate projection, view, and model matrices for timestamp t."""
        aspect = self.width / float(self.height)
        proj = perspective_matrix(42.0, aspect, 0.1, 100.0)

        # Gentle cinematic camera sway and drift
        if self.auto_rotate:
            drift_yaw = self.cam_yaw + math.sin(t * 0.32) * math.radians(14.0)
            drift_pitch = self.cam_pitch + 2.5 * math.cos(t * 0.40)
        else:
            drift_yaw = self.cam_yaw
            drift_pitch = self.cam_pitch

        rad_pitch = math.radians(drift_pitch)
        cam_x = self.cam_distance * math.cos(rad_pitch) * math.sin(drift_yaw)
        cam_y = self.cam_distance * math.sin(rad_pitch) + self.cam_target[1]
        cam_z = self.cam_distance * math.cos(rad_pitch) * math.cos(drift_yaw)
        cam_pos = np.array([cam_x, cam_y, cam_z], dtype=np.float32)

        view = look_at_matrix(cam_pos, self.cam_target, np.array([0.0, 1.0, 0.0], dtype=np.float32))

        # Model matrix: subtle vertical floating oscillation
        model = np.identity(4, dtype=np.float32)
        model[1, 3] = 0.02 * math.sin(t * 1.2)

        return proj, view, model, cam_pos

    def render_frame(self, t):
        """Render a single complete frame at time t."""
        self.ctx.clear(0.015, 0.018, 0.024, 1.0, depth=1.0)
        self.ctx.enable(moderngl.DEPTH_TEST)

        proj, view, model, cam_pos = self.compute_matrices(t)

        # 1. Render Botanical Mesh (Wireframe + SSS Shading)
        self.botanical_prog['m_proj'].write(proj.T.tobytes())
        self.botanical_prog['m_view'].write(view.T.tobytes())
        self.botanical_prog['m_model'].write(model.T.tobytes())
        self.botanical_prog['u_cam_pos'].value = tuple(cam_pos)
        self.botanical_prog['u_time'].value = float(t)
        self.botanical_prog['u_wireframe_mode'].value = int(self.wireframe_mode)

        self.mesh_vao.render(moderngl.TRIANGLES)

        # 2. Render 3D Pollen Bokeh Particles
        if t > 2.0:
            self.ctx.disable(moderngl.DEPTH_TEST)
            self.particle_prog['m_proj'].write(proj.T.tobytes())
            self.particle_prog['m_view'].write(view.T.tobytes())
            self.particle_prog['m_model'].write(model.T.tobytes())
            self.particle_prog['u_time'].value = float(t)
            self.p_vao.render(moderngl.POINTS)
            self.ctx.enable(moderngl.DEPTH_TEST)

        # 3. Render Botanical HUD Overlay
        self.ctx.disable(moderngl.DEPTH_TEST)
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

        print("\n" + "="*65)
        print("  LILIUM ORIENTALIS — Interactive Full-Screen Engine Active")
        print("="*65)
        print(f"  Display Mode : {'FULLSCREEN' if self.fullscreen else 'WINDOWED'} ({self.width}x{self.height})")
        print("  Controls:")
        print("    • Left Click + Drag  : Orbit 3D camera")
        print("    • Right Click + Drag : Pan camera position")
        print("    • Mouse Scroll       : Zoom in / out")
        print("    • Spacebar           : Pause / Play animation")
        print("    • 'F' / 'F11'        : Toggle Fullscreen / Windowed")
        print("    • 'W'                : Cycle Wireframe / Shaded / Mix")
        print("    • 'R'                : Restart compilation sequence")
        print("    • 'E'                : Export high-res MP4 video reel")
        print("    • ESC / 'Q'          : Exit viewer")
        print("="*65 + "\n")

        running = True
        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    if not self.fullscreen:
                        self.resize(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key in (pygame.K_f, pygame.K_F11):
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_w:
                        self.wireframe_mode = (self.wireframe_mode + 1) % 3
                        mode_names = ["Cinematic Hybrid Mix", "Pure Cyber Wireframe", "Photorealistic Shaded"]
                        print(f"[*] Visual mode: {mode_names[self.wireframe_mode]}")
                    elif event.key == pygame.K_r:
                        self.anim_time = 0.0
                        print("[*] Animation restarted at t = 0.0s")
                    elif event.key == pygame.K_e:
                        pygame.quit()
                        self.export_video()
                        return

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        dragging_left = True
                        self.auto_rotate = False
                        last_mouse_pos = event.pos
                    elif event.button == 3:
                        dragging_right = True
                        last_mouse_pos = event.pos
                    elif event.button == 4: # Scroll Up
                        self.cam_distance = max(1.5, self.cam_distance - 0.25)
                    elif event.button == 5: # Scroll Down
                        self.cam_distance = min(8.0, self.cam_distance + 0.25)

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
                        self.cam_yaw += dx * 0.012
                        self.cam_pitch = np.clip(self.cam_pitch + dy * 0.35, -75.0, 75.0)
                    elif dragging_right:
                        self.cam_target[0] -= dx * 0.003
                        self.cam_target[1] += dy * 0.003

            if not self.is_paused:
                self.anim_time += dt

            self.render_frame(self.anim_time)
            pygame.display.flip()

        pygame.quit()

    def export_video(self, output_filename="lilium_orientalis_reel.mp4", fps=30):
        """Render and export a 9:16 vertical video reel (720x1280 or 1080x1920)."""
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_filename)
        export_w, export_h = 720, 1280
        total_frames = int(self.total_duration * fps)

        print(f"\n[*] Initializing Video Export -> {output_path}")
        print(f"[*] Resolution: {export_w}x{export_h} | FPS: {fps} | Total Frames: {total_frames}")

        if not hasattr(self, 'ctx') or self.ctx is None:
            self.ctx = moderngl.create_context(standalone=True)

        fbo = self.ctx.simple_framebuffer((export_w, export_h))
        fbo.use()
        self.resize(export_w, export_h)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (export_w, export_h))

        if not writer.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            output_path = output_path.replace('.mp4', '.avi')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (export_w, export_h))

        start_time = time.time()
        for frame_idx in range(total_frames):
            t = (frame_idx / float(total_frames)) * self.total_duration
            self.render_frame(t)

            raw_bytes = fbo.read(components=3, alignment=1)
            img = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((export_h, export_w, 3))
            img = np.flipud(img)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            writer.write(img_bgr)

            if (frame_idx + 1) % 15 == 0 or frame_idx == total_frames - 1:
                pct = ((frame_idx + 1) / total_frames) * 100.0
                elapsed = time.time() - start_time
                fps_est = (frame_idx + 1) / max(0.01, elapsed)
                rem_sec = (total_frames - (frame_idx + 1)) / max(0.1, fps_est)
                print(f"\r  Rendering: [{frame_idx + 1:03d}/{total_frames}] {pct:5.1f}% | Speed: {fps_est:4.1f} fps | ETA: {rem_sec:4.1f}s", end="")

        writer.release()
        fbo.release()
        total_time = time.time() - start_time
        print(f"\n\n[+] Export Complete in {total_time:.1f}s!")
        print(f"[+] Reel Video saved successfully at:\n    {output_path}\n")

def main():
    parser = argparse.ArgumentParser(description="Lilium Orientalis — Procedural Botanical Compilation")
    parser.add_argument("--export", action="store_true", help="Render and export 14s MP4 reel video directly")
    parser.add_argument("--output", type=str, default="lilium_orientalis_reel.mp4", help="Output MP4 video filename")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second for video export (default: 30)")
    parser.add_argument("--res", type=str, default="720x1280", help="Resolution WxH for export (default: 720x1280)")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode instead of fullscreen")
    args = parser.parse_args()

    parts = args.res.split('x')
    width, height = int(parts[0]), int(parts[1])

    if args.export:
        renderer = LilyRenderer(width=width, height=height, is_headless=True)
        renderer.export_video(output_filename=args.output, fps=args.fps)
    else:
        # Default to opening in the full laptop screen!
        renderer = LilyRenderer(fullscreen=(not args.windowed), is_headless=False)
        renderer.run_interactive()

if __name__ == "__main__":
    main()
