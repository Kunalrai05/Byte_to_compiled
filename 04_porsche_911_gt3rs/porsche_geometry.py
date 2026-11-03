"""
Procedural 3D Geometry and Aerodynamic Flow System for the Porsche 911 GT3 RS.
Generates:
1. 3D Parametric Mesh of the Porsche 911 GT3 RS (992) with active DRS rear wing flap.
2. Heritage Morphing capability (1974 930 Turbo Whale-Tail -> 2024 992 GT3 RS).
3. Detailed 5-spoke center-lock magnesium wheels, drilled carbon-ceramic brake discs, and painted calipers.
4. 4-point Matrix LED headlights and continuous rear red lightbar.
5. Wind Tunnel CFD Streamline flow field with 1,500+ animated aerodynamic particle ribbons.
6. Studio dyno turntable and ground shadow plane.
"""

import numpy as np


def lerp(a, b, t):
    """Linear interpolation between a and b."""
    return a + (b - a) * t


# Material IDs for shader routing:
# 0: Car Body (Metallic Paint / Clearcoat)
# 1: Carbon Fiber Aero (Hood scoops, roof, wing, diffuser, mirrors)
# 2: Gloss Black Trim / Splitter / Rockers
# 3: Glass (Windshield, side windows, rear quarter windows)
# 4: 4-Point LED Headlights / DRLs (Emissive Bright White/Cyan)
# 5: Rear Continuous LED Lightbar (Emissive Bright Red)
# 6: Wheels (Satin Black / Pyro Red / Neodyme Gold)
# 7: Brake Discs (Perforated Carbon-Ceramic) & Calipers (Racing Yellow / Red)
# 8: Exhaust Tips (Titanium / Glow)
# 9: Floor / Turntable Platform


def create_vertex(pos, normal, color, uv, mat_id, morph_pos=None):
    """
    Format standard vertex:
    pos: [x, y, z]
    normal: [nx, ny, nz]
    color: [r, g, b]
    uv: [u, v]
    mat_id: [mat, roughness, metallic]
    morph_pos: [mx, my, mz] (position in 1974 930 Turbo heritage mode)
    """
    if morph_pos is None:
        morph_pos = pos
    return [
        pos[0], pos[1], pos[2],
        normal[0], normal[1], normal[2],
        color[0], color[1], color[2],
        uv[0], uv[1],
        mat_id[0], mat_id[1], mat_id[2],
        morph_pos[0], morph_pos[1], morph_pos[2]
    ]


def add_quad(verts, p0, p1, p2, p3, norm, color, uv_rect, mat_id,
             m0=None, m1=None, m2=None, m3=None):
    """Add a quad as two counter-clockwise triangles."""
    if m0 is None: m0 = p0
    if m1 is None: m1 = p1
    if m2 is None: m2 = p2
    if m3 is None: m3 = p3

    u0, v0, u1, v1 = uv_rect
    v_a = create_vertex(p0, norm, color, [u0, v0], mat_id, m0)
    v_b = create_vertex(p1, norm, color, [u1, v0], mat_id, m1)
    v_c = create_vertex(p2, norm, color, [u1, v1], mat_id, m2)
    v_d = create_vertex(p3, norm, color, [u0, v1], mat_id, m3)

    # Triangle 1: a -> b -> c
    verts.extend(v_a); verts.extend(v_b); verts.extend(v_c)
    # Triangle 2: a -> c -> d
    verts.extend(v_a); verts.extend(v_c); verts.extend(v_d)


def add_cylinder(verts, p_start, p_end, radius, segments, color, mat_id):
    """Generate a 3D cylinder tube between two points."""
    p_start = np.array(p_start, dtype=np.float32)
    p_end = np.array(p_end, dtype=np.float32)
    axis = p_end - p_start
    length = np.linalg.norm(axis)
    if length < 1e-6:
        return
    d = axis / length

    # Find arbitrary perpendicular vector
    if abs(d[0]) < 0.8:
        perp1 = np.cross(d, np.array([1.0, 0.0, 0.0], dtype=np.float32))
    else:
        perp1 = np.cross(d, np.array([0.0, 1.0, 0.0], dtype=np.float32))
    perp1 /= np.linalg.norm(perp1)
    perp2 = np.cross(d, perp1)

    theta = np.linspace(0, 2 * np.pi, segments + 1)
    for i in range(segments):
        th0, th1 = theta[i], theta[i+1]
        c0, s0 = np.cos(th0), np.sin(th0)
        c1, s1 = np.cos(th1), np.sin(th1)

        r0 = (perp1 * c0 + perp2 * s0) * radius
        r1 = (perp1 * c1 + perp2 * s1) * radius
        n0 = (perp1 * c0 + perp2 * s0)
        n1 = (perp1 * c1 + perp2 * s1)

        pt0_bot = p_start + r0
        pt1_bot = p_start + r1
        pt0_top = p_end + r0
        pt1_top = p_end + r1

        add_quad(verts, pt0_bot, pt1_bot, pt1_top, pt0_top,
                 (n0 + n1) * 0.5, color, [0.0, 0.0, 1.0, 1.0], mat_id)


