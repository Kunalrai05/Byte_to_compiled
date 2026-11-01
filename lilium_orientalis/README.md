# 🌷 Lilium Orientalis — Procedural 3D Botanical Compilation

> **As seen in viral Instagram Reels:** An interactive, mathematically generated 3D simulation of a blooming **Oriental Lily (Lilium Orientalis)** written in Python. Shows the 3-stage generative compilation from parametric Bezier curves & Bishop frames to cyber wireframes, and finally into a photorealistic botanical specimen with subsurface scattering and procedural papillae freckles.

---

## 🎬 Instagram Reel Structure & Virality Guide

### 1. The Video Format (9:16 Vertical)
* **0:00 – 0:03 (The Hook):** Show your laptop with VS Code on the left displaying `generate_lily_animation.py` and the initial wireframe growth on the right.
  * **Text on Screen:** *"What happens when imagination meets Python?"*
* **0:03 – 0:08 (Stage 1 & 2):** Zoom in to full-screen. Watch the glowing vascular stem and lanceolate leaves grow, followed by the blooming kinematics of the 6 petals and stamens.
* **0:08 – 0:14 (Stage 3 Reveal):** The glowing cyber wireframes materialize into lush, shaded petals with magenta flush, nectar furrows, and golden-brown pollen anthers with floating bokeh spores.
  * **Text on Screen:** *"Something beautiful gets compiled. 🌷"*

### 2. Ready-to-Copy Instagram Caption
```text
my obsession with flowers is getting out of hand… 🌷🎀
first i admired them, now i'm literally coding them into existence. 💻🪄

🌸 follow for more code turned into art ✨
💌 drop your favourite flower in the comments & maybe i'll bring it to life in my next reel! 🌷👇

#generativeart #pythonprogramming #creativecoding #codingreels #techreels #mathart #proceduralart #python3 #visualarts
```

### 3. Recommended Audio / Music
* Trending aesthetic synthwave, slow piano, or ambient lo-fi tracks (e.g. *resonance*, *interstellar theme lofi*, or classical piano with subtle vinyl crackle).

---

## 🚀 Quick Start

### 1. Interactive 3D Real-Time Engine (60 FPS)
Run the script directly to open the interactive viewer:
```bash
python generate_lily_animation.py
```

#### Interactive Controls:
* **Left Click + Drag:** Orbit camera in 3D around the plant.
* **Right Click + Drag:** Pan camera up / down / sideways.
* **Mouse Scroll:** Smooth zoom in / out.
* **Spacebar:** Pause / Resume the compilation animation.
* **`W` Key:** Cycle between **Cinematic Hybrid Mix**, **Pure Cyber Wireframe**, and **Photorealistic Shaded**.
* **`R` Key:** Restart the animation from $t = 0.0s$.
* **`E` Key:** Trigger direct MP4 video export.
* **`ESC` / `Q`:** Quit.

---

### 2. Export Video Directly to MP4 (No screen recorder needed!)
To export a pristine 14-second 9:16 vertical video reel:

```bash
# Standard 720x1280 (30 fps)
python generate_lily_animation.py --export

# Full HD 1080x1920 (30 fps)
python generate_lily_animation.py --export --res 1080x1920
```

The video file is automatically saved to:
`D:\projects\python_demos\lilium_orientalis\lilium_orientalis_reel.mp4`

---

## 🔬 Mathematical & Procedural Architecture

1. **Cubic Bézier Splines:** Used to formulate the graceful recurving spine curve of each of the 6 tepals, the central pistil, and the 6 arching filament stalks.
2. **Bishop Parallel Transport Frame:** Computes continuous normal vectors along 3D curves without Frenet-Serret singularities.
3. **Barycentric Wireframe Anti-Aliasing:** Real-time screen-space edge distance calculation via GPU fragment shader `fwidth()`.
4. **Subsurface Scattering (SSS):** Organic translucent back-scatter simulation in GLSL for realistic flower petal illumination.
5. **Procedural Papillae Generation:** 2D hash grid algorithm generating raised burgundy freckles along the nectar furrows of the petals.
6. **Botanical Telemetry HUD:** Anti-aliased scientific overlay displaying real-time stage progression and camera coordinates.
