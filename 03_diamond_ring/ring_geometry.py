"""
Parametric 3D Geometry for the Diamond Ring with Bottom-to-Top Growth Coordinates.
Generates:
1. Torus Ring Band with normalized bottom-to-top growth coordinates g in [0.00, 0.55].
2. 4 Platinum Prongs with growth coordinates g in [0.55, 0.75].
3. Brilliant-Cut Diamond Gemstone with growth coordinates g in [0.75, 1.00].
4. Studio Floor Plane for ground reflections.
"""

import numpy as np

TAU = 2.0 * np.pi
R_BAND = 1.02       # Major radius of the ring band
R_TUBE_X = 0.14     # Minor radius (width along Z axis)
R_TUBE_Y = 0.16     # Minor radius (radial height profile)

TABLE_Y = 1.56      # Flat top table facet
TABLE_R = 0.28      # Table radius
GIRDLE_Y = 1.34     # Diamond girdle (widest perimeter)
GIRDLE_R = 0.46     # Diamond girdle radius
CULET_Y = 1.06      # Bottom culet point


def create_vert(pos, norm, col, uv, growth, mat_attr):
    """
    Format standard vertex:
    pos(3f) norm(3f) col(3f) uv(2f) growth(1f) mat(3f) = 15 floats
    """
    return [
        pos[0], pos[1], pos[2],
        norm[0], norm[1], norm[2],
        col[0], col[1], col[2],
        uv[0], uv[1],
        growth,
        mat_attr[0], mat_attr[1], mat_attr[2]
    ]


def add_quad(verts, p0, p1, p2, p3, n0, n1, n2, n3, col, uv_rect, g0, g1, g2, g3, mat_attr):
    """Add a quad as two CCW triangles with per-vertex growth coordinates."""
    u0, v0, u1, v1 = uv_rect
    v_a = create_vert(p0, n0, col, [u0, v0], g0, mat_attr)
    v_b = create_vert(p1, n1, col, [u1, v0], g1, mat_attr)
    v_c = create_vert(p2, n2, col, [u1, v1], g2, mat_attr)
    v_d = create_vert(p3, n3, col, [u0, v1], g3, mat_attr)

    verts.extend(v_a); verts.extend(v_b); verts.extend(v_c)
    verts.extend(v_a); verts.extend(v_c); verts.extend(v_d)


def generate_ring_band(u_segs=100, v_segs=32):
    """
    Generate 3D Torus Ring Band standing upright in the X-Y plane.
    Bottom of band is at Y = -R_BAND (angle -pi/2), top is at Y = +R_BAND (angle +pi/2).
    Growth parameter g is mapped from 0.0 at the bottom to 0.55 at the top!
    """
    verts = []
    col_metal = [0.88, 0.91, 0.96] # Platinum / White Gold
    mat_metal = [0.0, 0.12, 0.95]  # [mat_id=0, roughness=0.12, metallic=0.95]

    # u: angle around the ring circle (starts at bottom -pi/2 and goes around)
    # v: angle around the tube cross-section
    u_vals = np.linspace(-np.pi * 0.5, np.pi * 1.5, u_segs, endpoint=False)
    v_vals = np.linspace(0.0, TAU, v_segs, endpoint=False)

    for i in range(u_segs):
        i_next = (i + 1) % u_segs
        u0, u1 = u_vals[i], u_vals[i_next]

        # Calculate growth progress g from bottom (Y = -R_BAND) to top (Y = +R_BAND):
        # Angle distance from bottom (-pi/2) symmetrically up both left & right sides
        angle_dist0 = abs(u0 - (-np.pi * 0.5))
        if angle_dist0 > np.pi:
            angle_dist0 = TAU - angle_dist0
        g0 = (angle_dist0 / np.pi) * 0.55

        angle_dist1 = abs(u1 - (-np.pi * 0.5))
        if angle_dist1 > np.pi:
            angle_dist1 = TAU - angle_dist1
        g1 = (angle_dist1 / np.pi) * 0.55

        cos_u0, sin_u0 = np.cos(u0), np.sin(u0)
        cos_u1, sin_u1 = np.cos(u1), np.sin(u1)

        for j in range(v_segs):
            j_next = (j + 1) % v_segs
            v0, v1 = v_vals[j], v_vals[j_next]

            cos_v0, sin_v0 = np.cos(v0), np.sin(v0)
            cos_v1, sin_v1 = np.cos(v1), np.sin(v1)

            # Positions
            p00 = [(R_BAND + R_TUBE_Y * cos_v0) * cos_u0, (R_BAND + R_TUBE_Y * cos_v0) * sin_u0, R_TUBE_X * sin_v0]
            p10 = [(R_BAND + R_TUBE_Y * cos_v0) * cos_u1, (R_BAND + R_TUBE_Y * cos_v0) * sin_u1, R_TUBE_X * sin_v0]
            p11 = [(R_BAND + R_TUBE_Y * cos_v1) * cos_u1, (R_BAND + R_TUBE_Y * cos_v1) * sin_u1, R_TUBE_X * sin_v1]
            p01 = [(R_BAND + R_TUBE_Y * cos_v1) * cos_u0, (R_BAND + R_TUBE_Y * cos_v1) * sin_u0, R_TUBE_X * sin_v1]

            # Normals
            n00 = [cos_v0 * cos_u0, cos_v0 * sin_u0, sin_v0]
            n10 = [cos_v0 * cos_u1, cos_v0 * sin_u1, sin_v0]
            n11 = [cos_v1 * cos_u1, cos_v1 * sin_u1, sin_v1]
            n01 = [cos_v1 * cos_u0, cos_v1 * sin_u0, sin_v1]

            add_quad(verts, p00, p10, p11, p01, n00, n10, n11, n01, col_metal,
                     [0.0, 0.0, 1.0, 1.0], g0, g1, g1, g0, mat_metal)

    return verts


