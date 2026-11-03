# ⏳ Episode 03: Harmonic Pendulum Wave (調和振り子)

> **"Order out of chaos through pure mathematics."** — An interactive 3D simulation of a 24-sphere **Harmonic Pendulum Wave machine** running at 60 FPS in pure Python and ModernGL. Tuned to exact harmonic frequencies ($f_n = \frac{k_0 + n}{T}$), the 24 suspended chrome spheres dance through traveling sine waves, interlaced double-helixes, standing wave nodes, apparent chaotic dispersion, and finally snap back into a single, breathtaking straight line at $t = 14.0\text{s}$.

---

## 🎬 Instagram Reel Structure & Virality Playbook

### 1. The Video Format (9:16 Vertical)
* **0:00 – 0:03 (The Hook — Hypnotic & Curios):** Shot of laptop screen with VS Code open displaying `generate_pendulum_animation.py` and the glowing wireframe spheres released in a straight line, immediately undulating into a smooth transverse wave.
  * **Text on Screen:** *"POV: Math wasn't supposed to be this satisfying... ⏳🌊✨"*
* **0:03 – 0:08 (The Build-up — Stage 1 & 2):** Full-screen transition. The wave splits into two interlaced sinusoidal snakes oscillating in opposite directions, tracked by glowing wave ribbons and floor reflections.
  * **Text on Screen:** *"24 pendulums tuned to exact harmonic frequencies $f_n = (k_0 + n)/T$ ⚡"*
* **0:08 – 0:13 (The Tension — Chaos & Pullback):** Spheres scatter into seeming random dispersion. Viewers think the pattern is broken, but then the waves reverse and start pulling back together.
  * **Text on Screen:** *"Wait for the exact moment of harmonic resolution... 🤯"*
* **0:13.8 – 0:14.0 (THE DOPAMINE CLIMAX — Beat Drop):** In the final second, all 24 spheres miraculously snap into a single, razor-sharp straight line in perfect synchronization!
  * **Text on Screen:** *"Pure mathematical perfection. 100% compiled. 💎"*

---

### 📌 What to Pin in the Comments (Copy & Paste)

Pin this comment at the top of your reel to drive high comment engagement and GitHub repository traffic:

```text
📌 All 24 spheres were released at the exact same millisecond. At 0:13, did you think they were going to realign or did it look like total chaos? 👇

💻 Complete source code & 60 FPS interactive engine:
🔗 https://github.com/Kunalrai05/Byte_to_compiled

Episode 04 is the Golden Ratio Sunflower (Fibonacci) 🌻 Drop a comment if you want it next!
```

---

### 🎵 Recommended Audio & Beat Drop Timestamp

* **Top Choice (Most Viral):** **Ludovico Einaudi — Experience (Slowed + Reverb / Piano Climax)**
  - *Beat-Drop Sync:* Align the emotional piano/violin climax drop at exactly **0:13.8s** when all 24 spheres snap into a straight line.
* **Alternative 1 (Epic & Intense):** **Hans Zimmer — Cornfield Chase (Slowed to 0.85x)**
  - Builds quiet tension from 0:00 to 0:08, swelling into the pipe organ drop at 0:13.8s.
* **Alternative 2 (Aesthetic Lo-Fi):** **Øneheart & reidenshi — Snowfall**
  - Atmospheric, peaceful, late-night coding aesthetic.

---

### 📝 Ready-to-Copy Instagram Caption

```text
POV: math wasn't supposed to be this satisfying... ⏳🌊✨

24 harmonic pendulums compiled in pure Python & ModernGL:
⚡ Each pendulum is mathematically tuned to complete exactly (k₀ + n) cycles in 14.0 seconds
⚡ Traveling transverse waves → interlaced double helix → standing wave nodes
⚡ Apparent chaos → instant coherent line alignment at t = 14.0s

"In mathematics, the art of proposing a question must be held of higher value than solving it." — Georg Cantor

👇 Did you predict the exact second they would realign?
🌸 Save this reel for your study & coding motivation!
💻 Source code on GitHub: https://github.com/Kunalrai05/Byte_to_compiled

#pendulumwave #physics #creativecoding #pythonprogramming #generativeart #satisfyingvideos #mathart #satisfyingreels #harmonicmotion #aestheticreels #techreels
```

---

## 🚀 Quick Start

### 1. Interactive 3D Real-Time Engine (60 FPS)
Launch in **Full Laptop Screen** (`1536x864` borderless 60 FPS):
```bash
cd 03_pendulum_wave
python generate_pendulum_animation.py
```

#### Interactive Controls:
* **Left Click + Drag:** Orbit 3D camera around the wave machine.
* **Right Click + Drag:** Pan camera target.
* **Mouse Scroll:** Smooth zoom in / out.
* **Spacebar:** Pause / Resume the harmonic dance.
* **`H` Key:** Toggle HUD Telemetry on / off (switches instantly to **Pure Cinematic View**).
* **`F` / `F11`:** Toggle Fullscreen / Windowed mode.
* **`W` Key:** Cycle visual modes (**Cinematic Hybrid Mix**, **Pure Wireframe**, **Photorealistic Shaded**).
* **`R` Key:** Restart animation from $t = 0.0s$.
* **`E` Key:** Trigger direct MP4 video export.
* **`ESC` / `Q`:** Quit.

---

## 🎬 Direct 9:16 Video Export (Ready for Instagram Reels)
Render a 14-second 9:16 vertical video reel:

```bash
# Standard 720x1280 (30 fps)
python generate_pendulum_animation.py --export

# Full HD 1080x1920 (30 fps)
python generate_pendulum_animation.py --export --res 1080x1920

# Windowed interactive test
python generate_pendulum_animation.py --windowed
```

The exported video is saved directly to:
`03_pendulum_wave/pendulum_reel.mp4`

---

## 🔬 Mathematical Architecture & Harmonic Physics

1. **The Fundamental Frequency Law:**
   For a wave machine of $N = 24$ pendulums and a master repetition period $T = 14.0\text{ s}$:
   The $n$-th pendulum ($n = 0, 1, \dots, 23$) executes exactly $k_n = k_0 + n$ oscillations (where $k_0 = 16$).
   $$f_n = \frac{k_0 + n}{T}, \quad \omega_n = 2\pi f_n = \frac{2\pi(k_0 + n)}{T}$$

2. **Pendulum Length from Gravity:**
   From small-angle pendulum physics $T_n = 2\pi \sqrt{\frac{L_n}{g}}$:
   $$L_n = g \left(\frac{T}{2\pi (k_0 + n)}\right)^2$$
   Shorter pendulums oscillate at higher frequencies, causing adjacent pendulums to continually drift in phase.

3. **Phase Difference & Wave Patterns:**
   The phase difference between adjacent pendulums at time $t$ is:
   $$\Delta \phi(t) = (\omega_{n+1} - \omega_n) t = \frac{2\pi}{T} t$$
   * At $t = 0$: $\Delta \phi = 0$ (in phase, straight line).
   * At $t = \frac{T}{4}$: $\Delta \phi = \frac{\pi}{2}$ (quadrature, four running waves).
   * At $t = \frac{T}{2}$: $\Delta \phi = \pi$ (anti-phase, two alternating zigzag waves).
   * At $t = T$: $\Delta \phi = 2\pi \equiv 0$ (full phase return, straight line alignment).
