"""
================================================================================
  PRUNUS SERRULATA (JAPANESE CHERRY BLOSSOM TREE / 桜の木)
  Procedural 3D Geometry Generator: Ancient Bonsai Arbor, Hanagasumi Canopy,
  Zen Island & Reflecting Pond, and Falling Petals (花吹雪 — Hanafubuki)
================================================================================
"""

import math
import numpy as np
from math_utils import (
    eval_cubic_bezier,
    compute_bishop_frame,
    normalize_v3,
    smoothstep,
    rotation_matrix_y,
    rotation_matrix_axis_angle
)

class SakuraModel:
    def __init__(self):
        self.vertices = []
        self.particles = []
        self.falling_petals = []

    def add_quad_grid(self, P, N, C, U, V, timing, mat):
        """
        Convert a 2D parametric surface grid P(Nu, Nv, 3) into indexed triangles
        with barycentric wireframe coordinates, UVs, timing easing, and material properties.
        """
        Nu, Nv, _ = P.shape
        bary_cycle = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        for i in range(Nu - 1):
            for j in range(Nv - 1):
                p00, p10, p11, p01 = P[i, j], P[i + 1, j], P[i + 1, j + 1], P[i, j + 1]
                n00, n10, n11, n01 = N[i, j], N[i + 1, j], N[i + 1, j + 1], N[i, j + 1]
                c00, c10, c11, c01 = C[i, j], C[i + 1, j], C[i + 1, j + 1], C[i, j + 1]

                u00 = np.array([U[i, j], V[i, j]], dtype=np.float32)
                u10 = np.array([U[i + 1, j], V[i + 1, j]], dtype=np.float32)
                u11 = np.array([U[i + 1, j + 1], V[i + 1, j + 1]], dtype=np.float32)
                u01 = np.array([U[i, j + 1], V[i, j + 1]], dtype=np.float32)

                # Triangle 1
                self.vertices.append(np.concatenate([p00, n00, c00, bary_cycle[0], u00, timing, mat]))
                self.vertices.append(np.concatenate([p10, n10, c10, bary_cycle[1], u10, timing, mat]))
                self.vertices.append(np.concatenate([p11, n11, c11, bary_cycle[2], u11, timing, mat]))

                # Triangle 2
                self.vertices.append(np.concatenate([p00, n00, c00, bary_cycle[0], u00, timing, mat]))
                self.vertices.append(np.concatenate([p11, n11, c11, bary_cycle[2], u11, timing, mat]))
                self.vertices.append(np.concatenate([p01, n01, c01, bary_cycle[2], u01, timing, mat]))

def compute_grid_normals(P):
    """Compute smooth surface normals for regular (Nu, Nv, 3) grid."""
    dP_du = np.zeros_like(P)
    dP_du[1:-1] = (P[2:] - P[:-2]) * 0.5
    dP_du[0] = P[1] - P[0]
    dP_du[-1] = P[-1] - P[-2]

    dP_dv = np.zeros_like(P)
    dP_dv[:, 1:-1] = (P[:, 2:] - P[:, :-2]) * 0.5
    dP_dv[:, 0] = P[:, 1] - P[:, 0]
    dP_dv[:, -1] = P[:, -1] - P[:, -2]

    normals = np.cross(dP_du, dP_dv)
    return normalize_v3(normals)

