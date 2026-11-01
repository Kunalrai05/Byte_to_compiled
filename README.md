# ⚡ Byte to Compiled — Creative Coding & Generative Reel Series

> *"What happens when imagination meets Python? Something beautiful gets compiled."*

Welcome to **Byte to Compiled**, a repository of procedural simulations, creative coding projects, and generative art engineered specifically for high-engagement, scroll-stopping Instagram Reels, TikTok, and YouTube Shorts.

Every episode is self-contained, lightweight, and includes both a **real-time full-screen 3D viewer** and a **one-click 9:16 vertical MP4 video exporter** formatted for social media.

---

## 📽️ Episodes Directory

| # | Project Title | Description | Tech Stack | Status |
|:---:|:---|:---|:---:|:---:|
| **01** | [**Lilium Orientalis**](01_lilium_orientalis/) | Procedural 3D blooming Oriental Lily with cyber wireframe growth, Blinn-Phong SSS, and scientific HUD telemetry. | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | ✅ Completed |
| **02** | **Neural Synapse Visualizer** | Glowing 3D neural brain network with electric signal impulses pulsating to audio frequencies. | `ModernGL`, `SoundDevice` | ⏳ Planned |
| **03** | **Cyberpunk Terminal Radar** | Retro-futuristic ASCII / wireframe rotating radar detecting nearby signals. | `Rich`, `Colorama`, `OpenCV` | ⏳ Planned |
| **04** | **Chaos Theory (Double Pendulum)** | Mesmerizing chaotic pendulum with neon glowing light trails and fractal wake. | `Pygame`, `SciPy` | ⏳ Planned |
| **05** | **The Boss Detector (Panic Switch)** | OpenCV webcam face tracker that minimizes games to Excel spreadsheets when someone approaches. | `OpenCV`, `PyAutoGUI` | ⏳ Planned |

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

## 🌸 Episode 01: Lilium Orientalis

### Quick Run (Full Screen):
```bash
cd 01_lilium_orientalis
python generate_lily_animation.py
```
* **Full Laptop Screen:** Automatically launches in full screen to showcase the beauty of the procedural botanical model.
* **Controls:** 
  * `Left Click + Drag`: Orbit in 3D
  * `Right Click + Drag`: Pan camera
  * `Mouse Scroll`: Zoom in / out
  * `Space`: Pause / Resume animation
  * `F` / `F11`: Toggle Fullscreen / Windowed
  * `W`: Cycle Wireframe / Shaded / Cinematic Mix
  * `R`: Reset animation
  * `E`: Export direct 9:16 MP4 Reel video

---
