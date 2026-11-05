# ⚡ Byte to Compiled — Creative Coding & Mathematical Visualizations

> *"What happens when imagination meets Python? Something beautiful gets compiled."*

Welcome to **Byte to Compiled**, an open-source series of procedural simulations, 3D botanical compilations, and mathematical creative coding engines written in Python.

Every episode is self-contained and comes equipped with:
- **Real-Time Interactive Viewer** (60 FPS, keyboard/mouse controls)
- **One-Click Headless 9:16 Vertical MP4 Exporter** (Direct video generation)
- **Complete Mathematical Derivations & Shading Architecture**

---

## 📽️ Episodes Directory

| # | Episode | Concept & Mathematical Model | Tech Stack | Status |
|:---:|:---|:---|:---:|:---:|
| **01** | [**Lilium Orientalis**](01_lilium_orientalis/) | Procedural 3D blooming Oriental Lily with cubic Bézier spines, Bishop parallel transport frames, organic subsurface scattering (SSS), and scientific HUD telemetry. | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | ✅ Available |
| **02** | [**Prunus Serrulata (Sakura Tree)**](02_cherry_blossom/) | Japanese Cherry Blossom Tree growing on a green meadow at evening dusk with Moyogi bonsai splines, setting sun, twilight stars, branch sway, and falling petals (*Hanafubuki*). | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | 🌸 Available |
| **03** | [**Diamond Engagement Ring**](03_diamond_ring/) | Procedural 3D Solitaire Diamond Ring with bottom-to-top materialization, concentric hollow halo shockwave burst, chromatic dispersion ($n=2.42$), and continuous 3D orbit on an obsidian studio floor. | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | 💍 Available |

---

## 🛠️ Global Requirements & Setup

To run any episode in this repository:

```bash
# Clone the repository
git clone https://github.com/Kunalrai05/Byte_to_compiled.git
cd Byte_to_compiled

# Install dependencies
pip install moderngl moderngl-window pygame numpy opencv-python pillow scipy
```

---

## 💍 Episode 03: 3D Diamond Engagement Ring // Materialization & Concentric Halo

### Full Laptop Screen Interactive Run:
```bash
cd 03_diamond_ring
python generate_diamond_ring.py
```
* **Interactive Controls:**
  * `Spacebar`: Pause / Resume animation
  * `R`: Replay materialization & halo shockwave
  * `Left Click + Drag`: Orbit 3D camera
  * `Mouse Scroll`: Dynamic camera zoom
  * `F` / `F11`: Toggle Fullscreen / Windowed
  * `E`: Export direct 9:16 vertical MP4 video
  * `ESC` / `Q`: Quit

### Headless Video Export:
```bash
python generate_diamond_ring.py --export
```

---

## 🌸 Episode 02: Prunus Serrulata (Japanese Cherry Blossom)

### Quick Run:
```bash
cd 02_cherry_blossom
python generate_sakura_animation.py
```

### Headless Video Export:
```bash
python generate_sakura_animation.py --export
```

---

## 🌷 Episode 01: Lilium Orientalis (Blooming Lily)

### Quick Run:
```bash
cd 01_lilium_orientalis
python generate_lily_animation.py
```

### Headless Video Export:
```bash
python generate_lily_animation.py --export
```
