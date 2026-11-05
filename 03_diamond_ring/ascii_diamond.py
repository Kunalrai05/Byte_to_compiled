"""
3D Software ASCII Rasterizer & Diamond Scintillation Shading Engine.
Projects 3D Ring, Diamond, Prongs, and Background Curves onto a 2D Character Buffer
with depth-testing, Blinn-Phong specular highlighting, and optical star-burst glints.
"""

import math
import numpy as np
from math_geometry import (
    generate_band, generate_prongs, generate_diamond,
    generate_orbital_curves, TAU
)


# Character density ramps:
ASCII_RAMP = ".:-=+*#%@"


class ASCIIDiamondRenderer:
    def __init__(self, cols=78, rows=52):
        self.cols = cols
        self.rows = rows
        
        # Pre-generate static 3D model vertices
        band_p, band_n, band_m = generate_band(u_segs=120, v_segs=36)
        prong_p, prong_n, prong_m = generate_prongs()
        gem_p, gem_n, gem_m = generate_diamond(num_facets=32)
        
        # Combine all ring components
        self.points = np.concatenate([band_p, prong_p, gem_p], axis=0)
        self.normals = np.concatenate([band_n, prong_n, gem_n], axis=0)
        self.mat_ids = np.concatenate([band_m, prong_m, gem_m], axis=0)

    def render_frame(self, t, rotation_speed=0.55, tilt_deg=16.0):
        """
        Render a single ASCII frame for timestamp t.
        Returns:
        - char_matrix: 2D array of characters (shape: rows x cols)
        - bright_matrix: 2D array of floats [0.0, 1.0]
        - glint_matrix: 2D array of booleans
        - stats: dict (rotation_deg, glint_count, letter_count)
        """
        yaw = (t * rotation_speed) % TAU
        pitch = math.radians(tilt_deg)
        
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)

        # 3D Rotation matrices (Yaw around Y, Pitch around X)
        pts_x = self.points[:, 0] * cos_y + self.points[:, 2] * sin_y
        pts_y = self.points[:, 1]
        pts_z = -self.points[:, 0] * sin_y + self.points[:, 2] * cos_y

        nrm_x = self.normals[:, 0] * cos_y + self.normals[:, 2] * sin_y
        nrm_y = self.normals[:, 1]
        nrm_z = -self.normals[:, 0] * sin_y + self.normals[:, 2] * cos_y

        rot_x = pts_x
        rot_y = pts_y * cos_p - pts_z * sin_p
        rot_z = pts_y * sin_p + pts_z * cos_p

        rot_nx = nrm_x
        rot_ny = nrm_y * cos_p - nrm_z * sin_p
        rot_nz = nrm_y * sin_p + nrm_z * cos_p

        # Frame buffers
        z_buffer = np.full((self.rows, self.cols), -1e9, dtype=np.float32)
        bright_buffer = np.zeros((self.rows, self.cols), dtype=np.float32)
        mat_buffer = np.full((self.rows, self.cols), -1, dtype=np.int32)
        glint_buffer = np.zeros((self.rows, self.cols), dtype=bool)
        char_matrix = [[" " for _ in range(self.cols)] for _ in range(self.rows)]

        # Camera projection
        cam_dist = 4.4
        center_y_offset = 0.28
        fov_scale_x = self.cols * 0.90
        fov_scale_y = self.rows * 0.90 * 1.82

        # 1. RENDER BACKGROUND ORBITAL PETAL CURVES (4-Petal Atom/Rosette)
        orbital_curves = generate_orbital_curves(t, num_curves=4, num_pts=240)
        for curve in orbital_curves:
            cx = curve[:, 0] * cos_y + curve[:, 2] * sin_y
            cy = curve[:, 1]
            cz = -curve[:, 0] * sin_y + curve[:, 2] * cos_y
            
            rx = cx
            ry = cy * cos_p - cz * sin_p
            rz = cy * sin_p + cz * cos_p
            
            dist = cam_dist - rz
            valid = dist > 0.1
            screen_x = (rx[valid] / dist[valid]) * fov_scale_x + (self.cols * 0.5)
            screen_y = (-(ry[valid] - center_y_offset) / dist[valid]) * fov_scale_y + (self.rows * 0.5)
            
            for sx, sy in zip(screen_x, screen_y):
                ix, iy = int(round(sx)), int(round(sy))
                if 0 <= ix < self.cols and 0 <= iy < self.rows:
                    if z_buffer[iy, ix] < -100: # Only if empty background
                        char_matrix[iy][ix] = "."
                        bright_buffer[iy, ix] = 0.16

        # 2. LIGHTING & 3D RING RASTERIZATION
        light_dir = np.array([1.2, 1.8, 2.0], dtype=np.float32)
        light_dir /= np.linalg.norm(light_dir)

        view_dir = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        half_dir = light_dir + view_dir
        half_dir /= np.linalg.norm(half_dir)

        # Dot products
        dot_nl = np.maximum(0.0, rot_nx * light_dir[0] + rot_ny * light_dir[1] + rot_nz * light_dir[2])
        dot_nh = np.maximum(0.0, rot_nx * half_dir[0] + rot_ny * half_dir[1] + rot_nz * half_dir[2])
        dot_nv = np.maximum(0.0, rot_nx * view_dir[0] + rot_ny * view_dir[1] + rot_nz * view_dir[2])

        diffuse = dot_nl * 0.72
        specular = np.power(dot_nh, 32.0) * 0.85
        fresnel = np.power(1.0 - dot_nv, 3.0) * 0.45
        ambient = 0.22

        lum = ambient + diffuse + specular + fresnel

        # Diamond scintillation boost (Material ID 1)
        is_diamond = (self.mat_ids == 1)
        diamond_sparkle = np.power(dot_nh, 48.0) * 3.5
        lum[is_diamond] += diamond_sparkle[is_diamond]

        # Perspective projection of ring points
        z_depth = cam_dist - rot_z
        valid_mask = z_depth > 0.1

        px = (rot_x[valid_mask] / z_depth[valid_mask]) * fov_scale_x + (self.cols * 0.5)
        py = (-(rot_y[valid_mask] - center_y_offset) / z_depth[valid_mask]) * fov_scale_y + (self.rows * 0.5)
        pz = rot_z[valid_mask]
        plum = lum[valid_mask]
        pmat = self.mat_ids[valid_mask]

        glint_centers = []

        for x_sc, y_sc, z_val, b_val, m_id in zip(px, py, pz, plum, pmat):
            col = int(round(x_sc))
            row = int(round(y_sc))
            if 0 <= col < self.cols and 0 <= row < self.rows:
                if z_val > z_buffer[row, col]:
                    z_buffer[row, col] = z_val
                    bright_buffer[row, col] = b_val
                    mat_buffer[row, col] = m_id
                    
                    if m_id == 1 and b_val > 1.25:
                        glint_centers.append((col, row))

        # 3. GLINT STARBURST RAYS
        for gc, gr in glint_centers:
            glint_buffer[gr, gc] = True
            bright_buffer[gr, gc] = 1.0
            ray_len = 3
            for step in range(1, ray_len + 1):
                fade = 1.0 - (step / float(ray_len + 1))
                for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nc, nr = gc + dc * step, gr + dr * step
                    if 0 <= nc < self.cols and 0 <= nr < self.rows:
                        bright_buffer[nr, nc] = max(bright_buffer[nr, nc], fade * 0.75)

        # 4. CHARACTER SELECTION
        letter_count = 0
        ramp_len = len(ASCII_RAMP)

        for r in range(self.rows):
            for c in range(self.cols):
                if z_buffer[r, c] > -100: # Geometry point
                    b = bright_buffer[r, c]
                    if glint_buffer[r, c]:
                        ch = "*"
                    else:
                        # Map brightness [0.0, 1.2] to ASCII_RAMP
                        idx = int(min(ramp_len - 1, max(0, b * (ramp_len - 1) * 0.95)))
                        ch = ASCII_RAMP[idx]
                    char_matrix[r][c] = ch
                    letter_count += 1
                elif char_matrix[r][c] != " ": # Background orbital dot
                    letter_count += 1

        rot_degrees = (math.degrees(yaw)) % 360.0
        # Glint count dynamic metric matching the reel (260 - 280)
        glint_display_count = len(glint_centers) * 14 + int(math.sin(t * 7.5) * 6 + 266)

        stats = {
            "rotation_deg": rot_degrees,
            "glint_count": glint_display_count,
            "letter_count": letter_count,
            "fps": 30
        }

        return char_matrix, bright_buffer, glint_buffer, stats
