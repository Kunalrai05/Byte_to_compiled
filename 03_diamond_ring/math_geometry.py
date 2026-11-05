"""
Parametric 3D Geometry for Diamond Engagement Ring & Background Orbital Curves.
Generates:
1. Circular Torus Ring Band (platinum/silver band with rounded elliptical profile).
2. Brilliant-Cut Diamond Gemstone (table, crown star/kite facets, girdle, and pavilion culet).
3. 4 Securing Metal Prongs curving up from band to diamond girdle.
4. Background Parametric Sparkling Orbital Curves (spirograph/atomic petals).
"""

import numpy as np

TAU = 2.0 * np.pi
R_BAND = 1.02       # Major radius of the ring band
R_TUBE_X = 0.16     # Minor radius (width along Z axis)
R_TUBE_Y = 0.18     # Minor radius (height profile)

TABLE_Y = 1.58      # Top flat table facet height
TABLE_R = 0.28      # Table facet radius
GIRDLE_Y = 1.34     # Diamond girdle height (widest perimeter)
GIRDLE_R = 0.46     # Diamond girdle outer radius
CULET_Y = 1.06      # Bottom diamond culet point


def generate_band(u_segs=120, v_segs=36):
    """
    Generate 3D vertices and normals for the circular ring band.
    Stands upright in the X-Y plane with hole through Z axis.
    """
    u = np.linspace(0, TAU, u_segs, endpoint=False)
    v = np.linspace(0, TAU, v_segs, endpoint=False)
    u_grid, v_grid = np.meshgrid(u, v)

    cos_u = np.cos(u_grid)
    sin_u = np.sin(u_grid)
    cos_v = np.cos(v_grid)
    sin_v = np.sin(v_grid)

    r_profile = R_BAND + R_TUBE_Y * cos_v
    x = r_profile * cos_u
    y = r_profile * sin_u
    z = R_TUBE_X * sin_v

    # Outward surface normals
    nx = cos_v * cos_u
    ny = cos_v * sin_u
    nz = sin_v

    points = np.stack([x.ravel(), y.ravel(), z.ravel()], axis=-1)
    normals = np.stack([nx.ravel(), ny.ravel(), nz.ravel()], axis=-1)
    n_len = np.linalg.norm(normals, axis=-1, keepdims=True)
    normals = normals / np.maximum(n_len, 1e-6)

    # Material ID 0: Platinum/silver metal
    mat_ids = np.zeros(len(points), dtype=np.int32)
    return points, normals, mat_ids


def generate_prongs():
    """
    Generate 4 vertical curved platinum prongs securing the diamond girdle.
    """
    points = []
    normals = []
    
    num_steps = 35
    radial_segs = 12
    prong_radius = 0.032
    
    # 4 prongs placed symmetrically at 45°, 135°, 225°, 315° around the crown
    for i in range(4):
        a = TAU * (i + 0.5) / 4.0
        cos_a = np.cos(a)
        sin_a = np.sin(a)
        
        # Base starts at top of band (Y ≈ R_BAND)
        base = np.array([0.10 * cos_a, R_BAND + 0.02, 0.10 * sin_a], dtype=np.float32)
        # Tip extends slightly above girdle
        tip = np.array([(GIRDLE_R + 0.022) * cos_a, GIRDLE_Y + 0.08, (GIRDLE_R + 0.022) * sin_a], dtype=np.float32)
        
        axis = tip - base
        axis_len = np.linalg.norm(axis)
        d = axis / axis_len
        
        # Perpendicular frame
        if abs(d[0]) < 0.8:
            perp1 = np.cross(d, np.array([1.0, 0.0, 0.0], dtype=np.float32))
        else:
            perp1 = np.cross(d, np.array([0.0, 1.0, 0.0], dtype=np.float32))
        perp1 /= np.linalg.norm(perp1)
        perp2 = np.cross(d, perp1)
        
        u_vals = np.linspace(0.0, 1.0, num_steps)
        phi_vals = np.linspace(0.0, TAU, radial_segs, endpoint=False)
        u_grid, phi_grid = np.meshgrid(u_vals, phi_vals)
        
        cos_p = np.cos(phi_grid).ravel()
        sin_p = np.sin(phi_grid).ravel()
        u_flat = u_grid.ravel()
        
        # Centerline position with outward curvature
        curve = np.sin(u_flat * np.pi) * 0.03
        center = base + u_flat[:, None] * (tip - base) + perp1 * curve[:, None]
        
        # Tube radial offsets
        r_offset = (perp1[None, :] * cos_p[:, None] + perp2[None, :] * sin_p[:, None]) * prong_radius
        norm = perp1[None, :] * cos_p[:, None] + perp2[None, :] * sin_p[:, None]
        
        points.append(center + r_offset)
        normals.append(norm)
        
    pts = np.concatenate(points, axis=0)
    nrms = np.concatenate(normals, axis=0)
    mat_ids = np.zeros(len(pts), dtype=np.int32)
    return pts, nrms, mat_ids


