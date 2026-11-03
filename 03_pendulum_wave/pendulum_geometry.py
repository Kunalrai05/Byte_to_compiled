"""
Geometric formulation & parametric surface generation for the Harmonic Pendulum Wave.
Calculates 24-pendulum mathematical harmonic dispersion, wave ribbons,
suspension frame, and reflective studio environment.
"""

import math
import numpy as np

NUM_PENDULUMS = 24
CYCLE_DURATION = 14.0  # Master cycle in seconds
BASE_CYCLES = 16.0     # Longest pendulum executes exactly 16 oscillations
MAX_AMPLITUDE = math.radians(34.0)
RAIL_Y = 1.35
X_SPAN = 4.8           # Rail width (-2.4 to +2.4)
SPHERE_RADIUS = 0.088

# Spectral chromatic color palette across 24 pendulums (Cyan -> Sapphire -> Violet -> Magenta -> Rose -> Amber -> Gold)
def get_pendulum_colors(num=NUM_PENDULUMS):
    colors = []
    for i in range(num):
        hue = float(i) / float(num - 1)
        r = 0.5 + 0.5 * math.sin(hue * 2.0 * math.pi - 1.2)
        g = 0.5 + 0.5 * math.sin(hue * 2.0 * math.pi + 1.0)
        b = 0.5 + 0.5 * math.sin(hue * 2.0 * math.pi + 3.0)
        col = np.array([r, g, b], dtype=np.float32)
        col = np.clip(col * 1.35, 0.0, 1.0)
        colors.append(col)
    return colors

def get_wave_pattern_info(t, total_duration=CYCLE_DURATION):
    """Classify current harmonic wave pattern for the telemetry HUD."""
    t_mod = math.fmod(t, total_duration)
    frac = t_mod / total_duration

    if frac < 0.03 or frac > 0.97:
        return "COHERENT LINE ALIGNMENT (PERFECT HARMONY)", (255, 255, 255)
    elif frac < 0.18:
        return "TRAVELING TRANSVERSE SINE WAVE", (120, 240, 255)
    elif frac < 0.36:
        return "INTERLACED DOUBLE HELIX WAVES", (255, 140, 220)
    elif frac < 0.54:
        return "TRIPLE HELIX & STANDING WAVE NODES", (255, 215, 100)
    elif frac < 0.78:
        return "PSEUDO-CHAOTIC HARMONIC DISPERSION", (180, 200, 255)
    elif frac < 0.92:
        return "REVERSE COHERENCE RETRIEVAL", (140, 255, 180)
    else:
        return "COHERENT LINE ALIGNMENT (PERFECT HARMONY)", (255, 255, 255)

def calculate_pendulums(t, colors=None):
    """
    Compute 3D position, angle, and wire vectors for all 24 pendulums at time t.
    Returns: list of dicts with pivot, pos, length, theta, color
    """
    if colors is None:
        colors = get_pendulum_colors(NUM_PENDULUMS)

    pendulums = []
    for n in range(NUM_PENDULUMS):
        x_frac = float(n) / float(NUM_PENDULUMS - 1)
        x_pos = -X_SPAN * 0.5 + x_frac * X_SPAN

        # Exact harmonic frequency formula:
        # k_n = BASE_CYCLES + n cycles per CYCLE_DURATION
        omega = 2.0 * math.pi * (BASE_CYCLES + n) / CYCLE_DURATION
        theta = MAX_AMPLITUDE * math.cos(omega * t)

        # Pendulum length: L ~ 1 / omega^2, normalized for aesthetic range
        length_norm = 1.0 - 0.48 * (float(n) / float(NUM_PENDULUMS - 1))
        length = 2.1 * length_norm

        pivot = np.array([x_pos, RAIL_Y, 0.0], dtype=np.float32)
        sphere_y = RAIL_Y - length * math.cos(theta)
        sphere_z = length * math.sin(theta)
        sphere_pos = np.array([x_pos, sphere_y, sphere_z], dtype=np.float32)

        pendulums.append({
            'index': n,
            'pivot': pivot,
            'pos': sphere_pos,
            'length': length,
            'theta': theta,
            'color': colors[n]
        })
    return pendulums