def generate_prongs(num_steps=24, radial_segs=12):
    """
    Generate 4 vertical curved platinum prongs.
    Growth parameter g maps from 0.55 (base on band) to 0.75 (tips at girdle).
    """
    verts = []
    col_metal = [0.90, 0.93, 0.98]
    mat_metal = [0.0, 0.10, 0.95]
    prong_radius = 0.030

    for i in range(4):
        a = TAU * (i + 0.5) / 4.0
        cos_a, sin_a = np.cos(a), np.sin(a)

        base = np.array([0.10 * cos_a, R_BAND + 0.02, 0.10 * sin_a], dtype=np.float32)
        tip = np.array([(GIRDLE_R + 0.022) * cos_a, GIRDLE_Y + 0.08, (GIRDLE_R + 0.022) * sin_a], dtype=np.float32)

        axis = tip - base
        axis_len = np.linalg.norm(axis)
        d = axis / axis_len

        perp1 = np.cross(d, [1.0, 0.0, 0.0]) if abs(d[0]) < 0.8 else np.cross(d, [0.0, 1.0, 0.0])
        perp1 /= np.linalg.norm(perp1)
        perp2 = np.cross(d, perp1)

        u_steps = np.linspace(0.0, 1.0, num_steps)
        phi_steps = np.linspace(0.0, TAU, radial_segs, endpoint=False)

        for step in range(num_steps - 1):
            u0, u1 = u_steps[step], u_steps[step + 1]
            g0 = 0.55 + u0 * 0.20
            g1 = 0.55 + u1 * 0.20

            c0 = base + u0 * (tip - base) + perp1 * (np.sin(u0 * np.pi) * 0.028)
            c1 = base + u1 * (tip - base) + perp1 * (np.sin(u1 * np.pi) * 0.028)

            for s in range(radial_segs):
                s_next = (s + 1) % radial_segs
                p0, p1 = phi_steps[s], phi_steps[s_next]

                cp0, sp0 = np.cos(p0), np.sin(p0)
                cp1, sp1 = np.cos(p1), np.sin(p1)

                r_off0 = (perp1 * cp0 + perp2 * sp0) * prong_radius
                r_off1 = (perp1 * cp1 + perp2 * sp1) * prong_radius

                pt00 = c0 + r_off0; n00 = perp1 * cp0 + perp2 * sp0
                pt10 = c0 + r_off1; n10 = perp1 * cp1 + perp2 * sp1
                pt11 = c1 + r_off1; n11 = perp1 * cp1 + perp2 * sp1
                pt01 = c1 + r_off0; n01 = perp1 * cp0 + perp2 * sp0

                add_quad(verts, pt00, pt10, pt11, pt01, n00, n10, n11, n01, col_metal,
                         [0.0, 0.0, 1.0, 1.0], g0, g0, g1, g1, mat_metal)

    return verts


