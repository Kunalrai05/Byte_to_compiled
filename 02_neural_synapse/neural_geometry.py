"""
Procedural 3D anatomical connectome generator for Human Synaptic Brain Network.
Generates cortical soma hubs, curved axonal tract fascicles via Bezier splines,
and drifting neurotransmitter vesicles.
"""

import math
import numpy as np
from math_utils import eval_cubic_bezier, normalize_v3

def generate_anatomical_brain_point(hemisphere=1, region=0):
    """
    Generate random 3D position inside human brain anatomy.
    hemisphere: +1 (right), -1 (left)
    region:
      0: Frontal Lobe (anterior)
      1: Parietal Lobe (superior)
      2: Occipital Lobe (posterior)
      3: Temporal Lobe (lateral inferior)
      4: Thalamus / Limbic Core (central deep)
      5: Cerebellum (inferior posterior)
    """
    # Base anatomical ellipsoid dimensions
    # x: lateral width, y: superior height, z: anterior/posterior
    if region == 0: # Frontal Lobe
        x = hemisphere * np.random.uniform(0.12, 0.85)
        y = np.random.uniform(0.05, 0.80)
        z = np.random.uniform(0.35, 1.25)
    elif region == 1: # Parietal Lobe
        x = hemisphere * np.random.uniform(0.15, 0.95)
        y = np.random.uniform(0.35, 1.05)
        z = np.random.uniform(-0.55, 0.35)
    elif region == 2: # Occipital Lobe
        x = hemisphere * np.random.uniform(0.10, 0.75)
        y = np.random.uniform(-0.10, 0.55)
        z = np.random.uniform(-1.25, -0.55)
    elif region == 3: # Temporal Lobe
        x = hemisphere * np.random.uniform(0.45, 1.05)
        y = np.random.uniform(-0.55, 0.10)
        z = np.random.uniform(-0.35, 0.55)
    elif region == 4: # Deep Thalamic Core
        x = hemisphere * np.random.uniform(0.04, 0.35)
        y = np.random.uniform(-0.15, 0.30)
        z = np.random.uniform(-0.25, 0.25)
    else: # Cerebellum
        x = hemisphere * np.random.uniform(0.10, 0.70)
        y = np.random.uniform(-0.85, -0.40)
        z = np.random.uniform(-1.05, -0.45)

    # Cortical sulci / gyri surface convolution modulation
    r = math.sqrt(x*x + y*y + z*z) + 1e-6
    theta = math.acos(np.clip(y / r, -1.0, 1.0))
    phi = math.atan2(z, x)

    # Brain shape envelope filter
    convolution = 1.0 + 0.06 * math.sin(7.0 * theta) * math.cos(5.0 * phi) + \
                        0.04 * math.cos(11.0 * theta) * math.sin(9.0 * phi)

    # Longitudinal fissure separation between left and right hemispheres
    fissure_gap = 0.08 * math.exp(-(x * 8.0)**2)

    pos = np.array([
        x * convolution + (0.05 if hemisphere > 0 else -0.05) + (fissure_gap if hemisphere > 0 else -fissure_gap),
        y * convolution,
        z * convolution
    ], dtype=np.float32)

    return pos

