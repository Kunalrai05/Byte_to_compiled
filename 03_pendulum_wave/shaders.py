"""
================================================================================
  GLSL SHADERS — HARMONIC PENDULUM WAVE
  Includes:
  - Studio Environment Background Shader with Cinematic Spotlighting
  - Metallic Specular Chrome & Fresnel Rim Shading for Pendulum Spheres
  - Barycentric Wireframe Glow Transition for Mathematical Compilation
  - Glowing Energy Wave Ribbon Shader Connecting Harmonic Nodes
  - Telemetry HUD Screen Quad Shaders
================================================================================
"""

# -----------------------------------------------------------------------------
# 1. Studio Background Shader
# -----------------------------------------------------------------------------
BG_VERTEX_SHADER = """
#version 330
in vec2 in_position;
in vec2 in_uv;
out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_position, 0.9999, 1.0);
}
"""

BG_FRAGMENT_SHADER = """
#version 330
uniform float u_time;
uniform vec2 u_resolution;
in vec2 v_uv;
out vec4 fragColor;

void main() {
    vec2 uv = v_uv;
    
    // Deep cinematic studio dusk gradient
    vec3 c_top = vec3(0.015, 0.020, 0.038);
    vec3 c_mid = vec3(0.035, 0.055, 0.095);
    vec3 c_glow = vec3(0.080, 0.135, 0.220);
    
    float y = uv.y;
    vec3 col = mix(c_glow, c_mid, smoothstep(0.18, 0.65, y));
    col = mix(col, c_top, smoothstep(0.65, 1.0, y));

    // Studio soft spotlight behind the pendulum suspension rail with subtle breathing
    float pulse = 0.95 + 0.05 * sin(u_time * 0.8);
    vec2 spot_pos = vec2(0.5, 0.65);
    float aspect = u_resolution.x / max(1.0, u_resolution.y);
    float d = length((uv - spot_pos) * vec2(aspect, 1.0));
    col += vec3(0.12, 0.26, 0.42) * exp(-d * 2.6) * 0.50 * pulse;

    // Subtle edge vignette
    vec2 vc = uv - vec2(0.5);
    col *= 1.0 - dot(vc, vc) * 0.38;

    fragColor = vec4(col, 1.0);
}
"""

# -----------------------------------------------------------------------------
# 2. Pendulum & Floor Mesh Shaders
# -----------------------------------------------------------------------------
PENDULUM_VERTEX_SHADER = """
#version 330
uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_time;

in vec3 in_position;
in vec3 in_normal;
in vec3 in_color;
in vec3 in_bary;
in vec2 in_uv;
in vec4 in_timing; // wire_t0, wire_t1, surf_t0, surf_t1
in vec3 in_mat;    // metallic, roughness, sphere_id / floor marker

out vec3 v_world_pos;
out vec3 v_normal;
out vec3 v_color;
out vec3 v_bary;
out vec2 v_uv;
out float v_wire_alpha;
out float v_surf_alpha;
out vec3 v_mat;

void main() {
    float wire_a = clamp((u_time - in_timing.x) / max(0.001, in_timing.y - in_timing.x), 0.0, 1.0);
    wire_a = wire_a * wire_a * (3.0 - 2.0 * wire_a);

    float surf_a = clamp((u_time - in_timing.z) / max(0.001, in_timing.w - in_timing.z), 0.0, 1.0);
    surf_a = surf_a * surf_a * (3.0 - 2.0 * surf_a);

    vec4 world_pos = m_model * vec4(in_position, 1.0);
    v_world_pos = world_pos.xyz;

    mat3 normal_matrix = transpose(inverse(mat3(m_model)));
    v_normal = normalize(normal_matrix * in_normal);

    v_color = in_color;
    v_bary = in_bary;
    v_uv = in_uv;
    v_wire_alpha = wire_a;
    v_surf_alpha = surf_a;
    v_mat = in_mat;

    gl_Position = m_proj * m_view * world_pos;
}
"""

