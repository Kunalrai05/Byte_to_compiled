"""
Mathematical utilities for neural connectome modeling.
Includes cubic spline interpolation, 3D anatomical projection,
orthonormal frames, and perspective/view camera matrices.
"""

import math
import numpy as np

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
    Evaluate cubic Bezier curve at parameter u in [0, 1].
    p0, p1, p2, p3: (3,) numpy arrays.
    u: (N,) numpy array.
    """
    u = np.asarray(u, dtype=np.float32)[:, None]
    omt = 1.0 - u
    pos = (omt**3) * p0 + \
          3.0 * (omt**2) * u * p1 + \
          3.0 * omt * (u**2) * p2 + \
          (u**3) * p3
    return pos

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
