# 🌸 Episode 02: Prunus Serrulata (Sakura / Cherry Blossom)

> **The Poetry of Spring in Pure Code:** An interactive, mathematically formulated 3D simulation of a blooming **Japanese Cherry Blossom branch (Prunus Serrulata)**. Features an ancient gnarled bonsai wood branch, 5-petaled notched sakura petals with deep ruby nectar eyes, golden staminal crowns, and a dynamic blizzard of tumbling falling petals (**花吹雪 — Hanafubuki**).

---

## 🎬 Instagram Reel Structure & Virality Guide

### 1. The Video Format (9:16 Vertical)
* **0:00 – 0:03 (The Hook):** Show your laptop with VS Code displaying `generate_sakura_animation.py` and the glowing branch wireframe growing in the dark.
  * **Text on Screen:** *"You loved the Lily… so I coded cherry blossoms in Python. 🌸"*
* **0:03 – 0:08 (Stage 1 & 2):** Cut to full-screen. Watch the gnarled bonsai branch bifurcate, followed by the blooming kinematics of the 5-notched sakura petals and golden stamens.
  * **Text on Screen:** *"5-petaled corolla & notched petal mathematics ✨"*
* **0:08 – 0:14 (Stage 3 Climax — Hanafubuki):** Wireframes cross-fade into translucent, luminous blush-pink petals with subsurface scattering (SSS). Falling cherry blossom petals start swirling across the camera in a spring breeze.
  * **Text on Screen:** *"Hanafubuki (Cherry Blossom Blizzard) compiled in pure Python. 🌸"*

### 2. Ready-to-Copy Instagram Caption
```text
you guys went crazy over the Lily, so here is Japanese Cherry Blossom (Sakura / 桜) coded from scratch in Python… 🌸🎀

5-petaled notched corollas, gnarled bonsai wood splines, and swirling falling petals (花吹雪 — Hanafubuki) using real-time GLSL shaders.

🌸 drop your favourite flower or tree in the comments & I’ll code it next! 👇
💌 tag someone who needs a little spring dopamine today ✨

#generativeart #creativecoding #pythonprogramming #sakurabloom #cherryblossom #codingreels #techreels #mathart #proceduralart #shaders
```

### 3. Recommended Audio / Music
* Trending aesthetic Japanese lofi / calm koto synth, soft piano (*e.g. Joe Hisaishi - Summer / Merry-Go-Round of Life lofi, or aesthetic slow synthwave*).

---

## 🚀 Quick Start

### 1. Interactive 3D Real-Time Engine (60 FPS)
Run the script to launch in **Full Laptop Screen** (`1536x864`):
```bash
python generate_sakura_animation.py
```

#### Interactive Controls:
* **Left Click + Drag:** Orbit camera in 3D around the cherry blossom branch.
* **Right Click + Drag:** Pan camera up / down / sideways.
* **Mouse Scroll:** Smooth zoom in / out.
* **Spacebar:** Pause / Resume the compilation animation.
* **`F` / `F11`:** Toggle Fullscreen / Windowed mode.
* **`W` Key:** Cycle between **Cinematic Hybrid Mix**, **Pure Cyber Wireframe**, and **Photorealistic Shaded**.
* **`R` Key:** Restart animation from $t = 0.0s$.
* **`E` Key:** Trigger direct MP4 video export.
* **`ESC` / `Q`:** Quit.

---

### 2. Export Video Directly to MP4 (No screen recorder needed!)
To export a pristine 14-second 9:16 vertical video reel:

```bash
# Standard 720x1280 (30 fps)
python generate_sakura_animation.py --export

# Full HD 1080x1920 (30 fps)
python generate_sakura_animation.py --export --res 1080x1920

# Windowed interactive test
python generate_sakura_animation.py --windowed
```

The video file is automatically saved to:
`02_cherry_blossom/sakura_reel.mp4`

---

## 🔬 Mathematical & Procedural Architecture

1. **Gnarled Bonsai Splines:** Cubic Bézier splines combined with Bishop frames to eliminate torsional twisting along the curved branch.
2. **Pentamerous Cleft Geometry:** Mathematical formulation of the signature V-cleft / heart notch at the tip of each of the 5 petals.
3. **Subsurface Scattering (SSS):** Half-Lambert diffuse wrap and back-scatter translucency simulating sunlight glowing through paper-thin sakura petals.
4. **Hanafubuki Aerodynamics:** Real-time GPU vertex shader simulating continuous looping pitch, roll, and yaw flutter of falling petals in a spring breeze.