def generate_uv_sphere(center, radius, color, sphere_id, timing, Nu=16, Nv=16):
    """Generate vertex buffer data for a 3D UV sphere with barycentric coordinates."""
    verts = []
    bary_cycle = [
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.0], dtype=np.float32)
    ]
    mat = np.array([0.88, 0.12, sphere_id], dtype=np.float32)

    for i in range(Nu):
        theta0 = math.pi * float(i) / Nu
        theta1 = math.pi * float(i + 1) / Nu
        y0 = math.cos(theta0)
        y1 = math.cos(theta1)
        r0 = math.sin(theta0)
        r1 = math.sin(theta1)

        for j in range(Nv):
            phi0 = 2.0 * math.pi * float(j) / Nv
            phi1 = 2.0 * math.pi * float(j + 1) / Nv

            p00 = center + radius * np.array([r0 * math.cos(phi0), y0, r0 * math.sin(phi0)], dtype=np.float32)
            p10 = center + radius * np.array([r1 * math.cos(phi0), y1, r1 * math.sin(phi0)], dtype=np.float32)
            p11 = center + radius * np.array([r1 * math.cos(phi1), y1, r1 * math.sin(phi1)], dtype=np.float32)
            p01 = center + radius * np.array([r0 * math.cos(phi1), y0, r0 * math.sin(phi1)], dtype=np.float32)

            n00 = (p00 - center) / radius
            n10 = (p10 - center) / radius
            n11 = (p11 - center) / radius
            n01 = (p01 - center) / radius

            uv00 = np.array([float(j)/Nv, float(i)/Nu], dtype=np.float32)
            uv10 = np.array([float(j)/Nv, float(i+1)/Nu], dtype=np.float32)
            uv11 = np.array([float(j+1)/Nv, float(i+1)/Nu], dtype=np.float32)
            uv01 = np.array([float(j+1)/Nv, float(i)/Nu], dtype=np.float32)

            verts.append(np.concatenate([p00, n00, color, bary_cycle[0], uv00, timing, mat]))
            verts.append(np.concatenate([p10, n10, color, bary_cycle[1], uv10, timing, mat]))
            verts.append(np.concatenate([p11, n11, color, bary_cycle[2], uv11, timing, mat]))

            verts.append(np.concatenate([p00, n00, color, bary_cycle[0], uv00, timing, mat]))
            verts.append(np.concatenate([p11, n11, color, bary_cycle[2], uv11, timing, mat]))
            verts.append(np.concatenate([p01, n01, color, bary_cycle[2], uv01, timing, mat]))

    return verts

def generate_cylinder_tube(p0, p1, radius, color, timing, N=8):
    """Generate 3D tube geometry for suspension wire or frame rail."""
    verts = []
    dp = p1 - p0
    length = float(np.linalg.norm(dp))
    if length < 1e-5:
        return verts
    dir_vec = dp / length

    ref = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    if abs(float(np.dot(dir_vec, ref))) > 0.9:
        ref = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    t1 = np.cross(dir_vec, ref)
    t1 /= float(np.linalg.norm(t1))
    t2 = np.cross(dir_vec, t1)

    mat = np.array([0.5, 0.4, 0.0], dtype=np.float32)
    bary_cycle = [
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.0], dtype=np.float32)
    ]

    for i in range(N):
        ang0 = 2.0 * math.pi * float(i) / N
        ang1 = 2.0 * math.pi * float(i + 1) / N

        c0, s0 = math.cos(ang0), math.sin(ang0)
        c1, s1 = math.cos(ang1), math.sin(ang1)

        norm0 = c0 * t1 + s0 * t2
        norm1 = c1 * t1 + s1 * t2

        v0 = p0 + radius * norm0
        v1 = p1 + radius * norm0
        v2 = p1 + radius * norm1
        v3 = p0 + radius * norm1

        uv0 = np.array([float(i)/N, 0.0], dtype=np.float32)
        uv1 = np.array([float(i)/N, 1.0], dtype=np.float32)
        uv2 = np.array([float(i+1)/N, 1.0], dtype=np.float32)
        uv3 = np.array([float(i+1)/N, 0.0], dtype=np.float32)

        verts.append(np.concatenate([v0, norm0, color, bary_cycle[0], uv0, timing, mat]))
        verts.append(np.concatenate([v1, norm0, color, bary_cycle[1], uv1, timing, mat]))
        verts.append(np.concatenate([v2, norm1, color, bary_cycle[2], uv2, timing, mat]))

        verts.append(np.concatenate([v0, norm0, color, bary_cycle[0], uv0, timing, mat]))
        verts.append(np.concatenate([v2, norm1, color, bary_cycle[2], uv2, timing, mat]))
        verts.append(np.concatenate([v3, norm1, color, bary_cycle[2], uv3, timing, mat]))

    return verts

