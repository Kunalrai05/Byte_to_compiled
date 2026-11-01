"""
GLSL Shaders for procedural botanical rendering.
Includes wireframe glow, Blinn-Phong lighting, Subsurface Scattering (SSS),
procedural petal papillae freckles, and stage materialization effects.
"""

BOTANICAL_VERTEX_SHADER = """
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

    // Growth progression
    float wire_a = clamp((u_time - wire_t0) / max(0.001, wire_t1 - wire_t0), 0.0, 1.0);
    // Smooth easing
    wire_a = wire_a * wire_a * (3.0 - 2.0 * wire_a);

    float surf_a = clamp((u_time - surf_t0) / max(0.001, surf_t1 - surf_t0), 0.0, 1.0);
    surf_a = surf_a * surf_a * (3.0 - 2.0 * surf_a);

    // Subtle breathing displacement
    vec3 pos = in_position;
    if (u_time > 10.0) {
        float breathe = sin(u_time * 1.5 + pos.y * 2.0) * 0.008;
        pos += in_normal * breathe;
    }

    vec4 world_pos = m_model * vec4(pos, 1.0);
    v_world_pos = world_pos.xyz;
    
    // Normal transform
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

BOTANICAL_FRAGMENT_SHADER = """
#version 330

uniform vec3 u_cam_pos;
uniform float u_time;
uniform int u_wireframe_mode; // 0 = normal mix, 1 = wireframe only, 2 = shaded only

in vec3 v_world_pos;
in vec3 v_normal;
in vec3 v_color;
in vec3 v_bary;
in vec2 v_uv;
in float v_wire_alpha;
in float v_surf_alpha;
in vec3 v_mat;

out vec4 fragColor;

