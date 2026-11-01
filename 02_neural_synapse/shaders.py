"""
GLSL Shaders for Neural Connectome & Synaptic Action Potentials.
Simulates glowing axonal fiber tractography, electrical spikes,
soma hubs with synaptic discharge, and neurotransmitter bokeh.
"""

FIBER_VERTEX_SHADER = """
#version 330

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_time;

in vec3 in_position;
in vec3 in_color;
in float in_u;
in float in_fiber_id;
in vec4 in_timing; // wire_t0, wire_t1, fire_phase, fire_speed

out vec3 v_color;
out float v_pulse;
out float v_alpha;

void main() {
    float wire_t0 = in_timing.x;
    float wire_t1 = in_timing.y;
    float fire_phase = in_timing.z + in_fiber_id * 0.02;
    float fire_speed = in_timing.w;

    // Stage 1 & 2: Axonal growth progression
    float grow = clamp((u_time - wire_t0) / max(0.001, wire_t1 - wire_t0), 0.0, 1.0);
    // Smooth easing
    grow = grow * grow * (3.0 - 2.0 * grow);

    // If fiber hasn't grown to this u point yet
    if (in_u > grow) {
        v_alpha = 0.0;
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0); // Clip away
        return;
    }

    // Stage 3: Action Potential (Electrical Spike) Propagation
    float pulse = 0.0;
    if (u_time > 6.5) {
        // Frequency and speed of synaptic firing
        float t_active = u_time - 6.5;
        // Periodic action potentials traveling from soma (u=0) to synapse (u=1)
        float wave_pos = fract(t_active * fire_speed * 0.22 + fire_phase * 0.35) * 1.4 - 0.2;
        float d = abs(in_u - wave_pos);
        // Sharp electrical wavefront with trailing decay
        pulse = exp(-d * d * 180.0);

        // Synaptic burst flash when pulse reaches axon terminus (u ~ 1.0)
        if (wave_pos > 0.95 && in_u > 0.88) {
            pulse += (wave_pos - 0.95) * 4.0;
        }
    }

    v_color = in_color;
    v_pulse = pulse;
    v_alpha = smoothstep(0.0, 0.2, grow);

    vec4 world_pos = m_model * vec4(in_position, 1.0);
    gl_Position = m_proj * m_view * world_pos;
}
"""

FIBER_FRAGMENT_SHADER = """
#version 330

in vec3 v_color;
in float v_pulse;
in float v_alpha;

out vec4 fragColor;

void main() {
    if (v_alpha <= 0.01) {
        discard;
    }

    // Delicate glowing fiber ribbon
    vec3 base_lum = v_color * 0.28;

    // Electrical action potential spike
    vec3 spike_halo = v_color * v_pulse * 1.8;
    vec3 spike_core = vec3(1.0, 1.0, 1.0) * pow(v_pulse, 2.0) * 2.5;

    vec3 final_rgb = base_lum + spike_halo + spike_core;
    float final_alpha = min(1.0, v_alpha * (0.28 + v_pulse * 0.85));

    fragColor = vec4(final_rgb, final_alpha);
}
"""

NODE_VERTEX_SHADER = """
#version 330

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_time;

in vec3 in_position;
in vec3 in_color;
in float in_size;
in vec2 in_timing; // birth_t0, birth_t1

out vec3 v_color;
out float v_flash;
out float v_alpha;

void main() {
    float birth_t0 = in_timing.x;
    float birth_t1 = in_timing.y;

    float grow = clamp((u_time - birth_t0) / max(0.001, birth_t1 - birth_t0), 0.0, 1.0);
    if (grow <= 0.001) {
        v_alpha = 0.0;
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
        return;
    }

    // Synaptic discharge flash in Stage 3
    float flash = 0.0;
    if (u_time > 6.5) {
        float f_t = u_time * 4.0 + in_position.x * 5.0 + in_position.z * 3.0;
        flash = pow(max(0.0, sin(f_t)), 16.0);
    }

    vec4 view_pos = m_view * m_model * vec4(in_position, 1.0);
    gl_Position = m_proj * view_pos;

    // Pinpoint star nodes
    float dist = length(view_pos.xyz);
    float base_sz = in_size * grow * (1.0 + flash * 0.5);
    gl_PointSize = clamp((base_sz * 110.0) / max(0.5, dist), 1.5, 14.0);

    v_color = in_color;
    v_flash = flash;
    v_alpha = grow;
}
"""

NODE_FRAGMENT_SHADER = """
#version 330

in vec3 v_color;
in float v_flash;
in float v_alpha;

out vec4 fragColor;

void main() {
    if (v_alpha <= 0.01) {
        discard;
    }

    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) {
        discard;
    }

    // Soft glowing radial profile with intense nucleus
    float core = smoothstep(0.25, 0.0, dist);
    float halo = smoothstep(0.5, 0.1, dist);

    vec3 col = mix(v_color, vec3(1.0, 1.0, 1.0), core * 0.75);
    col += vec3(1.0, 0.95, 0.9) * v_flash * 1.5;

    float alpha = (halo * 0.45 + core * 0.55) * v_alpha;
    fragColor = vec4(col * 0.85, alpha * 0.75);
}
"""

VESICLE_VERTEX_SHADER = """
#version 330

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_time;

in vec3 in_position;
in vec3 in_color;
in float in_phase;
in float in_speed;
in float in_radius;

out vec3 v_color;
out float v_alpha;

void main() {
    vec3 pos = in_position;

    // 3D Brownian drift
    float t = u_time * in_speed + in_phase;
    pos.x += sin(t * 0.9) * 0.12;
    pos.y += cos(t * 0.7) * 0.12;
    pos.z += sin(t * 1.1 + 1.5) * 0.12;

    vec4 view_pos = m_view * m_model * vec4(pos, 1.0);
    gl_Position = m_proj * view_pos;

    float dist = length(view_pos.xyz);
    gl_PointSize = clamp((in_radius * 360.0) / max(0.5, dist), 1.5, 14.0);

    v_color = in_color;
    v_alpha = 0.35 + 0.35 * sin(t * 1.8);
}
"""

VESICLE_FRAGMENT_SHADER = """
#version 330

in vec3 v_color;
in float v_alpha;
out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) {
        discard;
    }

    float bokeh = smoothstep(0.5, 0.0, dist);
    bokeh = pow(bokeh, 1.8);

    vec3 col = mix(v_color, vec3(1.0, 1.0, 1.0), 0.35);
    fragColor = vec4(col * 1.4, bokeh * v_alpha * 0.75);
}
"""

HUD_VERTEX_SHADER = """
#version 330

in vec2 in_position;
in vec2 in_uv;
out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""

HUD_FRAGMENT_SHADER = """
#version 330

uniform sampler2D u_hud_texture;
in vec2 v_uv;
out vec4 fragColor;

void main() {
    vec4 col = texture(u_hud_texture, v_uv);
    fragColor = col;
}
"""
