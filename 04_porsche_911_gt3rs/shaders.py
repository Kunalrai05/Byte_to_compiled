"""
ModernGL GLSL Shaders for the Porsche 911 GT3 RS Simulation.
Includes:
1. PBR Car Shader: Clearcoat metallic paint, carbon fiber weave, emissive LED lightbar & Matrix LEDs.
2. Active DRS Flap Shader: Dynamic hinge rotation around aerodynamic axis.
3. CFD Streamline Shader: Glowing motion-blurred aerodynamic ribbons.
4. Dark Studio Background Shader: Overhead softbox studio lighting & floor reflections.
5. 2D Orthographic HUD Quad Shader.
"""

# --- 1. PBR CAR & CHASSIS SHADER ---
CAR_VERT_SRC = """
#version 330 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec3 in_color;
layout (location = 3) in vec2 in_uv;
layout (location = 4) in vec3 in_mat;        // [mat_id, roughness, metallic]
layout (location = 5) in vec3 in_morph_pos;  // 1974 930 Turbo heritage position

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_morph; // 0.0 = 1974 930 Turbo, 1.0 = 2024 992 GT3 RS

out vec3 v_world_pos;
out vec3 v_normal;
out vec3 v_color;
out vec2 v_uv;
out vec3 v_mat;
out float v_scan_dist;

void main() {
    // Smooth geometric morphing between 1974 930 and 2024 992 GT3 RS
    vec3 blended_pos = mix(in_morph_pos, in_position, clamp(u_morph, 0.0, 1.0));
    
    vec4 world_p = m_model * vec4(blended_pos, 1.0);
    v_world_pos = world_p.xyz;
    
    mat3 norm_mat = transpose(inverse(mat3(m_model)));
    v_normal = normalize(norm_mat * in_normal);
    
    v_color = in_color;
    v_uv = in_uv;
    v_mat = in_mat;
    v_scan_dist = world_p.z;

    gl_Position = m_proj * m_view * world_p;
}
"""

