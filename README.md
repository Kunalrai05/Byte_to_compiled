# ✨ Code In Bloom — Viral Creative Coding & Generative Art Series

> *"What happens when imagination meets Python? Something beautiful gets compiled."*

Welcome to **Code In Bloom** (or **Compiled Beauty**), a curated repository of code snippets, procedural simulations, and generative art engineered specifically for high-engagement, scroll-stopping Instagram Reels, TikTok, and YouTube Shorts.

Every project in this repository is self-contained, lightweight, and comes with both a **real-time full-screen 3D viewer** and an **automatic 9:16 vertical MP4 video exporter** ready for social media.

---

## 📽️ Episodes Directory

| Episode | Project Title | Description | Tech Stack | Status |
|:---:|:---|:---|:---:|:---:|
| **01** | [**Lilium Orientalis**](lilium_orientalis/) | Procedural 3D blooming Oriental Lily with cyber wireframe growth, Blinn-Phong SSS, and scientific HUD telemetry. | `ModernGL`, `Pygame`, `NumPy`, `OpenCV` | ✅ Completed |
| **02** | **Neural Synapse Visualizer** | Glowing 3D neural brain network with electric signal impulses pulsating to audio frequencies. | `PyOpenGL` / `ModernGL`, `SoundDevice` | ⏳ Coming Soon |
| **03** | **Cyberpunk Terminal Radar** | Retro-futuristic ASCII / wireframe rotating radar detecting nearby Bluetooth & WiFi signals. | `Rich`, `Colorama`, `OpenCV` | ⏳ Coming Soon |
| **04** | **Chaos Theory (Double Pendulum)** | Mesmerizing chaotic pendulum with neon glowing light trails and fractal wake. | `Pygame`, `SciPy` | ⏳ Coming Soon |
| **05** | **The Boss Detector (Panic Switch)** | OpenCV webcam face tracker that minimizes games to Excel spreadsheets when someone approaches. | `OpenCV`, `PyAutoGUI` | ⏳ Coming Soon |

---

## 🛠️ Global Requirements & Setup

To run any episode in this repository:

```bash
# Clone the repository
git clone https://github.com/<your-username>/code-in-bloom.git
cd code-in-bloom

# Install dependencies
pip install moderngl moderngl-window pygame numpy opencv-python pillow scipy
```

---

## 🌸 Episode 01: Lilium Orientalis

### Quick Run (Full Screen):
```bash
cd lilium_orientalis
python generate_lily_animation.py
```
* **Full Laptop Screen:** Automatically launches in full screen to showcase the beauty of the procedural botanical model.
* **Controls:** 
  * `Left Click + Drag`: Orbit in 3D
  * `Space`: Pause/Play
  * `F` / `F11`: Toggle Fullscreen/Windowed
  * `W`: Cycle Wireframe / Shaded / Cinematic Mix
  * `E`: Export direct 9:16 MP4 Reel video

---

## 📜 Social Media Script Template

Every reel follows the high-retention 3-part viral formula:
1. **The Hook (0:00–0:03):** Cold code in VS Code editor (`generate_lily_animation.py`). Text: *"What happens when imagination meets Python?"*
2. **The Progression (0:03–0:08):** Wireframe compilation begins and unfolds.
3. **The Climax (0:08–0:14):** Full procedural bloom with glowing lighting and audio drop. Text: *"Something beautiful gets compiled. 🌷"*