// Procedural 2D noise / hash for papillae dots
float hash2(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main() {
    // If element hasn't started growing, discard
    if (v_wire_alpha <= 0.001) {
        discard;
    }

    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world_pos);

    // 1. Barycentric Wireframe calculation with screen-space anti-aliasing
    vec3 d = fwidth(v_bary);
    vec3 a3 = smoothstep(vec3(0.0), d * 1.15, v_bary);
    float edge_factor = min(min(a3.x, a3.y), a3.z);
    float is_edge = 1.0 - edge_factor;

    // Glowing wireframe colors:
    // Cyan/Green for foliage, Neon Magenta/White for petals
    vec3 wire_color = mix(
        vec3(0.20, 0.95, 0.45), // neon green foliage
        vec3(0.98, 0.45, 0.88), // neon magenta petals
        step(0.4, v_color.r)
    );
    // Wireframe glow core
    wire_color = mix(wire_color, vec3(1.0, 1.0, 1.0), is_edge * is_edge * 0.4);

    // 2. Surface Papillae (Oriental Lily raised magenta freckles along inner midrib)
    vec3 base_color = v_color;
    if (v_color.r > 0.5) { // Petal element
        float u_coord = v_uv.x;
        float v_coord = v_uv.y;
        float dist_midrib = abs(v_coord - 0.5) * 2.0;

        // Spots concentrated along lower-middle midrib
        if (dist_midrib < 0.65 && u_coord > 0.15 && u_coord < 0.82) {
            vec2 spot_grid = vec2(u_coord * 42.0, dist_midrib * 22.0);
            vec2 grid_id = floor(spot_grid);
            vec2 grid_uv = fract(spot_grid) - 0.5;

            float rnd = hash2(grid_id);
            if (rnd > 0.45) {
                float spot_rad = 0.28 * (1.0 - u_coord * 0.5);
                float d_spot = length(grid_uv);
                float spot_mask = smoothstep(spot_rad, spot_rad * 0.5, d_spot);
                vec3 papillae_color = vec3(0.55, 0.04, 0.22); // Deep burgundy/crimson
                base_color = mix(base_color, papillae_color, spot_mask * 0.92);
            }
        }
    }

    // 3. Lighting calculation (Blinn-Phong + Subsurface Scattering)
    vec3 light_dir1 = normalize(vec3(0.5, 1.0, 0.8));
    vec3 light_col1 = vec3(0.95, 0.92, 0.88); // Soft warm key

    vec3 light_dir2 = normalize(vec3(-0.7, -0.2, -0.6));
    vec3 light_col2 = vec3(0.25, 0.45, 0.65); // Subtle cool rim

    vec3 ambient = vec3(0.05, 0.06, 0.08) * base_color;

    // Diffuse with half-Lambert wrap for organic softness
    float NdotL1 = dot(N, light_dir1);
    float wrap1 = max(0.0, NdotL1 * 0.5 + 0.5);
    float NdotL2 = max(0.0, dot(N, light_dir2));
    vec3 diffuse = (wrap1 * light_col1 + NdotL2 * light_col2 * 0.5) * base_color;

    // Blinn-Phong Specular
    vec3 H1 = normalize(light_dir1 + V);
    float NdotH1 = max(0.0, dot(N, H1));
    float spec1 = pow(NdotH1, v_mat.z) * v_mat.y;

    vec3 specular = spec1 * vec3(1.0, 0.98, 0.95);

    // Subsurface Scattering (SSS): Organic petal translucency
    float sss_factor = v_mat.x;
    float back_scatter = pow(max(0.0, dot(-light_dir1, V)), 2.2) * sss_factor;
    vec3 sss_color = base_color * vec3(1.1, 0.4, 0.6) * back_scatter * 0.75;

    // Fresnel Rim lighting
    float fresnel = pow(1.0 - max(0.0, dot(N, V)), 3.0);
    vec3 rim = fresnel * vec3(0.7, 0.85, 1.0) * 0.35;

    vec3 shaded_surface = ambient + diffuse + specular + sss_color + rim;

    // 4. Composition & Materialization
    // Stage 1 & 2: Glowing Wireframe
    // Stage 3: Smooth transition into photorealistic shaded botanical specimen
    float wire_glow = is_edge * v_wire_alpha;
    vec3 final_rgb;

    if (u_wireframe_mode == 1) {
        // Pure wireframe
        if (is_edge < 0.1) discard;
        final_rgb = wire_color * 1.4;
    } else if (u_wireframe_mode == 2) {
        // Pure shaded
        final_rgb = shaded_surface;
    } else {
        // Cinematic bloom & materialization
        vec3 wire_layer = wire_color * wire_glow * 1.5;
        vec3 surface_layer = shaded_surface * v_surf_alpha;

        // Residual faint technical wireframe overlay for futuristic cyber aesthetic
        float tech_wire = is_edge * 0.18 * (1.0 - v_surf_alpha * 0.7);

        final_rgb = surface_layer + wire_layer * (1.0 - v_surf_alpha * 0.82) + wire_color * tech_wire;
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
out float v_size;

void main() {
    vec3 pos = in_position;
    
    // Drifting motion in 3D
    float t = u_time * in_speed + in_phase;
    pos.x += sin(t * 0.8) * 0.18;
    pos.y += mod(u_time * 0.08 * in_speed + in_phase * 0.2, 2.8) - 1.4;
    pos.z += cos(t * 0.7) * 0.18;

    vec4 view_pos = m_view * m_model * vec4(pos, 1.0);
    gl_Position = m_proj * view_pos;

    // Size attenuation with distance
    float dist = length(view_pos.xyz);
    gl_PointSize = clamp((in_radius * 800.0) / max(0.5, dist), 2.0, 48.0);

    // Pulsing brightness
    v_alpha = 0.5 + 0.5 * sin(t * 1.5);
}
"""

PARTICLE_FRAGMENT_SHADER = """
#version 330

in float v_alpha;
out vec4 fragColor;

void main() {
    // Soft circular particle shape (Gaussian / smoothstep bokeh)
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) {
        discard;
    }

    float bokeh = smoothstep(0.5, 0.0, dist);
    bokeh = pow(bokeh, 1.6);

    // Warm golden pollen glow
    vec3 col = mix(vec3(1.0, 0.88, 0.55), vec3(1.0, 0.45, 0.75), coord.y + 0.5);
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