CAR_FRAG_SRC = """
#version 330 core

in vec3 v_world_pos;
in vec3 v_normal;
in vec3 v_color;
in vec2 v_uv;
in vec3 v_mat;
in float v_scan_dist;

uniform vec3 u_cam_pos;
uniform vec3 u_body_color; // Selected car paint (Arctic Grey, Shark Blue, Guards Red, etc.)
uniform float u_time;
uniform float u_throttle;  // 0.0 to 1.0 engine throttle / RPM
uniform int u_wire_mode;   // 0: Shaded, 1: Wireframe/LiDAR, 2: Hybrid
uniform float u_scan_progress; // LiDAR scan wave across car

out vec4 frag_color;

void main() {
    float mat_id   = v_mat.x;
    float roughness= v_mat.y;
    float metallic = v_mat.z;

    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world_pos);

    // Dynamic car paint replacement for body panels
    vec3 base_color = v_color;
    if (mat_id < 0.5) { // Body panel
        base_color = u_body_color;
        // Subtle micro-surface clearcoat finish using UV coordinates
        float micro_finish = sin(v_uv.x * 48.0) * cos(v_uv.y * 48.0) * 0.03;
        base_color += vec3(micro_finish);
    }

    // Procedural Carbon Fiber weave texture
    if (abs(mat_id - 1.0) < 0.5) {
        float weave = sin(v_world_pos.x * 240.0) * sin(v_world_pos.z * 240.0);
        base_color = mix(vec3(0.08, 0.08, 0.09), vec3(0.18, 0.18, 0.20), clamp(weave * 0.5 + 0.5, 0.0, 1.0));
    }

    // Emissive Lighting Channels:
    // 4.0: 4-Point Matrix LED Headlights
    if (abs(mat_id - 4.0) < 0.5) {
        frag_color = vec4(v_color * 2.2, 1.0);
        return;
    }
    // 5.0: Continuous Rear Red LED Lightbar
    if (abs(mat_id - 5.0) < 0.5) {
        frag_color = vec4(v_color * 3.0, 1.0);
        return;
    }

    // Studio Lighting Setup (3 Key Lights + Soft Overhead Studio Lightbox)
    vec3 light_top = vec3(0.0, 4.8, 0.0);
    vec3 light_front = vec3(2.5, 3.2, -4.0);
    vec3 light_rear  = vec3(-3.0, 2.8, 3.8);

    vec3 L_top   = normalize(light_top - v_world_pos);
    vec3 L_front = normalize(light_front - v_world_pos);
    vec3 L_rear  = normalize(light_rear - v_world_pos);

    // Diffuse Lambertian
    float diff_top   = max(dot(N, L_top), 0.0) * 0.70;
    float diff_front = max(dot(N, L_front), 0.0) * 0.85;
    float diff_rear  = max(dot(N, L_rear), 0.0) * 0.50;

    // Dual-Layer Specular (Sharp Clearcoat + Soft Metallic Lobe)
    vec3 H_top   = normalize(L_top + V);
    vec3 H_front = normalize(L_front + V);
    vec3 H_rear  = normalize(L_rear + V);

    float spec_sharp = pow(max(dot(N, H_top), 0.0), 96.0) * 0.85
                     + pow(max(dot(N, H_front), 0.0), 96.0) * 1.10
                     + pow(max(dot(N, H_rear), 0.0), 96.0) * 0.65;

    float spec_soft  = pow(max(dot(N, H_top), 0.0), 18.0) * 0.35
                     + pow(max(dot(N, H_front), 0.0), 18.0) * 0.45;

    // Fresnel Rim Glow (Extreme sports car metallic curve)
    float NdotV = max(dot(N, V), 0.0);
    float fresnel = pow(1.0 - NdotV, 4.0);

    // Metallic Clearcoat Composite
    vec3 ambient = vec3(0.10, 0.12, 0.15) * base_color;
    vec3 diffuse = (diff_top + diff_front + diff_rear) * base_color;
    vec3 specular = vec3(1.0) * spec_sharp + base_color * spec_soft * metallic;
    vec3 rim = mix(vec3(0.4, 0.6, 0.8), base_color, metallic) * fresnel * 0.65;

    // Titanium Exhaust Heat Glow under hard throttle with heat pulse
    if (abs(mat_id - 8.0) < 0.5) {
        float pulse = 1.0 + 0.15 * sin(u_time * 12.0);
        vec3 heat_glow = vec3(1.8, 0.35, 0.05) * pow(u_throttle, 2.5) * pulse;
        specular += heat_glow;
    }

    // Floor platform reflection and shadow
    if (abs(mat_id - 9.0) < 0.5) {
        float r = length(v_world_pos.xz);
        float circle_fade = smoothstep(3.8, 1.5, r);
        ambient = vec3(0.04, 0.05, 0.06) * circle_fade;
        diffuse = vec3(0.08, 0.09, 0.11) * diff_top * circle_fade;
        specular = vec3(0.15) * pow(max(dot(N, H_top), 0.0), 32.0);
    }

    vec3 final_rgb = ambient + diffuse + specular + rim;

    // LiDAR Hologram Scanning Beam Sweep
    if (u_scan_progress > 0.01 && u_scan_progress < 1.0) {
        float scan_z = mix(-3.0, 3.0, u_scan_progress);
        float dist_to_laser = abs(v_world_pos.z - scan_z);
        if (dist_to_laser < 0.08) {
            float intensity = (1.0 - dist_to_laser / 0.08);
            final_rgb += vec3(0.1, 0.8, 1.0) * intensity * 3.5;
        }
    }

    // Wireframe / LiDAR styling
    if (u_wire_mode == 1) {
        final_rgb = mix(vec3(0.02, 0.05, 0.08), vec3(0.1, 0.85, 1.0), 0.7);
    }

    frag_color = vec4(final_rgb, 1.0);
}
"""

