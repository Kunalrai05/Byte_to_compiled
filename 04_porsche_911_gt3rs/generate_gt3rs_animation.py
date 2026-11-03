"""
Porsche 911 GT3 RS (992) Interactive Simulation & 9:16 Video Exporter.
Features:
- Full Laptop Screen (1536x864, 60 FPS) with borderless fullscreen support.
- 3D Procedural 911 GT3 RS with active DRS wing flap and 60-year morphing.
- Wind Tunnel CFD aerodynamic streamline particle system (1,600+ ribbons).
- Porsche Motorsport Telemetry HUD (9,000 RPM tachometer, shift lights, G-meter, Nürburgring 06:49.328).
- Headless 9:16 vertical MP4 video export for Instagram Reels.
"""

import sys
import os
import time
import math
import argparse
import numpy as np
import moderngl
import pygame
import cv2

from math_utils import (
    perspective_matrix, look_at_matrix, identity_matrix,
    rotate_x_matrix, rotate_y_matrix, rotate_z_matrix,
    translation_matrix, scale_matrix, smoothstep, lerp
)
import porsche_geometry
import shaders
from hud import PorscheHUD


def set_uniform(prog, name, val):
    """Safely set a uniform value or buffer on a ModernGL program."""
    if name in prog:
        if isinstance(val, (bytes, bytearray, memoryview)):
            prog[name].write(val)
        else:
            prog[name].value = val


