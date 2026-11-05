"""
ModernGL Shaders for the 3D Diamond Ring Simulation.
Includes:
1. Ring Materialization & PBR Shader: Bottom-to-top growth clipping, crystalline spark frontier,
   metallic platinum reflection, and chromatic diamond dispersion with facet glints.
2. Concentric Hollow Halo Shockwave Shader: Radiant circular shockwave burst expanding from center to all edges.
3. Studio Environment Shader: Soft overhead spotlight, floor reflections, and floating bokeh sparkles.
"""

# --- 1. RING & DIAMOND PBR SHADER ---
RING_VERT_SRC = """
#version 330 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec3 in_color;
layout (location = 3) in vec2 in_uv;
layout (location = 4) in float in_growth;
layout (location = 5) in vec3 in_mat; // [mat_id, roughness, metallic]

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_growth; // 0.0 to 1.0 growth progress

out vec3 v_world_pos;
out vec3 v_normal;
out vec3 v_color;
out vec2 v_uv;
out float v_growth;
out vec3 v_mat;

void main() {
    v_growth = in_growth;
    v_color = in_color;
    v_uv = in_uv;
    v_mat = in_mat;

    vec4 world_p = m_model * vec4(in_position, 1.0);
    v_world_pos = world_p.xyz;

    mat3 norm_mat = transpose(inverse(mat3(m_model)));
    v_normal = normalize(norm_mat * in_normal);

    gl_Position = m_proj * m_view * world_p;
}
"""

RING_FRAG_SRC = """
#version 330 core

in vec3 v_world_pos;
in vec3 v_normal;
in vec3 v_color;
in vec2 v_uv;
in float v_growth;
in vec3 v_mat;

uniform vec3 u_cam_pos;
uniform float u_growth;       // 0.0 to 1.0 (materialization frontier)
uniform float u_time;
uniform float u_flash;        // Completion starburst flash intensity

out vec4 frag_color;

void main() {
    float mat_id    = v_mat.x;
    float roughness = v_mat.y;
    float metallic  = v_mat.z;

    // --- BOTTOM-TO-TOP GROWTH CLIPPING ---
    // Floor (mat_id == 2.0) is always visible; ring & gem materialize progressively
    if (mat_id < 1.5) {
        if (v_growth > u_growth) {
            discard; // Not yet materialized
        }
    }

    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world_pos);

    // Three-point Studio Lighting (Key, Rim, Overhead Softbox)
    vec3 L_key = normalize(vec3(1.8, 3.2, 2.4) - v_world_pos);
    vec3 L_fill = normalize(vec3(-2.2, 1.8, 1.5) - v_world_pos);
    vec3 L_top  = normalize(vec3(0.0, 4.5, 0.0) - v_world_pos);

    vec3 H_key = normalize(L_key + V);
    vec3 H_top = normalize(L_top + V);

    float NdotV = max(dot(N, V), 0.0);
    float fresnel = pow(1.0 - NdotV, 3.5);

    vec3 final_rgb = vec3(0.0);

    // =========================================================================
    // MATERIAL 0: PLATINUM / WHITE GOLD RING BAND & PRONGS
    // =========================================================================
    if (mat_id < 0.5) {
        vec3 base_col = v_color;
        
        // Micro-surface metallic sheen using UV
        float micro = sin(v_uv.x * 64.0) * cos(v_uv.y * 64.0) * 0.02;
        base_col += vec3(micro);

        float diff_key = max(dot(N, L_key), 0.0) * 0.70;
        float diff_fill = max(dot(N, L_fill), 0.0) * 0.35;
        float diff_top  = max(dot(N, L_top),  0.0) * 0.50;

        float spec_sharp = pow(max(dot(N, H_key), 0.0), 64.0) * 1.40
                         + pow(max(dot(N, H_top), 0.0), 96.0) * 1.80;
        float spec_soft  = pow(max(dot(N, H_key), 0.0), 16.0) * 0.35;

        vec3 ambient = vec3(0.12, 0.14, 0.18) * base_col;
        vec3 diffuse = (diff_key + diff_fill + diff_top) * base_col;
        vec3 specular = vec3(1.0) * spec_sharp + base_col * spec_soft * metallic;
        vec3 rim = vec3(0.7, 0.85, 1.0) * fresnel * 0.75;

        final_rgb = ambient + diffuse + specular + rim;
    }

    // =========================================================================
    // MATERIAL 1: BRILLIANT-CUT DIAMOND GEMSTONE (CHROMATIC DISPERSION & GLINTS)
    // =========================================================================
    else if (mat_id < 1.5) {
        // High refractive index (n = 2.42) with prismatic chromatic dispersion
        vec3 R_red   = refract(-V, N, 1.0 / 2.40);
        vec3 R_green = refract(-V, N, 1.0 / 2.42);
        vec3 R_blue  = refract(-V, N, 1.0 / 2.44);

        float fire_r = pow(max(dot(R_red, L_key), 0.0), 8.0) * 0.75;
        float fire_g = pow(max(dot(R_green, L_key), 0.0), 8.0) * 0.75;
        float fire_b = pow(max(dot(R_blue, L_key), 0.0), 8.0) * 0.95;
        vec3 fire = vec3(fire_r, fire_g, fire_b);

        // Extreme facet specular glints
        float spec_glint = pow(max(dot(N, H_key), 0.0), 128.0) * 3.5
                         + pow(max(dot(N, H_top), 0.0), 96.0) * 2.8;

        // Facet edge highlights
        float facet_rim = pow(1.0 - NdotV, 2.0) * 0.95;

        vec3 diamond_body = v_color * 0.30;
        final_rgb = diamond_body + fire + vec3(spec_glint) + vec3(0.6, 0.85, 1.0) * facet_rim;

        // Completion flash bloom
        if (u_flash > 0.01) {
            final_rgb += vec3(1.2, 1.4, 1.8) * u_flash * 2.5;
        }
    }

    // =========================================================================
    // MATERIAL 2: STUDIO FLOOR PLATFORM & SOFT SHADOW
    // =========================================================================
    else {
        float r = length(v_world_pos.xz);
        float floor_falloff = smoothstep(4.2, 1.0, r);
        float shadow = smoothstep(0.0, 1.2, length(v_world_pos.xz));

        vec3 floor_base = vec3(0.04, 0.045, 0.055) * floor_falloff;
        float floor_spec = pow(max(dot(N, H_top), 0.0), 32.0) * 0.25 * floor_falloff;

        final_rgb = floor_base * (0.4 + 0.6 * shadow) + vec3(floor_spec);
    }

    // --- LUMINOUS GROWTH FRONTIER SPARK EDGE ---
    if (mat_id < 1.5 && u_growth < 0.999) {
        float dist_to_frontier = u_growth - v_growth;
        if (dist_to_frontier >= 0.0 && dist_to_frontier < 0.035) {
            float frontier_glow = (1.0 - dist_to_frontier / 0.035);
            // Brilliant crystalline spark rim
            vec3 spark_col = vec3(0.4, 0.9, 1.2) * 4.0;
            final_rgb += spark_col * frontier_glow;
        }
    }

    frag_color = vec4(final_rgb, 1.0);
}
"""

