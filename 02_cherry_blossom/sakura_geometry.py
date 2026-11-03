"""
Procedural 3D geometry generator for Prunus Serrulata (Japanese Cherry Blossom / Sakura).
Generates gnarled bonsai branches, 5-petaled notched sakura blossoms, staminal crowns,
flower buds, and tumbling falling petals (Hanafubuki).
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
        self.particles = []      # Floating pollen bokeh spores
        self.falling_petals = [] # Tumbling 3D sakura petals

    def add_quad_grid(self, P, N, C, U, V, timing, mat):
        """
        Convert a 2D grid of 3D points P(Nu, Nv, 3) into indexed triangles
        with barycentric wireframe coordinates, UVs, and timing.
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
    """Compute smooth surface normals for regular (Nu, Nv, 3) parametric grid."""
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

def generate_branch(model, p0, p1, p2, p3, r_base, r_tip, wire_t0, wire_t1, surf_t0, surf_t1, Nu=32, Nv=10):
    """Generate an organic gnarled cherry tree branch tube."""
    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(0.0, 2.0 * math.pi, Nv, endpoint=False, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    pos, tan = eval_cubic_bezier(p0, p1, p2, p3, u)
    T = normalize_v3(tan)
    N1, N2 = compute_bishop_frame(T)

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    # Ancient cherry bark: dark weathered chestnut/charcoal with subtle warmth
    c_bark_dark = np.array([0.18, 0.13, 0.11], dtype=np.float32)
    c_bark_light = np.array([0.28, 0.20, 0.17], dtype=np.float32)

    for i in range(Nu):
        ui = u[i]
        radius = r_base + (r_tip - r_base) * ui
        for j in range(Nv):
            vj = v[j]
            # Natural bark roughness & nodule bumps
            bark_bump = 1.0 + 0.08 * math.sin(6.0 * vj + ui * 14.0) + 0.04 * math.cos(3.0 * vj)
            r_j = radius * bark_bump
            P[i, j] = pos[i] + r_j * (math.cos(vj) * N1[i] + math.sin(vj) * N2[i])
            
            # Subtle bark striation color
            stripes = 0.5 + 0.5 * math.sin(ui * 25.0 + vj * 2.0)
            C[i, j] = (1.0 - stripes * 0.4) * c_bark_dark + (stripes * 0.4) * c_bark_light

    N = compute_grid_normals(P)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat = np.array([0.15, 0.20, 12.0], dtype=np.float32) # Wood has low SSS, low gloss
    model.add_quad_grid(P, N, C, U, V / (2.0 * math.pi), timing, mat)

def generate_sakura_petal(model, center, basis, scale, angle_deg, wire_t0, wire_t1, surf_t0, surf_t1, Nu=20, Nv=11):
    """
    Generate an individual Sakura petal featuring:
    - Delicate concave spoon cupping
    - The signature Sakura V-notch / cleft at the petal apex
    - Translucent pastel pink to ruby center gradient
    """
    length = 0.48 * scale
    max_w = 0.32 * scale

    # Spine Bezier curve: gentle outward and upward cup, flaring slightly at tip
    p0 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    p1 = np.array([0.06 * length, 0.25 * length, 0.0], dtype=np.float32)
    p2 = np.array([0.22 * length, 0.65 * length, 0.0], dtype=np.float32)
    p3 = np.array([0.42 * length, 0.85 * length, 0.0], dtype=np.float32)

    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(-1.0, 1.0, Nv, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    pos, tan = eval_cubic_bezier(p0, p1, p2, p3, u)
    T = normalize_v3(tan)
    N1, N2 = compute_bishop_frame(T)

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    # Sakura Color Palette:
    # Deep ruby nectar eye at base: [0.92, 0.14, 0.42]
    # Pastel Sakura blush body:    [0.98, 0.76, 0.84]
    # Pristine white edges:        [0.99, 0.96, 0.98]
    c_throat_ruby = np.array([0.94, 0.12, 0.44], dtype=np.float32)
    c_blush_pink = np.array([0.98, 0.74, 0.85], dtype=np.float32)
    c_white_tip = np.array([0.99, 0.96, 0.98], dtype=np.float32)

    for i in range(Nu):
        ui = u[i]
        # Obovate width profile
        sin_val = max(0.0, math.sin((ui**0.7) * math.pi))
        w = max_w * sin_val * (1.0 - 0.12 * ui)

        # The signature Sakura cleft/notch at the petal tip!
        # When u > 0.80 and v is near center (0), indent the length backward
        cleft_depth = 0.0
        if ui > 0.78:
            cleft_envelope = smoothstep(0.78, 1.0, ui)
            cleft_shape = (1.0 - np.clip(abs(v), 0.0, 1.0)**2)**2.0
        else:
            cleft_envelope = 0.0
            cleft_shape = np.zeros_like(v)

        for j in range(Nv):
            vj = v[j]
            # Delicate cupping across petal: center is recessed, edges curl upward
            cup = 0.22 * (vj**2) * max_w * (1.0 - 0.3 * ui)
            
            # Local position with notch indentation
            indent = cleft_envelope * cleft_shape[j] * (0.09 * length)
            P[i, j] = (pos[i] - indent * T[i]) + (vj * w) * N1[i] + cup * N2[i]

            # Pigment calculation:
            # Concentrated deep ruby at throat (u < 0.25), blush pink body, white edges
            edge_dist = abs(vj)
            throat_factor = 1.0 - smoothstep(0.04, 0.32, ui)
            tip_factor = smoothstep(0.55, 0.95, ui)

            col = (1.0 - tip_factor) * c_blush_pink + tip_factor * c_white_tip
            col = (1.0 - throat_factor) * col + throat_factor * c_throat_ruby
            
            # Subtle edge lightening
            col = mix_col = col * (1.0 - edge_dist * 0.08) + edge_dist * 0.08 * c_white_tip
            C[i, j] = col

    # Rotate into radial petal position (72 deg intervals for 5 petals)
    rot_rad = math.radians(angle_deg)
    R_z = rotation_matrix_y(rot_rad)

    P_rot = np.zeros_like(P)
    for i in range(Nu):
        for j in range(Nv):
            P_rot[i, j] = P[i, j] @ R_z.T

    # Transform to world space with flower center and orientation basis
    P_world = np.zeros_like(P_rot)
    for i in range(Nu):
        for j in range(Nv):
            P_world[i, j] = center + P_rot[i, j] @ basis.T

    N = compute_grid_normals(P_world)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    # High SSS for paper-thin, glowing cherry blossom petals
    mat = np.array([0.85, 0.30, 24.0], dtype=np.float32)
    model.add_quad_grid(P_world, N, C, U, (V + 1.0) * 0.5, timing, mat)

def generate_sakura_stamens(model, center, basis, scale, wire_t0, wire_t1, surf_t0, surf_t1):
    """
    Generate the crown of ~20 delicate filaments with glowing golden-yellow anthers.
    """
    num_stamens = 20
    length = 0.26 * scale
    
    # 1. Central Pistil
    p0 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    p1 = np.array([0.01 * scale, 0.12 * scale, 0.01 * scale], dtype=np.float32)
    p2 = np.array([0.02 * scale, 0.22 * scale, 0.01 * scale], dtype=np.float32)
    p3 = np.array([0.02 * scale, 0.32 * scale, 0.02 * scale], dtype=np.float32)
    
    Nu_p, Nv_p = 10, 6
    up = np.linspace(0.0, 1.0, Nu_p, dtype=np.float32)
    vp = np.linspace(0.0, 2.0 * math.pi, Nv_p, endpoint=False, dtype=np.float32)
    Up, Vp = np.meshgrid(up, vp, indexing='ij')
    
    ppos, ptan = eval_cubic_bezier(p0, p1, p2, p3, up)
    Tp = normalize_v3(ptan)
    Np1, Np2 = compute_bishop_frame(Tp)
    
    P_pistil = np.zeros((Nu_p, Nv_p, 3), dtype=np.float32)
    C_pistil = np.zeros((Nu_p, Nv_p, 3), dtype=np.float32)
    c_style = np.array([0.62, 0.88, 0.45], dtype=np.float32)
    c_stigma = np.array([0.88, 0.22, 0.35], dtype=np.float32)
    
    for i in range(Nu_p):
        rp = 0.008 * scale if up[i] < 0.85 else 0.016 * scale
        col = c_stigma if up[i] >= 0.85 else c_style
        for j in range(Nv_p):
            P_pistil[i, j] = ppos[i] + rp * (math.cos(vp[j]) * Np1[i] + math.sin(vp[j]) * Np2[i])
            C_pistil[i, j] = col
            
    P_pistil_world = center + P_pistil @ basis.T
    N_pistil = compute_grid_normals(P_pistil_world)
    timing_p = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat_p = np.array([0.4, 0.3, 20.0], dtype=np.float32)
    model.add_quad_grid(P_pistil_world, N_pistil, C_pistil, Up, Vp / (2.0 * math.pi), timing_p, mat_p)

    # 2. Radiating Stamens with Golden Anthers
    for k in range(num_stamens):
        st_delay = 0.03 * (k % 5)
        angle = k * (2.0 * math.pi / float(num_stamens)) + 0.12 * math.sin(k)
        ca = math.cos(angle)
        sa = math.sin(angle)
        
        flare_r = (0.12 + 0.04 * (k % 3)) * scale
        h_stamen = (0.22 + 0.06 * ((k * 3) % 4)) * scale
        
        fp0 = np.array([0.01 * scale * ca, 0.02 * scale, 0.01 * scale * sa], dtype=np.float32)
        fp1 = np.array([0.04 * scale * ca, 0.10 * scale, 0.04 * scale * sa], dtype=np.float32)
        fp2 = np.array([flare_r * 0.7 * ca, h_stamen * 0.7, flare_r * 0.7 * sa], dtype=np.float32)
        fp3 = np.array([flare_r * ca, h_stamen, flare_r * sa], dtype=np.float32)
        
        Nu_f, Nv_f = 8, 4
        uf = np.linspace(0.0, 1.0, Nu_f, dtype=np.float32)
        vf = np.linspace(0.0, 2.0 * math.pi, Nv_f, endpoint=False, dtype=np.float32)
        Uf, Vf = np.meshgrid(uf, vf, indexing='ij')
        
        fpos, ftan = eval_cubic_bezier(fp0, fp1, fp2, fp3, uf)
        Tf = normalize_v3(ftan)
        N1f, N2f = compute_bishop_frame(Tf)
        
        P_fil = np.zeros((Nu_f, Nv_f, 3), dtype=np.float32)
        C_fil = np.zeros((Nu_f, Nv_f, 3), dtype=np.float32)
        c_fil = np.array([0.98, 0.88, 0.92], dtype=np.float32)
        
        for i in range(Nu_f):
            rf = 0.004 * scale
            for j in range(Nv_f):
                P_fil[i, j] = fpos[i] + rf * (math.cos(vf[j]) * N1f[i] + math.sin(vf[j]) * N2f[i])
                C_fil[i, j] = c_fil
                
        P_fil_world = center + P_fil @ basis.T
        N_fil = compute_grid_normals(P_fil_world)
        timing_f = np.array([wire_t0 + st_delay, wire_t1 + st_delay, surf_t0 + st_delay, surf_t1 + st_delay], dtype=np.float32)
        mat_f = np.array([0.4, 0.25, 18.0], dtype=np.float32)
        model.add_quad_grid(P_fil_world, N_fil, C_fil, Uf, Vf / (2.0 * math.pi), timing_f, mat_f)
        
        # Golden pollen anther sphere
        anther_pos = fp3
        anther_r = 0.014 * scale
        Nu_a, Nv_a = 6, 6
        ua = np.linspace(-1.0, 1.0, Nu_a, dtype=np.float32)
        va = np.linspace(0.0, 2.0 * math.pi, Nv_a, endpoint=False, dtype=np.float32)
        Ua, Va = np.meshgrid(ua, va, indexing='ij')
        
        P_anther = np.zeros((Nu_a, Nv_a, 3), dtype=np.float32)
        C_anther = np.zeros((Nu_a, Nv_a, 3), dtype=np.float32)
        c_anther_gold = np.array([0.98, 0.84, 0.22], dtype=np.float32) # glowing gold
        
        for i in range(Nu_a):
            u_val = ua[i]
            r_val = anther_r * math.sqrt(max(0.0, 1.0 - u_val**2))
            for j in range(Nv_a):
                P_anther[i, j] = anther_pos + np.array([
                    r_val * math.cos(va[j]),
                    u_val * anther_r * 0.8,
                    r_val * math.sin(va[j])
                ], dtype=np.float32)
                C_anther[i, j] = c_anther_gold
                
        P_anther_world = center + P_anther @ basis.T
        N_anther = compute_grid_normals(P_anther_world)
        model.add_quad_grid(P_anther_world, N_anther, C_anther, (Ua + 1.0) * 0.5, Va / (2.0 * math.pi), timing_f, mat_f)

def generate_sakura_flower(model, center, basis, scale, wire_t0, wire_t1, surf_t0, surf_t1):
    """Generate a complete 5-petaled Sakura blossom."""
    # 5 Petals at 72 deg
    for p_idx in range(5):
        angle_deg = p_idx * 72.0
        p_delay = 0.06 * p_idx
        generate_sakura_petal(model, center, basis, scale, angle_deg,
                              wire_t0=wire_t0 + p_delay, wire_t1=wire_t1 + p_delay,
                              surf_t0=surf_t0 + p_delay, surf_t1=surf_t1 + p_delay)
                              
    # Crown of Stamens & Pistil
    generate_sakura_stamens(model, center, basis, scale,
                            wire_t0=wire_t0 + 0.4, wire_t1=wire_t1 + 0.4,
                            surf_t0=surf_t0 + 0.4, surf_t1=surf_t1 + 0.4)

def generate_sakura_bud(model, center, basis, scale, wire_t0, wire_t1, surf_t0, surf_t1):
    """Generate an unopened swollen cherry blossom bud with deep ruby pink tip."""
    Nu, Nv = 12, 8
    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(0.0, 2.0 * math.pi, Nv, endpoint=False, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    c_calyx_green = np.array([0.35, 0.55, 0.22], dtype=np.float32)
    c_bud_pink = np.array([0.94, 0.20, 0.45], dtype=np.float32)

    length = 0.22 * scale
    max_r = 0.08 * scale

    for i in range(Nu):
        ui = u[i]
        r = max_r * math.sin(ui**0.65 * math.pi)
        y = ui * length
        col = (1.0 - ui) * c_calyx_green + ui * c_bud_pink
        for j in range(Nv):
            P[i, j] = np.array([r * math.cos(v[j]), y, r * math.sin(v[j])], dtype=np.float32)
            C[i, j] = col

    P_world = center + P @ basis.T
    N = compute_grid_normals(P_world)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat = np.array([0.5, 0.35, 20.0], dtype=np.float32)
    model.add_quad_grid(P_world, N, C, U, V / (2.0 * math.pi), timing, mat)

def generate_falling_petal(model, base_pos, fall_speed, flutter_phase, scale, Nu=12, Nv=7):
    """Generate an individual floating/falling Sakura petal for Hanafubuki (flower blizzard)."""
    length = 0.28 * scale
    max_w = 0.20 * scale

    p0 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    p1 = np.array([0.04 * length, 0.25 * length, 0.0], dtype=np.float32)
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

    c_blush = np.array([0.98, 0.76, 0.86], dtype=np.float32)
    c_white = np.array([0.99, 0.96, 0.98], dtype=np.float32)

    for i in range(Nu):
        ui = u[i]
        sin_val = max(0.0, math.sin((ui**0.7) * math.pi))
        w = max_w * sin_val * (1.0 - 0.12 * ui)
        for j in range(Nv):
            vj = v[j]
            cup = 0.22 * (vj**2) * max_w * (1.0 - 0.3 * ui)
            P[i, j] = pos[i] + (vj * w) * N1[i] + cup * N2[i]
            col = (1.0 - ui * 0.4) * c_blush + (ui * 0.4) * c_white
            C[i, j] = col

    # Random initial tumble orientation
    rot = rotation_matrix_axis_angle([0.6, 1.0, 0.4], flutter_phase)
    P_world = np.zeros_like(P)
    for i in range(Nu):
        for j in range(Nv):
            P_world[i, j] = base_pos + P[i, j] @ rot.T

    N = compute_grid_normals(P_world)
    timing = np.array([7.0, 7.0, 7.0, 7.6], dtype=np.float32)
    mat = np.array([0.85, fall_speed, flutter_phase], dtype=np.float32)
    model.add_quad_grid(P_world, N, C, U, (V + 1.0) * 0.5, timing, mat)

def generate_full_sakura_specimen():
    """
    Assemble the complete Prunus Serrulata (Japanese Cherry Blossom) branch:
    - Gnarled bonsai cherry branch with elegant S-curve and bifurcations
    - Multiple blossom clusters (open 5-petaled flowers, half-open blossoms, buds)
    - Slender pedicels connecting flowers to branch nodes
    - Tumbling 3D falling petals (Hanafubuki)
    - Ambient golden pollen bokeh dust
    """
    model = SakuraModel()

    # 1. Main Ancient Branch (Diagonal bonsai s-curve across 3D space)
    # Starts bottom-left, reaches up-right, dipping and sweeping gracefully
    p0 = np.array([-1.5, -0.6, -0.2], dtype=np.float32)
    p1 = np.array([-0.6,  0.1,  0.1], dtype=np.float32)
    p2 = np.array([ 0.4,  0.4, -0.1], dtype=np.float32)
    p3 = np.array([ 1.4,  0.8,  0.2], dtype=np.float32)

    generate_branch(model, p0, p1, p2, p3, r_base=0.075, r_tip=0.035,
                    wire_t0=0.0, wire_t1=2.8, surf_t0=1.0, surf_t1=3.5)

    # 2. Secondary Branch Bifurcation (branching lower-center toward foreground)
    b2_p0 = np.array([-0.2, 0.22, 0.05], dtype=np.float32)
    b2_p1 = np.array([-0.1, 0.05, 0.25], dtype=np.float32)
    b2_p2 = np.array([ 0.1, -0.18, 0.38], dtype=np.float32)
    b2_p3 = np.array([ 0.35, -0.32, 0.48], dtype=np.float32)

    generate_branch(model, b2_p0, b2_p1, b2_p2, b2_p3, r_base=0.038, r_tip=0.020,
                    wire_t0=0.8, wire_t1=3.2, surf_t0=1.8, surf_t1=4.0)

    # 3. Tertiary Branchlet (reaching upwards top-center)
    b3_p0 = np.array([0.25, 0.38, -0.05], dtype=np.float32)
    b3_p1 = np.array([0.15, 0.65,  0.08], dtype=np.float32)
    b3_p2 = np.array([0.30, 0.95,  0.15], dtype=np.float32)
    b3_p3 = np.array([0.45, 1.25,  0.22], dtype=np.float32)

    generate_branch(model, b3_p0, b3_p1, b3_p2, b3_p3, r_base=0.032, r_tip=0.016,
                    wire_t0=1.2, wire_t1=3.6, surf_t0=2.2, surf_t1=4.4)

    # 4. Blossom Clusters (The Spectacular Floral Display)
    # Cluster 1: Center-left hero cluster (faces camera with slight tilt)
    c1_basis1 = rotation_matrix_axis_angle([0.2, 1.0, 0.3], math.radians(15.0)) @ rotation_matrix_axis_angle([1.0, 0.0, 0.0], math.radians(25.0))
    generate_sakura_flower(model, np.array([-0.25, 0.32, 0.28], dtype=np.float32), c1_basis1, 1.15,
                           wire_t0=3.2, wire_t1=5.8, surf_t0=6.5, surf_t1=9.5)

    c1_basis2 = rotation_matrix_axis_angle([-0.3, 1.0, 0.1], math.radians(-25.0)) @ rotation_matrix_axis_angle([1.0, 0.0, 0.0], math.radians(35.0))
    generate_sakura_flower(model, np.array([-0.55, 0.15, 0.22], dtype=np.float32), c1_basis2, 1.05,
                           wire_t0=3.6, wire_t1=6.2, surf_t0=6.8, surf_t1=9.8)

    # Cluster 2: Foreground-right dangling cluster
    c2_basis1 = rotation_matrix_axis_angle([0.1, 1.0, -0.2], math.radians(35.0)) @ rotation_matrix_axis_angle([1.0, 0.0, 0.0], math.radians(18.0))
    generate_sakura_flower(model, np.array([0.28, -0.25, 0.52], dtype=np.float32), c2_basis1, 1.10,
                           wire_t0=4.0, wire_t1=6.6, surf_t0=7.2, surf_t1=10.2)

    c2_basis2 = rotation_matrix_axis_angle([0.4, 0.2, 1.0], math.radians(45.0))
    generate_sakura_flower(model, np.array([0.48, -0.38, 0.45], dtype=np.float32), c2_basis2, 0.95,
                           wire_t0=4.3, wire_t1=6.9, surf_t0=7.5, surf_t1=10.5)

    # Cluster 3: Top-right canopy cluster
    c3_basis1 = rotation_matrix_axis_angle([-0.1, 1.0, 0.4], math.radians(-15.0)) @ rotation_matrix_axis_angle([1.0, 0.0, 0.0], math.radians(30.0))
    generate_sakura_flower(model, np.array([0.38, 1.15, 0.25], dtype=np.float32), c3_basis1, 1.05,
                           wire_t0=4.6, wire_t1=7.2, surf_t0=7.8, surf_t1=10.8)

    c3_basis2 = rotation_matrix_axis_angle([0.3, 1.0, -0.2], math.radians(40.0))
    generate_sakura_flower(model, np.array([0.58, 1.32, 0.18], dtype=np.float32), c3_basis2, 0.90,
                           wire_t0=4.9, wire_t1=7.5, surf_t0=8.1, surf_t1=11.1)

    # Cluster 4: Upper-mid delicate accent flowers
    c4_basis1 = rotation_matrix_axis_angle([0.0, 1.0, 0.0], math.radians(5.0)) @ rotation_matrix_axis_angle([1.0, 0.0, 0.0], math.radians(20.0))
    generate_sakura_flower(model, np.array([0.15, 0.55, 0.12], dtype=np.float32), c4_basis1, 1.00,
                           wire_t0=5.2, wire_t1=7.8, surf_t0=8.4, surf_t1=11.4)

    # 5. Flower Buds (ruby pink swollen buds about to burst)
    generate_sakura_bud(model, np.array([-0.05, 0.42, 0.18], dtype=np.float32),
                        rotation_matrix_axis_angle([0.5, 0.2, 1.0], math.radians(25.0)), 0.85,
                        wire_t0=2.2, wire_t1=4.2, surf_t0=3.2, surf_t1=5.2)

    generate_sakura_bud(model, np.array([0.65, 0.95, 0.28], dtype=np.float32),
                        rotation_matrix_axis_angle([-0.4, 0.3, 1.0], math.radians(-30.0)), 0.78,
                        wire_t0=2.6, wire_t1=4.6, surf_t0=3.6, surf_t1=5.6)

    generate_sakura_bud(model, np.array([0.18, -0.45, 0.42], dtype=np.float32),
                        rotation_matrix_axis_angle([0.2, 0.6, 1.0], math.radians(40.0)), 0.80,
                        wire_t0=3.0, wire_t1=5.0, surf_t0=4.0, surf_t1=6.0)

    # 6. Hanafubuki (Falling Tumbling Petals Swirling in Breeze)
    np.random.seed(108)
    num_falling = 36
    falling_petals = []
    for _ in range(num_falling):
        base_pos = np.array([
            np.random.uniform(-1.5, 1.5),
            np.random.uniform(-1.0, 1.6),
            np.random.uniform(-0.6, 0.8)
        ], dtype=np.float32)
        fall_speed = np.random.uniform(0.20, 0.45)
        swirl_speed = np.random.uniform(1.2, 2.8)
        flutter_phase = np.random.uniform(0.0, 2.0 * math.pi)
        scale = np.random.uniform(0.55, 0.90)
        falling_petals.append((base_pos, fall_speed, swirl_speed, flutter_phase, scale))
        generate_falling_petal(model, base_pos, fall_speed, flutter_phase, scale)
    model.falling_petals = falling_petals

    # 7. Ambient Glowing Golden Spores (Bokeh)
    num_particles = 140
    particles = []
    for _ in range(num_particles):
        pos = np.array([
            np.random.uniform(-1.8, 1.8),
            np.random.uniform(-1.6, 1.8),
            np.random.uniform(-1.2, 1.4)
        ], dtype=np.float32)
        phase = np.random.uniform(0.0, 2.0 * math.pi)
        speed = np.random.uniform(0.4, 1.0)
        radius = np.random.uniform(0.012, 0.038)
        particles.append((pos, phase, speed, radius))
    model.particles = particles

    # Pack mesh vertices
    vertex_data = np.array(model.vertices, dtype=np.float32)
    return vertex_data, model.particles, model.falling_petals