class PorscheGT3RSRenderer:
    def __init__(self, width=1536, height=864, fullscreen=False, is_headless=False):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.is_headless = is_headless
        self.total_duration = 14.0

        # Paint Finishes (Body Color Options)
        self.paint_presets = [
            ("Arctic Grey",  np.array([0.80, 0.83, 0.87], dtype=np.float32)),
            ("Shark Blue",   np.array([0.05, 0.45, 0.88], dtype=np.float32)),
            ("Guards Red",   np.array([0.85, 0.08, 0.05], dtype=np.float32)),
            ("Lizard Green", np.array([0.25, 0.85, 0.12], dtype=np.float32)),
            ("Triple Black", np.array([0.08, 0.08, 0.09], dtype=np.float32))
        ]
        self.paint_index = 0
        self.body_color = self.paint_presets[self.paint_index][1]

        # Interactive State
        self.is_paused = False
        self.show_hud = True
        self.wire_mode = 0  # 0: Shaded, 1: Wireframe, 2: Hybrid
        self.drs_manual = False
        self.throttle_manual = 0.0
        self.cam_preset = 0 # 0: Dynamic Cinematic, 1: Front 3/4, 2: Side Aero, 3: Top CFD, 4: Rear Wing, 5: Free

        # Free Orbit Camera Controls
        self.cam_yaw = 28.0
        self.cam_pitch = 18.0
        self.cam_dist = 6.2
        self.cam_target = np.array([0.0, 0.70, 0.0], dtype=np.float32)
        self.mouse_dragging_left = False
        self.mouse_dragging_right = False
        self.last_mouse_pos = (0, 0)

        if not self.is_headless:
            self._init_window()
            self._init_gl()
            self._init_geometry()
            self._init_hud()
            self._init_streamlines()

    def _init_window(self):
        """Initialize Pygame display with OpenGL context."""
        pygame.init()
        pygame.display.set_caption("Porsche 911 GT3 RS (992) // Weissach Aerodynamics & Telemetry Lab")

        # Query desktop resolution for perfect borderless fullscreen on user's laptop
        display_info = pygame.display.Info()
        self.desktop_w = display_info.current_w
        self.desktop_h = display_info.current_h

        if self.fullscreen:
            self.width = self.desktop_w
            self.height = self.desktop_h
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN
        else:
            self.width = min(1536, int(self.desktop_w * 0.92))
            self.height = min(864, int(self.desktop_h * 0.90))
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE

        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        self.clock = pygame.time.Clock()

    def _init_gl(self):
        """Initialize ModernGL context and shader programs."""
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        # 1. Car & Chassis Shader
        self.car_prog = self.ctx.program(
            vertex_shader=shaders.CAR_VERT_SRC,
            fragment_shader=shaders.CAR_FRAG_SRC
        )

        # 2. DRS Upper Wing Flap Shader
        self.drs_prog = self.ctx.program(
            vertex_shader=shaders.DRS_VERT_SRC,
            fragment_shader=shaders.CAR_FRAG_SRC
        )

        # 3. CFD Streamlines Shader
        self.stream_prog = self.ctx.program(
            vertex_shader=shaders.STREAMLINE_VERT_SRC,
            fragment_shader=shaders.STREAMLINE_FRAG_SRC
        )

        # 4. Background Studio Shader
        self.bg_prog = self.ctx.program(
            vertex_shader=shaders.BG_VERT_SRC,
            fragment_shader=shaders.BG_FRAG_SRC
        )

        # 5. HUD Quad Shader
        self.hud_prog = self.ctx.program(
            vertex_shader=shaders.HUD_VERT_SRC,
            fragment_shader=shaders.HUD_FRAG_SRC
        )

        # Setup Fullscreen Background Quad
        bg_quad = np.array([
            -1.0, -1.0,
             1.0, -1.0,
             1.0,  1.0,
            -1.0, -1.0,
             1.0,  1.0,
            -1.0,  1.0
        ], dtype=np.float32)
        self.bg_vbo = self.ctx.buffer(bg_quad.tobytes())
        self.bg_vao = self.ctx.vertex_array(self.bg_prog, [(self.bg_vbo, '2f', 'in_pos')])

        # Setup HUD Quad
        hud_quad = np.array([
            -1.0, -1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 1.0,
             1.0,  1.0,  1.0, 0.0,
            -1.0, -1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 0.0
        ], dtype=np.float32)
        self.hud_vbo = self.ctx.buffer(hud_quad.tobytes())
        self.hud_vao = self.ctx.vertex_array(self.hud_prog, [(self.hud_vbo, '2f 2f', 'in_pos', 'in_uv')])

        self.hud_texture = self.ctx.texture((self.width, self.height), 4)
        self.hud_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

    def _init_geometry(self):
        """Compile procedural Porsche meshes (body, wings, wheels, floor)."""
        # 1. Car Body + Wheels + Floor + Static Wing elements
        body_verts = porsche_geometry.generate_porsche_body()
        floor_verts = porsche_geometry.generate_studio_floor()
        wing_static_verts, drs_flap_verts = porsche_geometry.generate_swan_neck_rear_wing()

        # 4 Wheels
        # Front: cx = +-0.88, cy = 0.34, cz = -1.22, radius = 0.34, width = 0.26
        # Rear:  cx = +-0.94, cy = 0.35, cz =  1.23, radius = 0.35, width = 0.32
        wheel_verts = []
        wheel_verts.extend(porsche_geometry.generate_wheel_assembly([ 0.88, 0.34, -1.22], 0.34, 0.26, is_front=True))
        wheel_verts.extend(porsche_geometry.generate_wheel_assembly([-0.88, 0.34, -1.22], 0.34, 0.26, is_front=True))
        wheel_verts.extend(porsche_geometry.generate_wheel_assembly([ 0.94, 0.35,  1.23], 0.35, 0.32, is_front=False))
        wheel_verts.extend(porsche_geometry.generate_wheel_assembly([-0.94, 0.35,  1.23], 0.35, 0.32, is_front=False))

        all_static = []
        all_static.extend(floor_verts)
        all_static.extend(body_verts)
        all_static.extend(wheel_verts)
        all_static.extend(wing_static_verts)

        # Convert to numpy buffer: 3f(pos) 3f(norm) 3f(col) 2f(uv) 3f(mat) 3f(morph) = 17 floats
        s_data = np.array(all_static, dtype=np.float32)
        self.car_vbo = self.ctx.buffer(s_data.tobytes())
        self.car_vao = self.ctx.vertex_array(
            self.car_prog,
            [(self.car_vbo, '3f 3f 3f 2f 3f 3f',
              'in_position', 'in_normal', 'in_color', 'in_uv', 'in_mat', 'in_morph_pos')]
        )
        self.car_vert_count = len(all_static) // 17

        # 2. Active DRS Flap Mesh
        drs_data = np.array(drs_flap_verts, dtype=np.float32)
        self.drs_vbo = self.ctx.buffer(drs_data.tobytes())
        self.drs_vao = self.ctx.vertex_array(
            self.drs_prog,
            [(self.drs_vbo, '3f 3f 3f 2f 3f 3f',
              'in_position', 'in_normal', 'in_color', 'in_uv', 'in_mat', 'in_morph_pos')]
        )
        self.drs_vert_count = len(drs_flap_verts) // 17

    def _init_streamlines(self):
        """Initialize wind tunnel aerodynamic streamline seed particles."""
        self.streamlines = porsche_geometry.generate_cfd_streamlines(num_lines=1600)

    def _init_hud(self):
        """Initialize Porsche telemetry HUD generator."""
        self.hud = PorscheHUD(self.width, self.height)

    def resize(self, new_w, new_h):
        """Handle screen resize and update viewport / textures."""
        self.width = max(100, new_w)
        self.height = max(100, new_h)
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.hud = PorscheHUD(self.width, self.height)
        self.hud_texture.release()
        self.hud_texture = self.ctx.texture((self.width, self.height), 4)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode smoothly."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN
            self.screen = pygame.display.set_mode((self.desktop_w, self.desktop_h), flags)
            self.resize(self.desktop_w, self.desktop_h)
        else:
            w = int(self.desktop_w * 0.85)
            h = int(self.desktop_h * 0.85)
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
            self.screen = pygame.display.set_mode((w, h), flags)
            self.resize(w, h)

    def compute_cinematic_camera(self, t):
        """
        Compute choreographed cinematic camera views for the video reel:
        - 0.0s - 3.0s: Front 3/4 Low Track View (1974 -> 2024 morph & laser scan)
        - 3.0s - 7.5s: Side Aero Profile (Wind tunnel streamlines over roof & haunches)
        - 7.5s - 11.0s: Rear 3/4 Swan-Neck Wing closeup (9,000 RPM tachometer screaming)
        - 11.0s - 14.0s: DRS snaps open, dynamic top-rear speed chase at 296 KM/H
        """
        aspect = self.width / float(self.height)
        fovy = 38.0 if aspect > 1.0 else 48.0
        proj = perspective_matrix(fovy, aspect, 0.1, 50.0)

        # Camera positions based on timeline
        if t < 3.0:
            # Front 3/4 low angle, slowly drifting
            drift = t / 3.0
            eye = np.array([
                lerp(3.2, 2.6, drift),
                lerp(0.85, 1.10, drift),
                lerp(-3.8, -3.2, drift)
            ], dtype=np.float32)
            target = np.array([0.0, 0.65, -0.6], dtype=np.float32)

        elif t < 7.5:
            # Side aero profile tracking along car body
            drift = (t - 3.0) / 4.5
            eye = np.array([
                lerp(4.2, 3.8, drift),
                lerp(1.20, 1.35, drift),
                lerp(-1.2, 1.8, drift)
            ], dtype=np.float32)
            target = np.array([0.0, 0.75, lerp(-0.4, 0.8, drift)], dtype=np.float32)

        elif t < 11.0:
            # Rear 3/4 Swan-neck wing framing
            drift = (t - 7.5) / 3.5
            eye = np.array([
                lerp(-2.8, -2.4, drift),
                lerp(1.65, 1.55, drift),
                lerp(3.8, 3.2, drift)
            ], dtype=np.float32)
            target = np.array([0.0, 1.15, 1.70], dtype=np.float32)

        else:
            # High-speed blast with DRS active
            drift = (t - 11.0) / 3.0
            eye = np.array([
                lerp(1.8, 2.2, drift),
                lerp(1.80, 1.60, drift),
                lerp(3.6, 4.2, drift)
            ], dtype=np.float32)
            target = np.array([0.0, 0.90, 1.20], dtype=np.float32)

        view = look_at_matrix(eye, target)
        return proj, view, eye

    def compute_free_camera(self):
        """Compute camera matrix from user mouse orbit / pan."""
        aspect = self.width / float(self.height)
        fovy = 38.0 if aspect > 1.0 else 48.0
        proj = perspective_matrix(fovy, aspect, 0.1, 50.0)

        rad_yaw = math.radians(self.cam_yaw)
        rad_pitch = math.radians(self.cam_pitch)

        eye_x = self.cam_target[0] + self.cam_dist * math.cos(rad_pitch) * math.sin(rad_yaw)
        eye_y = self.cam_target[1] + self.cam_dist * math.sin(rad_pitch)
        eye_z = self.cam_target[2] + self.cam_dist * math.cos(rad_pitch) * math.cos(rad_yaw)
        eye = np.array([eye_x, eye_y, eye_z], dtype=np.float32)

        view = look_at_matrix(eye, self.cam_target)
        return proj, view, eye

    def run_interactive(self):
        """Main 60 FPS interactive engine loop."""
        running = True
        sim_time = 0.0

        print("\n=======================================================")
        print("  PORSCHE 911 GT3 RS (992) // WEISSACH SIMULATION")
        print("=======================================================")
        print("  Controls:")
        print("  * Left Mouse Drag : Orbit 3D camera")
        print("  * Right Mouse Drag: Pan camera target")
        print("  * Mouse Scroll    : Zoom in / out")
        print("  * Spacebar        : Pause / Resume animation")
        print("  * 'D' Key         : Toggle Active DRS Wing Flap")
        print("  * 'W' / Up Arrow  : Manual Throttle Revving (0-9000 RPM)")
        print("  * 'L' Key         : Cycle Paint Finishes (Arctic Grey, Shark Blue, Guards Red)")
        print("  * 'C' Key         : Switch Camera Angle Presets")
        print("  * 'H' Key         : Toggle Telemetry HUD")
        print("  * 'F' / 'F11'     : Toggle Fullscreen")
        print("  * 'E' Key         : Export 9:16 Vertical Video Reel")
        print("  * 'ESC' / 'Q'     : Quit")
        print("=======================================================\n")

        t_prev = time.time()

        while running:
            t_curr = time.time()
            dt = t_curr - t_prev
            t_prev = t_curr

            if not self.is_paused:
                sim_time += dt

            # Throttle decay if not held down
            self.throttle_manual = max(0.0, self.throttle_manual - dt * 1.5)

            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.resize(event.w, event.h)

                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_d:
                        self.drs_manual = not self.drs_manual
                        print(f"[*] DRS Wing Flap: {'ACTIVE (OPEN - 34°)' if self.drs_manual else 'CLOSED (860 KG DOWNFORCE)'}")
                    elif event.key in [pygame.K_f, pygame.K_F11]:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_h:
                        self.show_hud = not self.show_hud
                    elif event.key == pygame.K_l:
                        self.paint_index = (self.paint_index + 1) % len(self.paint_presets)
                        self.body_color = self.paint_presets[self.paint_index][1]
                        print(f"[*] Paint Finish: {self.paint_presets[self.paint_index][0]}")
                    elif event.key == pygame.K_c:
                        self.cam_preset = (self.cam_preset + 1) % 6
                    elif event.key == pygame.K_r:
                        sim_time = 0.0
                    elif event.key == pygame.K_e:
                        print("\n[*] Starting 9:16 Video Reel Export...")
                        self.export_video_reel()
                        t_prev = time.time()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.mouse_dragging_left = True
                        self.last_mouse_pos = event.pos
                    elif event.button == 3:
                        self.mouse_dragging_right = True
                        self.last_mouse_pos = event.pos
                    elif event.button == 4:
                        self.cam_dist = max(2.5, self.cam_dist - 0.35)
                    elif event.button == 5:
                        self.cam_dist = min(15.0, self.cam_dist + 0.35)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.mouse_dragging_left = False
                    elif event.button == 3:
                        self.mouse_dragging_right = False

                elif event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    dx = mx - self.last_mouse_pos[0]
                    dy = my - self.last_mouse_pos[1]
                    self.last_mouse_pos = event.pos

                    if self.mouse_dragging_left:
                        self.cam_preset = 5 # Switch to free orbit
                        self.cam_yaw += dx * 0.35
                        self.cam_pitch = max(-20.0, min(80.0, self.cam_pitch - dy * 0.35))
                    elif self.mouse_dragging_right:
                        self.cam_preset = 5
                        self.cam_target[0] -= dx * 0.005
                        self.cam_target[1] += dy * 0.005

            # Handle continuous throttle rev key
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.throttle_manual = min(1.0, self.throttle_manual + dt * 2.5)

            # Render Frame
            t_mod = sim_time % self.total_duration
            self.render_scene(t_mod)
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def render_scene(self, t):
        """Render all scene layers (studio bg, car body, active DRS, CFD streamlines, HUD)."""
        self.ctx.clear(0.01, 0.01, 0.02, 1.0)

        # 1. Background Studio
        self.ctx.disable(moderngl.DEPTH_TEST)
        if 'u_time' in self.bg_prog:
            self.bg_prog['u_time'].value = float(t)
        if 'u_resolution' in self.bg_prog:
            self.bg_prog['u_resolution'].value = (float(self.width), float(self.height))
        self.bg_vao.render(moderngl.TRIANGLES)
        self.ctx.enable(moderngl.DEPTH_TEST)

        # 2. Camera Matrices
        if self.cam_preset == 0:
            proj, view, cam_pos = self.compute_cinematic_camera(t)
        elif self.cam_preset == 1: # Front 3/4
            proj = perspective_matrix(38.0, self.width / float(self.height), 0.1, 50.0)
            eye = np.array([2.8, 1.0, -3.4], dtype=np.float32)
            view = look_at_matrix(eye, np.array([0.0, 0.65, -0.6], dtype=np.float32))
            cam_pos = eye
        elif self.cam_preset == 2: # Side Aero
            proj = perspective_matrix(38.0, self.width / float(self.height), 0.1, 50.0)
            eye = np.array([4.2, 1.25, 0.2], dtype=np.float32)
            view = look_at_matrix(eye, np.array([0.0, 0.70, 0.0], dtype=np.float32))
            cam_pos = eye
        elif self.cam_preset == 3: # Top CFD
            proj = perspective_matrix(42.0, self.width / float(self.height), 0.1, 50.0)
            eye = np.array([0.0, 5.2, 0.1], dtype=np.float32)
            view = look_at_matrix(eye, np.array([0.0, 0.6, 0.0], dtype=np.float32), up=np.array([0.0, 0.0, -1.0], dtype=np.float32))
            cam_pos = eye
        elif self.cam_preset == 4: # Rear Wing
            proj = perspective_matrix(38.0, self.width / float(self.height), 0.1, 50.0)
            eye = np.array([-2.2, 1.65, 3.2], dtype=np.float32)
            view = look_at_matrix(eye, np.array([0.0, 1.15, 1.70], dtype=np.float32))
            cam_pos = eye
        else: # Free Orbit
            proj, view, cam_pos = self.compute_free_camera()

        model = identity_matrix()

        # Telemetry variables
        # Morphing: 0.0s to 3.0s morphs from 0.0 (1974 930) to 1.0 (992 GT3 RS)
        morph_val = smoothstep(0.4, 2.8, t)
        # Laser scan progress: 0.0s to 3.0s sweeps from 0.0 to 1.0
        scan_progress = t / 3.0 if t < 3.0 else 0.0
        # Active DRS: opens during 11.0s - 14.0s or if manually triggered
        drs_active = self.drs_manual or (t >= 11.0)
        drs_pct = 1.0 if drs_active else 0.0
        drs_angle = -0.59 * drs_pct # 34 degrees in radians

        # Throttle / RPM
        throttle_val = max(self.throttle_manual, smoothstep(7.5, 11.0, t) if t < 11.0 else 0.85)

        # 3. Render Main Car Body
        set_uniform(self.car_prog, 'm_proj', proj.T.tobytes())
        set_uniform(self.car_prog, 'm_view', view.T.tobytes())
        set_uniform(self.car_prog, 'm_model', model.T.tobytes())
        set_uniform(self.car_prog, 'u_cam_pos', tuple(cam_pos))
        set_uniform(self.car_prog, 'u_body_color', tuple(self.body_color))
        set_uniform(self.car_prog, 'u_time', float(t))
        set_uniform(self.car_prog, 'u_throttle', float(throttle_val))
        set_uniform(self.car_prog, 'u_morph', float(morph_val))
        set_uniform(self.car_prog, 'u_wire_mode', self.wire_mode)
        set_uniform(self.car_prog, 'u_scan_progress', float(scan_progress))

        self.car_vao.render(moderngl.TRIANGLES, vertices=self.car_vert_count)

        # 4. Render Active DRS Upper Wing Flap
        set_uniform(self.drs_prog, 'm_proj', proj.T.tobytes())
        set_uniform(self.drs_prog, 'm_view', view.T.tobytes())
        set_uniform(self.drs_prog, 'm_model', model.T.tobytes())
        set_uniform(self.drs_prog, 'u_cam_pos', tuple(cam_pos))
        set_uniform(self.drs_prog, 'u_body_color', tuple(self.body_color))
        set_uniform(self.drs_prog, 'u_time', float(t))
        set_uniform(self.drs_prog, 'u_throttle', float(throttle_val))
        set_uniform(self.drs_prog, 'u_wire_mode', self.wire_mode)
        set_uniform(self.drs_prog, 'u_scan_progress', float(scan_progress))
        set_uniform(self.drs_prog, 'u_drs_angle', float(drs_angle))
        set_uniform(self.drs_prog, 'u_morph', float(morph_val))

        self.drs_vao.render(moderngl.TRIANGLES, vertices=self.drs_vert_count)

        # 5. Render Wind Tunnel CFD Streamlines (t > 2.5s)
        if t > 2.5:
            stream_data = porsche_geometry.compute_streamline_geometry(self.streamlines, t, drs_pct)
            if len(stream_data) > 0:
                s_vbo = self.ctx.buffer(stream_data.tobytes())
                s_vao = self.ctx.vertex_array(
                    self.stream_prog,
                    [(s_vbo, '3f 3f 1f', 'in_position', 'in_color', 'in_alpha')]
                )
                set_uniform(self.stream_prog, 'm_proj', proj.T.tobytes())
                set_uniform(self.stream_prog, 'm_view', view.T.tobytes())
                set_uniform(self.stream_prog, 'm_model', model.T.tobytes())

                self.ctx.disable(moderngl.DEPTH_TEST)
                s_vao.render(moderngl.TRIANGLES)
                self.ctx.enable(moderngl.DEPTH_TEST)

                s_vao.release()
                s_vbo.release()

        # 6. Render 2D Cockpit Telemetry HUD
        if self.show_hud:
            hud_img = self.hud.generate_hud_image(
                t, self.total_duration,
                throttle_pct=throttle_val,
                drs_active=drs_active,
                morph_pct=morph_val
            )
            raw_data = hud_img.tobytes()
            self.hud_texture.write(raw_data)
            self.hud_texture.use(0)

            self.ctx.disable(moderngl.DEPTH_TEST)
            self.hud_prog['u_texture'].value = 0
            self.hud_vao.render(moderngl.TRIANGLES)
            self.ctx.enable(moderngl.DEPTH_TEST)

    def export_video_reel(self, width=720, height=1280, output_path=None, fps=30):
        """
        Headless export of the 14-second 9:16 vertical video reel for Instagram.
        """
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), "gt3rs_reel.mp4")

        total_frames = int(self.total_duration * fps)
        print(f"\n=======================================================")
        print(f"[*] Exporting 9:16 Vertical Video Reel ({width}x{height})")
        print(f"[*] Frames: {total_frames} | Duration: {self.total_duration}s | FPS: {fps}")
        print(f"[*] Output Path: {output_path}")
        print(f"=======================================================\n")

        # Create headless OpenGL context
        export_ctx = moderngl.create_context(standalone=True)
        export_ctx.enable(moderngl.DEPTH_TEST)
        export_ctx.enable(moderngl.BLEND)
        export_ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        export_fbo = export_ctx.simple_framebuffer((width, height))
        export_fbo.use()

        # Shaders for export
        car_prog = export_ctx.program(vertex_shader=shaders.CAR_VERT_SRC, fragment_shader=shaders.CAR_FRAG_SRC)
        drs_prog = export_ctx.program(vertex_shader=shaders.DRS_VERT_SRC, fragment_shader=shaders.CAR_FRAG_SRC)
        stream_prog = export_ctx.program(vertex_shader=shaders.STREAMLINE_VERT_SRC, fragment_shader=shaders.STREAMLINE_FRAG_SRC)
        bg_prog = export_ctx.program(vertex_shader=shaders.BG_VERT_SRC, fragment_shader=shaders.BG_FRAG_SRC)

        # Background quad
        bg_quad = np.array([-1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0], dtype=np.float32)
        bg_vbo = export_ctx.buffer(bg_quad.tobytes())
        bg_vao = export_ctx.vertex_array(bg_prog, [(bg_vbo, '2f', 'in_pos')])

        # Geometry buffers
        body_verts = porsche_geometry.generate_porsche_body()
        floor_verts = porsche_geometry.generate_studio_floor()
        wing_static_verts, drs_flap_verts = porsche_geometry.generate_swan_neck_rear_wing()

        wheel_verts = []
        wheel_verts.extend(porsche_geometry.generate_wheel_assembly([ 0.88, 0.34, -1.22], 0.34, 0.26, is_front=True))
        wheel_verts.extend(porsche_geometry.generate_wheel_assembly([-0.88, 0.34, -1.22], 0.34, 0.26, is_front=True))
        wheel_verts.extend(porsche_geometry.generate_wheel_assembly([ 0.94, 0.35,  1.23], 0.35, 0.32, is_front=False))
        wheel_verts.extend(porsche_geometry.generate_wheel_assembly([-0.94, 0.35,  1.23], 0.35, 0.32, is_front=False))

        all_static = []
        all_static.extend(floor_verts)
        all_static.extend(body_verts)
        all_static.extend(wheel_verts)
        all_static.extend(wing_static_verts)

        s_data = np.array(all_static, dtype=np.float32)
        car_vbo = export_ctx.buffer(s_data.tobytes())
        car_vao = export_ctx.vertex_array(
            car_prog,
            [(car_vbo, '3f 3f 3f 2f 3f 3f',
              'in_position', 'in_normal', 'in_color', 'in_uv', 'in_mat', 'in_morph_pos')]
        )
        car_vert_count = len(all_static) // 17

        drs_data = np.array(drs_flap_verts, dtype=np.float32)
        drs_vbo = export_ctx.buffer(drs_data.tobytes())
        drs_vao = export_ctx.vertex_array(
            drs_prog,
            [(drs_vbo, '3f 3f 3f 2f 3f 3f',
              'in_position', 'in_normal', 'in_color', 'in_uv', 'in_mat', 'in_morph_pos')]
        )
        drs_vert_count = len(drs_flap_verts) // 17

        streamlines = porsche_geometry.generate_cfd_streamlines(num_lines=1600)
        hud = PorscheHUD(width, height)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        t_start = time.time()

        for frame_idx in range(total_frames):
            t = frame_idx / float(fps)

            export_fbo.use()
            export_ctx.clear(0.01, 0.01, 0.02, 1.0)

            # 1. Studio BG
            export_ctx.disable(moderngl.DEPTH_TEST)
            if 'u_time' in bg_prog:
                bg_prog['u_time'].value = float(t)
            if 'u_resolution' in bg_prog:
                bg_prog['u_resolution'].value = (float(width), float(height))
            bg_vao.render(moderngl.TRIANGLES)
            export_ctx.enable(moderngl.DEPTH_TEST)

            # 2. Camera Projection & View (Vertical 9:16)
            aspect = width / float(height)
            fovy = 50.0 # Slightly wider FOV for vertical frame
            proj = perspective_matrix(fovy, aspect, 0.1, 50.0)

            # Choreographed Camera Path (Framed for 9:16 vertical reels)
            if t < 3.0: # Front 3/4 low angle & morph
                drift = t / 3.0
                eye = np.array([lerp(3.8, 3.2, drift), lerp(1.10, 1.30, drift), lerp(-4.6, -4.0, drift)], dtype=np.float32)
                target = np.array([0.0, 0.65, -0.4], dtype=np.float32)
            elif t < 7.5: # Side profile wind tunnel CFD flow
                drift = (t - 3.0) / 4.5
                eye = np.array([lerp(5.2, 4.6, drift), lerp(1.50, 1.65, drift), lerp(-1.4, 2.0, drift)], dtype=np.float32)
                target = np.array([0.0, 0.75, lerp(-0.3, 0.8, drift)], dtype=np.float32)
            elif t < 11.0: # Rear 3/4 swan neck wing
                drift = (t - 7.5) / 3.5
                eye = np.array([lerp(-3.6, -3.0, drift), lerp(2.10, 1.90, drift), lerp(4.8, 4.2, drift)], dtype=np.float32)
                target = np.array([0.0, 1.05, 1.50], dtype=np.float32)
            else: # DRS blast & peak downforce
                drift = (t - 11.0) / 3.0
                eye = np.array([lerp(2.8, 3.4, drift), lerp(2.30, 2.10, drift), lerp(4.8, 5.4, drift)], dtype=np.float32)
                target = np.array([0.0, 0.90, 1.00], dtype=np.float32)

            view = look_at_matrix(eye, target)
            model = identity_matrix()

            morph_val = smoothstep(0.4, 2.8, t)
            scan_progress = t / 3.0 if t < 3.0 else 0.0
            drs_active = (t >= 11.0)
            drs_pct = 1.0 if drs_active else 0.0
            drs_angle = -0.59 * drs_pct
            throttle_val = smoothstep(7.5, 11.0, t) if t < 11.0 else 0.85

            # 3. Main Car Body
            set_uniform(car_prog, 'm_proj', proj.T.tobytes())
            set_uniform(car_prog, 'm_view', view.T.tobytes())
            set_uniform(car_prog, 'm_model', model.T.tobytes())
            set_uniform(car_prog, 'u_cam_pos', tuple(eye))
            set_uniform(car_prog, 'u_body_color', tuple(self.body_color))
            set_uniform(car_prog, 'u_time', float(t))
            set_uniform(car_prog, 'u_throttle', float(throttle_val))
            set_uniform(car_prog, 'u_morph', float(morph_val))
            set_uniform(car_prog, 'u_wire_mode', 0)
            set_uniform(car_prog, 'u_scan_progress', float(scan_progress))

            car_vao.render(moderngl.TRIANGLES, vertices=car_vert_count)

            # 4. DRS Upper Flap
            set_uniform(drs_prog, 'm_proj', proj.T.tobytes())
            set_uniform(drs_prog, 'm_view', view.T.tobytes())
            set_uniform(drs_prog, 'm_model', model.T.tobytes())
            set_uniform(drs_prog, 'u_cam_pos', tuple(eye))
            set_uniform(drs_prog, 'u_body_color', tuple(self.body_color))
            set_uniform(drs_prog, 'u_time', float(t))
            set_uniform(drs_prog, 'u_throttle', float(throttle_val))
            set_uniform(drs_prog, 'u_wire_mode', 0)
            set_uniform(drs_prog, 'u_scan_progress', float(scan_progress))
            set_uniform(drs_prog, 'u_drs_angle', float(drs_angle))
            set_uniform(drs_prog, 'u_morph', float(morph_val))

            drs_vao.render(moderngl.TRIANGLES, vertices=drs_vert_count)

            # 5. CFD Streamlines
            if t > 2.5:
                stream_data = porsche_geometry.compute_streamline_geometry(streamlines, t, drs_pct)
                if len(stream_data) > 0:
                    s_vbo = export_ctx.buffer(stream_data.tobytes())
                    s_vao = export_ctx.vertex_array(
                        stream_prog,
                        [(s_vbo, '3f 3f 1f', 'in_position', 'in_color', 'in_alpha')]
                    )
                    set_uniform(stream_prog, 'm_proj', proj.T.tobytes())
                    set_uniform(stream_prog, 'm_view', view.T.tobytes())
                    set_uniform(stream_prog, 'm_model', model.T.tobytes())

                    export_ctx.disable(moderngl.DEPTH_TEST)
                    s_vao.render(moderngl.TRIANGLES)
                    export_ctx.enable(moderngl.DEPTH_TEST)

                    s_vao.release()
                    s_vbo.release()

            # Read frame bytes from FBO
            raw_bytes = export_fbo.read(components=3)
            frame_np = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, width, 3))
            frame_np = np.flipud(frame_np)
            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)

            # Composite Telemetry HUD
            frame_with_hud = hud.draw_on_opencv_frame(
                frame_bgr, t, self.total_duration,
                throttle_pct=throttle_val,
                drs_active=drs_active,
                morph_pct=morph_val
            )
            writer.write(frame_with_hud)

            if (frame_idx + 1) % 15 == 0 or frame_idx == total_frames - 1:
                elapsed = time.time() - t_start
                rate = (frame_idx + 1) / max(0.001, elapsed)
                remaining = (total_frames - (frame_idx + 1)) / max(0.001, rate)
                pct = ((frame_idx + 1) / total_frames) * 100.0
                print(f"  Rendering: [{frame_idx+1:03d}/{total_frames:03d}] {pct:5.1f}% | Speed: {rate:4.1f} fps | ETA: {remaining:4.1f}s", end='\r')

        writer.release()
        car_vao.release()
        car_vbo.release()
        drs_vao.release()
        drs_vbo.release()
        bg_vao.release()
        bg_vbo.release()
        export_fbo.release()

        print(f"\n[+] Export Complete in {time.time() - t_start:.1f}s!")
        print(f"[+] Reel Video saved successfully at:\n    {output_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Porsche 911 GT3 RS (992) Simulation")
    parser.add_argument("--export", action="store_true", help="Render and export 14s MP4 video reel")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode instead of fullscreen")
    parser.add_argument("--res", type=str, default="720x1280", help="Resolution for export, e.g. 720x1280 or 1080x1920")
    args = parser.parse_args()

    if args.export:
        try:
            w, h = map(int, args.res.split('x'))
        except Exception:
            w, h = 720, 1280
        renderer = PorscheGT3RSRenderer(width=w, height=h, fullscreen=False, is_headless=True)
        renderer.export_video_reel(width=w, height=h)
    else:
        fullscreen = not args.windowed
        renderer = PorscheGT3RSRenderer(fullscreen=fullscreen, is_headless=False)
        renderer.run_interactive()


if __name__ == "__main__":
    main()