def generate_branch(model, p0, p1, p2, p3, r_base, r_tip, wire_t0, wire_t1, surf_t0, surf_t1, Nu=18, Nv=10):
    """Generate organic weathered cherry bark branch with smooth Bishop frame transport."""
    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(0.0, 2.0 * math.pi, Nv, endpoint=False, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    pos, tan = eval_cubic_bezier(p0, p1, p2, p3, u)
    T = normalize_v3(tan)
    N1, N2 = compute_bishop_frame(T)

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    # Ancient cherry bark: rich dark chestnut / charcoal with warm reddish undertones
    c_bark_dark = np.array([0.13, 0.08, 0.06], dtype=np.float32)
    c_bark_light = np.array([0.22, 0.15, 0.11], dtype=np.float32)
    c_moss_accent = np.array([0.16, 0.22, 0.10], dtype=np.float32)

    for i in range(Nu):
        ui = u[i]
        radius = r_base + (r_tip - r_base) * ui
        for j in range(Nv):
            vj = v[j]
            # Deep bark striations and natural furrowed ridges
            bark_bump = 1.0 + 0.09 * math.sin(7.0 * vj + ui * 18.0) + 0.04 * math.cos(3.0 * vj)
            r_j = radius * bark_bump
            P[i, j] = pos[i] + r_j * (math.cos(vj) * N1[i] + math.sin(vj) * N2[i])
            
            stripes = 0.5 + 0.5 * math.sin(ui * 28.0 + vj * 3.0)
            col = (1.0 - stripes * 0.45) * c_bark_dark + (stripes * 0.45) * c_bark_light
            # Lichen/moss accents on older lower branches
            up_dot = max(0.0, N2[i][1])
            if up_dot > 0.35 and ui < 0.65:
                col = col * 0.70 + c_moss_accent * 0.30
            C[i, j] = col

    N = compute_grid_normals(P)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat = np.array([0.08, 0.14, 8.0], dtype=np.float32) # Wood has low SSS, low gloss
    model.add_quad_grid(P, N, C, U, V / (2.0 * math.pi), timing, mat)

def generate_sakura_petal(model, center, basis, scale, angle_deg, wire_t0, wire_t1, surf_t0, surf_t1, Nu=10, Nv=6):
    """
    Generate an individual Sakura petal featuring:
    - Delicate concave spoon cupping
    - Characteristic apical V-notch / cleft at the petal tip
    - Translucent pastel blush-pink to deep ruby throat gradient
    """
    length = 0.32 * scale
    max_w = 0.22 * scale

    p0 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    p1 = np.array([0.05 * length, 0.25 * length, 0.0], dtype=np.float32)
    p2 = np.array([0.18 * length, 0.65 * length, 0.0], dtype=np.float32)
    p3 = np.array([0.35 * length, 0.85 * length, 0.0], dtype=np.float32)

    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(-1.0, 1.0, Nv, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    pos, tan = eval_cubic_bezier(p0, p1, p2, p3, u)
    T = normalize_v3(tan)
    N1, N2 = compute_bishop_frame(T)

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    c_throat_ruby = np.array([0.94, 0.12, 0.44], dtype=np.float32)
    c_blush_pink = np.array([0.98, 0.74, 0.85], dtype=np.float32)
    c_white_tip = np.array([0.99, 0.96, 0.98], dtype=np.float32)

    for i in range(Nu):
        ui = u[i]
        sin_val = max(0.0, math.sin((ui**0.7) * math.pi))
        w = max_w * sin_val * (1.0 - 0.12 * ui)

        # Cleft notch at petal apex
        cleft_envelope = smoothstep(0.78, 1.0, ui) if ui > 0.78 else 0.0
        cleft_shape = (1.0 - np.clip(abs(v), 0.0, 1.0)**2)**2.0 if ui > 0.78 else np.zeros_like(v)

        for j in range(Nv):
            vj = v[j]
            cup = 0.22 * (vj**2) * max_w * (1.0 - 0.3 * ui)
            indent = cleft_envelope * cleft_shape[j] * (0.09 * length)
            P[i, j] = (pos[i] - indent * T[i]) + (vj * w) * N1[i] + cup * N2[i]

            edge_dist = abs(vj)
            throat_factor = 1.0 - smoothstep(0.04, 0.30, ui)
            tip_factor = smoothstep(0.55, 0.95, ui)
            col = (1.0 - tip_factor) * c_blush_pink + tip_factor * c_white_tip
            col = (1.0 - throat_factor) * col + throat_factor * c_throat_ruby
            col = col * (1.0 - edge_dist * 0.08) + edge_dist * 0.08 * c_white_tip
            C[i, j] = col

    # Rotate into pentamerous radial position (72 deg intervals)
    rot_rad = math.radians(angle_deg)
    R_z = rotation_matrix_y(rot_rad)

    P_rot = np.zeros_like(P)
    for i in range(Nu):
        for j in range(Nv):
            P_rot[i, j] = P[i, j] @ R_z.T

    P_world = np.zeros_like(P_rot)
    for i in range(Nu):
        for j in range(Nv):
            P_world[i, j] = center + P_rot[i, j] @ basis.T

    N = compute_grid_normals(P_world)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat = np.array([0.88, 0.30, 24.0], dtype=np.float32) # High SSS for glowing translucent petals
    model.add_quad_grid(P_world, N, C, U, (V + 1.0) * 0.5, timing, mat)

def generate_sakura_flower(model, center, basis, scale, wire_t0, wire_t1, surf_t0, surf_t1):
    """Generate a complete 5-petaled Sakura blossom."""
    for p_idx in range(5):
        angle_deg = p_idx * 72.0
        p_delay = 0.04 * p_idx
        generate_sakura_petal(model, center, basis, scale, angle_deg,
                              wire_t0=wire_t0 + p_delay, wire_t1=wire_t1 + p_delay,
                              surf_t0=surf_t0 + p_delay, surf_t1=surf_t1 + p_delay)

def generate_flower_cluster(model, center, norm_dir, scale, wire_t0, wire_t1, surf_t0, surf_t1, num_flowers=3):
    """Generate a dense, cloud-like cluster of blooming sakura blossoms."""
    n = normalize_v3(norm_dir)
    ref = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    if abs(np.dot(n, ref)) > 0.9:
        ref = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    t1 = normalize_v3(np.cross(n, ref))
    t2 = normalize_v3(np.cross(n, t1))

    for idx in range(num_flowers):
        ang = idx * (2.0 * math.pi / float(num_flowers)) + 0.3 * (idx % 2)
        rad = 0.07 * scale
        offset = rad * (math.cos(ang) * t1 + math.sin(ang) * t2) + (0.03 * (idx % 2)) * n
        fl_center = center + offset
        
        fl_dir = normalize_v3(offset + 0.12 * n)
        fl_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        fl_side = normalize_v3(np.cross(fl_dir, fl_up))
        fl_basis = np.column_stack([fl_side, fl_dir, np.cross(fl_side, fl_dir)])
        
        dt = 0.05 * idx
        generate_sakura_flower(model, fl_center, fl_basis, scale * (0.85 + 0.15 * (idx % 2)),
                               wire_t0=wire_t0 + dt, wire_t1=wire_t1 + dt,
                               surf_t0=surf_t0 + dt, surf_t1=surf_t1 + dt)

def generate_falling_petal(model, base_pos, fall_speed, flutter_phase, scale, Nu=8, Nv=5):
    """Generate an individual floating/falling Sakura petal for Hanafubuki (flower blizzard)."""
    length = 0.16 * scale
    max_w = 0.12 * scale

    p0 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    p1 = np.array([0.03 * length, 0.25 * length, 0.0], dtype=np.float32)
    p2 = np.array([0.15 * length, 0.65 * length, 0.0], dtype=np.float32)
    p3 = np.array([0.30 * length, 0.85 * length, 0.0], dtype=np.float32)

    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(-1.0, 1.0, Nv, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    pos, tan = eval_cubic_bezier(p0, p1, p2, p3, u)
    T = normalize_v3(tan)
    N1, N2 = compute_bishop_frame(T)

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    c_blush = np.array([0.98, 0.76, 0.86], dtype=np.float32)
    c_white = np.array([0.99, 0.96, 0.98], dtype=np.float32)

    for i in range(Nu):
        ui = u[i]
        sin_val = max(0.0, math.sin((ui**0.7) * math.pi))
        w = max_w * sin_val * (1.0 - 0.12 * ui)
        for j in range(Nv):
            vj = v[j]
            cup = 0.20 * (vj**2) * max_w
            P[i, j] = pos[i] + (vj * w) * N1[i] + cup * N2[i]
            C[i, j] = (1.0 - ui * 0.4) * c_blush + (ui * 0.4) * c_white

    rot = rotation_matrix_axis_angle([0.6, 1.0, 0.4], flutter_phase)
    P_world = np.zeros_like(P)
    for i in range(Nu):
        for j in range(Nv):
            P_world[i, j] = base_pos + P[i, j] @ rot.T

    N = compute_grid_normals(P_world)
    timing = np.array([6.5, 6.5, 6.5, 7.2], dtype=np.float32)
    mat = np.array([0.88, fall_speed, flutter_phase], dtype=np.float32)
    model.add_quad_grid(P_world, N, C, U, (V + 1.0) * 0.5, timing, mat)

def generate_zen_island_and_pond(model, wire_t0, wire_t1, surf_t0, surf_t1):
    """
    Generate an authentic Japanese Zen garden:
    1. Mossy mound island where the tree roots anchor.
    2. Surrounding tranquil reflecting water pond with gentle ripples.
    3. Fallen petals resting on the moss and floating on the water (Hana-ikada).
    """
    # 1. Mossy Island
    Nu_m, Nv_m = 18, 24
    u_m = np.linspace(0.0, 1.0, Nu_m, dtype=np.float32)
    v_m = np.linspace(0.0, 2.0 * math.pi, Nv_m, endpoint=False, dtype=np.float32)
    Um, Vm = np.meshgrid(u_m, v_m, indexing='ij')

    P_m = np.zeros((Nu_m, Nv_m, 3), dtype=np.float32)
    C_m = np.zeros((Nu_m, Nv_m, 3), dtype=np.float32)

    c_moss_rich = np.array([0.16, 0.32, 0.12], dtype=np.float32)
    c_moss_warm = np.array([0.22, 0.38, 0.16], dtype=np.float32)
    c_stone_edge = np.array([0.20, 0.22, 0.24], dtype=np.float32)

    radius_m = 1.45
    for i in range(Nu_m):
        ui = u_m[i]
        r = radius_m * ui
        cos_val = max(0.0, math.cos(ui * 0.5 * math.pi))
        h = -0.90 + 0.26 * (cos_val**1.6)
        for j in range(Nv_m):
            vj = v_m[j]
            noise = 0.02 * math.sin(4.0 * vj + ui * 6.0)
            P_m[i, j] = np.array([
                (r + noise) * math.cos(vj),
                h,
                (r + noise) * math.sin(vj)
            ], dtype=np.float32)

            if ui < 0.82:
                moss_mix = (1.0 - ui * 0.5) + 0.1 * math.sin(3.0 * vj)
                col = moss_mix * c_moss_warm + (1.0 - moss_mix) * c_moss_rich
            else:
                stone_fac = smoothstep(0.82, 1.0, ui)
                col = (1.0 - stone_fac) * c_moss_rich + stone_fac * c_stone_edge
            C_m[i, j] = col

    N_m = compute_grid_normals(P_m)
    timing_m = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat_m = np.array([0.02, 0.05, 4.0], dtype=np.float32)
    model.add_quad_grid(P_m, N_m, C_m, Um, Vm / (2.0 * math.pi), timing_m, mat_m)

    # 2. Reflecting Water Pond
    Nu_w, Nv_w = 16, 28
    u_w = np.linspace(1.30, 4.8, Nu_w, dtype=np.float32)
    v_w = np.linspace(0.0, 2.0 * math.pi, Nv_w, endpoint=False, dtype=np.float32)
    Uw, Vw = np.meshgrid(u_w, v_w, indexing='ij')

    P_w = np.zeros((Nu_w, Nv_w, 3), dtype=np.float32)
    C_w = np.zeros((Nu_w, Nv_w, 3), dtype=np.float32)

    c_water_deep = np.array([0.06, 0.12, 0.20], dtype=np.float32)
    c_water_edge = np.array([0.10, 0.18, 0.26], dtype=np.float32)

    for i in range(Nu_w):
        rw = u_w[i]
        for j in range(Nv_w):
            vj = v_w[j]
            ripple = 0.005 * math.sin(rw * 8.0 - vj * 3.0)
            P_w[i, j] = np.array([
                rw * math.cos(vj),
                -0.905 + ripple,
                rw * math.sin(vj)
            ], dtype=np.float32)

            fade = smoothstep(1.30, 3.5, rw)
            C_w[i, j] = (1.0 - fade) * c_water_edge + fade * c_water_deep

    N_w = compute_grid_normals(P_w)
    timing_w = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat_w = np.array([0.00, 0.75, 48.0], dtype=np.float32)
    model.add_quad_grid(P_w, N_w, C_w, (Uw - 1.30) / 3.5, Vw / (2.0 * math.pi), timing_w, mat_w)

    # 3. Resting Petals on Moss Island and Floating on Pond Water
    np.random.seed(77)
    for _ in range(24):
        rad = np.random.uniform(0.20, 1.15)
        ang = np.random.uniform(0.0, 2.0 * math.pi)
        px = rad * math.cos(ang)
        pz = rad * math.sin(ang)
        py = -0.90 + 0.26 * (max(0.0, math.cos(rad / 1.45 * 0.5 * math.pi))**1.6) + 0.006
        pos = np.array([px, py, pz], dtype=np.float32)
        fl = np.random.uniform(0.0, 2.0 * math.pi)
        sc = np.random.uniform(0.60, 0.90)
        generate_falling_petal(model, pos, fall_speed=0.0, flutter_phase=fl, scale=sc)

    for _ in range(20):
        rad = np.random.uniform(1.35, 2.8)
        ang = np.random.uniform(0.0, 2.0 * math.pi)
        px = rad * math.cos(ang)
        pz = rad * math.sin(ang)
        py = -0.902
        pos = np.array([px, py, pz], dtype=np.float32)
        fl = np.random.uniform(0.0, 2.0 * math.pi)
        sc = np.random.uniform(0.60, 0.85)
        generate_falling_petal(model, pos, fall_speed=0.0, flutter_phase=fl, scale=sc)

def generate_full_sakura_specimen():
    """
    Assemble the complete majestic Japanese Cherry Blossom Tree (Prunus Serrulata):
    - Mossy Zen Island & surrounding reflecting water pond
    - Nebari root flare anchoring trunk to the earth
    - Ancient upright Moyogi bonsai trunk with furrowed aged bark
    - Sprawling natural boughs with arching-and-weeping s-curves
    - Hanagasumi: Cloud-like cherry blossom clusters across the entire canopy
    - Hanafubuki: Dynamic falling petals swirling in the spring breeze
    - Ambient golden-pink pollen fireflies
    """
    model = SakuraModel()

    # 1. Zen Island & Reflecting Pond
    generate_zen_island_and_pond(model, wire_t0=0.0, wire_t1=2.0, surf_t0=0.4, surf_t1=2.8)

    # 2. Nebari Root Anchors (4 curved roots anchoring the tree base)
    roots = [
        (np.array([ 0.0, -0.68,  0.0]), np.array([ 0.18, -0.74,  0.15]), np.array([ 0.36, -0.80,  0.28]), np.array([ 0.58, -0.85,  0.42])),
        (np.array([ 0.0, -0.68,  0.0]), np.array([-0.16, -0.74,  0.12]), np.array([-0.32, -0.80,  0.24]), np.array([-0.52, -0.85,  0.36])),
        (np.array([ 0.0, -0.68,  0.0]), np.array([ 0.14, -0.74, -0.16]), np.array([ 0.28, -0.80, -0.30]), np.array([ 0.46, -0.85, -0.45])),
        (np.array([ 0.0, -0.68,  0.0]), np.array([-0.15, -0.73, -0.15]), np.array([-0.30, -0.79, -0.28]), np.array([-0.48, -0.84, -0.42])),
    ]
    for r0, r1, r2, r3 in roots:
        generate_branch(model, r0, r1, r2, r3, r_base=0.085, r_tip=0.026,
                        wire_t0=0.2, wire_t1=2.2, surf_t0=0.8, surf_t1=3.0, Nu=10, Nv=6)

    # 3. Ancient Moyogi Bonsai Trunk: Sweeps right, arches left, curves gracefully upward
    t0 = np.array([ 0.00, -0.68,  0.00], dtype=np.float32)
    t1 = np.array([ 0.10, -0.42,  0.04], dtype=np.float32)
    t2 = np.array([ 0.14, -0.18, -0.02], dtype=np.float32)
    t3 = np.array([ 0.06,  0.05,  0.02], dtype=np.float32)
    generate_branch(model, t0, t1, t2, t3, r_base=0.15, r_tip=0.105,
                    wire_t0=0.4, wire_t1=2.6, surf_t0=1.0, surf_t1=3.4, Nu=14, Nv=8)

    u0 = t3
    u1 = np.array([-0.04,  0.28,  0.04], dtype=np.float32)
    u2 = np.array([-0.02,  0.58, -0.02], dtype=np.float32)
    u3 = np.array([ 0.05,  0.92,  0.02], dtype=np.float32)
    generate_branch(model, u0, u1, u2, u3, r_base=0.105, r_tip=0.065,
                    wire_t0=1.2, wire_t1=3.4, surf_t0=1.8, surf_t1=4.2, Nu=14, Nv=8)

    c0 = u3
    c1 = np.array([ 0.08,  1.12,  0.04], dtype=np.float32)
    c2 = np.array([ 0.05,  1.32, -0.02], dtype=np.float32)
    c3 = np.array([ 0.02,  1.48,  0.00], dtype=np.float32)
    generate_branch(model, c0, c1, c2, c3, r_base=0.065, r_tip=0.028,
                    wire_t0=2.0, wire_t1=4.2, surf_t0=2.8, surf_t1=5.0, Nu=12, Nv=6)

    # 4. Sprawling Natural Boughs with authentic Bonsai Arch-and-Weep Curves
    # Bough 1: Character Left Bough
    b1_0 = t3
    b1_1 = np.array([-0.42,  0.22,  0.10], dtype=np.float32)
    b1_2 = np.array([-0.88,  0.28,  0.16], dtype=np.float32)
    b1_3 = np.array([-1.38,  0.18,  0.22], dtype=np.float32)
    generate_branch(model, b1_0, b1_1, b1_2, b1_3, r_base=0.075, r_tip=0.032,
                    wire_t0=1.6, wire_t1=4.0, surf_t0=2.4, surf_t1=4.8)

    # Bough 2: Counter Right Bough
    b2_0 = u1
    b2_1 = np.array([ 0.40,  0.42,  0.16], dtype=np.float32)
    b2_2 = np.array([ 0.85,  0.48,  0.26], dtype=np.float32)
    b2_3 = np.array([ 1.30,  0.38,  0.32], dtype=np.float32)
    generate_branch(model, b2_0, b2_1, b2_2, b2_3, r_base=0.068, r_tip=0.030,
                    wire_t0=1.8, wire_t1=4.2, surf_t0=2.6, surf_t1=5.0)

    # Bough 3: Depth Back-Left Bough
    b3_0 = u2
    b3_1 = np.array([-0.18,  0.72, -0.32], dtype=np.float32)
    b3_2 = np.array([-0.36,  0.88, -0.62], dtype=np.float32)
    b3_3 = np.array([-0.52,  0.98, -0.92], dtype=np.float32)
    generate_branch(model, b3_0, b3_1, b3_2, b3_3, r_base=0.058, r_tip=0.026,
                    wire_t0=2.2, wire_t1=4.6, surf_t0=3.0, surf_t1=5.4)

    # Bough 4: High Right Canopy Bough
    b4_0 = u3
    b4_1 = np.array([ 0.35,  1.08, -0.08], dtype=np.float32)
    b4_2 = np.array([ 0.68,  1.18, -0.12], dtype=np.float32)
    b4_3 = np.array([ 0.98,  1.12, -0.15], dtype=np.float32)
    generate_branch(model, b4_0, b4_1, b4_2, b4_3, r_base=0.054, r_tip=0.024,
                    wire_t0=2.4, wire_t1=4.8, surf_t0=3.2, surf_t1=5.6)

    # 5. Secondary Graceful Branches
    sub_branches = [
        # Left bough sub-branches
        (b1_1, np.array([-0.65, 0.38, 0.05]), np.array([-0.88, 0.48, 0.02]), np.array([-1.12, 0.54, -0.02]), 0.036, 0.018, 2.5, 4.8),
        (b1_2, np.array([-1.05, 0.12, 0.28]), np.array([-1.22, 0.04, 0.38]), np.array([-1.38, -0.05, 0.46]), 0.032, 0.016, 2.8, 5.0),
        # Right bough sub-branches
        (b2_1, np.array([ 0.62, 0.58, 0.12]), np.array([ 0.85, 0.70, 0.08]), np.array([ 1.08, 0.78, 0.02]), 0.034, 0.018, 2.7, 4.9),
        (b2_2, np.array([ 1.02, 0.28, 0.42]), np.array([ 1.20, 0.18, 0.52]), np.array([ 1.35, 0.08, 0.60]), 0.030, 0.016, 2.9, 5.1),
        # Apex sub-branches
        (c1,   np.array([-0.22, 1.25, 0.12]), np.array([-0.42, 1.35, 0.18]), np.array([-0.58, 1.40, 0.22]), 0.032, 0.016, 3.1, 5.3),
        (c2,   np.array([ 0.25, 1.42, 0.08]), np.array([ 0.45, 1.48, 0.12]), np.array([ 0.62, 1.50, 0.15]), 0.028, 0.014, 3.3, 5.5),
    ]
    for sb0, sb1, sb2, sb3, rb, rt, wt, st in sub_branches:
        generate_branch(model, sb0, sb1, sb2, sb3, r_base=rb, r_tip=rt,
                        wire_t0=wt, wire_t1=wt + 2.2, surf_t0=st, surf_t1=st + 2.2, Nu=10, Nv=6)

    # 6. Hanagasumi: Cloud-like Cherry Blossom Canopy
    flower_nodes = [
        # Left Bough Canopy
        (b1_3, np.array([-0.8, 0.4, 0.4]), 1.15),
        (b1_3 + np.array([-0.12, 0.12, -0.08]), np.array([-0.6, 0.8, 0.1]), 1.08),
        (b1_2 + np.array([-0.08, 0.16, 0.10]), np.array([-0.4, 0.8, 0.4]), 1.10),
        (np.array([-1.12, 0.54, -0.02]), np.array([-0.7, 0.7, -0.2]), 1.10),
        (np.array([-1.38, -0.05, 0.46]), np.array([-0.5, -0.4, 0.8]), 1.05),
        (b1_1 + np.array([-0.05, 0.18, 0.12]), np.array([-0.2, 0.9, 0.4]), 1.05),
        
        # Right Bough Canopy
        (b2_3, np.array([ 0.8, 0.4, 0.4]), 1.18),
        (b2_3 + np.array([ 0.12, 0.12, -0.10]), np.array([ 0.7, 0.7, -0.2]), 1.10),
        (b2_2 + np.array([ 0.08, 0.16,  0.12]), np.array([ 0.5, 0.8,  0.3]), 1.12),
        (np.array([ 1.08, 0.78, 0.02]), np.array([ 0.6, 0.8, 0.1]), 1.10),
        (np.array([ 1.35, 0.08, 0.60]), np.array([ 0.5, -0.4, 0.8]), 1.05),
        (b2_1 + np.array([ 0.08, 0.20, -0.08]), np.array([ 0.3, 0.9, -0.3]), 1.05),

        # Back Depth Canopy
        (b3_3, np.array([-0.4, 0.6, -0.8]), 1.10),
        (b3_2 + np.array([-0.10, 0.14, -0.12]), np.array([-0.4, 0.8, -0.5]), 1.05),
        (b3_1 + np.array([ 0.12, 0.18, -0.15]), np.array([ 0.3, 0.8, -0.4]), 1.02),

        # High Right Canopy
        (b4_3, np.array([ 0.7, 0.5, -0.5]), 1.15),
        (b4_2 + np.array([ 0.10, 0.14, -0.08]), np.array([ 0.5, 0.8, -0.3]), 1.10),

        # Apex Crown (Full majestic floral dome)
        (c3, np.array([ 0.0, 1.0, 0.0]), 1.25),
        (c3 + np.array([-0.18, -0.05,  0.15]), np.array([-0.5, 0.8, 0.4]), 1.15),
        (c3 + np.array([ 0.18, -0.06, -0.15]), np.array([ 0.5, 0.8, -0.4]), 1.15),
        (np.array([-0.58, 1.40, 0.22]), np.array([-0.6, 0.7, 0.3]), 1.10),
        (np.array([ 0.62, 1.50, 0.15]), np.array([ 0.6, 0.7, 0.3]), 1.10),
        (c1 + np.array([ 0.05, 0.12,  0.15]), np.array([ 0.2, 0.9, 0.4]), 1.08),
    ]

    for idx, (pos, norm, sc) in enumerate(flower_nodes):
        wire_t = 3.6 + 0.14 * idx
        surf_t = 5.8 + 0.16 * idx
        generate_flower_cluster(model, pos, norm, sc,
                                wire_t0=wire_t, wire_t1=wire_t + 2.5,
                                surf_t0=surf_t, surf_t1=surf_t + 2.8,
                                num_flowers=3)

    # 7. Falling Petals (Hanafubuki) — Gentle, delicate petals drifting in the breeze
    np.random.seed(108)
    num_falling = 120
    falling_petals = []
    for _ in range(num_falling):
        base_pos = np.array([
            np.random.uniform(-1.9, 1.9),
            np.random.uniform(-0.6, 1.8),
            np.random.uniform(-1.0, 1.0)
        ], dtype=np.float32)
        fall_spd = np.random.uniform(0.16, 0.32)
        flutter = np.random.uniform(0.0, 2.0 * math.pi)
        scale = np.random.uniform(0.65, 0.95)
        falling_petals.append((base_pos, fall_spd, flutter, scale))
        generate_falling_petal(model, base_pos, fall_spd, flutter, scale)
    model.falling_petals = falling_petals

    # 8. Floating Ambient Golden-Pink Bokeh / Fireflies
    num_particles = 180
    particles = []
    for _ in range(num_particles):
        pos = np.array([
            np.random.uniform(-2.4, 2.4),
            np.random.uniform(-1.0, 2.2),
            np.random.uniform(-1.8, 1.8)
        ], dtype=np.float32)
        phase = np.random.uniform(0.0, 2.0 * math.pi)
        speed = np.random.uniform(0.25, 0.75)
        radius = np.random.uniform(0.015, 0.035)
        particles.append((pos, phase, speed, radius))
    model.particles = particles

    vertex_data = np.array(model.vertices, dtype=np.float32)
    return vertex_data, model.particles, model.falling_petals