def generate_connectome_network(num_nodes=1200, num_tracts=2400):
    """
    Generate complete 3D Neural Connectome Network:
    - Somas (Neuron hubs with distinct lobe colors)
    - Axonal Fibers (curved 3D spline bundles)
    - Action potential timings
    - Drifting neurotransmitter vesicles
    """
    np.random.seed(42)

    # Region color palettes
    # 0: Frontal (Electric Cyan)
    # 1: Parietal (Neon Violet / Purple)
    # 2: Occipital (Deep Rose / Magenta)
    # 3: Temporal (Bioluminescent Teal)
    # 4: Thalamic Core (Neural Gold)
    # 5: Cerebellum (Emerald / Mint Green)
    palette = [
        np.array([0.15, 0.88, 1.00], dtype=np.float32), # Cyan
        np.array([0.72, 0.32, 0.98], dtype=np.float32), # Violet
        np.array([0.98, 0.22, 0.58], dtype=np.float32), # Rose
        np.array([0.12, 0.95, 0.75], dtype=np.float32), # Teal
        np.array([1.00, 0.82, 0.28], dtype=np.float32), # Gold
        np.array([0.25, 0.92, 0.45], dtype=np.float32), # Emerald
    ]

    # 1. Generate Somas (Neuron Nodes)
    nodes = []
    node_vertices = [] # For points rendering
    for i in range(num_nodes):
        hemisphere = 1 if (i % 2 == 0) else -1
        region = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.26, 0.22, 0.16, 0.18, 0.10, 0.08])
        pos = generate_anatomical_brain_point(hemisphere, region)
        color = palette[region]

        # Stage 1: Nodes appear early (0.0s to 3.5s)
        birth_t0 = np.random.uniform(0.2, 3.2)
        birth_t1 = birth_t0 + 0.8
        size = np.random.uniform(6.0, 18.0) if region == 4 else np.random.uniform(4.0, 12.0)

        nodes.append({
            'pos': pos,
            'region': region,
            'hemisphere': hemisphere,
            'color': color,
            't0': birth_t0,
            't1': birth_t1,
            'size': size
        })

        # Node vertex layout: pos(3f), color(3f), size(1f), timing(2f)
        node_vertices.append([
            pos[0], pos[1], pos[2],
            color[0], color[1], color[2],
            size,
            birth_t0, birth_t1
        ])

    node_data = np.array(node_vertices, dtype=np.float32)

    # 2. Generate Axonal Fiber Tracts
    # Connect nodes based on realistic structural probability
    fiber_line_vertices = []
    tract_count = 0

    # Build spatial index for connecting nearby and functional hubs
    positions = np.array([n['pos'] for n in nodes])

    for i in range(num_nodes):
        n_a = nodes[i]
        pos_a = n_a['pos']

        # Determine number of outgoing axonal branches
        # Deep thalamic and frontal hubs have high degree (more connections)
        num_branches = np.random.randint(2, 6) if n_a['region'] in (0, 4) else np.random.randint(1, 4)

        for _ in range(num_branches):
            if tract_count >= num_tracts:
                break

            # 70% chance local connection, 30% chance long-range / callosal tract
            is_long_range = (np.random.random() < 0.30)
            if is_long_range:
                # Target opposite hemisphere (Corpus Callosum bridge) or deep thalamus
                candidates = [j for j in range(num_nodes) if nodes[j]['hemisphere'] != n_a['hemisphere'] or nodes[j]['region'] == 4]
                j = np.random.choice(candidates)
            else:
                # Find nearest neighbors in same hemisphere
                dists = np.linalg.norm(positions - pos_a, axis=1)
                # Same hemisphere, reasonable distance
                valid_mask = (dists > 0.05) & (dists < 0.85)
                candidate_indices = np.where(valid_mask)[0]
                if len(candidate_indices) == 0:
                    continue
                j = np.random.choice(candidate_indices)

            n_b = nodes[j]
            pos_b = n_b['pos']

            # Generate curved cubic Bézier spline for axonal tract
            # Control points arch inward toward corpus callosum / internal capsule
            mid = (pos_a + pos_b) * 0.5
            curve_sag = 0.22 if is_long_range else 0.10
            # Pull toward center for natural brain white matter curvature
            cp1 = pos_a + (mid - pos_a) * 0.55 - np.array([0.0, curve_sag, 0.0], dtype=np.float32)
            cp2 = pos_b + (mid - pos_b) * 0.55 - np.array([0.0, curve_sag, 0.0], dtype=np.float32)

            # Sample points along spline
            num_pts = 16 if is_long_range else 10
            u_vals = np.linspace(0.0, 1.0, num_pts, dtype=np.float32)
            spline_pts = eval_cubic_bezier(pos_a, cp1, cp2, pos_b, u_vals)

            # Stage 2: Axons grow from 3.5s to 7.5s
            wire_t0 = max(n_a['t1'], n_b['t1']) + np.random.uniform(0.1, 1.2)
            wire_t1 = wire_t0 + np.random.uniform(1.2, 2.2)

            # Stage 3: Synaptic firing starts from 7.0s onwards
            fire_phase = np.random.uniform(0.0, 10.0)
            fire_speed = np.random.uniform(2.5, 5.5)

            # Fiber color gradient from source node to target node
            col_a = n_a['color']
            col_b = n_b['color']

            for k in range(num_pts - 1):
                p0 = spline_pts[k]
                p1 = spline_pts[k + 1]
                u0 = u_vals[k]
                u1 = u_vals[k + 1]

                c0 = (1.0 - u0) * col_a + u0 * col_b
                c1 = (1.0 - u1) * col_a + u1 * col_b

                # Fiber vertex format:
                # pos(3f), color(3f), u_coord(1f), fiber_id(1f), timing(4f) -> wire_t0, wire_t1, fire_phase, fire_speed
                fiber_line_vertices.append([p0[0], p0[1], p0[2], c0[0], c0[1], c0[2], u0, float(tract_count), wire_t0, wire_t1, fire_phase, fire_speed])
                fiber_line_vertices.append([p1[0], p1[1], p1[2], c1[0], c1[1], c1[2], u1, float(tract_count), wire_t0, wire_t1, fire_phase, fire_speed])

            tract_count += 1

    fiber_data = np.array(fiber_line_vertices, dtype=np.float32)

    # 3. Drifting Neurotransmitter Spores (Synaptic Vesicles)
    vesicles = []
    num_vesicles = 250
    for _ in range(num_vesicles):
        # Pick random node as emitter
        node = nodes[np.random.randint(0, num_nodes)]
        pos = node['pos'] + np.random.normal(0, 0.08, size=3).astype(np.float32)
        phase = np.random.uniform(0.0, 2.0 * math.pi)
        speed = np.random.uniform(0.4, 1.2)
        radius = np.random.uniform(0.015, 0.035)
        color = node['color']
        vesicles.append([pos[0], pos[1], pos[2], color[0], color[1], color[2], phase, speed, radius])

    vesicle_data = np.array(vesicles, dtype=np.float32)

    return node_data, fiber_data, vesicle_data, tract_count
