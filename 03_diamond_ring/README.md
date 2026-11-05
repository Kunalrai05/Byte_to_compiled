# 💍 Episode 03: 3D Diamond Engagement Ring // Procedural Generation & Concentric Halo Shockwave

> **Real-Time OpenGL 3.3 Engine:** A mathematically rigorous 3D simulation of a **Solitaire Diamond Engagement Ring** built in Python with **ModernGL**, **Pygame**, and **GLSL Shaders**. Features progressive **bottom-to-top procedural materialization**, an **expanding concentric hollow halo shockwave**, and **physically modeled diamond chromatic dispersion with continuous 3D orbit**.

---

## 🎯 Visual Progression & Architecture

```
[0.0s – 4.0s]             [4.0s – 5.5s]                        [5.2s – End]
Progressive Materialization -> Concentric Hollow Shockwave -> 3D Continuous Orbit
(Bottom-to-Top Growth)        (Center to Screen Edges Burst)   (Dispersion & Glints)
```

1. **Phase 1: Bottom-to-Top Materialization ($0.0\text{s} \to 4.0\text{s}$)**
   - The platinum torus band materializes upward from the ground contact plane with glowing crystalline spark frontiers.
   - Four secure radial prongs curve upward around the crown.
   - The brilliant-cut diamond crystallizes at the top with facet geometry and chromatic fire.
2. **Phase 2: Concentric Hollow Halo Shockwave Burst ($4.0\text{s} \to 5.5\text{s}$)**
   - The exact moment generation completes, a concentric multi-ring hollow circle shockwave ignites from the center.
   - Sweeps outward across the entire screen all the way to the screen boundaries with Gaussian intensity falloff.
3. **Phase 3: Graceful 3D Orbit & Chromatic Dispersion ($5.2\text{s}+$ onwards)**
   - The ring initiates smooth 3D rotation with 3-wavelength chromatic refraction ($n_r = 2.40, n_g = 2.42, n_b = 2.44$).
   - High-exponent Blinn-Phong specular glints shimmer across the crown and pavilion facets.

---

## 🚀 Quick Start & Interactive Controls

### Full Laptop Screen Interactive Simulation (Default: 1536x864 Borderless)
Run the engine directly to open the full-screen 3D view (ideal for manual recording with phone camera):

```bash
cd 03_diamond_ring
python generate_diamond_ring.py
```

To run in windowed mode instead of fullscreen:
```bash
python generate_diamond_ring.py --windowed
```

### Controls:
| Key / Input | Action |
| :--- | :--- |
| **`Spacebar`** | Pause / Resume animation timeline |
| **`R`** | Replay simulation from $t = 0.0\text{s}$ (watch materialization & shockwave burst again) |
| **Left Click + Drag** | Interactive 3D camera orbit (Yaw & Pitch) |
| **Right Click + Drag** | Pan target point |
| **Mouse Scroll** | Dynamic camera zoom (Distance) |
| **`F` / `F11`** | Toggle Fullscreen / Windowed display |
| **`E`** | Trigger direct headless 9:16 vertical MP4 video export |
| **`ESC` / `Q`** | Exit simulation |

---

## 🎬 Direct Headless 9:16 Video Export

To render an ultra-smooth 9:16 vertical video reel (`diamond_ring_reel.mp4`):

```bash
# Standard 720x1280 @ 30 FPS (14.0s full sequence)
python generate_diamond_ring.py --export

# Full HD 1080x1920 @ 30 FPS
python generate_diamond_ring.py --export --res 1080x1920
```

The output video will be written to:
`03_diamond_ring/diamond_ring_reel.mp4`

---

## 🔬 Mathematical & Procedural Geometry

### 1. Parametric Torus Ring Band
The ring band is parameterized as an elliptical torus oriented vertically in the $X$-$Y$ plane:

$$\mathbf{p}_{\text{band}}(u, v) = \begin{pmatrix} (R + r_y \cos v) \cos u \\ (R + r_y \cos v) \sin u \\ r_x \sin v \end{pmatrix}, \quad u, v \in [0, 2\pi)$$

Where:
* $R = 1.05$: Major ring radius.
* $r_x = 0.16$: Lateral tube radius ($Z$-thickness).
* $r_y = 0.18$: Radial tube height ($X$-$Y$ plane thickness).
* Normalized growth parameter:
  $$g_{\text{band}}(u) = 0.55 \cdot \left| \frac{\text{atan2}(-\sin u, -\cos u)}{\pi} \right| \in [0.00, 0.55]$$
  Ensures generation proceeds monotonically upward from the bottom pole ($u = -\frac{\pi}{2}$) to the top prong base ($u = \frac{\pi}{2}$).

