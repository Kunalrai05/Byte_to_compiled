"""
Mathematical and 3D transformation utilities for the 3D Diamond Ring simulation.
Includes 4x4 matrix operations, camera look-at, perspective projection, and easing curves.
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
    """Return a 4x4 scaling matrix."""
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m


def rotate_x_matrix(angle_rad):
    """Return a 4x4 rotation matrix around X axis."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[1, 1], m[1, 2] = c, -s
    m[2, 1], m[2, 2] = s, c
    return m


def rotate_y_matrix(angle_rad):
    """Return a 4x4 rotation matrix around Y axis."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[0, 0], m[0, 2] = c, s
    m[2, 0], m[2, 2] = -s, c
    return m


def rotate_z_matrix(angle_rad):
    """Return a 4x4 rotation matrix around Z axis."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    m = np.eye(4, dtype=np.float32)
    m[0, 0], m[0, 1] = c, -s
    m[1, 0], m[1, 1] = s, c
    return m


def perspective_matrix(fovy_degrees, aspect, z_near, z_far):
    """Standard OpenGL perspective projection matrix."""
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
    """Standard camera look-at view matrix."""
    eye = np.asarray(eye, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    up = np.asarray(up, dtype=np.float32)

    forward = target - eye
    f_norm = np.linalg.norm(forward)
    forward = forward / f_norm if f_norm > 1e-6 else np.array([0.0, 0.0, -1.0], dtype=np.float32)

    right = np.cross(forward, up)
    r_norm = np.linalg.norm(right)
    right = right / r_norm if r_norm > 1e-6 else np.array([1.0, 0.0, 0.0], dtype=np.float32)

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
    """Hermite smoothstep interpolation."""
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-8), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    """Linear interpolation."""
    return a + (b - a) * t
