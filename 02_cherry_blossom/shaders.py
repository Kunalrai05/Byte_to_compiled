"""
GLSL Shaders for procedural Cherry Blossom (Prunus Serrulata) rendering.
Includes paper-thin translucent petal Subsurface Scattering (SSS),
gnarled wood Blinn-Phong lighting, falling petal kinematics, and barycentric wireframe glow.
"""

SAKURA_VERTEX_SHADER = """
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
in vec3 in_mat;    // sss_strength, spec_strength, shininess

out vec3 v_world_pos;
out vec3 v_normal;
out vec3 v_color;
out vec3 v_bary;
out vec2 v_uv;
out float v_wire_alpha;
out float v_surf_alpha;
out vec3 v_mat;

void main() {
    float wire_t0 = in_timing.x;
    float wire_t1 = in_timing.y;
    float surf_t0 = in_timing.z;
    float surf_t1 = in_timing.w;

    // Smooth growth easing
    float wire_a = clamp((u_time - wire_t0) / max(0.001, wire_t1 - wire_t0), 0.0, 1.0);
    wire_a = wire_a * wire_a * (3.0 - 2.0 * wire_a);

    float surf_a = clamp((u_time - surf_t0) / max(0.001, surf_t1 - surf_t0), 0.0, 1.0);
    surf_a = surf_a * surf_a * (3.0 - 2.0 * surf_a);

    vec3 pos = in_position;
    
    // Hanafubuki: Tumbling falling petals drifting in spring breeze
    if (in_timing.x >= 6.8) {
        float fall_t = max(0.0, u_time - 6.8);
        float fall_dist = mod(fall_t * (0.28 + in_mat.y * 0.2), 3.6) - 1.8;
        pos.y -= fall_dist;
        pos.x += sin(fall_t * 1.5 + in_mat.z) * 0.28 + fall_t * 0.04;
        pos.z += cos(fall_t * 1.1 + in_mat.z) * 0.20;

        // Aerodynamic pitch & roll tumbling
        float roll = fall_t * 2.8 + in_mat.z;
        float cr = cos(roll);
        float sr = sin(roll);
        vec3 p_rot = pos;
        p_rot.x = pos.x * cr - pos.y * sr * 0.2;
        p_rot.y = pos.x * sr * 0.2 + pos.y;
        pos = p_rot;
    } else if (u_time > 8.0) {
        // Gentle tree sway
        float wind = sin(u_time * 1.8 + pos.x * 2.0 + pos.y * 1.5) * 0.012;
        pos.x += wind * smoothstep(0.0, 1.0, pos.y);
    }

    vec4 world_pos = m_model * vec4(pos, 1.0);
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

SAKURA_FRAGMENT_SHADER = """
#version 330

