"""
Math and 3D transformation utilities for Porsche 911 GT3 RS simulation.
Contains 4x4 matrix operations, vector math, projections, and procedural interpolations.
"""

import numpy as np


def identity_matrix():
    """Return a 4x4 identity matrix."""
    return np.eye(4, dtype=np.float32)


def translation_matrix(tx, ty, tz):
    """Return a 4x4 translation matrix."""
    m = np.eye(4, dtype=np.float32)
    m[0, 3] = tx
    m[1, 3] = ty
    m[2, 3] = tz
    return m


def scale_matrix(sx, sy, sz):
    """Return a 4x4 non-uniform scaling matrix."""
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m


def rotate_x_matrix(angle_rad):
    """Return a 4x4 rotation matrix around the X axis."""
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[1, 1] = c
    m[1, 2] = -s
    m[2, 1] = s
    m[2, 2] = c
    return m


def rotate_y_matrix(angle_rad):
    """Return a 4x4 rotation matrix around the Y axis."""
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 2] = s
    m[2, 0] = -s
    m[2, 2] = c
    return m


def rotate_z_matrix(angle_rad):
    """Return a 4x4 rotation matrix around the Z axis."""
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 1] = -s
    m[1, 0] = s
    m[1, 1] = c
    return m


def perspective_matrix(fovy_degrees, aspect, z_near, z_far):
    """
    Standard OpenGL perspective projection matrix.
    fovy_degrees: Vertical field of view in degrees
    aspect: Width / Height
    z_near, z_far: Clipping planes
    """
    fovy_rad = np.radians(fovy_degrees)
    tan_half_fovy = np.tan(fovy_rad / 2.0)
    
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = 1.0 / (aspect * tan_half_fovy)
    m[1, 1] = 1.0 / tan_half_fovy
    m[2, 2] = -(z_far + z_near) / (z_far - z_near)
    m[2, 3] = -(2.0 * z_far * z_near) / (z_far - z_near)
    m[3, 2] = -1.0
    return m


def look_at_matrix(eye, target, up=np.array([0.0, 1.0, 0.0], dtype=np.float32)):
    """
    Standard camera look-at view matrix.
    eye: Camera position (x, y, z)
    target: Look-at target (x, y, z)
    up: World up vector
    """
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    up = np.asarray(up, dtype=np.float32)

    forward = target - eye
    f_norm = np.linalg.norm(forward)
    if f_norm < 1e-6:
        forward = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    else:
        forward = forward / f_norm

    right = np.cross(forward, up)
    r_norm = np.linalg.norm(right)
    if r_norm < 1e-6:
        right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    else:
        right = right / r_norm

    new_up = np.cross(right, forward)

    m = np.eye(4, dtype=np.float32)
    m[0, 0:3] = right
    m[1, 0:3] = new_up
    m[2, 0:3] = -forward
    m[0, 3] = -np.dot(right, eye)
    m[1, 3] = -np.dot(new_up, eye)
    m[2, 3] = np.dot(forward, eye)
    return m


def smoothstep(edge0, edge1, x):
    """Hermite smoothstep interpolation between edge0 and edge1."""
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-8), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def normalize(v):
    """Normalize a 1D vector."""
    n = np.linalg.norm(v)
    if n < 1e-8:
        return v
    return v / n
