# 💍 Episode 03: 3D Diamond Engagement Ring // Monochrome Coded & Binary Matrix

> **Real-Time OpenGL 3.3 Engine & Matrix Typography:** A mathematically derived 3D simulation of a **Solitaire Diamond Engagement Ring** rendered as a **monochrome Black & White matrix** composed of **pixelated binary digits (`0`, `1`) and programming keywords (`def`, `vec`, `gem`, `void`, `{}`, `<>`)**. Built with **ModernGL**, **Pygame**, and **GLSL Shaders**, featuring progressive **bottom-to-top materialization**, an **expanding concentric hollow halo shockwave burst**, and **continuous 3D orbit with facet glints**.

---

## 🎯 Visual Progression & Pipeline

```
[0.0s – 4.0s]                  [4.0s – 5.5s]                        [5.2s – End]
Progressive Materialization  -> Concentric Hollow Shockwave -> 3D Continuous Orbit
(Bottom-to-Top Binary Sweep)    (Center to Screen Edges Burst)   (Facet Glints Across Code)
```

1. **Phase 1: Bottom-to-Top Procedural Generation ($0.0\text{s} \to 4.0\text{s}$)**
   - The platinum band materializes upward from the ground plane with an electrifying machine-code binary flicker frontier (`0` and `1` cycling at 18 Hz).
   - Four secure radial prongs curve upward around the crown.
   - The 57-facet brilliant-cut diamond crystallizes at the crown, rendered in crystalline code symbols (`@`, `#`, `gem`, `1111`, `{}`, `[]`, `<>`).
2. **Phase 2: Concentric Hollow Halo Shockwave Burst ($4.0\text{s} \to 5.5\text{s}$)**
   - The instant generation completes, a multi-ring concentric hollow circle shockwave ignites from the center $(0.50, 0.52)$.
   - Sweeps outward across the entire screen all the way to the screen boundaries, illuminating the matrix grid in radiant white ripples.
3. **Phase 3: Continuous 3D Orbit ($5.2\text{s}+$ onwards)**
   - The ring initiates smooth 3D rotation with 3D normals and Blinn-Phong specular glints traveling dynamically across the coded typography.

---

## 🚀 Quick Start & Interactive Controls

### Full Laptop Screen Interactive Simulation (Default: 1536x864 Borderless)
Run the engine directly to open the full-screen 3D view (ideal for manual recording with a phone camera):

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
| **`M`** | Cycle visual mode: `0` (Coded Words + Binary) $\to$ `1` (Pure Binary `0`/`1`) $\to$ `2` (ASCII Density Ramp) |
| **`B`** | Toggle background subtle ambient digital rain ON / OFF (pure `#000000` void) |
| **`1` / `2` / `3`** | Adjust cell size: `1` (Fine 7x10) \| `2` (Medium 9x13) \| `3` (Large 12x17) |
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

# Pure Binary Matrix Mode Export
python generate_diamond_ring.py --export --mode 1
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
* **Table Facet:** Planar octagonal cap facet at $Y = 1.58$.
* Growth parameter: $g_{\text{gem}}(Y) = 0.75 + 0.25 \cdot \frac{Y - Y_{\text{culet}}}{Y_{\text{table}} - Y_{\text{culet}}} \in [0.75, 1.00]$.

---

## 💡 Two-Pass GLSL Shader Architecture

### Pass 1: 3D Ring Render to Offscreen Framebuffer (FBO)
* Vertex shader projects 3D coordinates and normals using MVP matrices.
* Fragment shader discards fragments with $v_{\text{growth}} > u_{\text{growth}}$ during progressive generation.
* Computes Blinn-Phong specular, metallic rim, and facet reflections:
  $$\text{FragColor} = \big[ \text{Luminance}, \; v_{\text{growth}}, \; \text{MatID}, \; \text{Visibility} \big]$$

### Pass 2: Fullscreen Coded Matrix & Concentric Halo Rasterizer
* Divides the screen into monospaced character cells $(c_x, c_y) = \lfloor \mathbf{x} / \mathbf{s}_{\text{cell}} \rfloor$.
* Samples the 3D ring buffer at the cell center to extract surface luminance and material properties.
* Maps the cell to a 512x512 texture atlas of monospaced typography (`Consolas`):
  * **Diamond Facets:** High-density crystalline glyphs (`@`, `#`, `gem`, `1111`, `{}`, `<>`).
  * **Band & Prongs:** Binary streams (`0`, `1`, `01`, `10`) and short keywords (`def`, `vec`, `rot`, `void`, `byte`, `math`, `0x1`).
  * **Materialization Frontier:** Rapid binary cycling (`0`/`1` at 18 Hz) with localized luminescence boost.
  * **Concentric Halo Burst:** Calculates radial distance $r = \| (u - u_c) \cdot (\text{aspect}, 1) \|$ and sweeps hollow Gaussian rings across the matrix to all screen edges.

---

## 📦 Project Structure

```
03_diamond_ring/
├── generate_diamond_ring.py  # Interactive 60 FPS full laptop screen app & headless video exporter
├── font_atlas.py             # Monospaced font atlas texture generator (Consolas typography)
├── ring_geometry.py          # Procedural 3D parametric meshes (band, prongs, diamond)
├── shaders.py                # GLSL shaders (Pass 1: 3D FBO render; Pass 2: Coded Matrix & Halo)
├── math_utils.py             # 4x4 matrix transforms, perspective projection, interpolation
└── README.md                 # Technical code documentation
```
