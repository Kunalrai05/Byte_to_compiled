"""
Procedural 3D geometry generator for Lilium Orientalis (Oriental Lily).
Generates parametric surfaces for stems, lanceolate leaves, blooming petals (tepals),
curved filaments with anthers, and pistil with 3-lobed stigma.
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

class BotanicalVertex:
    __slots__ = ('pos', 'normal', 'color', 'bary', 'uv', 'timing', 'mat')
    def __init__(self, pos, normal, color, bary, uv, timing, mat):
        self.pos = pos
        self.normal = normal
        self.color = color
        self.bary = bary
        self.uv = uv
        self.timing = timing
        self.mat = mat

class BotanicalModel:
    def __init__(self):
        self.vertices = [] # List of tuples / flat arrays
        self.particles = [] # Floating spore/pollen particles

    def add_quad_grid(self, P, N, C, U, V, timing, mat, wire_step_u=1, wire_step_v=1):
        """
        Convert a 2D grid of 3D points P(Nu, Nv, 3) into indexed triangles
        with barycentric wireframe coordinates and custom timings.
        """
        Nu, Nv, _ = P.shape
        bary_cycle = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        for i in range(Nu - 1):
            for j in range(Nv - 1):
                # Quad vertices
                p00 = P[i, j]
                p10 = P[i + 1, j]
                p11 = P[i + 1, j + 1]
                p01 = P[i, j + 1]

                n00 = N[i, j]
                n10 = N[i + 1, j]
                n11 = N[i + 1, j + 1]
                n01 = N[i, j + 1]

                c00 = C[i, j]
                c10 = C[i + 1, j]
                c11 = C[i + 1, j + 1]
                c01 = C[i, j + 1]

                u00 = np.array([U[i, j], V[i, j]], dtype=np.float32)
                u10 = np.array([U[i + 1, j], V[i + 1, j]], dtype=np.float32)
                u11 = np.array([U[i + 1, j + 1], V[i + 1, j + 1]], dtype=np.float32)
                u01 = np.array([U[i, j + 1], V[i, j + 1]], dtype=np.float32)

                # Triangle 1: (p00, p10, p11)
                self.vertices.append(np.concatenate([p00, n00, c00, bary_cycle[0], u00, timing, mat]))
                self.vertices.append(np.concatenate([p10, n10, c10, bary_cycle[1], u10, timing, mat]))
                self.vertices.append(np.concatenate([p11, n11, c11, bary_cycle[2], u11, timing, mat]))

                # Triangle 2: (p00, p11, p01)
                self.vertices.append(np.concatenate([p00, n00, c00, bary_cycle[0], u00, timing, mat]))
                self.vertices.append(np.concatenate([p11, n11, c11, bary_cycle[1], u11, timing, mat]))
                self.vertices.append(np.concatenate([p01, n01, c01, bary_cycle[2], u01, timing, mat]))

def compute_grid_normals(P):
    """Compute smooth surface normals for a regular (Nu, Nv, 3) parametric grid."""
    Nu, Nv, _ = P.shape
    # Tangents in u
    dP_du = np.zeros_like(P)
    dP_du[1:-1] = (P[2:] - P[:-2]) * 0.5
    dP_du[0] = P[1] - P[0]
    dP_du[-1] = P[-1] - P[-2]

    # Tangents in v
    dP_dv = np.zeros_like(P)
    dP_dv[:, 1:-1] = (P[:, 2:] - P[:, :-2]) * 0.5
    dP_dv[:, 0] = P[:, 1] - P[:, 0]
    dP_dv[:, -1] = P[:, -1] - P[:, -2]

    normals = np.cross(dP_du, dP_dv)
    return normalize_v3(normals)

def generate_stem(model, p0, p1, p2, p3, r_base, r_tip, wire_t0, wire_t1, surf_t0, surf_t1, Nu=36, Nv=12):
    """Generate a curved botanical stem tube using cubic Bezier & Bishop frame."""
    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(0.0, 2.0 * math.pi, Nv, endpoint=False, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    pos, tan = eval_cubic_bezier(p0, p1, p2, p3, u)
    T = normalize_v3(tan)
    N1, N2 = compute_bishop_frame(T)

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    c_base = np.array([0.08, 0.38, 0.14], dtype=np.float32)
    c_tip = np.array([0.16, 0.55, 0.22], dtype=np.float32)

    for i in range(Nu):
        radius = r_base + (r_tip - r_base) * u[i]
        # subtle longitudinal ridges on stem
        for j in range(Nv):
            r_j = radius * (1.0 + 0.05 * math.cos(4.0 * v[j]))
            P[i, j] = pos[i] + r_j * (math.cos(v[j]) * N1[i] + math.sin(v[j]) * N2[i])
            C[i, j] = (1.0 - u[i]) * c_base + u[i] * c_tip

    N = compute_grid_normals(P)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat = np.array([0.35, 0.40, 25.0], dtype=np.float32) # sss, spec, shininess
    model.add_quad_grid(P, N, C, U, V / (2.0 * math.pi), timing, mat)

def generate_leaf(model, attach_pt, attach_tan, length, max_width, wire_t0, wire_t1, surf_t0, surf_t1, Nu=20, Nv=9):
    """
    Generate lanceolate lily leaf arching gracefully from stem attachment point.
    """
    # Create leaf curve control points in local frame
    p0 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    p1 = np.array([0.35 * length, 0.12 * length, 0.0], dtype=np.float32)
    p2 = np.array([0.75 * length, 0.05 * length, 0.0], dtype=np.float32)
    p3 = np.array([1.00 * length, -0.22 * length, 0.0], dtype=np.float32) # drooping tip

    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(-1.0, 1.0, Nv, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    pos, tan = eval_cubic_bezier(p0, p1, p2, p3, u)
    T = normalize_v3(tan)
    N1, N2 = compute_bishop_frame(T)

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    c_leaf_inner = np.array([0.12, 0.52, 0.20], dtype=np.float32)
    c_leaf_outer = np.array([0.18, 0.65, 0.26], dtype=np.float32)

    for i in range(Nu):
        # Lanceolate profile: narrow base, widest at ~0.35, sharp tip
        ui = u[i]
        sin_val = max(0.0, math.sin(ui * math.pi))
        w = max_width * (sin_val**0.7) * (1.0 - 0.25 * ui)
        for j in range(Nv):
            vj = v[j]
            # V-fold cross section
            cup = 0.25 * (vj**2) * max_width * (1.0 - ui)
            P[i, j] = pos[i] + (vj * w) * N1[i] + cup * N2[i]
            
            # Subtly lighter near edges
            edge_fac = abs(vj)
            C[i, j] = (1.0 - edge_fac * 0.3) * c_leaf_inner + (edge_fac * 0.3) * c_leaf_outer

    # Align leaf with attach_tan
    leaf_dir = normalize_v3(attach_tan)
    up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    side = normalize_v3(np.cross(up, leaf_dir))
    norm_up = np.cross(leaf_dir, side)
    R_basis = np.column_stack([leaf_dir, norm_up, side])

    P_world = np.zeros_like(P)
    for i in range(Nu):
        for j in range(Nv):
            P_world[i, j] = attach_pt + P[i, j] @ R_basis.T

    N = compute_grid_normals(P_world)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat = np.array([0.45, 0.55, 30.0], dtype=np.float32)
    model.add_quad_grid(P_world, N, C, U, (V + 1.0) * 0.5, timing, mat)

def generate_lily_petal(model, center, basis, scale, angle_deg, is_inner, wire_t0, wire_t1, surf_t0, surf_t1, Nu=24, Nv=11):
    """
    Generate an individual Lily petal (tepal) with realistic recurve,
    fluted channel, ruffled edges, and papillae dots.
    """
    # Inner petals are broader and softer, outer are slightly slimmer
    max_w = 0.42 * scale if is_inner else 0.34 * scale
    length = 1.0 * scale

    # Spine Bezier curve: flower bud -> open bloom recurve
    p0 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    p1 = np.array([0.18 * length, 0.45 * length, 0.0], dtype=np.float32)
    p2 = np.array([0.55 * length, 0.78 * length, 0.0], dtype=np.float32)
    p3 = np.array([0.88 * length, 0.50 * length, 0.0], dtype=np.float32) # elegant backward recurve!

    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(-1.0, 1.0, Nv, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    pos, tan = eval_cubic_bezier(p0, p1, p2, p3, u)
    T = normalize_v3(tan)
    N1, N2 = compute_bishop_frame(T)

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    # Color gradients:
    # Throat: soft lime green/cream [0.85, 0.95, 0.70]
    # Mid-body: rich crimson/magenta [0.88, 0.16, 0.45]
    # Edge/Tip: pure pristine white [0.98, 0.98, 0.98]
    c_throat = np.array([0.70, 0.90, 0.50], dtype=np.float32)
    c_magenta = np.array([0.90, 0.08, 0.44], dtype=np.float32)
    c_white = np.array([0.98, 0.96, 0.97], dtype=np.float32)

    for i in range(Nu):
        ui = u[i]
        # Characteristic Lily petal silhouette
        # Starts narrow at receptacle, balloons out at 40-50% length, tapers to pointy tip
        sin_pet = max(0.0, math.sin((ui**0.75) * math.pi))
        w = max_w * sin_pet * (1.0 - 0.22 * ui)

        # Edge waves / ruffling: Oriental lilies have gentle undulating waves on petal borders
        edge_wave_amp = 0.04 * scale * (ui**1.2) * (1.0 - ui * 0.3)

        for j in range(Nv):
            vj = v[j]
            # Curvature across petal: deep center furrow (midrib), sides curling upward
            furrow = 0.18 * (vj**2) * max_w * (1.0 - 0.4 * ui)
            wave = edge_wave_amp * math.sin(ui * 18.0) * (abs(vj)**1.5)

            # Local displacement
            P[i, j] = pos[i] + (vj * w) * N1[i] + (furrow + wave) * N2[i]

            # Pigment calculation:
            # Distance from center rib (vj) and distance along petal (ui)
            rib_dist = abs(vj)
            
            # Throat fade
            throat_mix = smoothstep(0.0, 0.25, ui)
            # Magenta flush along midrib
            magenta_band = math.exp(-(rib_dist * 2.4)**2) * smoothstep(0.08, 0.32, ui) * (1.0 - smoothstep(0.78, 1.0, ui))
            
            col = (1.0 - throat_mix) * c_throat + throat_mix * c_white
            col = (1.0 - magenta_band * 0.92) * col + (magenta_band * 0.92) * c_magenta
            C[i, j] = col

    # Rotate petal into radial position around flower axis
    rot_rad = math.radians(angle_deg)
    R_z = rotation_matrix_y(rot_rad)

    P_rot = np.zeros_like(P)
    for i in range(Nu):
        for j in range(Nv):
            P_rot[i, j] = P[i, j] @ R_z.T

    # Transform to world space with flower basis
    P_world = np.zeros_like(P_rot)
    for i in range(Nu):
        for j in range(Nv):
            P_world[i, j] = center + P_rot[i, j] @ basis.T

    N = compute_grid_normals(P_world)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    # High subsurface scattering (SSS) for translucent petals
    mat = np.array([0.75, 0.35, 18.0], dtype=np.float32)
    model.add_quad_grid(P_world, N, C, U, (V + 1.0) * 0.5, timing, mat)

def generate_stamens_and_pistil(model, center, basis, scale, wire_t0, wire_t1, surf_t0, surf_t1):
    """
    Generate the 6 curved stamens with golden-brown anthers and the central pistil.
    """
    # 1. Central Pistil (female organ)
    # Longer style that gently arches forward
    p0 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    p1 = np.array([0.02 * scale, 0.40 * scale, 0.02 * scale], dtype=np.float32)
    p2 = np.array([0.06 * scale, 0.75 * scale, 0.08 * scale], dtype=np.float32)
    p3 = np.array([0.08 * scale, 0.95 * scale, 0.12 * scale], dtype=np.float32)

    Nu_p, Nv_p = 20, 8
    up = np.linspace(0.0, 1.0, Nu_p, dtype=np.float32)
    vp = np.linspace(0.0, 2.0 * math.pi, Nv_p, endpoint=False, dtype=np.float32)
    Up, Vp = np.meshgrid(up, vp, indexing='ij')

    ppos, ptan = eval_cubic_bezier(p0, p1, p2, p3, up)
    Tp = normalize_v3(ptan)
    Np1, Np2 = compute_bishop_frame(Tp)

    P_pistil = np.zeros((Nu_p, Nv_p, 3), dtype=np.float32)
    C_pistil = np.zeros((Nu_p, Nv_p, 3), dtype=np.float32)

    c_style = np.array([0.45, 0.82, 0.38], dtype=np.float32)
    c_stigma = np.array([0.55, 0.25, 0.35], dtype=np.float32) # purplish 3-lobed stigma

    for i in range(Nu_p):
        is_stigma = up[i] > 0.88
        col = c_stigma if is_stigma else c_style
        for j in range(Nv_p):
            rp = 0.016 * scale if not is_stigma else 0.038 * scale * (1.0 + 0.25 * math.cos(3.0 * vp[j]))
            P_pistil[i, j] = ppos[i] + rp * (math.cos(vp[j]) * Np1[i] + math.sin(vp[j]) * Np2[i])
            C_pistil[i, j] = col

    P_pistil_world = center + P_pistil @ basis.T
    N_pistil = compute_grid_normals(P_pistil_world)
    timing_p = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat_p = np.array([0.4, 0.3, 20.0], dtype=np.float32)
    model.add_quad_grid(P_pistil_world, N_pistil, C_pistil, Up, Vp / (2.0 * math.pi), timing_p, mat_p)

    # 2. 6 Filaments with Anthers (male organs)
    for k in range(6):
        st_delay = 0.08 * k
        angle = k * (2.0 * math.pi / 6.0) + 0.52
        ca = math.cos(angle)
        sa = math.sin(angle)

        # Filaments flare outward from flower center
        flare = 0.38 * scale
        h_tip = 0.78 * scale

        fp0 = np.array([0.02 * scale * ca, 0.02 * scale, 0.02 * scale * sa], dtype=np.float32)
        fp1 = np.array([0.08 * scale * ca, 0.32 * scale, 0.08 * scale * sa], dtype=np.float32)
        fp2 = np.array([0.18 * scale * ca, 0.62 * scale, 0.18 * scale * sa], dtype=np.float32)
        fp3 = np.array([flare * ca, h_tip, flare * sa], dtype=np.float32)

        Nu_f, Nv_f = 16, 6
        uf = np.linspace(0.0, 1.0, Nu_f, dtype=np.float32)
        vf = np.linspace(0.0, 2.0 * math.pi, Nv_f, endpoint=False, dtype=np.float32)
        Uf, Vf = np.meshgrid(uf, vf, indexing='ij')

        fpos, ftan = eval_cubic_bezier(fp0, fp1, fp2, fp3, uf)
        Tf = normalize_v3(ftan)
        N1f, N2f = compute_bishop_frame(Tf)

        P_fil = np.zeros((Nu_f, Nv_f, 3), dtype=np.float32)
        C_fil = np.zeros((Nu_f, Nv_f, 3), dtype=np.float32)
        c_fil_base = np.array([0.55, 0.85, 0.38], dtype=np.float32)
        c_fil_tip = np.array([0.92, 0.95, 0.88], dtype=np.float32)

        for i in range(Nu_f):
            rf = scale * 0.009 * (1.0 - 0.35 * uf[i])
            col = (1.0 - uf[i]) * c_fil_base + uf[i] * c_fil_tip
            for j in range(Nv_f):
                P_fil[i, j] = fpos[i] + rf * (math.cos(vf[j]) * N1f[i] + math.sin(vf[j]) * N2f[i])
                C_fil[i, j] = col

        P_fil_world = center + P_fil @ basis.T
        N_fil = compute_grid_normals(P_fil_world)
        timing_f = np.array([wire_t0 + st_delay, wire_t1 + st_delay, surf_t0 + st_delay, surf_t1 + st_delay], dtype=np.float32)
        mat_f = np.array([0.3, 0.25, 20.0], dtype=np.float32)
        model.add_quad_grid(P_fil_world, N_fil, C_fil, Uf, Vf / (2.0 * math.pi), timing_f, mat_f)

        # Anther perched at tip (elongated ellipsoid perpendicular to filament)
        anther_center = fp3
        anther_len = 0.09 * scale
        anther_r = 0.024 * scale

        Nu_a, Nv_a = 8, 8
        ua = np.linspace(-1.0, 1.0, Nu_a, dtype=np.float32)
        va = np.linspace(0.0, 2.0 * math.pi, Nv_a, endpoint=False, dtype=np.float32)
        Ua, Va = np.meshgrid(ua, va, indexing='ij')

        P_anther = np.zeros((Nu_a, Nv_a, 3), dtype=np.float32)
        C_anther = np.zeros((Nu_a, Nv_a, 3), dtype=np.float32)
        c_pollen = np.array([0.78, 0.38, 0.12], dtype=np.float32) # Cinnamon golden-brown pollen

        # Anther orientation perpendicular to filament
        side_axis = normalize_v3(np.cross(Tf[-1], np.array([0.0, 1.0, 0.0], dtype=np.float32)))
        up_axis = np.cross(Tf[-1], side_axis)

        for i in range(Nu_a):
            u_val = ua[i]
            r_val = anther_r * math.sqrt(max(0.0, 1.0 - u_val**2))
            for j in range(Nv_a):
                disp = (u_val * anther_len * 0.5) * side_axis + \
                       (r_val * math.cos(va[j])) * Tf[-1] + \
                       (r_val * math.sin(va[j])) * up_axis
                P_anther[i, j] = anther_center + disp
                C_anther[i, j] = c_pollen

        P_anther_world = center + P_anther @ basis.T
        N_anther = compute_grid_normals(P_anther_world)
        model.add_quad_grid(P_anther_world, N_anther, C_anther, (Ua + 1.0) * 0.5, Va / (2.0 * math.pi), timing_f, mat_f)

def generate_bud(model, center, basis, scale, wire_t0, wire_t1, surf_t0, surf_t1):
    """Generate an unopened swollen Lily flower bud."""
    Nu, Nv = 18, 10
    u = np.linspace(0.0, 1.0, Nu, dtype=np.float32)
    v = np.linspace(0.0, 2.0 * math.pi, Nv, endpoint=False, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing='ij')

    P = np.zeros((Nu, Nv, 3), dtype=np.float32)
    C = np.zeros((Nu, Nv, 3), dtype=np.float32)

    c_base = np.array([0.15, 0.55, 0.22], dtype=np.float32)
    c_tip_pink = np.array([0.88, 0.32, 0.55], dtype=np.float32)

    length = 0.55 * scale
    max_r = 0.12 * scale

    for i in range(Nu):
        ui = u[i]
        # Tear-drop / spindle shape
        r = max_r * math.sin(ui**0.6 * math.pi)
        y = ui * length
        col = (1.0 - ui) * c_base + ui * c_tip_pink
        for j in range(Nv):
            # 3 petal seams on bud
            r_seam = r * (1.0 + 0.12 * math.cos(3.0 * v[j]))
            P[i, j] = np.array([r_seam * math.cos(v[j]), y, r_seam * math.sin(v[j])], dtype=np.float32)
            C[i, j] = col

    P_world = center + P @ basis.T
    N = compute_grid_normals(P_world)
    timing = np.array([wire_t0, wire_t1, surf_t0, surf_t1], dtype=np.float32)
    mat = np.array([0.45, 0.40, 22.0], dtype=np.float32)
    model.add_quad_grid(P_world, N, C, U, V / (2.0 * math.pi), timing, mat)

def generate_full_botanical_specimen():
    """
    Assemble the complete multi-blossom Lilium Orientalis specimen:
    - Main sturdy stem with natural gentle sway
    - Alternating lanceolate foliage leaves
    - 3 large showy blooms at staggered heights & angles
    - 2 unopened buds crowning the apex
    - Ambient 3D floating pollen spores
    """
    model = BotanicalModel()

    # Main stem curve
    p0 = np.array([0.0, -1.8, 0.0], dtype=np.float32)
    p1 = np.array([0.04, -0.6, 0.02], dtype=np.float32)
    p2 = np.array([-0.05, 0.6, -0.03], dtype=np.float32)
    p3 = np.array([0.02, 1.6, 0.0], dtype=np.float32)

    # Stem growth: Stage 1 (0.0s to 3.0s)
    generate_stem(model, p0, p1, p2, p3, r_base=0.055, r_tip=0.032,
                  wire_t0=0.0, wire_t1=2.8, surf_t0=1.0, surf_t1=3.5)

    # Leaves along main stem (spiraling arrangement)
    leaf_configs = [
        # (height_y, angle_deg, length, width, wire_t0)
        (-1.4,   20.0, 0.75, 0.16, 0.4),
        (-1.1,  150.0, 0.82, 0.17, 0.7),
        (-0.8,  270.0, 0.88, 0.18, 1.0),
        (-0.5,   60.0, 0.85, 0.17, 1.3),
        (-0.2,  190.0, 0.80, 0.16, 1.6),
        ( 0.1,  310.0, 0.76, 0.15, 1.9),
        ( 0.4,   90.0, 0.70, 0.14, 2.2),
        ( 0.7,  220.0, 0.65, 0.13, 2.5),
        ( 1.0,  340.0, 0.58, 0.12, 2.8),
    ]

    for y_pos, angle, l_len, l_w, t0 in leaf_configs:
        rad = math.radians(angle)
        attach = np.array([0.04 * math.cos(rad), y_pos, 0.04 * math.sin(rad)], dtype=np.float32)
        attach_tan = np.array([math.cos(rad), 0.35, math.sin(rad)], dtype=np.float32)
        generate_leaf(model, attach, attach_tan, l_len, l_w,
                      wire_t0=t0, wire_t1=t0 + 1.6, surf_t0=t0 + 0.8, surf_t1=t0 + 2.2)

    # 3 Blooming Lilies:
    # Flower 1: Top-left facing (blooms first in Stage 2)
    basis1 = rotation_matrix_axis_angle([0.3, 1.0, 0.2], math.radians(-35.0)) @ rotation_matrix_axis_angle([1.0, 0.0, 0.0], math.radians(30.0))
    center1 = np.array([-0.38, 0.55, 0.25], dtype=np.float32)

    # Flower 2: Center-right facing
    basis2 = rotation_matrix_axis_angle([-0.2, 1.0, 0.4], math.radians(45.0)) @ rotation_matrix_axis_angle([1.0, 0.0, 0.0], math.radians(25.0))
    center2 = np.array([0.35, 0.30, 0.18], dtype=np.float32)

    # Flower 3: Lower-center facing front
    basis3 = rotation_matrix_axis_angle([0.0, 1.0, 0.0], math.radians(10.0)) @ rotation_matrix_axis_angle([1.0, 0.0, 0.0], math.radians(42.0))
    center3 = np.array([-0.05, -0.15, 0.40], dtype=np.float32)

    flower_specs = [
        (center1, basis1, 0.95, 3.2, 5.8, 6.5, 9.5),
        (center2, basis2, 0.90, 3.8, 6.4, 7.0, 10.0),
        (center3, basis3, 1.02, 4.4, 7.0, 7.6, 10.6),
    ]

    for center, basis, scale, w_t0, w_t1, s_t0, s_t1 in flower_specs:
        # 6 Tepals (3 inner alternating with 3 outer)
        for p_idx in range(6):
            is_inner = (p_idx % 2 == 0)
            angle_deg = p_idx * 60.0
            p_delay = 0.08 * p_idx
            generate_lily_petal(model, center, basis, scale, angle_deg, is_inner,
                                wire_t0=w_t0 + p_delay, wire_t1=w_t1 + p_delay,
                                surf_t0=s_t0 + p_delay, surf_t1=s_t1 + p_delay)

        # Stamens and Pistil
        generate_stamens_and_pistil(model, center, basis, scale,
                                    wire_t0=w_t0 + 0.6, wire_t1=w_t1 + 0.6,
                                    surf_t0=s_t0 + 0.6, surf_t1=s_t1 + 0.6)

    # 2 Unopened Buds at top
    bud_basis1 = rotation_matrix_axis_angle([0.3, 0.1, 1.0], math.radians(20.0))
    generate_bud(model, np.array([-0.12, 1.25, -0.05], dtype=np.float32), bud_basis1, 0.85,
                 wire_t0=2.2, wire_t1=4.0, surf_t0=3.2, surf_t1=5.0)

    bud_basis2 = rotation_matrix_axis_angle([-0.4, 0.2, 1.0], math.radians(-25.0))
    generate_bud(model, np.array([0.15, 1.45, 0.02], dtype=np.float32), bud_basis2, 0.78,
                 wire_t0=2.5, wire_t1=4.3, surf_t0=3.5, surf_t1=5.3)

    # 3D Floating Pollen / Spore Particles (Bokeh effect)
    np.random.seed(42)
    num_particles = 120
    particles = []
    for _ in range(num_particles):
        pos = np.array([
            np.random.uniform(-1.2, 1.2),
            np.random.uniform(-1.5, 1.8),
            np.random.uniform(-1.0, 1.2)
        ], dtype=np.float32)
        phase = np.random.uniform(0.0, 2.0 * math.pi)
        speed = np.random.uniform(0.3, 0.9)
        radius = np.random.uniform(0.012, 0.035)
        particles.append((pos, phase, speed, radius))
    model.particles = particles

    # Pack vertices into contiguous numpy array
    vertex_data = np.array(model.vertices, dtype=np.float32)
    return vertex_data, model.particles