### 2. Four Secure Prongs
The 4 prongs follow cubic Hermite spline paths anchoring from the band crest to the diamond girdle:

$$\mathbf{p}_{\text{prong}}(s, \alpha) = (1 - s)^2 \mathbf{p}_{\text{base}} + 2s(1 - s) \mathbf{p}_{\text{mid}} + s^2 \mathbf{p}_{\text{tip}}, \quad s \in [0, 1]$$

Each prong is lofted with an elliptical cylinder cross-section:
* Growth parameter: $g_{\text{prong}}(s) = 0.55 + 0.20 \cdot s \in [0.55, 0.75]$.

### 3. Brilliant-Cut Gemstone Topology
The diamond is modeled with four distinct geometric facet zones:
* **Culet Vertex:** Bottom sharp tip at $Y = 1.06$.
* **Pavilion Facets:** Converging triangular facets connecting the culet to the girdle ($Y = 1.34, R = 0.46$).
* **Crown Facets:** Bezel and kite facets sloping from the girdle to the table facet ($Y = 1.58, R = 0.28$).
* **Table Facet:** Planar octagonal cap facet.
* Growth parameter: $g_{\text{gem}}(Y) = 0.75 + 0.25 \cdot \frac{Y - Y_{\text{culet}}}{Y_{\text{table}} - Y_{\text{culet}}} \in [0.75, 1.00]$.

---

## 💡 GLSL Shader Pipeline

### 1. Progressive Growth Frontier & Crystalline Sparks
In `RING_FRAG_SRC`, geometry fragments above the active threshold $u\_growth$ are discarded:
```glsl
if (mat_id < 1.5) {
    if (v_growth > u_growth) {
        discard;
    }
}
```
A luminous spark border illuminates the active frontier:
```glsl
float dist_to_frontier = u_growth - v_growth;
if (dist_to_frontier >= 0.0 && dist_to_frontier < 0.035) {
    float frontier_glow = (1.0 - dist_to_frontier / 0.035);
    vec3 spark_col = vec3(0.4, 0.9, 1.2) * 4.0;
    final_rgb += spark_col * frontier_glow;
}
```

### 2. Chromatic Diamond Refraction & Prismatic Fire
Diamond light refraction is modeled using Snell's Law across three color wavelengths:
```glsl
vec3 R_red   = refract(-V, N, 1.0 / 2.40);
vec3 R_green = refract(-V, N, 1.0 / 2.42);
vec3 R_blue  = refract(-V, N, 1.0 / 2.44);

float fire_r = pow(max(dot(R_red, L_key), 0.0), 8.0) * 0.75;
float fire_g = pow(max(dot(R_green, L_key), 0.0), 8.0) * 0.75;
float fire_b = pow(max(dot(R_blue, L_key), 0.0), 8.0) * 0.95;
vec3 fire = vec3(fire_r, fire_g, fire_b);
```

### 3. Concentric Hollow Halo Shockwave
In `SHOCKWAVE_FRAG_SRC`, 3 concentric rings expand from the ring center with aspect-ratio correction:
```glsl
vec2 p = v_uv - u_center;
p.x *= u_aspect;
float dist = length(p);

float radii[3] = float[3](u_shock_radius, u_shock_radius * 0.82, u_shock_radius * 0.65);
float weights[3] = float[3](1.0, 0.65, 0.35);
float thicknesses[3] = float[3](0.045, 0.035, 0.025);

for (int i = 0; i < 3; ++i) {
    float r = radii[i];
    if (r > 0.01) {
        float ring_dist = abs(dist - r);
        float thick = thicknesses[i];
        if (ring_dist < thick) {
            float edge = 1.0 - ring_dist / thick;
            float halo = pow(edge, 2.5) * weights[i];
            vec3 ring_col = mix(vec3(0.5, 0.85, 1.0), vec3(1.0, 1.0, 1.2), edge);
            glow_color += ring_col * halo;
        }
    }
}
```

---

## 📦 Project Structure

```
03_diamond_ring/
├── generate_diamond_ring.py  # Interactive 60 FPS full laptop screen app & headless video exporter
├── ring_geometry.py          # Procedural 3D parametric meshes (band, prongs, diamond, studio floor)
├── shaders.py                # GLSL shaders (PBR metallic, chromatic dispersion, shockwave halo)
├── math_utils.py             # 4x4 matrix transforms, perspective projection, interpolation
└── README.md                 # Technical code documentation
```