uniform vec3 u_cam_pos;
uniform float u_time;
uniform int u_wireframe_mode; // 0 = hybrid mix, 1 = wireframe only, 2 = shaded only

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
    if (v_wire_alpha <= 0.001) {
        discard;
    }

    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world_pos);

    // 1. Barycentric Wireframe calculation with anti-aliasing
    vec3 d = fwidth(v_bary);
    vec3 a3 = smoothstep(vec3(0.0), d * 1.15, v_bary);
    float edge_factor = min(min(a3.x, a3.y), a3.z);
    float is_edge = 1.0 - edge_factor;

    // Wireframe colors:
    // Cyan/Green for wood branch, Neon Sakura Rose for petals
    vec3 wire_color = mix(
        vec3(0.25, 0.95, 0.75), // cyan-green wood
        vec3(0.98, 0.48, 0.82), // neon sakura pink
        step(0.35, v_color.r)
    );
    wire_color = mix(wire_color, vec3(1.0, 1.0, 1.0), is_edge * is_edge * 0.4);

    // 2. Dual-Source Lighting + Subsurface Scattering (SSS)
    // Subtle organic petal vein micro-texture using UV coordinates
    float vein = sin(v_uv.y * 42.0) * 0.025 * smoothstep(0.1, 0.7, v_uv.x);
    vec3 base_color = v_color + vec3(vein);

    vec3 light_dir1 = normalize(vec3(0.5, 1.0, 0.75));
    vec3 light_col1 = vec3(0.95, 0.90, 0.86) * 0.85; // Soft warm sunlight

    vec3 light_dir2 = normalize(vec3(-0.7, -0.3, -0.5));
    vec3 light_col2 = vec3(0.30, 0.50, 0.75) * 0.50; // Cool sky rim

    vec3 ambient = vec3(0.12, 0.12, 0.15) * base_color;

    // Half-Lambert diffuse wrap for paper-thin floral translucency
    float NdotL1 = dot(N, light_dir1);
    float wrap1 = max(0.0, NdotL1 * 0.5 + 0.5);
    float NdotL2 = max(0.0, dot(N, light_dir2));
    vec3 diffuse = (wrap1 * light_col1 + NdotL2 * light_col2 * 0.5) * base_color;

    // Specular highlight (moist delicate petal gloss)
    vec3 H1 = normalize(light_dir1 + V);
    float NdotH1 = max(0.0, dot(N, H1));
    float spec1 = pow(NdotH1, v_mat.z) * v_mat.y;
    vec3 specular = spec1 * vec3(1.0, 0.96, 0.92);

    // Subsurface Scattering (SSS): Light passing through delicate petal tissue
    float sss_factor = v_mat.x;
    float back_scatter = pow(max(0.0, dot(-light_dir1, V)), 2.0) * sss_factor;
    vec3 sss_color = base_color * vec3(1.35, 0.40, 0.65) * back_scatter * 0.95;

    // Soft Fresnel rim glow
    float fresnel = pow(1.0 - max(0.0, dot(N, V)), 3.0);
    vec3 rim = fresnel * vec3(0.95, 0.85, 1.0) * 0.35;

    vec3 shaded_surface = ambient + diffuse + specular + sss_color + rim;

    // 3. Composition & Stage Materialization
    float wire_glow = is_edge * v_wire_alpha;
    vec3 final_rgb;

    if (u_wireframe_mode == 1) {
        if (is_edge < 0.1) discard;
        final_rgb = wire_color * 1.4;
    } else if (u_wireframe_mode == 2) {
        final_rgb = shaded_surface;
    } else {
        vec3 wire_layer = wire_color * wire_glow * 1.4;
        vec3 surface_layer = shaded_surface * v_surf_alpha;
        
        // Hide tech wireframe on wood branch in Stage 3, keep subtle glow on petals
        float is_petal = step(0.35, v_color.r);
        float tech_wire = is_edge * (is_petal * 0.12) * (1.0 - v_surf_alpha * 0.85);

        final_rgb = surface_layer + wire_layer * (1.0 - v_surf_alpha * 0.88) + wire_color * tech_wire;
    }

    fragColor = vec4(final_rgb, max(v_wire_alpha, v_surf_alpha));
}
"""

PARTICLE_VERTEX_SHADER = """
#version 330

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform float u_time;

in vec3 in_position;
in float in_phase;
in float in_speed;
in float in_radius;

out float v_alpha;

void main() {
    vec3 pos = in_position;
    
    // Drifting motion in spring breeze
    float t = u_time * in_speed + in_phase;
    pos.x += sin(t * 0.7) * 0.22;
    pos.y += mod(u_time * 0.09 * in_speed + in_phase * 0.3, 3.2) - 1.6;
    pos.z += cos(t * 0.6) * 0.22;

    vec4 view_pos = m_view * m_model * vec4(pos, 1.0);
    gl_Position = m_proj * view_pos;

    float dist = length(view_pos.xyz);
    gl_PointSize = clamp((in_radius * 850.0) / max(0.5, dist), 2.0, 45.0);

    v_alpha = 0.5 + 0.5 * sin(t * 1.4);
}
"""

PARTICLE_FRAGMENT_SHADER = """
#version 330

in float v_alpha;
out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) {
        discard;
    }

    float bokeh = smoothstep(0.5, 0.0, dist);
    bokeh = pow(bokeh, 1.6);

    // Warm golden-pink pollen glow
    vec3 col = mix(vec3(1.0, 0.90, 0.65), vec3(1.0, 0.60, 0.80), coord.y + 0.5);
    fragColor = vec4(col * 1.5, bokeh * v_alpha * 0.85);
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
