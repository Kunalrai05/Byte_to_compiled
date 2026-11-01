"""
Mathematical utilities for procedural botanical modeling.
Includes cubic Bezier curve evaluation, Bishop frame (parallel transport frame)
computation, smoothstep interpolation, and 3D geometric transformations.
"""

import numpy as np
import math

def normalize_v3(v, eps=1e-8):
    """Normalize array of 3D vectors along last axis."""
    norm = np.linalg.norm(v, axis=-1, keepdims=True)
    norm = np.maximum(norm, eps)
    return v / norm

def smoothstep(edge0, edge1, x):
    """Smooth Hermite interpolation between edge0 and edge1."""
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def eval_cubic_bezier(p0, p1, p2, p3, u):
    """
    Evaluate cubic Bezier curve and its derivative at parameter u in [0, 1].
    p0, p1, p2, p3: (3,) numpy arrays.
    u: (N,) numpy array.
    Returns:
        pos: (N, 3) positions
        tan: (N, 3) tangent vectors (unnormalized)
    """
    u = np.asarray(u, dtype=np.float32)[:, None]
    omt = 1.0 - u
    
    # Position: B(u) = (1-u)^3*p0 + 3*(1-u)^2*u*p1 + 3*(1-u)*u^2*p2 + u^3*p3
    pos = (omt**3) * p0 + \
          3.0 * (omt**2) * u * p1 + \
          3.0 * omt * (u**2) * p2 + \
          (u**3) * p3
          
    # Tangent: B'(u) = 3*(1-u)^2*(p1-p0) + 6*(1-u)*u*(p2-p1) + 3*u^2*(p3-p2)
    tan = 3.0 * (omt**2) * (p1 - p0) + \
          6.0 * omt * u * (p2 - p1) + \
          3.0 * (u**2) * (p3 - p2)
          
    return pos, tan

def compute_bishop_frame(T):
    """
    Compute Bishop (parallel transport) frame along tangent vectors T.
    T: (N, 3) unit tangent vectors.
    Returns:
        N1: (N, 3) first normal vectors
        N2: (N, 3) second normal vectors
        Such that (T[i], N1[i], N2[i]) forms an orthonormal right-handed basis.
    """
    N = len(T)
    N1 = np.zeros_like(T)
    N2 = np.zeros_like(T)
    
    # Initial normal vector perpendicular to T[0]
    t0 = T[0]
    if abs(t0[0]) < 0.9:
        init_v = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    else:
        init_v = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        
    n1_0 = np.cross(t0, init_v)
    n1_0 = n1_0 / (np.linalg.norm(n1_0) + 1e-8)
    n2_0 = np.cross(t0, n1_0)
    n2_0 = n2_0 / (np.linalg.norm(n2_0) + 1e-8)
    
    N1[0] = n1_0
    N2[0] = n2_0
    
    # Parallel transport along curve
    for i in range(1, N):
        v1 = T[i - 1]
        v2 = T[i]
        axis = np.cross(v1, v2)
        axis_len = np.linalg.norm(axis)
        
        if axis_len < 1e-7:
            # Vectors are collinear, keep previous frame
            N1[i] = N1[i - 1]
            N2[i] = N2[i - 1]
        else:
            axis = axis / axis_len
            angle = math.atan2(axis_len, np.dot(v1, v2))
            
            # Rodrigues rotation of N1[i-1] around axis by angle
            ca = math.cos(angle)
            sa = math.sin(angle)
            
            n1_prev = N1[i - 1]
            n1_cur = n1_prev * ca + np.cross(axis, n1_prev) * sa + axis * np.dot(axis, n1_prev) * (1.0 - ca)
            # Re-orthogonalize against T[i]
            n1_cur = n1_cur - np.dot(n1_cur, T[i]) * T[i]
            n1_cur = n1_cur / (np.linalg.norm(n1_cur) + 1e-8)
            
            n2_cur = np.cross(T[i], n1_cur)
            n2_cur = n2_cur / (np.linalg.norm(n2_cur) + 1e-8)
            
            N1[i] = n1_cur
            N2[i] = n2_cur
            
    return N1, N2

def rotation_matrix_y(angle_rad):
    """3x3 rotation matrix around Y axis."""
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([
        [c, 0.0, s],
        [0.0, 1.0, 0.0],
        [-s, 0.0, c]
    ], dtype=np.float32)

def rotation_matrix_axis_angle(axis, angle_rad):
    """3x3 rotation matrix around arbitrary axis."""
    axis = np.asarray(axis, dtype=np.float32)
    axis = axis / (np.linalg.norm(axis) + 1e-8)
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    C = 1.0 - c
    x, y, z = axis
    return np.array([
        [x*x*C + c,   x*y*C - z*s, x*z*C + y*s],
        [y*x*C + z*s, y*y*C + c,   y*z*C - x*s],
        [z*x*C - y*s, z*y*C + x*s, z*z*C + c]
    ], dtype=np.float32)
def perspective_matrix(fovy_deg, aspect, znear, zfar):
    """Generate 4x4 perspective projection matrix (OpenGL style)."""
    f = 1.0 / math.tan(math.radians(fovy_deg) / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (zfar + znear) / (znear - zfar)
    m[2, 3] = (2.0 * zfar * znear) / (znear - zfar)
    m[3, 2] = -1.0
    return m

def look_at_matrix(eye, target, up):
    """Generate 4x4 LookAt view matrix."""
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    up = np.asarray(up, dtype=np.float32)

    forward = target - eye
    forward = forward / (np.linalg.norm(forward) + 1e-8)

    side = np.cross(forward, up)
    side = side / (np.linalg.norm(side) + 1e-8)

    true_up = np.cross(side, forward)

    m = np.identity(4, dtype=np.float32)
    m[0, 0:3] = side
    m[1, 0:3] = true_up
    m[2, 0:3] = -forward
    m[0, 3] = -np.dot(side, eye)
    m[1, 3] = -np.dot(true_up, eye)
    m[2, 3] = np.dot(forward, eye)
    return m
