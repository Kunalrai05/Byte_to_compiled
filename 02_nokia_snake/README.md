# 📱 Episode 02: Nokia 3310 Snake (100% Hamiltonian AI)

> **The Childhood Myth Solved:** Did anyone in human history ever actually beat Snake on the Nokia 3310? We built an unbeatable autonomous AI using a mathematical **Hamiltonian Cycle with topological shortcuts** that fills **100% of the entire dot-matrix LCD screen** without ever crashing.

---

## 🎬 Instagram Reel Structure & Virality Guide

### 1. The Video Format (9:16 Vertical)
* **0:00 – 0:03 (The Emotional Nostalgia Hook):** Shows the iconic Nokia 3310 phone casing and retro olive-green monochrome LCD screen as the snake begins hunting.
  * **Text on Screen:** *"POV: You let Python play Snake on your dad's Nokia 3310..."*
* **0:03 – 0:11 (The Hypersonic Weave):** The AI accelerates into hypersonic speed, filling 50% -> 80% -> 95% of the board with impossible serpentine precision.
  * **Text on Screen:** *"HAMILTONIAN CYCLE SOLVER // Zero collisions. Pure math."*
* **0:11 – 0:14 (The 100% Climax & Comment Bait):** The final apple is devoured, turning the entire screen solid black. The victory banner flashes: `100% COMPLETED! ALL CELLS OCCUPIED`.
  * **Text on Screen:** *"100% BOARD FILLED! Did anyone ever beat this legit? 👇"*

### 2. Ready-to-Copy Instagram Caption
```text
my dad always told me it was impossible to fill the whole screen on a Nokia 3310… so I let Python prove him wrong 🐍📱✨

we used a Hamiltonian cycle algorithm to guarantee zero collisions, filling 100% of the board (all 240 cells).

drop your childhood Snake high score in the comments 👇
be honest, did anyone ever beat this legit? 😂

#pythonprogramming #nokia3310 #retrogaming #snakegame #creativecoding #codingreels #techreels #algorithms #90skids #nostalgia
```

### 3. Recommended Audio / Music
* Trending 80s/90s retro synth, fast-paced electronic beat, or nostalgic chiptune audio (e.g. *crystal castles*, *subway surfers fast synth*, or *retro game over 8-bit sound*).

---

## 🚀 Quick Start

### 1. Interactive Full Laptop Screen Engine (60 FPS)
Launch the simulator directly:
```bash
python generate_snake_animation.py
```
* **Full Laptop Screen:** Automatically launches across your entire screen (`1536x864`) with side telemetry dashboards and an active retro Nokia phone in the center.

#### Interactive Controls:
* **`M` Key:** Toggle between **Manual Play** (you control the snake with Arrow keys / WASD) and **AI Autopilot**.
* **`1`, `2`, `3`, `4`:** Instant speed multipliers (`1x` normal, `5x` fast, `20x` warp, `250 FPS` max).
* **`Spacebar`:** Pause / Resume.
* **`F` / `F11`:** Toggle Fullscreen / Windowed.
* **`R` Key:** Reset game.
* **`E` Key:** Trigger direct MP4 video export.
* **`ESC` / `Q`:** Quit.

---

### 2. Export Video Directly to MP4 (No screen recorder needed!)
To export the 14-second 9:16 vertical video reel:

```bash
# Standard 720x1280 (30 fps)
python generate_snake_animation.py --export

# Windowed interactive test
python generate_snake_animation.py --windowed
```

The video file is automatically saved to:
`02_nokia_snake/nokia_snake_reel.mp4`

---

## 🔬 Mathematical Architecture: The Hamiltonian Cycle

1. **Cycle Construction:** The grid graph $G = (V, E)$ is partitioned into an even $20 \times 12$ matrix. A deterministic Hamiltonian loop is pre-calculated that visits every cell in an unbroken closed cycle: $0 \to 1 \to \dots \to N-1 \to 0$.
2. **Topological Lookahead Shortcuts:** While the snake is under 60% density, it takes shortcut jumps toward the food, provided the shortcut does not jump across its own tail.
3. **Safety Fallback:** As density exceeds 65%, the algorithm strictly reverts to the base Hamiltonian sequence, guaranteeing that the snake's tail always vacates each cell right before the head enters.
4. **Passive Matrix LCD Persistence:** The renderer simulates authentic monochrome liquid crystal decay by applying exponential phosphor falloff to previous pixel coordinates.