# --- 2. ACTIVE DRS REAR WING FLAP SHADER ---
DRS_VERT_SRC = """
#version 330 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec3 in_color;
layout (location = 3) in vec2 in_uv;
layout (location = 4) in vec3 in_mat;
layout (location = 5) in vec3 in_morph_pos;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_drs_angle; // Angle in radians (0.0 = high downforce, -0.45 = open DRS)
uniform float u_morph;     // 0.0 = 1974 930, 1.0 = 2024 992 GT3 RS

out vec3 v_world_pos;
out vec3 v_normal;
out vec3 v_color;
out vec2 v_uv;
out vec3 v_mat;

void main() {
    // Hinge line is at Y = 1.36, Z = 1.90
    vec3 hinge = vec3(0.0, 1.36, 1.90);
    vec3 blended_p = mix(in_morph_pos, in_position, clamp(u_morph, 0.0, 1.0));

    // Rotate around X-axis relative to hinge
    float c = cos(u_drs_angle);
    float s = sin(u_drs_angle);
    vec3 local_p = blended_p - vec3(0.0, 0.0, 0.0);
    vec3 rot_p;
    rot_p.x = local_p.x;
    rot_p.y = local_p.y * c - local_p.z * s;
    rot_p.z = local_p.y * s + local_p.z * c;

    vec3 final_local = hinge + rot_p;

    vec4 world_p = m_model * vec4(final_local, 1.0);
    v_world_pos = world_p.xyz;

    mat3 norm_mat = transpose(inverse(mat3(m_model)));
    vec3 rot_n;
    rot_n.x = in_normal.x;
    rot_n.y = in_normal.y * c - in_normal.z * s;
    rot_n.z = in_normal.y * s + in_normal.z * c;
    v_normal = normalize(norm_mat * rot_n);

    v_color = in_color;
    v_uv = in_uv;
    v_mat = in_mat;

    gl_Position = m_proj * m_view * world_p;
}
"""

# --- 3. CFD AERODYNAMIC STREAMLINE SHADER ---
STREAMLINE_VERT_SRC = """
#version 330 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_color;
layout (location = 2) in float in_alpha;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

out vec3 v_color;
out float v_alpha;

void main() {
    v_color = in_color;
    v_alpha = in_alpha;
    gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
}
"""

STREAMLINE_FRAG_SRC = """
#version 330 core

in vec3 v_color;
in float v_alpha;

out vec4 frag_color;

void main() {
    // Neon glow ribbon
    frag_color = vec4(v_color * 1.6, v_alpha);
}
"""

# --- 4. STUDIO BACKGROUND & SOFTBOX SHADER ---
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
    
    // Obsidian deep dark studio backdrop
    vec3 col_center = vec3(0.035, 0.045, 0.065);
    vec3 col_edge   = vec3(0.008, 0.010, 0.015);
    
    float vignette = length(p * vec2(1.0, 1.25));
    vec3 bg = mix(col_center, col_edge, smoothstep(0.1, 1.4, vignette));

    // Subtle overhead softbox light reflection glow with breathing pulse
    float breathe = sin(u_time * 0.6) * 0.004;
    float softbox = (exp(-pow(p.y - 0.65, 2.0) * 14.0) * exp(-pow(p.x, 2.0) * 2.8) + breathe) * 0.04;
    bg += vec3(0.1, 0.2, 0.3) * softbox;

    frag_color = vec4(bg, 1.0);
}
"""

# --- 5. 2D HUD OVERLAY SHADER ---
HUD_VERT_SRC = """
#version 330 core

layout (location = 0) in vec2 in_pos;
layout (location = 1) in vec2 in_uv;

out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

HUD_FRAG_SRC = """
#version 330 core

in vec2 v_uv;
uniform sampler2D u_texture;

out vec4 frag_color;

void main() {
    frag_color = texture(u_texture, v_uv);
}
"""