def generate_wheel_assembly(center, radius, width, is_front=True):
    """
    Generate detailed Porsche center-lock wheel:
    Tire tread, outer rim lip, 5-split-spoke magnesium rim,
    drilled carbon-ceramic brake disc, and red/yellow brake caliper.
    """
    verts = []
    cx, cy, cz = center
    sign_x = 1.0 if cx > 0 else -1.0
    half_w = width * 0.5
    outer_x = cx + sign_x * half_w
    inner_x = cx - sign_x * half_w

    rim_radius = radius * 0.74
    disc_radius = rim_radius * 0.72

    # Materials:
    mat_tire = [2.0, 0.85, 0.05]     # Rubber
    mat_rim = [6.0, 0.25, 0.85]      # Satin magnesium rim
    mat_disc = [7.0, 0.45, 0.70]     # Carbon-ceramic disc
    mat_caliper = [7.0, 0.20, 0.30]  # Racing Yellow / Red caliper

    tire_col = [0.12, 0.12, 0.13]
    rim_col = [0.85, 0.20, 0.15] if cx > 0 else [0.85, 0.20, 0.15] # Pyro Red accent option
    disc_col = [0.28, 0.29, 0.31]
    caliper_col = [0.95, 0.78, 0.08] # Porsche Carbon Ceramic yellow caliper

    num_segments = 24
    theta = np.linspace(0, 2 * np.pi, num_segments + 1)

    # 1. Tire Outer Tread (Cylindrical shell)
    for i in range(num_segments):
        th0, th1 = theta[i], theta[i+1]
        c0, s0 = np.cos(th0), np.sin(th0)
        c1, s1 = np.cos(th1), np.sin(th1)

        p0 = [inner_x, cy + s0 * radius, cz + c0 * radius]
        p1 = [outer_x, cy + s0 * radius, cz + c0 * radius]
        p2 = [outer_x, cy + s1 * radius, cz + c1 * radius]
        p3 = [inner_x, cy + s1 * radius, cz + c1 * radius]
        norm = [0.0, (s0 + s1) * 0.5, (c0 + c1) * 0.5]
        add_quad(verts, p0, p1, p2, p3, norm, tire_col, [0.0, 0.0, 1.0, 1.0], mat_tire)

        # Tire sidewalls (inner & outer)
        # Outer sidewall: from rim_radius to tire radius
        pw0 = [outer_x, cy + s0 * rim_radius, cz + c0 * rim_radius]
        pw1 = [outer_x, cy + s0 * radius,     cz + c0 * radius]
        pw2 = [outer_x, cy + s1 * radius,     cz + c1 * radius]
        pw3 = [outer_x, cy + s1 * rim_radius, cz + c1 * rim_radius]
        add_quad(verts, pw0, pw1, pw2, pw3, [sign_x, 0.0, 0.0], tire_col, [0.0, 0.0, 1.0, 1.0], mat_tire)

    # 2. Brake Disc (Stationary inside the wheel)
    disc_x = cx + sign_x * (half_w * 0.15)
    for i in range(16):
        th0 = theta[i * (num_segments // 16)]
        th1 = theta[(i + 1) * (num_segments // 16)]
        c0, s0 = np.cos(th0), np.sin(th0)
        c1, s1 = np.cos(th1), np.sin(th1)

        pd0 = [disc_x, cy, cz]
        pd1 = [disc_x, cy + s0 * disc_radius, cz + c0 * disc_radius]
        pd2 = [disc_x, cy + s1 * disc_radius, cz + c1 * disc_radius]
        add_quad(verts, pd0, pd1, pd2, pd0, [sign_x, 0.0, 0.0], disc_col, [0.0, 0.0, 1.0, 1.0], mat_disc)

    # 3. Brake Caliper (Massive 6-piston monobloc caliper)
    caliper_angle = np.pi * 0.55 if is_front else np.pi * 0.45
    cal_c = np.cos(caliper_angle)
    cal_s = np.sin(caliper_angle)
    cal_pos = [disc_x + sign_x * 0.03, cy + cal_s * disc_radius * 0.95, cz + cal_c * disc_radius * 0.95]
    cal_size = [0.06, 0.12, 0.06]
    # Simple block for caliper
    add_quad(verts,
             [cal_pos[0], cal_pos[1] - cal_size[1]*0.5, cal_pos[2] - cal_size[2]*0.5],
             [cal_pos[0], cal_pos[1] + cal_size[1]*0.5, cal_pos[2] - cal_size[2]*0.5],
             [cal_pos[0], cal_pos[1] + cal_size[1]*0.5, cal_pos[2] + cal_size[2]*0.5],
             [cal_pos[0], cal_pos[1] - cal_size[1]*0.5, cal_pos[2] + cal_size[2]*0.5],
             [sign_x, 0.0, 0.0], caliper_col, [0.0, 0.0, 1.0, 1.0], mat_caliper)

    # 4. Magnesium Lightweight 5-Double-Spoke Wheel
    spoke_depth = outer_x - sign_x * 0.03
    hub_radius = rim_radius * 0.22
    for spoke_i in range(5):
        base_angle = spoke_i * (2.0 * np.pi / 5.0)
        for offset in [-0.12, 0.12]:
            ang = base_angle + offset
            c_spk = np.cos(ang)
            s_spk = np.sin(ang)
            spk_inner = [spoke_depth, cy + np.sin(base_angle) * hub_radius, cz + np.cos(base_angle) * hub_radius]
            spk_outer = [outer_x - sign_x * 0.015, cy + s_spk * rim_radius * 0.92, cz + c_spk * rim_radius * 0.92]
            add_cylinder(verts, spk_inner, spk_outer, radius=0.018, segments=6, color=rim_col, mat_id=mat_rim)

    # Center-lock nut (Aluminum red/black)
    hub_center = [outer_x + sign_x * 0.01, cy, cz]
    add_cylinder(verts, [outer_x - sign_x * 0.04, cy, cz], hub_center, radius=hub_radius*0.7, segments=12, color=[0.9, 0.1, 0.1], mat_id=mat_rim)

    return verts


def generate_porsche_body():
    """
    Generate the iconic 3D Porsche 911 GT3 RS body mesh with dual-state
    morphing geometry (1974 930 Turbo Whale-Tail <-> 2024 992 GT3 RS Track Weapon).
    
    Includes:
    - Sloping front nose with dual hood ventilation nostrils
    - Wide front fenders with aerodynamic wheel-arch louvers
    - Steep windshield and teardrop greenhouse flyline
    - Double-bubble roof with twin aerodynamic vortex fins
    - Flared muscular rear haunches with side intercooler intakes
    - Rear bumper vents, aerodynamic diffuser with vertical strakes
    - Dual center-exit titanium exhaust pipes
    - Swan-neck rear wing supports and active upper DRS wing flap
    - 4-point Matrix LED headlights and continuous rear red lightbar
    """
    verts = []

    # Color definitions
    body_col = [0.82, 0.85, 0.88]      # Arctic Grey metallic baseline
    carbon_col = [0.15, 0.15, 0.16]    # Carbon fiber
    trim_col = [0.08, 0.08, 0.09]      # Gloss black aerodynamic trim
    glass_col = [0.10, 0.14, 0.18]     # Dark tinted automotive glass
    led_white = [1.80, 2.00, 2.40]     # High-intensity Matrix LED
    led_red = [2.50, 0.15, 0.10]       # Ultra-bright rear lightbar

    # Material attributes [mat_id, roughness, metallic]
    mat_body   = [0.0, 0.18, 0.75]
    mat_carbon = [1.0, 0.40, 0.20]
    mat_trim   = [2.0, 0.25, 0.10]
    mat_glass  = [3.0, 0.05, 0.95]
    mat_led_w  = [4.0, 0.00, 0.00]
    mat_led_r  = [5.0, 0.00, 0.00]
    mat_exhaust= [8.0, 0.35, 0.90]

    # --- 1. FRONT SPLITTER & FRONT BUMPER (Z: -2.30 to -1.90) ---
    for sign in [-1.0, 1.0]:
        # Splitter lower shelf
        p0 = [0.0, 0.08, -2.28];         m0 = [0.0, 0.12, -2.18]
        p1 = [sign * 0.92, 0.08, -2.22]; m1 = [sign * 0.84, 0.12, -2.12]
        p2 = [sign * 0.94, 0.12, -1.95]; m2 = [sign * 0.85, 0.16, -1.90]
        p3 = [0.0, 0.12, -1.98];         m3 = [0.0, 0.16, -1.92]
        norm = [0.0, 1.0, 0.0]
        add_quad(verts, p0, p1, p2, p3, norm, trim_col, [0, 0, 1, 1], mat_trim, m0, m1, m2, m3)

        # Front bumper face / radiator air dam
        p_b0 = [0.0, 0.12, -2.28];         mb0 = [0.0, 0.16, -2.18]
        p_b1 = [sign * 0.92, 0.12, -2.22]; mb1 = [sign * 0.84, 0.16, -2.12]
        p_b2 = [sign * 0.91, 0.38, -2.18]; mb2 = [sign * 0.82, 0.42, -2.08]
        p_b3 = [0.0, 0.38, -2.24];         mb3 = [0.0, 0.42, -2.12]
        add_quad(verts, p_b0, p_b1, p_b2, p_b3, [0.0, 0.2, -0.98], trim_col, [0, 0, 1, 1], mat_trim, mb0, mb1, mb2, mb3)

    # --- 2. HOOD WITH DUAL CARBON NOSTRILS (Z: -2.20 to -0.75) ---
    # The 992 GT3 RS has two deep carbon radiator scoops in the center of the hood
    for sign in [-1.0, 1.0]:
        # Inner hood nostril (carbon fiber in GT3 RS, smooth painted hood in 1974 930)
        h0 = [0.0, 0.40, -2.22];         mh0 = [0.0, 0.42, -2.12]
        h1 = [sign * 0.28, 0.40, -2.18]; mh1 = [sign * 0.28, 0.44, -2.10]
        h2 = [sign * 0.30, 0.62, -1.20]; mh2 = [sign * 0.30, 0.64, -1.20]
        h3 = [0.0, 0.63, -1.20];         mh3 = [0.0, 0.65, -1.20]
        add_quad(verts, h0, h1, h2, h3, [0.0, 0.6, -0.8], carbon_col, [0, 0, 1, 1], mat_carbon, mh0, mh1, mh2, mh3)

        # Outer painted hood sheet
        ho0 = [sign * 0.28, 0.40, -2.18]; mho0 = [sign * 0.28, 0.44, -2.10]
        ho1 = [sign * 0.68, 0.48, -2.05]; mho1 = [sign * 0.62, 0.50, -2.00]
        ho2 = [sign * 0.72, 0.74, -0.85]; mho2 = [sign * 0.66, 0.74, -0.85]
        ho3 = [sign * 0.30, 0.68, -0.85]; mho3 = [sign * 0.30, 0.70, -0.85]
        add_quad(verts, ho0, ho1, ho2, ho3, [sign * 0.3, 0.8, -0.5], body_col, [0, 0, 1, 1], mat_body, mho0, mho1, mho2, mho3)

    # --- 3. FRONT FENDERS & 4-POINT LED HEADLIGHTS (Z: -2.10 to -0.65) ---
    for sign in [-1.0, 1.0]:
        # Fender top crest
        f0 = [sign * 0.68, 0.48, -2.05]; mf0 = [sign * 0.62, 0.50, -2.00]
        f1 = [sign * 0.92, 0.65, -1.80]; mf1 = [sign * 0.84, 0.66, -1.78]
        f2 = [sign * 0.94, 0.82, -1.15]; mf2 = [sign * 0.86, 0.80, -1.15]
        f3 = [sign * 0.72, 0.74, -0.85]; mf3 = [sign * 0.66, 0.74, -0.85]
        add_quad(verts, f0, f1, f2, f3, [sign * 0.7, 0.6, -0.4], body_col, [0, 0, 1, 1], mat_body, mf0, mf1, mf2, mf3)

        # Fender wheel arch drop
        fa0 = [sign * 0.92, 0.65, -1.80]; mfa0 = [sign * 0.84, 0.66, -1.78]
        fa1 = [sign * 0.94, 0.35, -1.70]; mfa1 = [sign * 0.86, 0.35, -1.70]
        fa2 = [sign * 0.95, 0.35, -0.80]; mfa2 = [sign * 0.87, 0.35, -0.80]
        fa3 = [sign * 0.94, 0.82, -1.15]; mfa3 = [sign * 0.86, 0.80, -1.15]
        add_quad(verts, fa0, fa1, fa2, fa3, [sign * 0.95, 0.1, 0.0], body_col, [0, 0, 1, 1], mat_body, mfa0, mfa1, mfa2, mfa3)

        # Aerodynamic Fender Top Louvers / Slats (Carbon in 992 GT3 RS, smooth in 1974 930)
        l0 = [sign * 0.78, 0.80, -1.40]; ml0 = [sign * 0.74, 0.78, -1.40]
        l1 = [sign * 0.90, 0.80, -1.40]; ml1 = [sign * 0.82, 0.78, -1.40]
        l2 = [sign * 0.89, 0.82, -1.15]; ml2 = [sign * 0.81, 0.80, -1.15]
        l3 = [sign * 0.76, 0.82, -1.15]; ml3 = [sign * 0.72, 0.80, -1.15]
        add_quad(verts, l0, l1, l2, l3, [0.0, 1.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon, ml0, ml1, ml2, ml3)

        # 4-Point Matrix LED Headlight cluster
        hl_cx = sign * 0.76
        hl_cy = 0.66
        hl_cz = -1.85
        # 4 glowing LED projector gems
        for dx, dy in [(-0.035, -0.025), (0.035, -0.025), (-0.035, 0.025), (0.035, 0.025)]:
            p_led0 = [hl_cx + dx - 0.02, hl_cy + dy - 0.02, hl_cz]
            p_led1 = [hl_cx + dx + 0.02, hl_cy + dy - 0.02, hl_cz]
            p_led2 = [hl_cx + dx + 0.02, hl_cy + dy + 0.02, hl_cz]
            p_led3 = [hl_cx + dx - 0.02, hl_cy + dy + 0.02, hl_cz]
            add_quad(verts, p_led0, p_led1, p_led2, p_led3, [0.0, 0.2, -0.98], led_white, [0, 0, 1, 1], mat_led_w)

    # --- 4. GREENHOUSE: WINDSHIELD, ROOF, REAR WINDOW (Z: -0.75 to +1.40) ---
    # Windshield
    w0 = [-0.68, 0.75, -0.75]; mw0 = [-0.62, 0.75, -0.75]
    w1 = [ 0.68, 0.75, -0.75]; mw1 = [ 0.62, 0.75, -0.75]
    w2 = [ 0.58, 1.22,  0.05]; mw2 = [ 0.54, 1.20,  0.05]
    w3 = [-0.58, 1.22,  0.05]; mw3 = [-0.54, 1.20,  0.05]
    add_quad(verts, w0, w1, w2, w3, [0.0, 0.8, -0.6], glass_col, [0, 0, 1, 1], mat_glass, mw0, mw1, mw2, mw3)

    # Double-Bubble Roof (Carbon fiber with twin longitudinal roof fins)
    r0 = [-0.58, 1.22,  0.05]; mr0 = [-0.54, 1.20,  0.05]
    r1 = [ 0.58, 1.22,  0.05]; mr1 = [ 0.54, 1.20,  0.05]
    r2 = [ 0.56, 1.20,  0.70]; mr2 = [ 0.52, 1.18,  0.70]
    r3 = [-0.56, 1.20,  0.70]; mr3 = [-0.52, 1.18,  0.70]
    add_quad(verts, r0, r1, r2, r3, [0.0, 1.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon, mr0, mr1, mr2, mr3)

    # Roof Vortex Aerodynamic Fins (Left & Right roof fins on the 992 GT3 RS)
    for sign in [-1.0, 1.0]:
        rf0 = [sign * 0.38, 1.22, 0.10]; mrf0 = [sign * 0.38, 1.20, 0.10]
        rf1 = [sign * 0.38, 1.26, 0.20]; mrf1 = [sign * 0.38, 1.20, 0.20] # Fin collapses in 930
        rf2 = [sign * 0.38, 1.26, 0.65]; mrf2 = [sign * 0.38, 1.20, 0.65]
        rf3 = [sign * 0.38, 1.20, 0.68]; mrf3 = [sign * 0.38, 1.18, 0.68]
        add_quad(verts, rf0, rf1, rf2, rf3, [sign * 1.0, 0.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon, mrf0, mrf1, mrf2, mrf3)

    # Sloping Rear Fastback Window
    rw0 = [-0.56, 1.20, 0.70]; mrw0 = [-0.52, 1.18, 0.70]
    rw1 = [ 0.56, 1.20, 0.70]; mrw1 = [ 0.52, 1.18, 0.70]
    rw2 = [ 0.60, 0.88, 1.48]; mr2 =  [ 0.56, 0.86, 1.45]
    rw3 = [-0.60, 0.88, 1.48]; mr3 =  [-0.56, 0.86, 1.45]
    add_quad(verts, rw0, rw1, rw2, rw3, [0.0, 0.7, 0.7], glass_col, [0, 0, 1, 1], mat_glass, mrw0, mrw1, mr2, mr3)

    # Side Doors and Windows (Left & Right)
    for sign in [-1.0, 1.0]:
        # Side door glass
        sg0 = [sign * 0.58, 1.22, 0.05]; msg0 = [sign * 0.54, 1.20, 0.05]
        sg1 = [sign * 0.68, 0.82, -0.65]; msg1 = [sign * 0.64, 0.80, -0.65]
        sg2 = [sign * 0.74, 0.82,  0.65]; msg2 = [sign * 0.68, 0.80,  0.65]
        sg3 = [sign * 0.56, 1.20,  0.70]; msg3 = [sign * 0.52, 1.18,  0.70]
        add_quad(verts, sg0, sg1, sg2, sg3, [sign * 0.95, 0.2, 0.0], glass_col, [0, 0, 1, 1], mat_glass, msg0, msg1, msg2, msg3)

        # Door lower body panel
        sd0 = [sign * 0.68, 0.82, -0.65]; msd0 = [sign * 0.64, 0.80, -0.65]
        sd1 = [sign * 0.82, 0.32, -0.65]; msd1 = [sign * 0.76, 0.32, -0.65]
        sd2 = [sign * 0.88, 0.32,  0.65]; msd2 = [sign * 0.78, 0.32,  0.65]
        sd3 = [sign * 0.74, 0.82,  0.65]; msd3 = [sign * 0.68, 0.80,  0.65]
        add_quad(verts, sd0, sd1, sd2, sd3, [sign * 1.0, 0.0, 0.0], body_col, [0, 0, 1, 1], mat_body, msd0, msd1, msd2, msd3)

    # --- 5. FLARED REAR HAUNCHES & SIDE INTAKES (Z: 0.65 to 1.95) ---
    for sign in [-1.0, 1.0]:
        # Haunch upper swelling
        rh0 = [sign * 0.74, 0.82, 0.65]; mrh0 = [sign * 0.68, 0.80, 0.65]
        rh1 = [sign * 0.98, 0.84, 1.20]; mrh1 = [sign * 0.90, 0.80, 1.20]
        rh2 = [sign * 0.95, 0.84, 1.85]; mrh2 = [sign * 0.88, 0.80, 1.80]
        rh3 = [sign * 0.60, 0.88, 1.48]; mrh3 = [sign * 0.56, 0.86, 1.45]
        add_quad(verts, rh0, rh1, rh2, rh3, [sign * 0.8, 0.6, 0.1], body_col, [0, 0, 1, 1], mat_body, mrh0, mrh1, mrh2, mrh3)

        # Haunch wheel arch drop
        rw0 = [sign * 0.98, 0.84, 1.20]; mrw0 = [sign * 0.90, 0.80, 1.20]
        rw1 = [sign * 0.99, 0.35, 0.75]; mrw1 = [sign * 0.91, 0.35, 0.75]
        rw2 = [sign * 0.98, 0.35, 1.75]; mrw2 = [sign * 0.90, 0.35, 1.70]
        rw3 = [sign * 0.95, 0.84, 1.85]; mrw3 = [sign * 0.88, 0.80, 1.80]
        add_quad(verts, rw0, rw1, rw2, rw3, [sign * 0.98, 0.1, 0.0], body_col, [0, 0, 1, 1], mat_body, mrw0, mrw1, mrw2, mrw3)

        # Side intercooler intake scoop (in front of rear wheel)
        si0 = [sign * 0.88, 0.40, 0.68]; msi0 = [sign * 0.80, 0.40, 0.68]
        si1 = [sign * 0.98, 0.40, 0.80]; msi1 = [sign * 0.88, 0.40, 0.78]
        si2 = [sign * 0.98, 0.70, 0.80]; msi2 = [sign * 0.88, 0.68, 0.78]
        si3 = [sign * 0.88, 0.70, 0.68]; msi3 = [sign * 0.80, 0.68, 0.68]
        add_quad(verts, si0, si1, si2, si3, [sign * 0.6, 0.0, -0.8], trim_col, [0, 0, 1, 1], mat_trim, msi0, msi1, msi2, msi3)

    # --- 6. REAR DECKLID, LIGHTBAR, DIFFUSER & EXHAUSTS (Z: 1.50 to 2.25) ---
    # Rear decklid surface
    rd0 = [-0.60, 0.88, 1.48]; mrd0 = [-0.56, 0.86, 1.45]
    rd1 = [ 0.60, 0.88, 1.48]; mrd1 = [ 0.56, 0.86, 1.45]
    rd2 = [ 0.92, 0.82, 1.98]; mrd2 = [ 0.85, 0.78, 1.95]
    rd3 = [-0.92, 0.82, 1.98]; mrd3 = [-0.85, 0.78, 1.95]
    add_quad(verts, rd0, rd1, rd2, rd3, [0.0, 0.8, 0.6], body_col, [0, 0, 1, 1], mat_body, mrd0, mrd1, mrd2, mrd3)

    # Continuous Ultra-Thin LED Lightbar across the entire rear width
    lb0 = [-0.92, 0.82, 1.98]; mlb0 = [-0.85, 0.78, 1.95]
    lb1 = [ 0.92, 0.82, 1.98]; mlb1 = [ 0.85, 0.78, 1.95]
    lb2 = [ 0.92, 0.77, 2.01]; mlb2 = [ 0.85, 0.74, 1.98]
    lb3 = [-0.92, 0.77, 2.01]; mlb3 = [-0.85, 0.74, 1.98]
    add_quad(verts, lb0, lb1, lb2, lb3, [0.0, 0.2, 0.98], led_red, [0, 0, 1, 1], mat_led_r, mlb0, mlb1, mlb2, mlb3)

    # Rear bumper vertical drop & license recess
    rb0 = [-0.92, 0.77, 2.01]; mrb0 = [-0.85, 0.74, 1.98]
    rb1 = [ 0.92, 0.77, 2.01]; mrb1 = [ 0.85, 0.74, 1.98]
    rb2 = [ 0.88, 0.32, 2.08]; mrb2 = [ 0.82, 0.34, 2.05]
    rb3 = [-0.88, 0.32, 2.08]; mrb3 = [-0.82, 0.34, 2.05]
    add_quad(verts, rb0, rb1, rb2, rb3, [0.0, 0.1, 0.99], body_col, [0, 0, 1, 1], mat_body, mrb0, mrb1, mrb2, mrb3)

    # Rear Aerodynamic Carbon Diffuser with vertical aerodynamic strakes
    dif0 = [-0.88, 0.32, 2.08]; mdif0 = [-0.82, 0.34, 2.05]
    dif1 = [ 0.88, 0.32, 2.08]; mdif1 = [ 0.82, 0.34, 2.05]
    dif2 = [ 0.84, 0.10, 2.22]; mdif2 = [ 0.78, 0.14, 2.15]
    dif3 = [-0.84, 0.10, 2.22]; mdif3 = [-0.78, 0.14, 2.15]
    add_quad(verts, dif0, dif1, dif2, dif3, [0.0, -0.6, 0.8], carbon_col, [0, 0, 1, 1], mat_carbon, mdif0, mdif1, mdif2, mdif3)

    # Diffuser 4 vertical fins/strakes
    for strake_x in [-0.55, -0.22, 0.22, 0.55]:
        s_p0 = [strake_x, 0.30, 2.08]; ms_p0 = [strake_x, 0.32, 2.05]
        s_p1 = [strake_x, 0.08, 2.22]; ms_p1 = [strake_x, 0.12, 2.15]
        s_p2 = [strake_x, 0.16, 2.22]; ms_p2 = [strake_x, 0.18, 2.15]
        s_p3 = [strake_x, 0.34, 2.08]; ms_p3 = [strake_x, 0.35, 2.05]
        add_quad(verts, s_p0, s_p1, s_p2, s_p3, [1.0, 0.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon, ms_p0, ms_p1, ms_p2, ms_p3)

    # Dual Center-Exit Titanium Exhaust Pipes
    ex_y = 0.26
    ex_z = 2.16
    for ex_x in [-0.075, 0.075]:
        add_cylinder(verts, [ex_x, ex_y, ex_z - 0.15], [ex_x, ex_y, ex_z + 0.02],
                     radius=0.045, segments=12, color=[0.35, 0.38, 0.42], mat_id=mat_exhaust)

    return verts


def generate_swan_neck_rear_wing():
    """
    Generate the massive 992 GT3 RS Swan-Neck Rear Wing:
    1. Twin swan-neck overhead carbon mounting pylons.
    2. Lower main wing blade (fixed carbon element).
    3. Active upper DRS wing flap that pivots on command.
    4. 1974 930 Whale Tail morph configuration (morphs to flat low-deck whale tail).
    """
    verts_static = []
    verts_drs_flap = []

    carbon_col = [0.14, 0.14, 0.15]
    mat_carbon = [1.0, 0.35, 0.20]

    # --- 1. Swan-Neck Uprights (Mounted from above the wing) ---
    for sign in [-1.0, 1.0]:
        pylon_x = sign * 0.44
        # Pylon base on rear decklid (Y: 0.88, Z: 1.62)
        # Swan neck loops UP and OVER to Y: 1.48, Z: 1.82
        pts = [
            [pylon_x, 0.88, 1.62],
            [pylon_x, 1.15, 1.70],
            [pylon_x, 1.42, 1.78],
            [pylon_x, 1.48, 1.88], # Swan-neck loop top
            [pylon_x, 1.38, 1.90]  # Attaches to top of wing blade
        ]
        # In 1974 930 Turbo, uprights collapse down to decklid level
        morph_pts = [
            [pylon_x, 0.86, 1.58],
            [pylon_x, 0.90, 1.65],
            [pylon_x, 0.92, 1.75],
            [pylon_x, 0.94, 1.85],
            [pylon_x, 0.92, 1.88]
        ]
        for k in range(len(pts) - 1):
            p0 = pts[k];     p1 = pts[k+1]
            m0 = morph_pts[k]; m1 = morph_pts[k+1]
            add_quad(verts_static,
                     [p0[0] - 0.015, p0[1], p0[2]],
                     [p0[0] + 0.015, p0[1], p0[2]],
                     [p1[0] + 0.015, p1[1], p1[2]],
                     [p1[0] - 0.015, p1[1], p1[2]],
                     [sign * 1.0, 0.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon,
                     [m0[0] - 0.015, m0[1], m0[2]],
                     [m0[0] + 0.015, m0[1], m0[2]],
                     [m1[0] + 0.015, m1[1], m1[2]],
                     [m1[0] - 0.015, m1[1], m1[2]])

    # --- 2. Lower Main Wing Airfoil Plane (Fixed) ---
    w_span = 0.88 # Half width = 1.76m full span
    # Main blade cross section
    # Leading edge: Z = 1.68, Y = 1.36
    # Trailing edge: Z = 1.88, Y = 1.34
    for sign in [-1.0, 1.0]:
        x0 = 0.0
        x1 = sign * w_span

        # 992 GT3 RS wing vs 1974 930 Whale Tail (Whale tail sits low at Y: 0.95, Z: 1.70 to 2.05)
        # Upper surface
        wb0 = [x0, 1.36, 1.68]; mwb0 = [x0, 0.94, 1.62]
        wb1 = [x1, 1.36, 1.68]; mwb1 = [sign * 0.78, 0.94, 1.62]
        wb2 = [x1, 1.34, 1.88]; mwb2 = [sign * 0.82, 0.96, 1.95]
        wb3 = [x0, 1.34, 1.88]; mwb3 = [x0, 0.96, 1.95]
        add_quad(verts_static, wb0, wb1, wb2, wb3, [0.0, 1.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon, mwb0, mwb1, mwb2, mwb3)

        # Lower surface
        wb_b0 = [x0, 1.32, 1.70]; mwb_b0 = [x0, 0.90, 1.64]
        wb_b1 = [x1, 1.32, 1.70]; mwb_b1 = [sign * 0.78, 0.90, 1.64]
        wb_b2 = [x1, 1.33, 1.88]; mwb_b2 = [sign * 0.82, 0.94, 1.95]
        wb_b3 = [x0, 1.33, 1.88]; mwb_b3 = [x0, 0.94, 1.95]
        add_quad(verts_static, wb_b0, wb_b1, wb_b2, wb_b3, [0.0, -1.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon, mwb_b0, mwb_b1, mwb_b2, mwb_b3)

        # Endplates (Huge vertical carbon endplates with "GT3 RS" embossing)
        ep0 = [x1, 1.25, 1.62]; mep0 = [sign * 0.82, 0.90, 1.62]
        ep1 = [x1, 1.48, 1.62]; mep1 = [sign * 0.82, 0.98, 1.62]
        ep2 = [x1, 1.48, 2.05]; mep2 = [sign * 0.82, 0.98, 2.00]
        ep3 = [x1, 1.25, 2.05]; mep3 = [sign * 0.82, 0.90, 2.00]
        add_quad(verts_static, ep0, ep1, ep2, ep3, [sign * 1.0, 0.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon, mep0, mep1, mep2, mep3)

    # --- 3. Active Upper DRS Wing Flap (Rotates on Hinge) ---
    # Hinge line: Y = 1.36, Z = 1.90
    # The flap spans width 1.74m and length 0.16m
    for sign in [-1.0, 1.0]:
        x0 = 0.0
        x1 = sign * (w_span - 0.02)
        # Flap local coords relative to hinge [0, 0, 0]:
        # Top face
        f_p0 = [x0, 0.015, 0.0]
        f_p1 = [x1, 0.015, 0.0]
        f_p2 = [x1, 0.015, 0.16]
        f_p3 = [x0, 0.015, 0.16]
        add_quad(verts_drs_flap, f_p0, f_p1, f_p2, f_p3, [0.0, 1.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon)

        # Bottom face
        fb_p0 = [x0, -0.015, 0.0]
        fb_p1 = [x1, -0.015, 0.0]
        fb_p2 = [x1, -0.015, 0.16]
        fb_p3 = [x0, -0.015, 0.16]
        add_quad(verts_drs_flap, fb_p0, fb_p1, fb_p2, fb_p3, [0.0, -1.0, 0.0], carbon_col, [0, 0, 1, 1], mat_carbon)

    return verts_static, verts_drs_flap


def generate_cfd_streamlines(num_lines=1600):
    """
    Generate aerodynamic wind tunnel streamline particles.
    Returns:
    - Initial seed positions [x, y, z]
    - Trajectory points and velocity scalars for rendering glowing flow ribbons
    """
    np.random.seed(992) # Porsche 992 generation seed!
    
    streamlines = []
    # Seed particles in a distribution concentrated around the car body
    for _ in range(num_lines):
        # Transverse x: -1.2 to +1.2
        sx = np.random.uniform(-1.25, 1.25)
        # Vertical y: 0.10 to 1.75
        sy = np.random.uniform(0.12, 1.65)
        # Streamline length parameter
        length_seg = 18
        # Path z spans from -5.0 (upstream) to +5.0 (downstream)
        z_start = np.random.uniform(-5.0, -1.5)
        
        streamlines.append({
            'sx': sx,
            'sy': sy,
            'z_start': z_start,
            'speed': np.random.uniform(7.5, 11.5),
            'phase': np.random.uniform(0.0, 2.0 * np.pi)
        })

    return streamlines


def compute_streamline_geometry(streamlines, t, drs_open_pct):
    """
    Compute animated 3D ribbon vertices for aerodynamic CFD flow visualization.
    Streamlines bend realistically around the nose, hood nostrils, roof, and wing flap.
    """
    ribbon_verts = []
    # Color palette:
    # High speed laminar: Cyan [0.0, 0.9, 1.0]
    # Accelerating flow: Neon Blue [0.1, 0.4, 1.0]
    # Downforce / Stagnation: Amber/Red [1.0, 0.35, 0.05]

    for s in streamlines:
        # Animated forward progress along Z axis
        z_lead = s['z_start'] + (t * s['speed']) % 10.0 - 5.0
        
        # Build 10 connected segments behind the leading particle
        pts = []
        vels = []
        for step in range(8):
            cur_z = z_lead - step * 0.16
            cur_x = s['sx']
            cur_y = s['sy']

            # Aerodynamic body deflection simulation:
            # 1. Front Nose deflection (Z: -2.3 to -0.8)
            if -2.3 < cur_z < -0.8:
                dist_front = 1.0 - (cur_z + 2.3) / 1.5
                if abs(cur_x) < 0.9:
                    # Air pushed upward over hood or sideways around fenders
                    lift = max(0.0, 0.65 - cur_y) * 0.55
                    cur_y += lift * (1.0 - abs(cur_x)/1.0)
                    cur_x *= 1.0 + 0.15 * (1.0 - abs(cur_z + 1.5))

            # 2. Windshield & Roof deflection (Z: -0.8 to +0.8)
            elif -0.8 <= cur_z <= 0.8:
                if abs(cur_x) < 0.7:
                    # Flow accelerates over the curved roof
                    roof_h = 1.25 - 0.25 * (cur_z * cur_z)
                    if cur_y < roof_h + 0.15:
                        cur_y = max(cur_y, roof_h + 0.05)

            # 3. Swan-neck Rear Wing interaction (Z: 1.4 to 2.2)
            elif 1.4 < cur_z < 2.2:
                if abs(cur_x) < 0.95:
                    wing_h = 1.35
                    # Downforce downwash angle:
                    # When DRS is closed, wing forces air sharply downwards (high downwash)
                    # When DRS is open, air flows horizontally through the slot gap
                    downwash = lerp(-0.35, -0.05, drs_open_pct)
                    if cur_y > 1.25:
                        cur_y += downwash * (cur_z - 1.4)

            # Calculate aerodynamic velocity magnitude for color mapping
            local_speed = 1.0
            if -2.2 < cur_z < -1.8:
                local_speed = 0.55 # Stagnation zone at front bumper
            elif -0.6 < cur_z < 0.6 and cur_y > 1.1:
                local_speed = 1.45 # High speed suction over roof
            elif 1.5 < cur_z < 2.0 and cur_y < 1.35:
                # Flow through wing slot
                local_speed = 1.6 if drs_open_pct > 0.5 else 0.8

            pts.append([cur_x, cur_y, cur_z])
            vels.append(local_speed)

        # Assemble triangle strips for the ribbon
        rib_width = 0.010
        for seg in range(len(pts) - 1):
            p_a = pts[seg]
            p_b = pts[seg + 1]
            v_a = vels[seg]
            v_b = vels[seg + 1]
            fade_a = 1.0 - (seg / float(len(pts)))
            fade_b = 1.0 - ((seg + 1) / float(len(pts)))

            # Color from velocity
            c_a = [lerp(0.0, 1.0, max(0.0, 1.0 - v_a)),
                   lerp(0.9, 0.4, max(0.0, 1.0 - v_a)),
                   lerp(1.0, 0.1, max(0.0, 1.0 - v_a))]
            c_b = [lerp(0.0, 1.0, max(0.0, 1.0 - v_b)),
                   lerp(0.9, 0.4, max(0.0, 1.0 - v_b)),
                   lerp(1.0, 0.1, max(0.0, 1.0 - v_b))]

            # Quad strip
            p0 = [p_a[0] - rib_width, p_a[1], p_a[2]]
            p1 = [p_a[0] + rib_width, p_a[1], p_a[2]]
            p2 = [p_b[0] + rib_width, p_b[1], p_b[2]]
            p3 = [p_b[0] - rib_width, p_b[1], p_b[2]]

            # Format: pos(3f), color(3f), alpha(1f)
            # Tri 1: p0 -> p1 -> p2
            ribbon_verts.extend([p0[0], p0[1], p0[2], c_a[0], c_a[1], c_a[2], fade_a * 0.75])
            ribbon_verts.extend([p1[0], p1[1], p1[2], c_a[0], c_a[1], c_a[2], fade_a * 0.75])
            ribbon_verts.extend([p2[0], p2[1], p2[2], c_b[0], c_b[1], c_b[2], fade_b * 0.75])
            # Tri 2: p0 -> p2 -> p3
            ribbon_verts.extend([p0[0], p0[1], p0[2], c_a[0], c_a[1], c_a[2], fade_a * 0.75])
            ribbon_verts.extend([p2[0], p2[1], p2[2], c_b[0], c_b[1], c_b[2], fade_b * 0.75])
            ribbon_verts.extend([p3[0], p3[1], p3[2], c_b[0], c_b[1], c_b[2], fade_b * 0.75])

    return np.array(ribbon_verts, dtype=np.float32)


def generate_studio_floor():
    """
    Generate dark high-tech Porsche studio dyno turntable platform
    with glowing circular outer ring and ground shadow plane.
    """
    verts = []
    mat_floor = [9.0, 0.35, 0.60]
    mat_ring  = [4.0, 0.00, 0.00] # Emissive cyan/white ring

    floor_y = 0.0
    radius = 3.8
    num_segs = 48
    theta = np.linspace(0, 2 * np.pi, num_segs + 1)

    # Circular turntable disc
    for i in range(num_segs):
        th0, th1 = theta[i], theta[i+1]
        c0, s0 = np.cos(th0), np.sin(th0)
        c1, s1 = np.cos(th1), np.sin(th1)

        p_center = [0.0, floor_y, 0.0]
        p0 = [c0 * radius, floor_y, s0 * radius]
        p1 = [c1 * radius, floor_y, s1 * radius]
        norm = [0.0, 1.0, 0.0]
        floor_col = [0.05, 0.06, 0.08]

        add_quad(verts, p_center, p0, p1, p_center, norm, floor_col, [0, 0, 1, 1], mat_floor)

        # Glowing outer turntable rim
        r_outer = radius + 0.04
        po0 = [c0 * r_outer, floor_y + 0.002, s0 * r_outer]
        po1 = [c1 * r_outer, floor_y + 0.002, s1 * r_outer]
        add_quad(verts, p0, po0, po1, p1, norm, [0.4, 0.8, 1.0], [0, 0, 1, 1], mat_ring)

    return verts
