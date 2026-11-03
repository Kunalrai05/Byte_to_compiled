# ⚡ Byte to Compiled — Creative Coding & Botanical Reel Series

> *"What happens when imagination meets Python? Something beautiful gets compiled."*

Welcome to **Byte to Compiled**, an open-source series of procedural simulations, botanical compilations, and creative coding algorithms engineered specifically for high-engagement, viral Instagram Reels, TikTok, and YouTube Shorts.

Every episode is self-contained, lightweight, and comes equipped with:
- **Full-Screen Laptop Interactive Viewer** (60 FPS, keyboard/mouse controls)
- **One-Click 9:16 Vertical MP4 Exporter** (Pre-timed for viral audio drops)
- **Instagram Reel Templates** (Hooks, comment bait triggers, and audio recommendations)

---

## 📽️ Episodes Directory

| # | Episode | Concept | Tech Stack | Status |
|:---:|:---|:---|:---:|:---:|
| **01** | [**Lilium Orientalis**](01_lilium_orientalis/) | Procedural 3D blooming Oriental Lily with cyber wireframe growth, Blinn-Phong SSS, and scientific HUD telemetry. | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | ✅ Completed |
| **02** | [**Prunus Serrulata (Sakura Tree)**](02_cherry_blossom/) | Majestic Japanese Cherry Blossom Tree growing on a lush green meadow at evening dusk with setting sun, blurred city shadow silhouette, twilight stars, gentle breeze branch sway, and falling petals (Hanafubuki). | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | 🌸 Completed |
| **03** | [**Harmonic Pendulum Wave**](03_pendulum_wave/) | 24-sphere kinetic pendulum wave simulation with frequency dispersion, traveling sine waves, interlaced double-helixes, obsidian floor reflections, and coherent straight line realignment at $t=14.0\text{s}$. | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | ⏳ Completed |
| **04** | [**Porsche 911 GT3 RS (992)**](04_porsche_911_gt3rs/) | Aerodynamic active aero simulation with 60-year heritage morph (1974 930 Turbo), 1,600+ wind tunnel CFD streamlines, active DRS flap actuation, 9,000 RPM flat-6 redline, and Nürburgring telemetry HUD. | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | 🏎️ Completed |
| **05** | [**Fibonacci Sunflower**]() | In Development — Sacred geometry floret distribution at the Golden Angle ($137.508^\circ$) blooming into radiant golden petals. | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | 🌻 Upcoming |

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

## 🌸 Episode 02: Prunus Serrulata (Sakura Tree & Peaceful Zen Garden)

### Quick Run (Full Screen):
```bash
cd 02_cherry_blossom
python generate_sakura_animation.py
```
* **Full Laptop Screen:** Automatically launches in full screen to showcase the peaceful, serene blooming tree and drifting petals.
* **Controls:**
  * `Left Click + Drag`: Orbit in 3D
  * `Right Click + Drag`: Pan camera
  * `Mouse Scroll`: Zoom in / out
  * `Space`: Pause / Resume animation
  * `H`: Toggle HUD Telemetry on / off (Pure Zen View)
  * `F` / `F11`: Toggle Fullscreen / Windowed
  * `W`: Cycle Wireframe / Shaded / Cinematic Mix
  * `R`: Reset animation
  * `E`: Export direct 9:16 MP4 Reel video

---

## ⏳ Episode 03: Harmonic Pendulum Wave (Kinetic Resonance)

### Quick Run (Full Screen):
```bash
cd 03_pendulum_wave
python generate_pendulum_animation.py
```
* **Full Laptop Screen:** Launches in full screen with 60 FPS real-time kinetic physics.
* **Controls:**
  * `Left Click + Drag`: Orbit camera around the wave in 3D
  * `Right Click + Drag`: Pan camera target
  * `Mouse Scroll`: Zoom in / out
  * `Space`: Pause / Resume animation
  * `H`: Toggle HUD Telemetry on / off (Pure Cinematic View)
  * `F` / `F11`: Toggle Fullscreen / Windowed
  * `W`: Cycle Wireframe / Photorealistic / Cinematic Mix
  * `R`: Reset animation & camera
  * `E`: Export direct 9:16 MP4 Reel video
---
