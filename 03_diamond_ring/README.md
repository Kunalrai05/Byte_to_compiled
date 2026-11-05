# 💎 Episode 03: 3D Diamond Engagement Ring // ASCII Generative Art

> **Parametric 3D Geometry & ASCII Character Shading:** An interactive, mathematical 3D simulation of a **Solitaire Diamond Engagement Ring** rendered entirely via software rasterization and luminance-mapped ASCII typography. Features a split-screen viewport combining a rotating 3D ASCII gem with optical starburst glints on top, paired with an authentic VS Code dark editor canvas on the bottom.

---

## 🚀 Quick Start

### 1. Interactive 3D Real-Time Engine (30–60 FPS)
Run the script to launch the interactive viewer:
```bash
cd 03_diamond_ring
python generate_diamond_reel.py
```

#### Interactive Controls:
* **`Spacebar`:** Pause / Resume continuous rotation.
* **`Left` / `Right` Arrow:** Manually scrub / control the ring rotation angle.
* **`F` / `F11`:** Toggle Fullscreen / Windowed preview.
* **`R` Key:** Restart rotation from $t = 0.0s$.
* **`E` Key:** Trigger direct headless 9:16 MP4 video export.
* **`ESC` / `Q`:** Quit.

---

## 🎬 Direct 9:16 Video Export

To render a 12-second 9:16 vertical video (720x1280 @ 30 FPS, perfectly timed for a seamless 360° loop):

```bash
# Standard 720x1280 (30 fps)
python generate_diamond_reel.py --export

# Full HD 1080x1920 (30 fps)
python generate_diamond_reel.py --export --res 1080x1920
```

The video file is automatically saved to:
`03_diamond_ring/diamond_ring_reel.mp4`

---

## 🔬 Mathematical & Procedural Architecture

### 1. Parametric Torus Ring Band
The ring band is modeled as an elliptical torus standing vertically in the $X$-$Y$ plane:

$$\mathbf{p}_{\text{band}}(u, v) = \begin{pmatrix} (R + r_y \cos v) \cos u \\ (R + r_y \cos v) \sin u \\ r_x \sin v \end{pmatrix}, \quad u, v \in [0, 2\pi)$$

Where:
* $R = 1.02$ (major ring radius).
* $r_x = 0.16$ (cross-section width along $Z$).
* $r_y = 0.18$ (cross-section height profile).

### 2. Brilliant-Cut Diamond Facet Geometry
The diamond gemstone is constructed from four interconnected topological zones:
1. **Table Facet:** Flat circular polygon at height $Y = 1.58$ with radius $R_{\text{table}} = 0.28$ and upward normal $\mathbf{N} = (0, 1, 0)$.
2. **Crown Facets:** Star, kite, and bezel facets sloping outward from the table down to the girdle at $Y = 1.34$, $R_{\text{girdle}} = 0.46$.
3. **Girdle:** Narrow vertical perimeter separating the crown from the pavilion.
4. **Pavilion Facets:** Tapered triangular facets converging downward from the girdle to a sharp culet vertex at $Y = 1.06$.

### 3. Securing Prongs
Four radial platinum prongs rising from $(0.10 \cos \alpha, R_{\text{band}}, 0.10 \sin \alpha)$ to $(R_{\text{girdle}} \cos \alpha, Y_{\text{girdle}} + 0.08, R_{\text{girdle}} \sin \alpha)$ along angles $\alpha_i = \frac{2\pi(i + 0.5)}{4}$, cradling the diamond girdle with an outward Hermite curvature.

### 4. Software ASCII Rasterizer & Depth Buffering
1. **3D Matrix Rotation:** Vertices and normals are transformed by instantaneous yaw $\theta(t) = \omega t$ and pitch $\phi \approx 16^\circ$.
2. **Z-Buffering:** A 2D depth array tracks the closest surface point per cell $(c, r)$ on a $78 \times 52$ character grid.
3. **Photometric Shading:** Blinn-Phong specular lighting and Fresnel rim:
   $$L = k_a + k_d \max(0, \mathbf{N} \cdot \mathbf{L}) + k_s (\max(0, \mathbf{N} \cdot \mathbf{H}))^{32} + k_f (1 - \mathbf{N} \cdot \mathbf{V})^3$$
4. **Diamond Scintillation & Optical Starburst:** Diamond facets facing the half-vector $\mathbf{H}$ trigger radiant glints with 4-point cross flare rays ($*$, $+$, $\cdot$) propagating into neighboring cells.
5. **Character Density Ramp:** Luminance is quantized across ASCII ramp `".:-=+*#%@"`.

### 5. Split-Screen Layout & Typography
* **Top Pane (55%):** Pure black `#030305` terminal canvas rendering the glowing 3D ASCII ring, background 4-petal mathematical orbital rosette curves, and telemetry headers.
* **Bottom Pane (45%):** VS Code dark editor canvas (`#0c0c0e`) rendering line-numbered, syntax-highlighted Python code with active line highlight bands and an animated blinking cursor.