def generate_diamond_gem(num_facets=24):
    """
    Generate Brilliant-Cut Diamond Gemstone mesh:
    1. Pavilion facets (culet Y=1.06 up to girdle Y=1.34): g in [0.75, 0.88]
    2. Crown kite & star facets (girdle Y=1.34 up to table Y=1.56): g in [0.88, 0.98]
    3. Flat table top facet (Y=1.56): g in [0.98, 1.00]
    """
    verts = []
    col_diamond = [0.96, 0.98, 1.00]
    mat_diamond = [1.0, 0.02, 0.05] # [mat_id=1, roughness=0.02, metallic=0.05]

    theta_vals = np.linspace(0.0, TAU, num_facets, endpoint=False)
    p_culet = [0.0, CULET_Y, 0.0]

    # --- 1. Pavilion Facets (Triangles from Culet up to Girdle) ---
    for i in range(num_facets):
        i_next = (i + 1) % num_facets
        th0, th1 = theta_vals[i], theta_vals[i_next]

        p_g0 = [GIRDLE_R * np.cos(th0), GIRDLE_Y, GIRDLE_R * np.sin(th0)]
        p_g1 = [GIRDLE_R * np.cos(th1), GIRDLE_Y, GIRDLE_R * np.sin(th1)]

        # Facet normal
        v1 = np.array(p_g0) - np.array(p_culet)
        v2 = np.array(p_g1) - np.array(p_culet)
        norm = np.cross(v1, v2)
        norm /= np.linalg.norm(norm)

        # Triangle: culet -> p_g1 -> p_g0
        v_a = create_vert(p_culet, norm, col_diamond, [0.5, 0.0], 0.75, mat_diamond)
        v_b = create_vert(p_g1,    norm, col_diamond, [1.0, 1.0], 0.88, mat_diamond)
        v_c = create_vert(p_g0,    norm, col_diamond, [0.0, 1.0], 0.88, mat_diamond)
        verts.extend(v_a); verts.extend(v_b); verts.extend(v_c)

    # --- 2. Crown Facets (Quads from Girdle up to Table) ---
    for i in range(num_facets):
        i_next = (i + 1) % num_facets
        th0, th1 = theta_vals[i], theta_vals[i_next]

        p_g0 = [GIRDLE_R * np.cos(th0), GIRDLE_Y, GIRDLE_R * np.sin(th0)]
        p_g1 = [GIRDLE_R * np.cos(th1), GIRDLE_Y, GIRDLE_R * np.sin(th1)]
        p_t1 = [TABLE_R * np.cos(th1),  TABLE_Y,  TABLE_R * np.sin(th1)]
        p_t0 = [TABLE_R * np.cos(th0),  TABLE_Y,  TABLE_R * np.sin(th0)]

        v1 = np.array(p_g1) - np.array(p_g0)
        v2 = np.array(p_t0) - np.array(p_g0)
        norm = np.cross(v1, v2)
        norm /= np.linalg.norm(norm)

        add_quad(verts, p_g0, p_g1, p_t1, p_t0, norm, norm, norm, norm, col_diamond,
                 [0.0, 0.0, 1.0, 1.0], 0.88, 0.88, 0.98, 0.98, mat_diamond)

    # --- 3. Table Facet (Flat Octagonal / Polygon Top) ---
    p_center = [0.0, TABLE_Y, 0.0]
    norm_up = [0.0, 1.0, 0.0]
    for i in range(num_facets):
        i_next = (i + 1) % num_facets
        th0, th1 = theta_vals[i], theta_vals[i_next]

        p_t0 = [TABLE_R * np.cos(th0), TABLE_Y, TABLE_R * np.sin(th0)]
        p_t1 = [TABLE_R * np.cos(th1), TABLE_Y, TABLE_R * np.sin(th1)]

        v_a = create_vert(p_center, norm_up, col_diamond, [0.5, 0.5], 1.00, mat_diamond)
        v_b = create_vert(p_t0,     norm_up, col_diamond, [0.0, 1.0], 0.98, mat_diamond)
        v_c = create_vert(p_t1,     norm_up, col_diamond, [1.0, 1.0], 0.98, mat_diamond)
        verts.extend(v_a); verts.extend(v_b); verts.extend(v_c)

    return verts


def generate_studio_floor(radius=4.5, num_segs=48):
    """
    Generate dark studio ground platform for soft shadows and reflections.
    """
    verts = []
    floor_y = -1.25
    col_floor = [0.03, 0.04, 0.05]
    mat_floor = [2.0, 0.35, 0.50] # Floor material

    theta = np.linspace(0.0, TAU, num_segs, endpoint=False)
    p_center = [0.0, floor_y, 0.0]
    norm_up = [0.0, 1.0, 0.0]

    for i in range(num_segs):
        i_next = (i + 1) % num_segs
        th0, th1 = theta[i], theta[i_next]

        p0 = [radius * np.cos(th0), floor_y, radius * np.sin(th0)]
        p1 = [radius * np.cos(th1), floor_y, radius * np.sin(th1)]

        v_a = create_vert(p_center, norm_up, col_floor, [0.5, 0.5], 0.0, mat_floor)
        v_b = create_vert(p0,       norm_up, col_floor, [0.0, 1.0], 0.0, mat_floor)
        v_c = create_vert(p1,       norm_up, col_floor, [1.0, 1.0], 0.0, mat_floor)
        verts.extend(v_a); verts.extend(v_b); verts.extend(v_c)

    return verts