PENDULUM_FRAGMENT_SHADER = """
#version 330
uniform vec3 u_cam_pos;
uniform float u_time;
uniform int u_mode; // 0: Cinematic Hybrid, 1: Wireframe, 2: Photorealistic

in vec3 v_world_pos;
in vec3 v_normal;
in vec3 v_color;
in vec3 v_bary;
in vec2 v_uv;
in float v_wire_alpha;
in float v_surf_alpha;
in vec3 v_mat;

out vec4 fragColor;

void main() {
    if (v_wire_alpha <= 0.001) discard;

    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world_pos);

    // 1. Barycentric Wireframe with anti-aliasing
    vec3 d = fwidth(v_bary);
    vec3 a3 = smoothstep(vec3(0.0), d * 1.15, v_bary);
    float edge_factor = min(min(a3.x, a3.y), a3.z);
    float is_edge = 1.0 - edge_factor;

    vec3 wire_col = mix(vec3(0.15, 0.95, 0.85), vec3(1.0, 0.45, 0.85), step(0.5, v_color.r));
    wire_col = mix(wire_col, vec3(1.0), is_edge * is_edge * 0.5);

    // 2. Studio Lighting (Key light + Rim light + Ambient)
    vec3 L1 = normalize(vec3(0.55, 0.85, 0.60));
    vec3 L1_col = vec3(1.0, 0.96, 0.92) * 1.25;

    vec3 L2 = normalize(vec3(-0.65, 0.35, -0.50));
    vec3 L2_col = vec3(0.35, 0.65, 1.00) * 0.85;

    vec3 ambient = vec3(0.14, 0.16, 0.22) * v_color;

    // Diffuse
    float NdotL1 = max(0.0, dot(N, L1));
    float NdotL2 = max(0.0, dot(N, L2));
    vec3 diffuse = (NdotL1 * L1_col + NdotL2 * L2_col) * v_color;

    // Specular (Blinn-Phong Metallic Chrome)
    vec3 H1 = normalize(L1 + V);
    float NdotH1 = max(0.0, dot(N, H1));
    float spec = pow(NdotH1, 38.0) * v_mat.x;
    vec3 specular = spec * vec3(1.0, 0.98, 0.95);

    // Fresnel Rim Glow
    float fresnel = pow(1.0 - max(0.0, dot(N, V)), 3.0);
    vec3 rim = fresnel * vec3(0.85, 0.95, 1.0) * 0.65;

    // Subtle micro-surface finish
    float micro = sin(v_uv.x * 32.0) * cos(v_uv.y * 32.0) * 0.015;
    diffuse += vec3(micro);

    // Reflective Studio Floor
    float is_floor = step(v_mat.z, -0.5);
    if (is_floor > 0.5) {
        vec2 grid_uv = v_world_pos.xz * 2.0;
        float lines = max(
            smoothstep(0.96, 0.985, abs(sin(grid_uv.x * 3.14159))),
            smoothstep(0.96, 0.985, abs(sin(grid_uv.y * 3.14159)))
        );
        vec3 floor_base = vec3(0.020, 0.028, 0.045);
        vec3 floor_grid = vec3(0.09, 0.24, 0.38) * lines * 0.70;
        diffuse = floor_base + floor_grid;
        specular = vec3(0.0);
        rim = fresnel * vec3(0.12, 0.22, 0.35);
    }

    vec3 shaded = ambient + diffuse + specular + rim;

    vec3 final_rgb;
    if (u_mode == 1) {
        if (is_edge < 0.1) discard;
        final_rgb = wire_col * 1.5;
    } else if (u_mode == 2) {
        final_rgb = shaded;
    } else {
        float wire_fade = (1.0 - smoothstep(0.0, 0.85, v_surf_alpha));
        float wire_glow = is_edge * v_wire_alpha * wire_fade;
        vec3 wire_layer = wire_col * wire_glow * 1.6;
        vec3 surface_layer = shaded * v_surf_alpha;
        final_rgb = surface_layer + wire_layer;
    }

    fragColor = vec4(final_rgb, max(v_wire_alpha, v_surf_alpha));
}
"""

# -----------------------------------------------------------------------------
# 3. Wave Ribbon Shader (Visualizing Continuous Sine Wave / Double Helix)
# -----------------------------------------------------------------------------
RIBBON_VERTEX_SHADER = """
#version 330
uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_time;

in vec3 in_position;
in vec3 in_color;
in float in_alpha;

out vec3 v_color;
out float v_alpha;

void main() {
    v_color = in_color;
    v_alpha = in_alpha;
    gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
}
"""

RIBBON_FRAGMENT_SHADER = """
#version 330
in vec3 v_color;
in float v_alpha;
out vec4 fragColor;

void main() {
    fragColor = vec4(v_color * 1.4, v_alpha * 0.75);
}
"""

# -----------------------------------------------------------------------------
# 4. HUD Screen Quad Shaders
# -----------------------------------------------------------------------------
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
    vec4 tex = texture(u_hud_texture, v_uv);
    fragColor = tex;
}
"""
