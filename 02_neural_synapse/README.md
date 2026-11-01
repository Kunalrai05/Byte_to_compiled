# 🧠 Synaptic Connectome — Human Brain Neural Network Simulation

> **Byte to Compiled — Episode 02:** An interactive, hardware-accelerated 3D simulation of human brain cytoarchitecture and synaptic action potentials written in Python. Simulates 1,400 cortical soma hubs, 2,800 curved axonal fiber tracts, real-time traveling action potential spikes, and a live oscillating EEG brainwave telemetry HUD.

---

## 🎬 Instagram Reel Structure & Virality Guide

### 1. The Video Format (9:16 Vertical)
* **0:00 – 0:03 (The Hook):** Show your laptop with VS Code displaying `generate_synapse_animation.py` with dark theme syntax highlighting.
  * **Text on Screen:** *"What happens when a human thought meets Python?"*
* **0:03 – 0:07 (Stage 1 & 2):** Zoom in to full-screen. Watch the 6 anatomical brain lobes populate with glowing soma nodes and millions of curved axonal white matter tracts connecting across the corpus callosum.
* **0:07 – 0:14 (Stage 3 Climax):** The network synchronizes. Electric action potentials (white-hot traveling spikes) race through the neural pathways, accompanied by real-time EEG gamma wave telemetry and drifting neurotransmitter vesicles.
  * **Text on Screen:** *"A conscious thought gets compiled. 🧠⚡"*

### 2. Ready-to-Copy Instagram Caption
```text
what happens when a single thought meets Python? 🧠⚡
simulating the human synaptic connectome in pure code. 💻🪄

1,400 cortical somas, 2,800 axonal tract fascicles, and traveling electrical action potentials — compiled from math into glowing digital consciousness. ✨

⚡ save this for your next coding project
👇 which organ or physical phenomenon should i code next in Episode 3?

#neuroscience #generativeart #pythonprogramming #creativecoding #codingreels #techreels #brainsimulation #neuralnetwork #proceduralart #python3 #aiart
```

### 3. Recommended Audio / Music
* Deep, futuristic cyber bass / synthwave with a sharp bass drop right at 0:07 when Stage 3 action potentials ignite (e.g. *Memory Reboot*, *Kavinsky - Nightcall remix*, or *Interstellar No Time For Caution beat drop*).

---

## 🚀 Quick Start

### 1. Interactive 3D Real-Time Engine (60 FPS)
Run the script to launch immediately in full laptop screen:
```bash
python generate_synapse_animation.py
```

#### Interactive Controls:
* **Left Click + Drag:** Orbit 3D brain camera.
* **Right Click + Drag:** Pan camera position.
* **Mouse Scroll:** Smooth zoom in / out.
* **Spacebar:** Pause / Resume animation.
* **`F` / `F11`:** Toggle Fullscreen / Windowed.
* **`R` Key:** Restart animation from $t = 0.0s$.
* **`E` Key:** Trigger direct MP4 video export.
* **`ESC` / `Q`:** Quit.

---

### 2. Export Video Directly to MP4
To export a pristine 14-second 9:16 vertical video reel:

```bash
# Standard 720x1280 (30 fps)
python generate_synapse_animation.py --export

# Full HD 1080x1920 (30 fps)
python generate_synapse_animation.py --export --res 1080x1920
```

The video file is automatically saved to:
`02_neural_synapse/neural_synapse_reel.mp4`

---

## 🔬 Scientific & Architectural Implementation

1. **Brodmann Cortical Mapping:** Distributes soma hubs across 6 functional brain regions (Frontal, Parietal, Occipital, Temporal, Deep Thalamic Core, and Cerebellar Folia).
2. **Diffusion Tractography (Axonal Splines):** Curved cubic Bézier splines simulate white matter tracts traversing through the internal capsule and corpus callosum.
3. **Traveling Wave Action Potentials:** GLSL vertex and fragment equations simulate high-velocity electrical spikes with exponential decay and terminal synaptic discharges.
4. **Live EEG Telemetry HUD:** Real-time multi-frequency Fourier wave superposition displaying active gamma oscillations (42 Hz) in the screen overlay.