# --- 2. CONCENTRIC HOLLOW HALO SHOCKWAVE POST-PROCESS SHADER ---
SHOCKWAVE_VERT_SRC = """
#version 330 core

layout (location = 0) in vec2 in_pos;
out vec2 v_uv;

void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

SHOCKWAVE_FRAG_SRC = """
#version 330 core

in vec2 v_uv;

uniform vec2 u_center;          // Screen center in UV space (0.5, 0.5)
uniform float u_aspect;         // Width / Height
uniform float u_shock_radius;   // Current expanding radius (0.0 to 2.2)
uniform float u_shock_alpha;    // Fade intensity (1.0 down to 0.0)
uniform float u_time;

out vec4 frag_color;

void main() {
    if (u_shock_alpha < 0.005) {
        discard;
    }

    // Normalized radial distance from shockwave center with aspect ratio correction
    vec2 p = v_uv - u_center;
    p.x *= u_aspect;
    float dist = length(p);

    vec3 glow_color = vec3(0.0);

    // 3 Concentric Hollow Halo Rings:
    // Main shockwave wave, secondary trailing wave, and outer leading ripple
    float radii[3] = float[3](u_shock_radius, u_shock_radius * 0.82, u_shock_radius * 0.65);
    float weights[3] = float[3](1.0, 0.65, 0.35);
    float thicknesses[3] = float[3](0.045, 0.035, 0.025);

    for (int i = 0; i < 3; ++i) {
        float r = radii[i];
        if (r > 0.01) {
            float ring_dist = abs(dist - r);
            float thick = thicknesses[i];
            if (ring_dist < thick) {
                // Hollow ring profile (sharp peak at r, smooth Gaussian falloff)
                float edge = 1.0 - ring_dist / thick;
                float halo = pow(edge, 2.5) * weights[i];

                // Radiant diamond cyan/white energy
                vec3 ring_col = mix(vec3(0.5, 0.85, 1.0), vec3(1.0, 1.0, 1.2), edge);
                glow_color += ring_col * halo;
            }
        }
    }

    // Central radiant burst when shockwave first ignites (r < 0.3)
    if (u_shock_radius < 0.45) {
        float core = exp(-pow(dist, 2.0) * 28.0) * (1.0 - u_shock_radius / 0.45);
        glow_color += vec3(1.2, 1.3, 1.6) * core * 1.5;
    }

    float total_alpha = clamp(length(glow_color) * u_shock_alpha, 0.0, 1.0);
    frag_color = vec4(glow_color * u_shock_alpha, total_alpha);
}
"""

# --- 3. STUDIO BACKGROUND & SOFT LIGHT SHADER ---
BG_VERT_SRC = """
#version 330 core

layout (location = 0) in vec2 in_pos;
out vec2 v_uv;

void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.9999, 1.0);
}
"""

BG_FRAG_SRC = """
#version 330 core

in vec2 v_uv;
uniform float u_time;
uniform vec2 u_resolution;

out vec4 frag_color;

void main() {
    vec2 p = (v_uv - 0.5) * 2.0;

    // Obsidian black deep studio backdrop
    vec3 col_center = vec3(0.035, 0.045, 0.065);
    vec3 col_edge   = vec3(0.005, 0.006, 0.009);

    float vignette = length(p * vec2(1.0, 1.25));
    vec3 bg = mix(col_center, col_edge, smoothstep(0.1, 1.4, vignette));

    // Subtle overhead soft spotlight cone
    float spot = exp(-pow(p.x, 2.0) * 3.5) * exp(-pow(p.y - 0.4, 2.0) * 1.5) * 0.06;
    bg += vec3(0.6, 0.75, 0.95) * spot;

    // Gentle breathing floating bokeh particles
    float bokeh = sin(p.x * 12.0 + u_time * 0.4) * cos(p.y * 12.0 - u_time * 0.3);
    if (bokeh > 0.92) {
        bg += vec3(0.3, 0.5, 0.7) * (bokeh - 0.92) * 0.8;
    }

    frag_color = vec4(bg, 1.0);
}
"""
