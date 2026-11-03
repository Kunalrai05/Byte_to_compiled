"""
================================================================================
  HARMONIC PENDULUM WAVE // 調和振り子
  Kinetic Resonance Simulation & Coherent Frequency Dispersion
  Episode 03 of Byte to Compiled (Aesthetic Creative Coding Series)
================================================================================
Usage:
  python generate_pendulum_animation.py            # Launches in FULL LAPTOP SCREEN
  python generate_pendulum_animation.py --windowed # Opens in a window
  python generate_pendulum_animation.py --export   # Render & export 14s MP4 video reel

Controls:
  Left Mouse Drag  : Orbit 3D camera
  Right Mouse Drag : Pan camera target
  Mouse Scroll     : Zoom in / out
  Spacebar         : Pause / Resume animation
  H                : Toggle HUD Telemetry on / off (Pure Cinematic View)
  F / F11          : Toggle Fullscreen / Windowed
  W                : Toggle Visual Modes (Cinematic Hybrid / Pure Wireframe / Photorealistic)
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
import pendulum_geometry
from hud import PendulumHUD

class PendulumWaveRenderer:
    def __init__(self, width=None, height=None, fullscreen=True, is_headless=False):
        self.is_headless = is_headless
        self.fullscreen = fullscreen
        self.total_duration = pendulum_geometry.CYCLE_DURATION # 14.0 seconds for exact harmonic loop

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

        # Camera parameters (Elevated 3/4 side perspective down the wave)
        self.cam_distance = 5.8
        self.cam_yaw = math.radians(38.0)
        self.cam_pitch = math.radians(22.0)
        self.cam_target = np.array([0.0, 0.15, 0.0], dtype=np.float32)
        self.auto_rotate = True

        # Render modes
        self.visual_mode = 0 # 0: Cinematic Hybrid, 1: Wireframe, 2: Photorealistic
        self.show_hud = True
        self.show_ribbon = True
        self.anim_time = 0.0
        self.is_paused = False

        self.colors = pendulum_geometry.get_pendulum_colors(pendulum_geometry.NUM_PENDULUMS)

        # Initialize graphics
        self._init_gl()
        self._init_static_geometry()
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
            pygame.display.set_caption("HARMONIC PENDULUM WAVE // Kinetic Resonance Engine")
            self.ctx = moderngl.create_context()

        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        # 1. Background studio shader
        self.bg_prog = self.ctx.program(
            vertex_shader=shaders.BG_VERTEX_SHADER,
            fragment_shader=shaders.BG_FRAGMENT_SHADER
        )

        # 2. Pendulum mesh shader
        self.pendulum_prog = self.ctx.program(
            vertex_shader=shaders.PENDULUM_VERTEX_SHADER,
            fragment_shader=shaders.PENDULUM_FRAGMENT_SHADER
        )

        # 3. Wave ribbon shader
        self.ribbon_prog = self.ctx.program(
            vertex_shader=shaders.RIBBON_VERTEX_SHADER,
            fragment_shader=shaders.RIBBON_FRAGMENT_SHADER
        )

        # Screen quad for background
        quad_vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0, -1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 1.0,
        ], dtype=np.float32)

        self.screen_quad_vbo = self.ctx.buffer(quad_vertices.tobytes())
        self.bg_vao = self.ctx.vertex_array(
            self.bg_prog,
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

    def _init_static_geometry(self):
        """Generate static studio floor and suspension frame rail."""
        static_verts = []

        # Floor
        static_verts.extend(pendulum_geometry.generate_studio_floor(size=7.0))

        # Top suspension metal rail
        rail_p0 = np.array([-pendulum_geometry.X_SPAN * 0.55, pendulum_geometry.RAIL_Y, 0.0], dtype=np.float32)
        rail_p1 = np.array([ pendulum_geometry.X_SPAN * 0.55, pendulum_geometry.RAIL_Y, 0.0], dtype=np.float32)
        static_verts.extend(pendulum_geometry.generate_cylinder_tube(
            rail_p0, rail_p1, radius=0.032,
            color=np.array([0.38, 0.44, 0.52], dtype=np.float32),
            timing=np.array([0.0, 1.0, 0.0, 2.0], dtype=np.float32)
        ))

        # Support A-frame vertical stand legs at each end
        leg_z = 0.85
        leg_floor_y = -1.8
        for rx in [-pendulum_geometry.X_SPAN * 0.55, pendulum_geometry.X_SPAN * 0.55]:
            top_pt = np.array([rx, pendulum_geometry.RAIL_Y, 0.0], dtype=np.float32)
            leg_front = np.array([rx, leg_floor_y,  leg_z], dtype=np.float32)
            leg_back  = np.array([rx, leg_floor_y, -leg_z], dtype=np.float32)
            static_verts.extend(pendulum_geometry.generate_cylinder_tube(
                top_pt, leg_front, radius=0.024,
                color=np.array([0.28, 0.32, 0.38], dtype=np.float32),
                timing=np.array([0.0, 1.0, 0.0, 2.0], dtype=np.float32)
            ))
            static_verts.extend(pendulum_geometry.generate_cylinder_tube(
                top_pt, leg_back, radius=0.024,
                color=np.array([0.28, 0.32, 0.38], dtype=np.float32),
                timing=np.array([0.0, 1.0, 0.0, 2.0], dtype=np.float32)
            ))

        s_data = np.array(static_verts, dtype=np.float32)
        self.static_vbo = self.ctx.buffer(s_data.tobytes())
        self.static_vao = self.ctx.vertex_array(
            self.pendulum_prog,
            [(self.static_vbo, '3f 3f 3f 3f 2f 4f 3f',
              'in_position', 'in_normal', 'in_color', 'in_bary', 'in_uv', 'in_timing', 'in_mat')]
        )
        self.static_vert_count = len(static_verts)

    def _init_hud(self):
        """Initialize telemetry HUD generator."""
        self.hud = PendulumHUD(self.width, self.height)

    def resize(self, new_w, new_h):
        """Handle screen resize or fullscreen toggle."""
        self.width = max(100, new_w)
        self.height = max(100, new_h)
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.hud = PendulumHUD(self.width, self.height)
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
        """Compute camera projection, view, and model matrices for timestamp t."""
        aspect = self.width / float(self.height)
        fovy = 38.0 if aspect > 1.0 else 46.0
        proj = perspective_matrix(fovy, aspect, 0.1, 50.0)

        if self.auto_rotate:
            # Cinematic camera choreography synced to the harmonic cycle
            t_norm = (t % self.total_duration) / self.total_duration
            
            # Camera sweeps from 3/4 isometric down along the rail into front alignment
            yaw = self.cam_yaw + math.sin(t_norm * 2.0 * math.pi) * math.radians(16.0)
            pitch = self.cam_pitch + math.cos(t_norm * 2.0 * math.pi) * math.radians(5.0)
            dist = self.cam_distance + 0.35 * math.sin(t_norm * math.pi)
        else:
            yaw = self.cam_yaw
            pitch = self.cam_pitch
            dist = self.cam_distance

        cam_x = dist * math.cos(pitch) * math.sin(yaw)
        cam_y = dist * math.sin(pitch) + self.cam_target[1]
        cam_z = dist * math.cos(pitch) * math.cos(yaw)
        cam_pos = np.array([cam_x, cam_y, cam_z], dtype=np.float32)

        view = look_at_matrix(cam_pos, self.cam_target, np.array([0.0, 1.0, 0.0], dtype=np.float32))
        model = np.identity(4, dtype=np.float32)
        return proj, view, model, cam_pos

    def render_frame(self, t):
        """Render a single complete frame at timestamp t."""
        self.ctx.clear(0.015, 0.020, 0.038, 1.0, depth=1.0)

        # 1. Background Studio Atmosphere
        self.ctx.disable(moderngl.DEPTH_TEST)
        if 'u_time' in self.bg_prog:
            self.bg_prog['u_time'].value = float(t)
        if 'u_resolution' in self.bg_prog:
            self.bg_prog['u_resolution'].value = (float(self.width), float(self.height))
        self.bg_vao.render(moderngl.TRIANGLES)
        self.ctx.enable(moderngl.DEPTH_TEST)

        proj, view, model, cam_pos = self.compute_matrices(t)

        # 2. Render Static Floor & Rail
        self.pendulum_prog['m_proj'].write(proj.T.tobytes())
        self.pendulum_prog['m_view'].write(view.T.tobytes())
        self.pendulum_prog['m_model'].write(model.T.tobytes())
        self.pendulum_prog['u_cam_pos'].value = tuple(cam_pos)
        self.pendulum_prog['u_time'].value = float(t)
        self.pendulum_prog['u_mode'].value = int(self.visual_mode)
        self.static_vao.render(moderngl.TRIANGLES)

        # 3. Dynamic Pendulums (24 Spheres + Suspension Wires)
        pendulums = pendulum_geometry.calculate_pendulums(t, self.colors)
        dynamic_verts = []

        timing = np.array([0.0, 2.5, 0.5, 4.0], dtype=np.float32)
        for p in pendulums:
            # Wire
            wire_col = p['color'] * 0.65 + np.array([0.22, 0.32, 0.42], dtype=np.float32) * 0.35
            dynamic_verts.extend(pendulum_geometry.generate_cylinder_tube(
                p['pivot'], p['pos'], radius=0.007,
                color=wire_col, timing=timing
            ))
            # Sphere
            dynamic_verts.extend(pendulum_geometry.generate_uv_sphere(
                p['pos'], pendulum_geometry.SPHERE_RADIUS,
                p['color'], float(p['index']), timing
            ))

        d_data = np.array(dynamic_verts, dtype=np.float32)
        dyn_vbo = self.ctx.buffer(d_data.tobytes())
        dyn_vao = self.ctx.vertex_array(
            self.pendulum_prog,
            [(dyn_vbo, '3f 3f 3f 3f 2f 4f 3f',
              'in_position', 'in_normal', 'in_color', 'in_bary', 'in_uv', 'in_timing', 'in_mat')]
        )
        dyn_vao.render(moderngl.TRIANGLES)
        dyn_vao.release()
        dyn_vbo.release()

        # 4. Wave Energy Ribbon (Connecting all 24 spheres along the wave)
        if self.show_ribbon and t > 0.5:
            ribbon_data = pendulum_geometry.generate_wave_ribbon(pendulums, width=0.024, alpha=0.85)
            if len(ribbon_data) > 0:
                self.ctx.disable(moderngl.DEPTH_TEST)
                self.ribbon_prog['m_proj'].write(proj.T.tobytes())
                self.ribbon_prog['m_view'].write(view.T.tobytes())
                self.ribbon_prog['m_model'].write(model.T.tobytes())
                if 'u_time' in self.ribbon_prog:
                    self.ribbon_prog['u_time'].value = float(t)

                rib_vbo = self.ctx.buffer(ribbon_data.tobytes())
                rib_vao = self.ctx.vertex_array(
                    self.ribbon_prog,
                    [(rib_vbo, '3f 3f 1f', 'in_position', 'in_color', 'in_alpha')]
                )
                rib_vao.render(moderngl.TRIANGLES)
                rib_vao.release()
                rib_vbo.release()
                self.ctx.enable(moderngl.DEPTH_TEST)

        # 5. Telemetry HUD Overlay
        if self.show_hud:
            self.ctx.disable(moderngl.DEPTH_TEST)
            hud_img = self.hud.render_overlay(t, self.total_duration)
            self.hud_texture.write(hud_img.tobytes())
            self.hud_texture.use(location=0)
            self.hud_prog['u_hud_texture'].value = 0
            self.hud_vao.render(moderngl.TRIANGLES)
            self.ctx.enable(moderngl.DEPTH_TEST)

    def run_interactive(self):
        """Run real-time interactive 60 FPS viewer window."""
        clock = pygame.time.Clock()
        dragging_left = False
        dragging_right = False
        last_mouse_pos = (0, 0)

        print("\n" + "="*68)
        print("  HARMONIC PENDULUM WAVE // Kinetic Resonance Active")
        print("="*68)
        print(f"  Display Mode : {'FULLSCREEN' if self.fullscreen else 'WINDOWED'} ({self.width}x{self.height})")
        print("  Controls:")
        print("    Left Drag   : Orbit camera around wave")
        print("    Right Drag  : Pan camera target")
        print("    Scroll Wheel: Zoom in / out")
        print("    Spacebar    : Pause / Resume animation")
        print("    H           : Toggle HUD Telemetry on / off")
        print("    F / F11     : Toggle Fullscreen / Windowed")
        print("    W           : Cycle Visual Modes (Hybrid / Wireframe / Photorealistic)")
        print("    R           : Restart animation from t = 0")
        print("    E           : Export 14s MP4 video reel")
        print("    ESC / Q     : Quit")
        print("="*68 + "\n")

        running = True
        while running:
            dt = clock.tick(60) / 1000.0

            if not self.is_paused:
                self.anim_time += dt
                if self.anim_time > self.total_duration:
                    self.anim_time = 0.0 # Seamless infinite harmonic loop

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
                        modes = ["Cinematic Hybrid Mix", "Pure Wireframe", "Photorealistic Shaded"]
                        print(f"[*] Visual Mode: {modes[self.visual_mode]}")
                    elif event.key == pygame.K_r:
                        self.anim_time = 0.0
                        self.cam_distance = 5.8
                        self.cam_yaw = math.radians(38.0)
                        self.cam_pitch = math.radians(22.0)
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
                        self.cam_distance = max(2.5, self.cam_distance - 0.35)
                    elif event.button == 5: # Scroll Down
                        self.cam_distance = min(15.0, self.cam_distance + 0.35)

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
                        self.cam_pitch = np.clip(self.cam_pitch + dy * 0.006, math.radians(-10.0), math.radians(65.0))
                    elif dragging_right:
                        self.cam_target[0] += dx * 0.010
                        self.cam_target[1] -= dy * 0.010

                elif event.type == pygame.VIDEORESIZE:
                    if not self.fullscreen:
                        self.resize(event.w, event.h)

            self.render_frame(self.anim_time)
            pygame.display.flip()

        pygame.quit()

    def export_video_reel(self, output_path=None, fps=30, width=720, height=1280):
        """Headless high-fidelity 9:16 vertical MP4 video reel exporter."""
        if output_path is None:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pendulum_reel.mp4")

        total_frames = int(self.total_duration * fps)
        print(f"\n[*] Initializing Pendulum Wave Reel Export -> {output_path}")
        print(f"[*] Resolution: {width}x{height} | FPS: {fps} | Total Frames: {total_frames}")

        export_ctx = moderngl.create_context(standalone=True)
        export_fbo = export_ctx.simple_framebuffer((width, height))
        export_fbo.use()
        export_ctx.enable(moderngl.DEPTH_TEST)
        export_ctx.enable(moderngl.BLEND)
        export_ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        # Programs
        bg_prog = export_ctx.program(vertex_shader=shaders.BG_VERTEX_SHADER, fragment_shader=shaders.BG_FRAGMENT_SHADER)
        p_prog = export_ctx.program(vertex_shader=shaders.PENDULUM_VERTEX_SHADER, fragment_shader=shaders.PENDULUM_FRAGMENT_SHADER)
        rib_prog = export_ctx.program(vertex_shader=shaders.RIBBON_VERTEX_SHADER, fragment_shader=shaders.RIBBON_FRAGMENT_SHADER)

        # Background quad
        quad_verts = np.array([-1,-1,0,0, 1,-1,1,0, 1,1,1,1, -1,-1,0,0, 1,1,1,1, -1,1,0,1], dtype=np.float32)
        bg_vbo = export_ctx.buffer(quad_verts.tobytes())
        bg_vao = export_ctx.vertex_array(bg_prog, [(bg_vbo, '2f 2f', 'in_position', 'in_uv')])

        # Static floor & rail
        static_verts = []
        static_verts.extend(pendulum_geometry.generate_studio_floor(size=7.0))
        rail_p0 = np.array([-pendulum_geometry.X_SPAN * 0.55, pendulum_geometry.RAIL_Y, 0.0], dtype=np.float32)
        rail_p1 = np.array([ pendulum_geometry.X_SPAN * 0.55, pendulum_geometry.RAIL_Y, 0.0], dtype=np.float32)
        static_verts.extend(pendulum_geometry.generate_cylinder_tube(
            rail_p0, rail_p1, radius=0.032,
            color=np.array([0.38, 0.44, 0.52], dtype=np.float32),
            timing=np.array([0.0, 1.0, 0.0, 2.0], dtype=np.float32)
        ))

        # Support stands
        for rx in [-pendulum_geometry.X_SPAN * 0.55, pendulum_geometry.X_SPAN * 0.55]:
            top_pt = np.array([rx, pendulum_geometry.RAIL_Y, 0.0], dtype=np.float32)
            static_verts.extend(pendulum_geometry.generate_cylinder_tube(
                top_pt, np.array([rx, -1.8,  0.85], dtype=np.float32), radius=0.024,
                color=np.array([0.28, 0.32, 0.38], dtype=np.float32),
                timing=np.array([0.0, 1.0, 0.0, 2.0], dtype=np.float32)
            ))
            static_verts.extend(pendulum_geometry.generate_cylinder_tube(
                top_pt, np.array([rx, -1.8, -0.85], dtype=np.float32), radius=0.024,
                color=np.array([0.28, 0.32, 0.38], dtype=np.float32),
                timing=np.array([0.0, 1.0, 0.0, 2.0], dtype=np.float32)
            ))

        s_data = np.array(static_verts, dtype=np.float32)
        s_vbo = export_ctx.buffer(s_data.tobytes())
        s_vao = export_ctx.vertex_array(p_prog, [(s_vbo, '3f 3f 3f 3f 2f 4f 3f',
                                                 'in_position', 'in_normal', 'in_color', 'in_bary', 'in_uv', 'in_timing', 'in_mat')])

        hud = PendulumHUD(width, height)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        t_start = time.time()
        for frame_idx in range(total_frames):
            t = (frame_idx / float(fps))

            export_fbo.clear(0.015, 0.020, 0.038, 1.0, depth=1.0)

            # 1. Background
            export_ctx.disable(moderngl.DEPTH_TEST)
            if 'u_time' in bg_prog:
                bg_prog['u_time'].value = float(t)
            if 'u_resolution' in bg_prog:
                bg_prog['u_resolution'].value = (float(width), float(height))
            bg_vao.render(moderngl.TRIANGLES)
            export_ctx.enable(moderngl.DEPTH_TEST)

            # 2. Camera Matrices
            aspect = width / float(height)
            proj = perspective_matrix(46.0, aspect, 0.1, 50.0)

            t_norm = (t % self.total_duration) / self.total_duration
            yaw = math.radians(38.0) + math.sin(t_norm * 2.0 * math.pi) * math.radians(16.0)
            pitch = math.radians(22.0) + math.cos(t_norm * 2.0 * math.pi) * math.radians(5.0)
            dist = 6.2 + 0.35 * math.sin(t_norm * math.pi)

            cam_x = dist * math.cos(pitch) * math.sin(yaw)
            cam_y = dist * math.sin(pitch) + 0.15
            cam_z = dist * math.cos(pitch) * math.cos(yaw)
            cam_pos = np.array([cam_x, cam_y, cam_z], dtype=np.float32)

            view = look_at_matrix(cam_pos, np.array([0.0, 0.15, 0.0], dtype=np.float32), np.array([0.0, 1.0, 0.0], dtype=np.float32))
            model = np.identity(4, dtype=np.float32)

            # 3. Static Floor & Rail
            p_prog['m_proj'].write(proj.T.tobytes())
            p_prog['m_view'].write(view.T.tobytes())
            p_prog['m_model'].write(model.T.tobytes())
            p_prog['u_cam_pos'].value = tuple(cam_pos)
            p_prog['u_time'].value = float(t)
            p_prog['u_mode'].value = 0
            s_vao.render(moderngl.TRIANGLES)

            # 4. Dynamic Spheres & Wires
            pendulums = pendulum_geometry.calculate_pendulums(t, self.colors)
            dyn_verts = []
            timing = np.array([0.0, 2.5, 0.5, 4.0], dtype=np.float32)

            for p in pendulums:
                wire_col = p['color'] * 0.65 + np.array([0.22, 0.32, 0.42], dtype=np.float32) * 0.35
                dyn_verts.extend(pendulum_geometry.generate_cylinder_tube(
                    p['pivot'], p['pos'], radius=0.007,
                    color=wire_col, timing=timing
                ))
                dyn_verts.extend(pendulum_geometry.generate_uv_sphere(
                    p['pos'], pendulum_geometry.SPHERE_RADIUS,
                    p['color'], float(p['index']), timing
                ))

            d_data = np.array(dyn_verts, dtype=np.float32)
            d_vbo = export_ctx.buffer(d_data.tobytes())
            d_vao = export_ctx.vertex_array(p_prog, [(d_vbo, '3f 3f 3f 3f 2f 4f 3f',
                                                     'in_position', 'in_normal', 'in_color', 'in_bary', 'in_uv', 'in_timing', 'in_mat')])
            d_vao.render(moderngl.TRIANGLES)
            d_vao.release()
            d_vbo.release()

            # 5. Wave Ribbon
            if t > 0.5:
                rib_data = pendulum_geometry.generate_wave_ribbon(pendulums, width=0.024, alpha=0.85)
                if len(rib_data) > 0:
                    export_ctx.disable(moderngl.DEPTH_TEST)
                    rib_prog['m_proj'].write(proj.T.tobytes())
                    rib_prog['m_view'].write(view.T.tobytes())
                    rib_prog['m_model'].write(model.T.tobytes())
                    if 'u_time' in rib_prog:
                        rib_prog['u_time'].value = float(t)

                    rib_vbo = export_ctx.buffer(rib_data.tobytes())
                    rib_vao = export_ctx.vertex_array(rib_prog, [(rib_vbo, '3f 3f 1f', 'in_position', 'in_color', 'in_alpha')])
                    rib_vao.render(moderngl.TRIANGLES)
                    rib_vao.release()
                    rib_vbo.release()
                    export_ctx.enable(moderngl.DEPTH_TEST)

            # Read back frame and composite HUD
            raw_bytes = export_fbo.read(components=3)
            frame_np = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, width, 3))
            frame_np = np.flipud(frame_np)
            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)

            frame_with_hud = hud.draw_on_opencv_frame(frame_bgr, t, self.total_duration)
            writer.write(frame_with_hud)

            if (frame_idx + 1) % 15 == 0 or frame_idx == total_frames - 1:
                elapsed = time.time() - t_start
                rate = (frame_idx + 1) / max(0.001, elapsed)
                remaining = (total_frames - (frame_idx + 1)) / max(0.001, rate)
                pct = ((frame_idx + 1) / total_frames) * 100.0
                print(f"  Rendering: [{frame_idx+1:03d}/{total_frames:03d}] {pct:5.1f}% | Speed: {rate:4.1f} fps | ETA: {remaining:4.1f}s", end='\r')

        writer.release()
        s_vao.release()
        s_vbo.release()
        bg_vao.release()
        bg_vbo.release()
        export_fbo.release()
        print(f"\n[+] Export Complete in {time.time() - t_start:.1f}s!")
        print(f"[+] Reel Video saved successfully at:\n    {output_path}\n")

def main():
    parser = argparse.ArgumentParser(description="Harmonic Pendulum Wave Kinetic Simulation")
    parser.add_argument("--export", action="store_true", help="Render and export 14s MP4 video reel")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode instead of fullscreen")
    parser.add_argument("--res", type=str, default="720x1280", help="Resolution for export, e.g. 720x1280 or 1080x1920")
    args = parser.parse_args()

    if args.export:
        try:
            w, h = map(int, args.res.split('x'))
        except Exception:
            w, h = 720, 1280
        renderer = PendulumWaveRenderer(width=w, height=h, fullscreen=False, is_headless=True)
        renderer.export_video_reel(width=w, height=h)
    else:
        fullscreen = not args.windowed
        renderer = PendulumWaveRenderer(fullscreen=fullscreen, is_headless=False)
        renderer.run_interactive()

if __name__ == "__main__":
    main()
