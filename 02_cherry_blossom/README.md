# 🌸 Episode 02: Prunus Serrulata (Japanese Cherry Blossom Tree / 桜の木)

> **The Poetry of Spring & Calm Serenity in Pure Code:** An interactive 3D simulation of a majestic **Japanese Cherry Blossom Tree (Prunus Serrulata)** growing gracefully on a verdant green grassy hill meadow at evening dusk. Features an ancient gnarled upright Moyogi bonsai trunk, sprawling arched boughs, cloud-like floral clusters (*Hanagasumi*), a glowing setting sun sinking behind the horizon, a distant blurred shadow city skyline (*Tokyo twilight silhouette*), stars emerging across the twilight sky with the evening star (Venus), and a soothing spring breeze carrying swirling cherry blossom petals (**花吹雪 — Hanafubuki**).

---

## 🚀 Quick Start

### 1. Interactive 3D Real-Time Engine (60 FPS)
Run the script to launch in **Full Laptop Screen** (`1536x864`):
```bash
cd 02_cherry_blossom
python generate_sakura_animation.py
```

#### Interactive Controls:
* **Left Click + Drag:** Orbit camera in 3D around the tree.
* **Right Click + Drag:** Pan camera position.
* **Mouse Scroll:** Smooth zoom in / out.
* **Spacebar:** Pause / Resume the compilation animation.
* **`H` Key:** Toggle HUD Telemetry on / off (switches instantly to **Pure Zen View** without any text).
* **`F` / `F11`:** Toggle Fullscreen / Windowed mode.
* **`W` Key:** Cycle between **Cinematic Hybrid Mix**, **Pure Cyber Wireframe**, and **Photorealistic Shaded**.
* **`R` Key:** Restart animation from $t = 0.0s$.
* **`E` Key:** Trigger direct MP4 video export.
* **`ESC` / `Q`:** Quit.

---

## 🎬 Direct 9:16 Video Export (Ready for Instagram Reels)
To render a 14-second 9:16 vertical video reel (no screen recording software required):

```bash
# Standard 720x1280 (30 fps)
python generate_sakura_animation.py --export

# Full HD 1080x1920 (30 fps)
python generate_sakura_animation.py --export --res 1080x1920

# Windowed interactive test
python generate_sakura_animation.py --windowed
```

The exported video is saved directly to:
`02_cherry_blossom/sakura_reel.mp4`

---

## 🔬 Mathematical & Procedural Architecture

1. **Ancient Moyogi Bonsai Trunk & Sprawling Boughs:** Formulated with 3D cubic Bézier curves and Bishop parallel transport frames to eliminate torsion and create authentic Japanese bonsai sweeping arches.
2. **Pentamerous Cleft Geometry:** Mathematical formulation of 5-petaled notched cordate corollas with concave cupping, deep ruby throats, and white-pink blush gradients.
3. **Harmonic Spring Breeze Physics:** GPU vertex shader calculates multi-harmonic wind oscillation that sways upper branches and blossoms naturally while keeping the roots firmly anchored in the meadow.
4. **Subsurface Scattering (SSS):** Half-Lambert wrap diffuse lighting and back-scatter translucency simulating warm sunset light glowing through paper-thin floral tissue.
5. **Verdant Meadow & Evening Dusk Sky:** Expansive green grass terrain with resting fallen petals, setting sun disk and golden horizon rays, distant blurred city shadow skyline with warm bokeh lights, and twilight stars with Venus.
6. **Continuous Hanafubuki Aerodynamics:** 120+ tumbling 3D petals drifting on aerodynamic wind vectors with sinusoidal fluttering and pitch/roll tumbling.
