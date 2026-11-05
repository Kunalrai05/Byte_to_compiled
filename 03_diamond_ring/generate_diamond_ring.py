"""
Monochrome Coded & Binary 3D Diamond Engagement Ring Simulation.
Episode 03 of Byte to Compiled.

Features:
1. Full Laptop Screen Display (1536x864, 60 FPS, Borderless Fullscreen default).
2. Pure Monochrome Black & White Aesthetic (#000000 backdrop, brilliant #FFFFFF coded typography).
3. Ring structure rendered in pixelated binary digits ('0', '1') and programming keywords ('def', 'vec', 'gem', 'void', '{}', '<>').
4. Phase 1 (0.0s - 4.0s): Bottom-to-Top Materialization with rapid machine code binary flicker at the frontier.
5. Phase 2 (4.0s - 5.5s): Concentric Hollow Halo Shockwave Burst sweeping from center to all screen edges.
6. Phase 3 (5.2s+): Graceful 3D continuous rotation with diamond facet specular glints traveling across characters.
7. Interactive mode toggles (M key: Coded Words / Binary / ASCII; 1/2/3 keys: Cell Size).
8. Headless 9:16 MP4 video exporter for Instagram Reels & YouTube Shorts.
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
    smoothstep, lerp
)
import ring_geometry
import shaders
import font_atlas


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

        # Animation Timeline:
        # 0.0s to 4.0s: Bottom-to-top materialization
        # 4.0s to 5.5s: Concentric hollow halo shockwave burst
        # 5.2s+: 3D continuous rotation
        self.growth_duration = 4.0
        self.shockwave_start = 4.0
        self.shockwave_duration = 1.5
        self.rotation_start = 5.2

        # State
        self.is_paused = False
        self.sim_time = 0.0

        # Visual Modes
        # 0: Coded Words & Binary (Default)
        # 1: Pure Binary Matrix ('0' & '1')
        # 2: Classic ASCII Density Ramp (' ' to '@')
        self.mode = 0
        self.bg_noise = 0.035 # Faint digital ambiance
        self.cell_w = 9.0
        self.cell_h = 13.0

        # Interactive Camera
        self.cam_yaw = 0.0
        self.cam_pitch = 14.0
        self.cam_dist = 4.5
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
        pygame.display.set_caption("Episode 03: Coded & Binary Diamond Ring // 3D Procedural Matrix")

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
        """Initialize ModernGL context, textures, and shader programs."""
        self.ctx = moderngl.create_context()

        # 1. Shaders
        self.ring_prog = self.ctx.program(
            vertex_shader=shaders.RING_VERT_SRC,
            fragment_shader=shaders.RING_FRAG_SRC
        )
        self.coded_prog = self.ctx.program(
            vertex_shader=shaders.CODED_VERT_SRC,
            fragment_shader=shaders.CODED_FRAG_SRC
        )

        # 2. Font Atlas Texture
        atlas_bytes, atlas_size = font_atlas.build_font_atlas(tile_w=32, tile_h=32, cols=16, rows=16)
        self.font_atlas_tex = self.ctx.texture(atlas_size, 1, atlas_bytes)
        self.font_atlas_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)

        # 3. Offscreen FBO for 3D Pass
        self._init_fbo(self.width, self.height)

        # 4. Fullscreen Quad
        quad_verts = np.array([
            -1.0, -1.0,
             1.0, -1.0,
             1.0,  1.0,
            -1.0, -1.0,
             1.0,  1.0,
            -1.0,  1.0
        ], dtype=np.float32)
        self.quad_vbo = self.ctx.buffer(quad_verts.tobytes())
        self.quad_vao = self.ctx.vertex_array(self.coded_prog, [(self.quad_vbo, '2f', 'in_pos')])

    def _init_fbo(self, w, h):
        """Create or resize the 3D ring offscreen framebuffer."""
        if hasattr(self, 'ring_fbo') and self.ring_fbo:
            self.ring_fbo.release()
            self.ring_tex.release()
            self.ring_depth.release()

        self.ring_tex = self.ctx.texture((w, h), 4, dtype='f2')
        self.ring_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.ring_depth = self.ctx.depth_renderbuffer((w, h))
        self.ring_fbo = self.ctx.framebuffer(
            color_attachments=[self.ring_tex],
            depth_attachment=self.ring_depth
        )

    def _init_geometry(self):
        """Compile procedural 3D meshes (band, prongs, diamond gem)."""
        all_verts = []
        all_verts.extend(ring_geometry.generate_ring_band(u_segs=110, v_segs=36))
        all_verts.extend(ring_geometry.generate_prongs(num_steps=28, radial_segs=14))
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
        self._init_fbo(self.width, self.height)

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

    def render_scene(self, t, width=None, height=None, target_fbo=None, is_export=False):
        """
        Two-Pass Render Pipeline:
        Pass 1: Render 3D ring mesh into offscreen FBO (Luminance, Growth, MatID, Vis).
        Pass 2: Fullscreen coded matrix shader (Rasterizes into pixelated binary digits & code words with shockwave).
        """
        w = width if width is not None else self.width
        h = height if height is not None else self.height

        # =====================================================================
        # PASS 1: 3D PARAMETRIC RING GEOMETRY RENDER TO FBO
        # =====================================================================
        fbo = self.ring_fbo if not is_export else self.export_ring_fbo
        fbo.use()
        self.ctx.viewport = (0, 0, w, h)
        self.ctx.clear(0.0, 0.0, 0.0, 0.0)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.BLEND)

        aspect = w / float(h)
        fovy = 38.0 if aspect > 1.0 else 52.0
        proj = perspective_matrix(fovy, aspect, 0.1, 50.0)

        # 3D Orbit Camera
        auto_yaw = 0.0
        if t > self.rotation_start:
            dt_rot = t - self.rotation_start
            auto_yaw = dt_rot * 0.72 # Smooth rotation speed

        total_yaw = auto_yaw + math.radians(self.cam_yaw)
        pitch_rad = math.radians(self.cam_pitch)

        eye_x = self.cam_target[0] + self.cam_dist * math.cos(pitch_rad) * math.sin(total_yaw)
        eye_y = self.cam_target[1] + self.cam_dist * math.sin(pitch_rad)
        eye_z = self.cam_target[2] + self.cam_dist * math.cos(pitch_rad) * math.cos(total_yaw)
        eye = np.array([eye_x, eye_y, eye_z], dtype=np.float32)

        view = look_at_matrix(eye, self.cam_target)
        model = identity_matrix()

        # Growth Progress: 0.0 to 1.0 over growth_duration
        if t <= self.growth_duration:
            growth_pct = smoothstep(0.1, self.growth_duration, t)
        else:
            growth_pct = 1.0

        # Completion Flash
        if 4.0 <= t <= 4.7:
            flash_intensity = math.exp(-(t - 4.0) * 6.0)
        else:
            flash_intensity = 0.0

        set_uniform(self.ring_prog, 'm_proj', proj.T.tobytes())
        set_uniform(self.ring_prog, 'm_view', view.T.tobytes())
        set_uniform(self.ring_prog, 'm_model', model.T.tobytes())
        set_uniform(self.ring_prog, 'u_cam_pos', tuple(eye))
        set_uniform(self.ring_prog, 'u_growth', float(growth_pct))
        set_uniform(self.ring_prog, 'u_time', float(t))
        set_uniform(self.ring_prog, 'u_flash', float(flash_intensity))

        vao = self.ring_vao if not is_export else self.export_ring_vao
        vao.render(moderngl.TRIANGLES, vertices=self.ring_vert_count)

        # =====================================================================
        # PASS 2: FULLSCREEN CODED & BINARY MATRIX RASTERIZER
        # =====================================================================
        if target_fbo is not None:
            target_fbo.use()
        else:
            self.ctx.screen.use()

        self.ctx.viewport = (0, 0, w, h)
        self.ctx.disable(moderngl.DEPTH_TEST)

        # Concentric Hollow Halo Shockwave Calculations
        shock_radius = 0.0
        shock_alpha = 0.0
        if self.shockwave_start <= t <= (self.shockwave_start + self.shockwave_duration):
            dt_shock = t - self.shockwave_start
            shock_pct = dt_shock / self.shockwave_duration
            shock_radius = (shock_pct ** 0.82) * 2.3
            shock_alpha = (1.0 - shock_pct) ** 1.4

        # Cell size for export vs screen
        if is_export:
            cell_size = (8.0, 12.0)
        else:
            cell_size = (self.cell_w, self.cell_h)

        ring_tex = self.ring_tex if not is_export else self.export_ring_tex
        ring_tex.use(location=0)
        self.font_atlas_tex.use(location=1)

        set_uniform(self.coded_prog, 'u_ring_tex', 0)
        set_uniform(self.coded_prog, 'u_font_atlas', 1)
        set_uniform(self.coded_prog, 'u_resolution', (float(w), float(h)))
        set_uniform(self.coded_prog, 'u_cell_size', cell_size)
        set_uniform(self.coded_prog, 'u_time', float(t))
        set_uniform(self.coded_prog, 'u_growth', float(growth_pct))
        set_uniform(self.coded_prog, 'u_shock_radius', float(shock_radius))
        set_uniform(self.coded_prog, 'u_shock_alpha', float(shock_alpha))
        set_uniform(self.coded_prog, 'u_shock_center', (0.5, 0.52))
        set_uniform(self.coded_prog, 'u_mode', int(self.mode))
        set_uniform(self.coded_prog, 'u_bg_noise', float(self.bg_noise))

        quad_vao = self.quad_vao if not is_export else self.export_quad_vao
        quad_vao.render(moderngl.TRIANGLES)

    def run_interactive(self):
        """Main 60 FPS interactive loop (Full Laptop Screen)."""
        running = True
        print("\n=======================================================")
        print("  EPISODE 03: CODED & BINARY 3D DIAMOND RING")
        print("=======================================================")
        print("  Monochrome Black & White Coded Matrix Engine")
        print("  Full Laptop Screen Display (1536x864, 60 FPS)")
        print("  * Spacebar    : Pause / Resume animation")
        print("  * 'R' Key     : Replay from 0.0s (materialization & halo)")
        print("  * 'M' Key     : Cycle Mode (0: Coded+Binary, 1: Pure Binary, 2: ASCII)")
        print("  * 'B' Key     : Toggle Background subtle digital rain")
        print("  * '1','2','3' : Change Cell Size (Fine, Medium, Large)")
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
                        print("[*] Replaying Coded Ring Generation...")
                    elif event.key == pygame.K_m:
                        self.mode = (self.mode + 1) % 3
                        modes = ["Coded Words & Binary Matrix", "Pure Binary Matrix ('0' & '1')", "Classic ASCII Density Ramp"]
                        print(f"[*] Switched Mode: {modes[self.mode]}")
                    elif event.key == pygame.K_b:
                        self.bg_noise = 0.0 if self.bg_noise > 0.001 else 0.035
                        print(f"[*] Background Ambiance: {'ON' if self.bg_noise > 0.001 else 'OFF'}")
                    elif event.key == pygame.K_1:
                        self.cell_w, self.cell_h = 7.0, 10.0
                        print("[*] Cell Size: Fine (7x10)")
                    elif event.key == pygame.K_2:
                        self.cell_w, self.cell_h = 9.0, 13.0
                        print("[*] Cell Size: Medium (9x13)")
                    elif event.key == pygame.K_3:
                        self.cell_w, self.cell_h = 12.0, 17.0
                        print("[*] Cell Size: Large (12x17)")
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
        print(f"[*] Exporting 9:16 Coded Video Reel ({width}x{height})")
        print(f"[*] Frames: {total_frames} | Duration: {self.total_duration}s | FPS: {fps}")
        print(f"[*] Output: {output_path}")
        print(f"=======================================================\n")

        # Headless standalone context if running without display
        if not hasattr(self, 'ctx') or self.ctx is None:
            self.ctx = moderngl.create_context(standalone=True)
            self.ring_prog = self.ctx.program(
                vertex_shader=shaders.RING_VERT_SRC,
                fragment_shader=shaders.RING_FRAG_SRC
            )
            self.coded_prog = self.ctx.program(
                vertex_shader=shaders.CODED_VERT_SRC,
                fragment_shader=shaders.CODED_FRAG_SRC
            )
            atlas_bytes, atlas_size = font_atlas.build_font_atlas(tile_w=32, tile_h=32, cols=16, rows=16)
            self.font_atlas_tex = self.ctx.texture(atlas_size, 1, atlas_bytes)
            self.font_atlas_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)

        # Setup export geometry & FBOs
        all_verts = []
        all_verts.extend(ring_geometry.generate_ring_band(u_segs=110, v_segs=36))
        all_verts.extend(ring_geometry.generate_prongs(num_steps=28, radial_segs=14))
        all_verts.extend(ring_geometry.generate_diamond_gem(num_facets=24))

        v_data = np.array(all_verts, dtype=np.float32)
        export_ring_vbo = self.ctx.buffer(v_data.tobytes())
        self.export_ring_vao = self.ctx.vertex_array(
            self.ring_prog,
            [(export_ring_vbo, '3f 3f 3f 2f 1f 3f',
              'in_position', 'in_normal', 'in_color', 'in_uv', 'in_growth', 'in_mat')]
        )
        self.ring_vert_count = len(all_verts) // 15

        quad_verts = np.array([
            -1.0, -1.0,
             1.0, -1.0,
             1.0,  1.0,
            -1.0, -1.0,
             1.0,  1.0,
            -1.0,  1.0
        ], dtype=np.float32)
        export_quad_vbo = self.ctx.buffer(quad_verts.tobytes())
        self.export_quad_vao = self.ctx.vertex_array(self.coded_prog, [(export_quad_vbo, '2f', 'in_pos')])

        self.export_ring_tex = self.ctx.texture((width, height), 4, dtype='f2')
        self.export_ring_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.export_ring_depth = self.ctx.depth_renderbuffer((width, height))
        self.export_ring_fbo = self.ctx.framebuffer(
            color_attachments=[self.export_ring_tex],
            depth_attachment=self.export_ring_depth
        )

        # Final output FBO
        export_out_tex = self.ctx.texture((width, height), 4)
        export_out_fbo = self.ctx.framebuffer(color_attachments=[export_out_tex])

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        t_start = time.time()

        for frame_idx in range(total_frames):
            sim_t = frame_idx / float(fps)

            self.render_scene(
                sim_t,
                width=width,
                height=height,
                target_fbo=export_out_fbo,
                is_export=True
            )

            raw_bytes = export_out_fbo.read(components=3)
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
        self.export_ring_vao.release()
        export_ring_vbo.release()
        self.export_quad_vao.release()
        export_quad_vbo.release()
        self.export_ring_fbo.release()
        self.export_ring_tex.release()
        self.export_ring_depth.release()
        export_out_fbo.release()
        export_out_tex.release()

        print(f"\n[+] Export Complete in {time.time() - t_start:.1f}s!")
        print(f"[+] Video Reel saved successfully at:\n    {output_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Episode 03: Monochrome Coded & Binary Diamond Ring")
    parser.add_argument("--export", action="store_true", help="Render and export 14s MP4 video reel")
    parser.add_argument("--windowed", action="store_true", help="Launch in windowed mode instead of fullscreen")
    parser.add_argument("--mode", type=int, default=0, help="0: Coded Words & Binary, 1: Pure Binary, 2: ASCII")
    parser.add_argument("--res", type=str, default="720x1280", help="Resolution for export, e.g. 720x1280 or 1080x1920")
    args = parser.parse_args()

    if args.export:
        try:
            w, h = map(int, args.res.split('x'))
        except Exception:
            w, h = 720, 1280
        engine = DiamondRingEngine(width=w, height=h, fullscreen=False, is_headless=True)
        engine.mode = args.mode
        engine.export_video_reel(width=w, height=h)
    else:
        fullscreen = not args.windowed
        engine = DiamondRingEngine(fullscreen=fullscreen, is_headless=False)
        engine.mode = args.mode
        engine.run_interactive()


if __name__ == "__main__":
    main()
