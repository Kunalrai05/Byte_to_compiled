"""
Mathematical utilities for 3D camera projections and transformations.
"""
import math
import numpy as np

def perspective_matrix(fovy_degrees, aspect, z_near, z_far):
    """Create a 4x4 OpenGL perspective projection matrix."""
    f = 1.0 / math.tan(math.radians(fovy_degrees) / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (z_far + z_near) / (z_near - z_far)
    m[2, 3] = (2.0 * z_far * z_near) / (z_near - z_far)
    m[3, 2] = -1.0
    return m

def look_at_matrix(eye, target, up):
    """Create a 4x4 OpenGL look-at view matrix."""
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    up = np.asarray(up, dtype=np.float32)

    forward = target - eye
    forward = forward / np.linalg.norm(forward)

    side = np.cross(forward, up)
    side = side / np.linalg.norm(side)

    up_vec = np.cross(side, forward)

    m = np.identity(4, dtype=np.float32)
    m[0, :3] = side
    m[1, :3] = up_vec
    m[2, :3] = -forward
    m[0, 3] = -np.dot(side, eye)
    m[1, 3] = -np.dot(up_vec, eye)
    m[2, 3] = np.dot(forward, eye)
    return m

def smoothstep(edge0, edge1, x):
    """Hermite interpolation between edge0 and edge1."""
    t = np.clip((x - edge0) / max(1e-6, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
