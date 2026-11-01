"""
================================================================================
  EPISODE 02: SYNAPTIC CONNECTOME — Neural Brain Network Emulation
  Designed for High-Engagement Aesthetic Tech & Coding Reels
================================================================================
Usage:
  python generate_synapse_animation.py            # Opens in FULL LAPTOP SCREEN
  python generate_synapse_animation.py --windowed # Opens in a window
  python generate_synapse_animation.py --export   # Render & export 14s MP4 video reel

Controls:
  Left Mouse Drag  : Orbit 3D camera
  Right Mouse Drag : Pan camera
  Mouse Scroll     : Zoom in / out
  Spacebar         : Pause / Resume animation
  F / F11          : Toggle Fullscreen / Windowed
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

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from math_utils import (
    perspective_matrix,
    look_at_matrix,
    smoothstep
)
import neural_geometry
import shaders
from hud import NeuroHUD

class NeuralRenderer:
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
        self.cam_distance = 4.2
        self.cam_yaw = 0.0
        self.cam_pitch = 14.0
        self.cam_target = np.array([0.0, 0.05, 0.0], dtype=np.float32)
        self.auto_rotate = True

        self.anim_time = 0.0
        self.is_paused = False

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
            pygame.display.set_caption("EP 02: SYNAPTIC CONNECTOME // Neural Network Simulation")
            self.ctx = moderngl.create_context()

        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.enable(moderngl.BLEND)
        # Additive blending for electric glowing trails
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)

        # Programs
        self.fiber_prog = self.ctx.program(
            vertex_shader=shaders.FIBER_VERTEX_SHADER,
            fragment_shader=shaders.FIBER_FRAGMENT_SHADER
        )

        self.node_prog = self.ctx.program(
            vertex_shader=shaders.NODE_VERTEX_SHADER,
            fragment_shader=shaders.NODE_FRAGMENT_SHADER
        )

        self.vesicle_prog = self.ctx.program(
            vertex_shader=shaders.VESICLE_VERTEX_SHADER,
            fragment_shader=shaders.VESICLE_FRAGMENT_SHADER
        )

        self.hud_prog = self.ctx.program(
            vertex_shader=shaders.HUD_VERTEX_SHADER,
            fragment_shader=shaders.HUD_FRAGMENT_SHADER
        )

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
        """Generate procedural connectome and upload to GPU VBOs."""
        print("[*] Generating 3D anatomical connectome tracts & somas...")
        node_data, fiber_data, vesicle_data, tract_count = neural_geometry.generate_connectome_network(
            num_nodes=1400,
            num_tracts=2800
        )

        # 1. Somas (Nodes)
        self.node_vbo = self.ctx.buffer(node_data.tobytes())
        self.node_vao = self.ctx.vertex_array(
            self.node_prog,
            [(self.node_vbo, '3f 3f 1f 2f', 'in_position', 'in_color', 'in_size', 'in_timing')]
        )
        self.node_count = len(node_data)

        # 2. Fibers (Axons)
        self.fiber_vbo = self.ctx.buffer(fiber_data.tobytes())
        self.fiber_vao = self.ctx.vertex_array(
            self.fiber_prog,
            [(self.fiber_vbo, '3f 3f 1f 1f 4f', 'in_position', 'in_color', 'in_u', 'in_fiber_id', 'in_timing')]
        )
        self.fiber_vertex_count = len(fiber_data)

        # 3. Vesicles
        self.vesicle_vbo = self.ctx.buffer(vesicle_data.tobytes())
        self.vesicle_vao = self.ctx.vertex_array(
            self.vesicle_prog,
            [(self.vesicle_vbo, '3f 3f 1f 1f 1f', 'in_position', 'in_color', 'in_phase', 'in_speed', 'in_radius')]
        )
        self.vesicle_count = len(vesicle_data)

        print(f"[+] Loaded {self.node_count:,} soma hubs, {tract_count:,} axonal fascicles ({self.fiber_vertex_count:,} vertices), and {self.vesicle_count} neurotransmitter particles.")

    def _init_hud(self):
        self.hud = NeuroHUD(self.width, self.height)

    def resize(self, new_w, new_h):
        self.width = max(100, new_w)
        self.height = max(100, new_h)
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.hud = NeuroHUD(self.width, self.height)
        self.hud_texture.release()
        self.hud_texture = self.ctx.texture((self.width, self.height), 4)

    def toggle_fullscreen(self):
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
        aspect = self.width / float(self.height)
        proj = perspective_matrix(44.0, aspect, 0.1, 100.0)

        # Smooth continuous 3D camera drift
        if self.auto_rotate:
            drift_yaw = self.cam_yaw + math.sin(t * 0.28) * math.radians(22.0) + (t * 0.05)
            drift_pitch = self.cam_pitch + 4.0 * math.sin(t * 0.35)
        else:
            drift_yaw = self.cam_yaw
            drift_pitch = self.cam_pitch

        rad_pitch = math.radians(drift_pitch)
        cam_x = self.cam_distance * math.cos(rad_pitch) * math.sin(drift_yaw)
        cam_y = self.cam_distance * math.sin(rad_pitch) + self.cam_target[1]
        cam_z = self.cam_distance * math.cos(rad_pitch) * math.cos(drift_yaw)
        cam_pos = np.array([cam_x, cam_y, cam_z], dtype=np.float32)

        view = look_at_matrix(cam_pos, self.cam_target, np.array([0.0, 1.0, 0.0], dtype=np.float32))

        # Model matrix: subtle floating oscillation
        model = np.identity(4, dtype=np.float32)
        model[1, 3] = 0.02 * math.sin(t * 1.5)

        return proj, view, model, cam_pos

    def render_frame(self, t):
        # Deep space background
        self.ctx.clear(0.008, 0.010, 0.016, 1.0)

        proj, view, model, cam_pos = self.compute_matrices(t)

        # 1. Render Axonal Fiber Tracts (Lines with Additive Plasma Glow)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
        self.fiber_prog['m_proj'].write(proj.T.tobytes())
        self.fiber_prog['m_view'].write(view.T.tobytes())
        self.fiber_prog['m_model'].write(model.T.tobytes())
        self.fiber_prog['u_time'].value = float(t)
        self.fiber_vao.render(moderngl.LINES)

        # 2. Render Soma Hubs (Points)
        self.node_prog['m_proj'].write(proj.T.tobytes())
        self.node_prog['m_view'].write(view.T.tobytes())
        self.node_prog['m_model'].write(model.T.tobytes())
        self.node_prog['u_time'].value = float(t)
        self.node_vao.render(moderngl.POINTS)

        # 3. Render Drifting Neurotransmitter Spores
        if t > 2.0:
            self.vesicle_prog['m_proj'].write(proj.T.tobytes())
            self.vesicle_prog['m_view'].write(view.T.tobytes())
            self.vesicle_prog['m_model'].write(model.T.tobytes())
            self.vesicle_prog['u_time'].value = float(t)
            self.vesicle_vao.render(moderngl.POINTS)

        # 4. Render Neuro-Imaging HUD Overlay
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        hud_img = self.hud.render_overlay(t, self.total_duration)
        self.hud_texture.write(hud_img.tobytes())
        self.hud_texture.use(location=0)
        self.hud_prog['u_hud_texture'].value = 0
        self.hud_vao.render(moderngl.TRIANGLES)

    def run_interactive(self):
        clock = pygame.time.Clock()
        dragging_left = False
        dragging_right = False
        last_mouse_pos = (0, 0)

        print("\n" + "="*65)
        print("  SYNAPTIC CONNECTOME — Neural Network Engine Active")
        print("="*65)
        print(f"  Display Mode : {'FULLSCREEN' if self.fullscreen else 'WINDOWED'} ({self.width}x{self.height})")
        print("  Controls:")
        print("    • Left Click + Drag  : Orbit 3D brain")
        print("    • Right Click + Drag : Pan camera position")
        print("    • Mouse Scroll       : Zoom in / out")
        print("    • Spacebar           : Pause / Play animation")
        print("    • 'F' / 'F11'        : Toggle Fullscreen / Windowed")
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
                    elif event.button == 4:
                        self.cam_distance = max(1.2, self.cam_distance - 0.20)
                    elif event.button == 5:
                        self.cam_distance = min(7.5, self.cam_distance + 0.20)

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
                        self.cam_pitch = np.clip(self.cam_pitch + dy * 0.35, -80.0, 80.0)
                    elif dragging_right:
                        self.cam_target[0] -= dx * 0.003
                        self.cam_target[1] += dy * 0.003

            if not self.is_paused:
                self.anim_time += dt

            self.render_frame(self.anim_time)
            pygame.display.flip()

        pygame.quit()

    def export_video(self, output_filename="neural_synapse_reel.mp4", fps=30):
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
    parser = argparse.ArgumentParser(description="Synaptic Connectome — Neural Brain Network Emulation")
    parser.add_argument("--export", action="store_true", help="Render and export 14s MP4 reel video directly")
    parser.add_argument("--output", type=str, default="neural_synapse_reel.mp4", help="Output MP4 video filename")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second for video export (default: 30)")
    parser.add_argument("--res", type=str, default="720x1280", help="Resolution WxH for export (default: 720x1280)")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode instead of fullscreen")
    args = parser.parse_args()

    parts = args.res.split('x')
    width, height = int(parts[0]), int(parts[1])

    if args.export:
        renderer = NeuralRenderer(width=width, height=height, is_headless=True)
        renderer.export_video(output_filename=args.output, fps=args.fps)
    else:
        renderer = NeuralRenderer(fullscreen=(not args.windowed), is_headless=False)
        renderer.run_interactive()

if __name__ == "__main__":
    main()
