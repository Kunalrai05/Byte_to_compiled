"""
================================================================================
  GLSL SHADERS — PRUNUS SERRULATA (CHERRY BLOSSOM TREE / 桜の木)
  Includes:
  - Atmospheric Japanese Twilight Dawn Sky, Mount Fuji, and Reflecting Pond
  - Spring Breeze Branch Sway & Aerodynamic Petal Tumbling (Hanafubuki)
  - Petal Subsurface Scattering (SSS) & Paper-Thin Translucency Wrap
  - Barycentric Wireframe Glow with Seamless Photorealistic Transition
  - Floating Bokeh Pollen/Firefly Particles
================================================================================
"""

# -----------------------------------------------------------------------------
# 1. Background Atmospheric Environment Shader (Sky, Mount Fuji, Reflecting Pond)
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
    
    // 1. Serene Japanese Twilight-to-Dawn Sky Gradient
    vec3 c_zenith = vec3(0.035, 0.045, 0.11);   // Deep twilight indigo
    vec3 c_mid    = vec3(0.18, 0.14, 0.28);     // Soft twilight lavender
    vec3 c_dawn   = vec3(0.55, 0.35, 0.44);     // Rosy peach
    vec3 c_glow   = vec3(0.85, 0.68, 0.60);     // Warm golden dawn horizon

    float y = uv.y;
    vec3 sky;
    if (y > 0.40) {
        float f = (y - 0.40) / 0.60;
        sky = mix(c_mid, c_zenith, pow(f, 0.85));
    } else {
        float f = y / 0.40;
        sky = mix(c_glow, c_mid, pow(f, 0.7));
    }

    // 2. Wide, Majestic Mount Fuji Silhouette
    float fuji_cx = 0.65;
    float dx = abs(uv.x - fuji_cx);
    // Authentic broad stratovolcano slope
    float fuji_slope = exp(-pow(dx * 1.8, 1.45)) * 0.34;
    // Flat caldera summit
    float caldera = exp(-pow(dx * 22.0, 2.0)) * 0.014;
    float fuji_base = 0.26;
    float fuji_peak = fuji_base + max(0.0, fuji_slope - caldera);

    if (uv.y < fuji_peak && uv.y >= fuji_base) {
        float snow_line = fuji_base + fuji_slope * 0.58;
        vec3 mountain_rock = vec3(0.18, 0.15, 0.26);
        vec3 mountain_snow = vec3(0.92, 0.88, 0.96);
        float snow_factor = smoothstep(snow_line, fuji_peak, uv.y);
        vec3 mtn_col = mix(mountain_rock, mountain_snow, snow_factor);
        
        float haze = smoothstep(fuji_base, fuji_base + 0.12, uv.y);
        sky = mix(sky, mtn_col, 0.68 * haze);
    }

    // 3. Calm Reflecting Water Pond at bottom
    if (uv.y < 0.22) {
        float water_depth = (0.22 - uv.y) / 0.22;
        float ripple = sin(uv.x * 45.0 + u_time * 1.2) * 0.003 * (1.0 - water_depth);
        float ref_y = 0.22 + (0.22 - uv.y) + ripple;
        
        vec3 water_tint = vec3(0.08, 0.14, 0.22);
        vec3 ref_sky = mix(c_glow, c_mid, clamp(ref_y, 0.0, 1.0));
        vec3 water = mix(ref_sky * 0.65, water_tint, water_depth * 0.55);

        float shore_mist = exp(-pow((uv.y - 0.22) * 18.0, 2.0));
        water = mix(water, vec3(0.75, 0.70, 0.80), shore_mist * 0.45);

        sky = water;
    }

    // 4. Soft morning mist drift
    float mist = sin(uv.x * 5.0 + u_time * 0.2) * 0.5 + 0.5;
    mist *= exp(-pow((uv.y - 0.24) * 12.0, 2.0));
    sky = mix(sky, vec3(0.82, 0.78, 0.88), mist * 0.25);

    // Subtle soft vignette for calm atmosphere
    vec2 vc = uv - vec2(0.5);
    float vignette = 1.0 - dot(vc, vc) * 0.30;
    sky *= vignette;

    fragColor = vec4(sky, 1.0);
}
"""

# -----------------------------------------------------------------------------
# 2. Sakura Tree & Petal Vertex/Fragment Shaders
# -----------------------------------------------------------------------------
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
    
    // Dynamic falling petals kinematics (Hanafubuki)
    // Only petals with active fall_speed (in_mat.y > 0.05) fall; resting ground petals stay put
    if (in_timing.x >= 6.4 && in_mat.y > 0.05) {
        float fall_t = max(0.0, u_time - 6.4);
        float fall_dist = mod(fall_t * (0.24 + in_mat.y * 0.16), 3.2) - 1.6;
        pos.y -= fall_dist;
        pos.x += sin(fall_t * 1.35 + in_mat.z) * 0.32 + fall_t * 0.05;
        pos.z += cos(fall_t * 1.10 + in_mat.z) * 0.22;

        float roll = fall_t * 2.4 + in_mat.z;
        float cr = cos(roll);
        float sr = sin(roll);
        vec3 p_rot = pos;
        p_rot.x = pos.x * cr - pos.y * sr * 0.2;
        p_rot.y = pos.x * sr * 0.2 + pos.y;
        pos = p_rot;
    } else {
        // Peaceful spring breeze swaying the tree branches
        float wind_phase = u_time * 1.35 + pos.x * 0.8 + pos.z * 0.6;
        float wind_sway = (sin(wind_phase) * 0.028 + sin(wind_phase * 2.1) * 0.010);
        float sway_h = smoothstep(-0.6, 1.4, pos.y);
        pos.x += wind_sway * sway_h;
        pos.z += wind_sway * 0.45 * sway_h;
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
    float vein = sin(v_uv.y * 36.0) * 0.02 * smoothstep(0.1, 0.7, v_uv.x);
    vec3 base_color = v_color + vec3(vein);

    // Warm golden dawn sunlight from the right
    vec3 light_dir1 = normalize(vec3(0.65, 0.75, 0.55));
    vec3 light_col1 = vec3(1.0, 0.92, 0.85) * 0.88;

    // Cool skylight fill from top-left
    vec3 light_dir2 = normalize(vec3(-0.55, 0.85, -0.40));
    vec3 light_col2 = vec3(0.35, 0.48, 0.72) * 0.45;

    vec3 ambient = vec3(0.14, 0.13, 0.18) * base_color;

    // Half-Lambert diffuse wrap for paper-thin floral translucency
    float NdotL1 = dot(N, light_dir1);
    float wrap1 = max(0.0, NdotL1 * 0.5 + 0.5);
    float NdotL2 = max(0.0, dot(N, light_dir2));
    vec3 diffuse = (wrap1 * light_col1 + NdotL2 * light_col2 * 0.5) * base_color;

    // Specular highlight
    vec3 H1 = normalize(light_dir1 + V);
    float NdotH1 = max(0.0, dot(N, H1));
    float spec1 = pow(NdotH1, v_mat.z) * v_mat.y;
    vec3 specular = spec1 * vec3(1.0, 0.96, 0.92);

    // Subsurface Scattering (SSS) & Fresnel rim ONLY for delicate floral petals
    float is_petal = step(0.35, v_color.r);

    float sss_factor = v_mat.x * is_petal;
    float back_scatter = pow(max(0.0, dot(-light_dir1, V)), 2.0) * sss_factor;
    vec3 sss_color = base_color * vec3(1.35, 0.40, 0.65) * back_scatter * 0.92;

    // Soft Fresnel rim glow (only on petals)
    float fresnel = pow(1.0 - max(0.0, dot(N, V)), 3.0) * is_petal;
    vec3 rim = fresnel * vec3(0.95, 0.85, 1.0) * 0.35;

    vec3 shaded_surface = ambient + diffuse + specular + sss_color + rim;

    // 3. Composition: Clean cross-fade so Stage 3 is 100% smooth photorealistic!
    vec3 final_rgb;

    if (u_wireframe_mode == 1) {
        if (is_edge < 0.1) discard;
        final_rgb = wire_color * 1.4;
    } else if (u_wireframe_mode == 2) {
        final_rgb = shaded_surface;
    } else {
        // Hybrid mix: Wireframe fades completely away as surface alpha reaches 1.0
        float wire_fade = (1.0 - smoothstep(0.0, 0.85, v_surf_alpha));
        float wire_glow = is_edge * v_wire_alpha * wire_fade;
        vec3 wire_layer = wire_color * wire_glow * 1.5;
        vec3 surface_layer = shaded_surface * v_surf_alpha;
        
        final_rgb = surface_layer + wire_layer;
    }

    fragColor = vec4(final_rgb, max(v_wire_alpha, v_surf_alpha));
}
"""

# -----------------------------------------------------------------------------
# 3. Floating Pollen Bokeh / Firefly Shaders
# -----------------------------------------------------------------------------
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
    pos.x += sin(t * 0.7) * 0.25;
    pos.y += mod(u_time * 0.08 * in_speed + in_phase * 0.3, 3.4) - 1.7;
    pos.z += cos(t * 0.6) * 0.25;

    vec4 view_pos = m_view * m_model * vec4(pos, 1.0);
    gl_Position = m_proj * view_pos;

    float dist = length(view_pos.xyz);
    gl_PointSize = clamp((in_radius * 900.0) / max(0.5, dist), 2.0, 48.0);

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
    vec4 col = texture(u_hud_texture, v_uv);
    fragColor = col;
}
"""