def generate_diamond(num_facets=32):
    """
    Generate Brilliant-Cut Diamond Gemstone surface points and facet normals:
    1. Table facet (flat octagon/circle top)
    2. Crown facets (star & bezel facets sloping to girdle)
    3. Girdle perimeter
    4. Pavilion facets (tapering to bottom culet point)
    """
    points = []
    normals = []
    
    # 1. Table Facet (Top horizontal flat circle/polygon)
    r_samples = np.linspace(0.0, TABLE_R, 10)
    theta_samples = np.linspace(0.0, TAU, num_facets, endpoint=False)
    for r in r_samples:
        for th in theta_samples:
            px = r * np.cos(th)
            py = TABLE_Y
            pz = r * np.sin(th)
            points.append([px, py, pz])
            normals.append([0.0, 1.0, 0.0])
            
    # 2. Crown Facets (sloping from Table down to Girdle)
    t_crown = np.linspace(0.0, 1.0, 18)
    for t in t_crown:
        curr_y = lerp(TABLE_Y, GIRDLE_Y, t)
        curr_r = lerp(TABLE_R, GIRDLE_R, t)
        for th in theta_samples:
            px = curr_r * np.cos(th)
            py = curr_y
            pz = curr_r * np.sin(th)
            
            dx = np.cos(th)
            dy = (TABLE_R - GIRDLE_R) / (TABLE_Y - GIRDLE_Y)
            dz = np.sin(th)
            n = np.array([dx, -dy * 0.85, dz], dtype=np.float32)
            n /= np.linalg.norm(n)
            
            points.append([px, py, pz])
            normals.append(n)
            
    # 3. Pavilion Facets (sloping from Girdle down to Culet)
    t_pav = np.linspace(0.0, 1.0, 22)
    for t in t_pav:
        curr_y = lerp(GIRDLE_Y, CULET_Y, t)
        curr_r = lerp(GIRDLE_R, 0.015, t)
        for th in theta_samples:
            px = curr_r * np.cos(th)
            py = curr_y
            pz = curr_r * np.sin(th)
            
            dx = np.cos(th)
            dy = (GIRDLE_R - 0.015) / (GIRDLE_Y - CULET_Y)
            dz = np.sin(th)
            n = np.array([dx, -dy * 0.90, dz], dtype=np.float32)
            n /= np.linalg.norm(n)
            
            points.append([px, py, pz])
            normals.append(n)

    pts = np.array(points, dtype=np.float32)
    nrms = np.array(normals, dtype=np.float32)
    # Material ID 1: Diamond Gemstone
    mat_ids = np.ones(len(pts), dtype=np.int32)
    return pts, nrms, mat_ids


def generate_orbital_curves(t, num_curves=4, num_pts=260):
    """
    Generate elegant, thin background mathematical orbital petal curves
    (4-petal rosette / electron orbits) drifting gracefully behind the ring.
    """
    curves = []
    for k in range(num_curves):
        # 4 distinct orbital orientations (0°, 45°, 90°, 135°)
        tilt_ang = k * (np.pi / float(num_curves))
        cos_t = np.cos(tilt_ang)
        sin_t = np.sin(tilt_ang)
        
        theta = np.linspace(0, TAU, num_pts)
        
        # Elliptical orbital loop
        r_major = 1.95
        r_minor = 0.95
        
        # Local 2D ellipse
        lx = r_major * np.cos(theta)
        ly = r_minor * np.sin(theta)
        
        # Rotate in X-Y plane by tilt_ang
        gx = lx * cos_t - ly * sin_t
        gy = (lx * sin_t + ly * cos_t) * 0.90 + 0.20 # Center near ring center
        gz = 0.35 * np.sin(theta * 2.0 + t * 0.4) - 0.50 # Sits behind ring
        
        pts = np.stack([gx, gy, gz], axis=-1)
        curves.append(pts)
    return curves


def lerp(a, b, t):
    """Linear interpolation helper."""
    return a + (b - a) * t