def generate_studio_floor(size=8.0):
    """Generate dark reflective studio floor with subtle cyber grid."""
    verts = []
    p0 = np.array([-size, -1.8, -size], dtype=np.float32)
    p1 = np.array([ size, -1.8, -size], dtype=np.float32)
    p2 = np.array([ size, -1.8,  size], dtype=np.float32)
    p3 = np.array([-size, -1.8,  size], dtype=np.float32)

    norm = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    color = np.array([0.04, 0.06, 0.09], dtype=np.float32)
    timing = np.array([0.0, 1.0, 0.0, 2.0], dtype=np.float32)
    mat = np.array([0.9, 0.05, -1.0], dtype=np.float32) # -1 marks floor

    bary = [
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.0], dtype=np.float32)
    ]

    verts.append(np.concatenate([p0, norm, color, bary[0], np.array([0.0, 0.0], dtype=np.float32), timing, mat]))
    verts.append(np.concatenate([p1, norm, color, bary[1], np.array([1.0, 0.0], dtype=np.float32), timing, mat]))
    verts.append(np.concatenate([p2, norm, color, bary[2], np.array([1.0, 1.0], dtype=np.float32), timing, mat]))

    verts.append(np.concatenate([p0, norm, color, bary[0], np.array([0.0, 0.0], dtype=np.float32), timing, mat]))
    verts.append(np.concatenate([p2, norm, color, bary[2], np.array([1.0, 1.0], dtype=np.float32), timing, mat]))
    verts.append(np.concatenate([p3, norm, color, bary[2], np.array([0.0, 1.0], dtype=np.float32), timing, mat]))
    return verts

def generate_wave_ribbon(pendulums, width=0.035, alpha=0.85):
    """
    Generate glowing 3D ribbon connecting all spheres along the wave.
    Traces the continuous harmonic curve in real-time.
    """
    ribbon_verts = []
    num = len(pendulums)
    if num < 2:
        return np.array([], dtype=np.float32)

    for i in range(num - 1):
        p0 = pendulums[i]['pos']
        p1 = pendulums[i + 1]['pos']
        c0 = pendulums[i]['color']
        c1 = pendulums[i + 1]['color']

        v0_top = p0 + np.array([0.0,  width, 0.0], dtype=np.float32)
        v0_bot = p0 + np.array([0.0, -width, 0.0], dtype=np.float32)
        v1_top = p1 + np.array([0.0,  width, 0.0], dtype=np.float32)
        v1_bot = p1 + np.array([0.0, -width, 0.0], dtype=np.float32)

        # Triangle 1
        ribbon_verts.extend([v0_top[0], v0_top[1], v0_top[2], c0[0], c0[1], c0[2], alpha])
        ribbon_verts.extend([v0_bot[0], v0_bot[1], v0_bot[2], c0[0], c0[1], c0[2], alpha])
        ribbon_verts.extend([v1_top[0], v1_top[1], v1_top[2], c1[0], c1[1], c1[2], alpha])

        # Triangle 2
        ribbon_verts.extend([v0_bot[0], v0_bot[1], v0_bot[2], c0[0], c0[1], c0[2], alpha])
        ribbon_verts.extend([v1_bot[0], v1_bot[1], v1_bot[2], c1[0], c1[1], c1[2], alpha])
        ribbon_verts.extend([v1_top[0], v1_top[1], v1_top[2], c1[0], c1[1], c1[2], alpha])

    return np.array(ribbon_verts, dtype=np.float32)
