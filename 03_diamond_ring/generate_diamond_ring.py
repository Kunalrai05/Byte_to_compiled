"""
3D Diamond Engagement Ring Simulation & Generation Engine.
Episode 03 of Byte to Compiled.

Features:
1. Full Laptop Screen Display (1536x864, 60 FPS, Borderless Fullscreen default).
2. Phase 1 (0.0s - 4.0s): Bottom-to-Top Materialization (band -> 4 prongs -> brilliant diamond).
3. Phase 2 (4.0s - 5.5s): Concentric Hollow Halo Shockwave Burst expanding from center to all edges.
4. Phase 3 (5.5s+): Graceful 3D Rotation with diamond refraction & facet glints.
5. Headless 9:16 MP4 video exporter for Instagram Reels & YouTube Shorts.
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
import ring_geometry
import shaders


def set_uniform(prog, name, val):
    """Safely set a ModernGL uniform value."""
    if name in prog:
        if isinstance(val, (bytes, bytearray, memoryview)):
            prog[name].write(val)
        else:
            prog[name].value = val


class DiamondRingEngine:
    def __init__(self, width=1536, height=864, fullscreen=True, is_headless=False):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.is_headless = is_headless
        self.total_duration = 14.0

        # Animation Timing:
        # 0.0s to 4.0s: Bottom-to-top growth
        # 4.0s to 5.5s: Concentric hollow halo shockwave burst
        # 5.5s+: 3D continuous rotation
        self.growth_duration = 4.0
        self.shockwave_start = 4.0
        self.shockwave_duration = 1.5
        self.rotation_start = 5.2

        # State
        self.is_paused = False
        self.sim_time = 0.0

        # Interactive Camera
        self.cam_yaw = 0.0
        self.cam_pitch = 14.0
        self.cam_dist = 4.6
        self.cam_target = np.array([0.0, 0.25, 0.0], dtype=np.float32)
        self.mouse_dragging_left = False
        self.mouse_dragging_right = False
        self.last_mouse_pos = (0, 0)

        if not self.is_headless:
            self._init_window()
            self._init_gl()
            self._init_geometry()

    def _init_window(self):
        """Initialize Pygame display with OpenGL context."""
        pygame.init()
        pygame.display.set_caption("Episode 03: Diamond Engagement Ring // Materialization & Concentric Halo")

        display_info = pygame.display.Info()
        self.desktop_w = display_info.current_w
        self.desktop_h = display_info.current_h

        if self.fullscreen:
            self.width = self.desktop_w
            self.height = self.desktop_h
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN
        else:
            self.width = min(1536, int(self.desktop_w * 0.90))
            self.height = min(864, int(self.desktop_h * 0.88))
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE

        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        self.clock = pygame.time.Clock()

    def _init_gl(self):
        """Initialize ModernGL context and shader programs."""
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        # 1. Ring PBR Shader
        self.ring_prog = self.ctx.program(
            vertex_shader=shaders.RING_VERT_SRC,
            fragment_shader=shaders.RING_FRAG_SRC
        )

        # 2. Concentric Hollow Halo Shockwave Shader
        self.shock_prog = self.ctx.program(
            vertex_shader=shaders.SHOCKWAVE_VERT_SRC,
            fragment_shader=shaders.SHOCKWAVE_FRAG_SRC
        )

        # 3. Studio Background Shader
        self.bg_prog = self.ctx.program(
            vertex_shader=shaders.BG_VERT_SRC,
            fragment_shader=shaders.BG_FRAG_SRC
        )

        # Setup Fullscreen Quads
        quad_verts = np.array([
            -1.0, -1.0,
             1.0, -1.0,
             1.0,  1.0,
            -1.0, -1.0,
             1.0,  1.0,
            -1.0,  1.0
        ], dtype=np.float32)

        self.quad_vbo = self.ctx.buffer(quad_verts.tobytes())
        self.bg_vao = self.ctx.vertex_array(self.bg_prog, [(self.quad_vbo, '2f', 'in_pos')])
        self.shock_vao = self.ctx.vertex_array(self.shock_prog, [(self.quad_vbo, '2f', 'in_pos')])

    def _init_geometry(self):
        """Compile procedural 3D meshes (band, prongs, diamond, floor)."""
        all_verts = []
        all_verts.extend(ring_geometry.generate_studio_floor(radius=4.5))
        all_verts.extend(ring_geometry.generate_ring_band(u_segs=100, v_segs=32))
        all_verts.extend(ring_geometry.generate_prongs(num_steps=24, radial_segs=12))
        all_verts.extend(ring_geometry.generate_diamond_gem(num_facets=24))

        v_data = np.array(all_verts, dtype=np.float32)
        self.ring_vbo = self.ctx.buffer(v_data.tobytes())
        self.ring_vao = self.ctx.vertex_array(
            self.ring_prog,
            [(self.ring_vbo, '3f 3f 3f 2f 1f 3f',
              'in_position', 'in_normal', 'in_color', 'in_uv', 'in_growth', 'in_mat')]
        )
        self.ring_vert_count = len(all_verts) // 15

    def resize(self, new_w, new_h):
        """Handle screen resize and update viewport."""
        self.width = max(100, new_w)
        self.height = max(100, new_h)
        self.ctx.viewport = (0, 0, self.width, self.height)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode smoothly."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN
            self.screen = pygame.display.set_mode((self.desktop_w, self.desktop_h), flags)
            self.resize(self.desktop_w, self.desktop_h)
        else:
            w = min(1536, int(self.desktop_w * 0.90))
            h = min(864, int(self.desktop_h * 0.88))
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
            self.screen = pygame.display.set_mode((w, h), flags)
            self.resize(w, h)

    def render_scene(self, t, width=None, height=None, is_export=False):
        """
        Render complete 3D scene:
        1. Studio dark background.
        2. Progressively materializing 3D ring & diamond (bottom-to-top).
        3. Concentric hollow halo shockwave burst expanding to all screen edges.
        4. Graceful 3D rotation once completed.
        """
        w = width if width is not None else self.width
        h = height if height is not None else self.height

        self.ctx.clear(0.01, 0.01, 0.02, 1.0)

        # 1. Background Studio
        self.ctx.disable(moderngl.DEPTH_TEST)
        set_uniform(self.bg_prog, 'u_time', float(t))
        set_uniform(self.bg_prog, 'u_resolution', (float(w), float(h)))
        self.bg_vao.render(moderngl.TRIANGLES)
        self.ctx.enable(moderngl.DEPTH_TEST)

        # 2. Camera Matrices
        aspect = w / float(h)
        fovy = 38.0 if aspect > 1.0 else 52.0 # Wider FOV for vertical phone orientation
        proj = perspective_matrix(fovy, aspect, 0.1, 50.0)

        # Orbit camera calculation:
        # Before 5.2s, facing forward with slight tilt.
        # After 5.2s, starts rotating continuously around vertical Y axis!
        auto_yaw = 0.0
        if t > self.rotation_start:
            dt_rot = t - self.rotation_start
            auto_yaw = dt_rot * 0.70 # Smooth rotation speed

        total_yaw = auto_yaw + math.radians(self.cam_yaw)
        pitch_rad = math.radians(self.cam_pitch)

        eye_x = self.cam_target[0] + self.cam_dist * math.cos(pitch_rad) * math.sin(total_yaw)
        eye_y = self.cam_target[1] + self.cam_dist * math.sin(pitch_rad)
        eye_z = self.cam_target[2] + self.cam_dist * math.cos(pitch_rad) * math.cos(total_yaw)
        eye = np.array([eye_x, eye_y, eye_z], dtype=np.float32)

        view = look_at_matrix(eye, self.cam_target)
        model = identity_matrix()

        # 3. Growth & Completion Metrics
        # Growth: 0.0s to 4.0s materializes from 0.0 to 1.0 (bottom to top)
        if t <= self.growth_duration:
            growth_pct = smoothstep(0.1, self.growth_duration, t)
        else:
            growth_pct = 1.0

        # Completion Flash: bursts at 4.0s and fades by 4.8s
        if 4.0 <= t <= 4.8:
            flash_intensity = math.exp(-(t - 4.0) * 5.0)
        else:
            flash_intensity = 0.0

        # Render 3D Ring Mesh
        set_uniform(self.ring_prog, 'm_proj', proj.T.tobytes())
        set_uniform(self.ring_prog, 'm_view', view.T.tobytes())
        set_uniform(self.ring_prog, 'm_model', model.T.tobytes())
        set_uniform(self.ring_prog, 'u_cam_pos', tuple(eye))
        set_uniform(self.ring_prog, 'u_growth', float(growth_pct))
        set_uniform(self.ring_prog, 'u_time', float(t))
        set_uniform(self.ring_prog, 'u_flash', float(flash_intensity))

        self.ring_vao.render(moderngl.TRIANGLES, vertices=self.ring_vert_count)

        # 4. CONCENTRIC HOLLOW HALO SHOCKWAVE BURST (t in [4.0s, 5.5s])
        # Expands outward from the ring center all the way to the edges of the screen!
        if self.shockwave_start <= t <= (self.shockwave_start + self.shockwave_duration):
            dt_shock = t - self.shockwave_start
            shock_pct = dt_shock / self.shockwave_duration

            # Expands rapidly from 0.0 to 2.4 across screen
            shock_radius = (shock_pct ** 0.82) * 2.2
            # Fades out smoothly as it reaches the boundaries
            shock_alpha = (1.0 - shock_pct) ** 1.5

            self.ctx.disable(moderngl.DEPTH_TEST)
            set_uniform(self.shock_prog, 'u_center', (0.5, 0.52)) # Center of diamond ring
            set_uniform(self.shock_prog, 'u_aspect', float(aspect))
            set_uniform(self.shock_prog, 'u_shock_radius', float(shock_radius))
            set_uniform(self.shock_prog, 'u_shock_alpha', float(shock_alpha))
            set_uniform(self.shock_prog, 'u_time', float(t))

            self.shock_vao.render(moderngl.TRIANGLES)
            self.ctx.enable(moderngl.DEPTH_TEST)

    def run_interactive(self):
        """Main 60 FPS interactive loop (Full Laptop Screen)."""
        running = True
        print("\n=======================================================")
        print("  EPISODE 03: 3D DIAMOND RING // MATERIALIZATION & HALO")
        print("=======================================================")
        print("  Full Laptop Screen Display (1536x864 60 FPS)")
        print("  * Spacebar    : Pause / Resume animation")
        print("  * 'R' Key     : Replay from 0.0s (watch generation & halo)")
        print("  * Mouse Drag  : Free 3D camera orbit")
        print("  * Mouse Scroll: Zoom in / out")
        print("  * 'F' / 'F11' : Toggle Fullscreen / Windowed")
        print("  * 'E' Key     : Export direct 9:16 vertical MP4 video reel")
        print("  * 'ESC' / 'Q' : Quit")
        print("=======================================================\n")

        t_prev = time.time()

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
                    self.resize(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_r:
                        self.sim_time = 0.0
                        print("[*] Replaying Diamond Ring Generation...")
                    elif event.key in [pygame.K_f, pygame.K_F11]:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_e:
                        print("\n[*] Starting Direct 9:16 MP4 Video Reel Export...")
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
                        self.cam_dist = max(2.0, self.cam_dist - 0.25)
                    elif event.button == 5:
                        self.cam_dist = min(12.0, self.cam_dist + 0.25)

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
                        self.cam_yaw += dx * 0.40
                        self.cam_pitch = max(-40.0, min(80.0, self.cam_pitch - dy * 0.40))
                    elif self.mouse_dragging_right:
                        self.cam_target[0] -= dx * 0.005
                        self.cam_target[1] += dy * 0.005

            self.render_scene(self.sim_time)
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def export_video_reel(self, width=720, height=1280, output_path=None, fps=30):
        """
        Headless export of the 14-second 9:16 vertical video reel for Instagram and YouTube.
        """
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), "diamond_ring_reel.mp4")

        total_frames = int(self.total_duration * fps)
        print(f"\n=======================================================")
        print(f"[*] Exporting 9:16 Vertical Video Reel ({width}x{height})")
        print(f"[*] Frames: {total_frames} | Duration: {self.total_duration}s | FPS: {fps}")
        print(f"[*] Output: {output_path}")
        print(f"=======================================================\n")

        # Headless ModernGL context
        export_ctx = moderngl.create_context(standalone=True)
        export_ctx.enable(moderngl.DEPTH_TEST)
        export_ctx.enable(moderngl.BLEND)
        export_ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        export_fbo = export_ctx.simple_framebuffer((width, height))
        export_fbo.use()

        ring_prog = export_ctx.program(vertex_shader=shaders.RING_VERT_SRC, fragment_shader=shaders.RING_FRAG_SRC)
        shock_prog = export_ctx.program(vertex_shader=shaders.SHOCKWAVE_VERT_SRC, fragment_shader=shaders.SHOCKWAVE_FRAG_SRC)
        bg_prog = export_ctx.program(vertex_shader=shaders.BG_VERT_SRC, fragment_shader=shaders.BG_FRAG_SRC)

        quad_verts = np.array([-1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0], dtype=np.float32)
        quad_vbo = export_ctx.buffer(quad_verts.tobytes())
        bg_vao = export_ctx.vertex_array(bg_prog, [(quad_vbo, '2f', 'in_pos')])
        shock_vao = export_ctx.vertex_array(shock_prog, [(quad_vbo, '2f', 'in_pos')])

        all_verts = []
        all_verts.extend(ring_geometry.generate_studio_floor(radius=4.5))
        all_verts.extend(ring_geometry.generate_ring_band(u_segs=100, v_segs=32))
        all_verts.extend(ring_geometry.generate_prongs(num_steps=24, radial_segs=12))
        all_verts.extend(ring_geometry.generate_diamond_gem(num_facets=24))

        v_data = np.array(all_verts, dtype=np.float32)
        ring_vbo = export_ctx.buffer(v_data.tobytes())
        ring_vao = export_ctx.vertex_array(
            ring_prog,
            [(ring_vbo, '3f 3f 3f 2f 1f 3f', 'in_position', 'in_normal', 'in_color', 'in_uv', 'in_growth', 'in_mat')]
        )
        vert_count = len(all_verts) // 15

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        t_start = time.time()
        aspect = width / float(height)
        proj = perspective_matrix(52.0, aspect, 0.1, 50.0)

        for frame_idx in range(total_frames):
            t = (frame_idx / float(fps))

            export_fbo.use()
            export_ctx.clear(0.01, 0.01, 0.02, 1.0)

            # 1. Background
            export_ctx.disable(moderngl.DEPTH_TEST)
            set_uniform(bg_prog, 'u_time', float(t))
            set_uniform(bg_prog, 'u_resolution', (float(width), float(height)))
            bg_vao.render(moderngl.TRIANGLES)
            export_ctx.enable(moderngl.DEPTH_TEST)

            # 2. Camera View & Rotation
            auto_yaw = 0.0
            if t > self.rotation_start:
                auto_yaw = (t - self.rotation_start) * 0.70

            pitch_rad = math.radians(14.0)
            eye_x = self.cam_dist * math.cos(pitch_rad) * math.sin(auto_yaw)
            eye_y = 0.25 + self.cam_dist * math.sin(pitch_rad)
            eye_z = self.cam_dist * math.cos(pitch_rad) * math.cos(auto_yaw)
            eye = np.array([eye_x, eye_y, eye_z], dtype=np.float32)

            view = look_at_matrix(eye, self.cam_target)
            model = identity_matrix()

            growth_pct = smoothstep(0.1, self.growth_duration, t) if t <= self.growth_duration else 1.0
            flash_intensity = math.exp(-(t - 4.0) * 5.0) if 4.0 <= t <= 4.8 else 0.0

            # 3. Render Ring Mesh
            set_uniform(ring_prog, 'm_proj', proj.T.tobytes())
            set_uniform(ring_prog, 'm_view', view.T.tobytes())
            set_uniform(ring_prog, 'm_model', model.T.tobytes())
            set_uniform(ring_prog, 'u_cam_pos', tuple(eye))
            set_uniform(ring_prog, 'u_growth', float(growth_pct))
            set_uniform(ring_prog, 'u_time', float(t))
            set_uniform(ring_prog, 'u_flash', float(flash_intensity))

            ring_vao.render(moderngl.TRIANGLES, vertices=vert_count)

            # 4. Concentric Halo Shockwave Burst
            if self.shockwave_start <= t <= (self.shockwave_start + self.shockwave_duration):
                dt_shock = t - self.shockwave_start
                shock_pct = dt_shock / self.shockwave_duration
                shock_radius = (shock_pct ** 0.82) * 2.2
                shock_alpha = (1.0 - shock_pct) ** 1.5

                export_ctx.disable(moderngl.DEPTH_TEST)
                set_uniform(shock_prog, 'u_center', (0.5, 0.52))
                set_uniform(shock_prog, 'u_aspect', float(aspect))
                set_uniform(shock_prog, 'u_shock_radius', float(shock_radius))
                set_uniform(shock_prog, 'u_shock_alpha', float(shock_alpha))
                set_uniform(shock_prog, 'u_time', float(t))

                shock_vao.render(moderngl.TRIANGLES)
                export_ctx.enable(moderngl.DEPTH_TEST)

            # Read back frame
            raw_bytes = export_fbo.read(components=3)
            frame_np = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, width, 3))
            frame_np = np.flipud(frame_np)
            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)

            writer.write(frame_bgr)

            if (frame_idx + 1) % 15 == 0 or frame_idx == total_frames - 1:
                elapsed = time.time() - t_start
                rate = (frame_idx + 1) / max(0.001, elapsed)
                remaining = (total_frames - (frame_idx + 1)) / max(0.001, rate)
                pct = ((frame_idx + 1) / total_frames) * 100.0
                print(f"  Rendering: [{frame_idx+1:03d}/{total_frames:03d}] {pct:5.1f}% | Speed: {rate:4.1f} fps | ETA: {remaining:4.1f}s", end='\r')

        writer.release()
        ring_vao.release()
        ring_vbo.release()
        shock_vao.release()
        bg_vao.release()
        quad_vbo.release()
        export_fbo.release()

        print(f"\n[+] Export Complete in {time.time() - t_start:.1f}s!")
        print(f"[+] Video Reel saved successfully at:\n    {output_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Episode 03: 3D Diamond Ring Generation & Halo Burst")
    parser.add_argument("--export", action="store_true", help="Render and export 14s MP4 video reel")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode instead of fullscreen")
    parser.add_argument("--res", type=str, default="720x1280", help="Resolution for export, e.g. 720x1280 or 1080x1920")
    args = parser.parse_args()

    if args.export:
        try:
            w, h = map(int, args.res.split('x'))
        except Exception:
            w, h = 720, 1280
        engine = DiamondRingEngine(width=w, height=h, fullscreen=False, is_headless=True)
        engine.export_video_reel(width=w, height=h)
    else:
        fullscreen = not args.windowed
        engine = DiamondRingEngine(fullscreen=fullscreen, is_headless=False)
        engine.run_interactive()


if __name__ == "__main__":
    main()
