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

// Pseudo-random hash for procedural stars and city lights
float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main() {
    vec2 uv = v_uv;
    
    // 1. Calm Evening Sky Gradient (Sunset transitioning into Twilight Stars)
    // Deep twilight indigo at the zenith
    vec3 c_zenith   = vec3(0.04, 0.06, 0.16);
    // Twilight royal blue / dusky violet
    vec3 c_twilight = vec3(0.12, 0.13, 0.28);
    // Evening magenta / dusty rose
    vec3 c_rose     = vec3(0.46, 0.20, 0.35);
    // Warm golden-amber sunset glow at horizon
    vec3 c_sunset   = vec3(0.92, 0.52, 0.22);
    // Golden horizon sunburst
    vec3 c_sunglow  = vec3(1.00, 0.76, 0.42);

    float y = uv.y;
    vec3 sky;
    if (y > 0.52) {
        float f = (y - 0.52) / 0.48;
        sky = mix(c_twilight, c_zenith, pow(f, 0.85));
    } else if (y > 0.26) {
        float f = (y - 0.26) / 0.26;
        sky = mix(c_sunset, c_twilight, pow(f, 0.75));
    } else {
        float f = y / 0.26;
        sky = mix(c_sunglow, c_sunset, pow(f, 0.65));
    }

    // 2. Setting Sun Disk & Sunset Atmospheric Halo
    vec2 sun_pos = vec2(0.58, 0.38);
    float aspect = u_resolution.x / max(1.0, u_resolution.y);
    vec2 sun_delta = (uv - sun_pos) * vec2(aspect, 1.0);
    float sun_dist = length(sun_delta);
    
    // Setting sun disk dipping into the distant evening city skyline
    float sun_disk = smoothstep(0.055, 0.030, sun_dist);
    // Expansive warm sunset flare and crepuscular sky glow
    float sun_halo = exp(-sun_dist * 3.2) * 1.10;
    // Sunset horizontal ray streaks
    float sun_rays = exp(-abs(uv.y - sun_pos.y) * 14.0) * exp(-abs(uv.x - sun_pos.x) * 3.5) * 0.40;
    sky += c_sunglow * (sun_disk * 2.0 + sun_halo * 0.65 + sun_rays);

    // 3. Evening Stars roughly appearing in the upper twilight sky
    if (uv.y > 0.42) {
        float star_fade = smoothstep(0.42, 0.74, uv.y);
        
        // Multi-scale star grid
        vec2 star_uv = uv * vec2(52.0, 38.0);
        vec2 grid_id = floor(star_uv);
        vec2 grid_f  = fract(star_uv) - 0.5;

        float rnd = hash21(grid_id);
        if (rnd > 0.70) {
            vec2 offset = vec2(hash21(grid_id + 1.2) - 0.5, hash21(grid_id + 3.7) - 0.5) * 0.7;
            float d_star = length(grid_f - offset);
            
            float twinkle = 0.65 + 0.35 * sin(u_time * (1.8 + rnd * 2.2) + rnd * 15.0);
            float star_bright = smoothstep(0.14, 0.0, d_star) * (rnd - 0.70) * 4.2 * twinkle;
            
            vec3 star_col = mix(vec3(0.85, 0.92, 1.0), vec3(1.0, 0.96, 0.82), rnd * 0.5);
            sky += star_col * star_bright * star_fade;
        }

        // The Evening Star (Venus) shining brightly in the dusk sky
        vec2 venus_pos = vec2(0.28, 0.75);
        float d_venus = length((uv - venus_pos) * vec2(aspect, 1.0));
        float venus_core = smoothstep(0.014, 0.001, d_venus);
        float venus_glow = exp(-d_venus * 45.0) * 0.70;
        sky += vec3(0.96, 0.98, 1.0) * (venus_core + venus_glow) * star_fade;
    }

    // 4. Distant Blurred City Shadow Silhouette on the Horizon ("city seem like blur showdaw")
    // Natural expansive skyline with layered high-rises and architectural silhouettes
    float city_x = uv.x * 18.0;
    float block_id = floor(city_x);
    float block_f = fract(city_x);

    // Varied building widths and heights
    float h1 = 0.34 + 0.09 * hash21(vec2(block_id, 13.7));
    float h2 = 0.34 + 0.09 * hash21(vec2(block_id + 1.0, 13.7));
    
    // Landmark high-rise towers
    if (mod(block_id, 4.0) < 1.0) h1 += 0.07 * hash21(vec2(block_id, 41.2));
    if (mod(block_id, 7.0) < 1.0) h1 += 0.10 * hash21(vec2(block_id, 83.1));
    if (abs(block_id - 12.0) < 0.9) h1 += 0.14; // Tokyo Tower / Central Spire

    // Stepped building rooftops with smooth blurred transitions
    float step_f = smoothstep(0.08, 0.22, block_f) * (1.0 - smoothstep(0.78, 0.92, block_f));
    float city_height = mix(0.32, h1, step_f);

    // Soft camera lens bokeh blur on distant skyline
    float blur_factor = 0.026;
    float city_mask = smoothstep(city_height + blur_factor, city_height - blur_factor, uv.y);
    city_mask *= smoothstep(0.24, 0.34, uv.y);

    // Distant blurred city shadow silhouette
    vec3 c_city_shadow = mix(vec3(0.08, 0.09, 0.16), c_sunset * 0.42, 0.32);
    sky = mix(sky, c_city_shadow, city_mask * 0.92);

    // Warm bokeh city night lights shimmering inside the blur shadow
    if (city_mask > 0.08 && uv.y < city_height) {
        vec2 light_grid = uv * vec2(120.0, 90.0);
        float l_id = hash21(floor(light_grid));
        if (l_id > 0.60) {
            float l_twinkle = 0.70 + 0.30 * sin(u_time * 2.8 + l_id * 37.0);
            vec3 l_col = mix(vec3(1.0, 0.84, 0.45), vec3(0.68, 0.90, 1.0), l_id * 0.35);
            sky += l_col * (l_id - 0.60) * 3.0 * l_twinkle * city_mask;
        }
        // Blinking red aviation beacon on central spire
        if (abs(block_id - 12.0) < 0.9 && uv.y > (city_height - 0.03)) {
            float beacon = step(0.5, fract(u_time * 1.0));
            sky += vec3(1.0, 0.18, 0.18) * 2.0 * beacon * city_mask;
        }
    }

    // 5. Soft evening atmosphere vignette
    vec2 vc = uv - vec2(0.5);
    float vignette = 1.0 - dot(vc, vc) * 0.26;
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
    vec3 wire_color = mix(
        vec3(0.20, 0.95, 0.65), // cyber emerald for wood & grass
        vec3(0.98, 0.48, 0.82), // neon sakura pink for petals
        step(0.35, v_color.r)
    );
    wire_color = mix(wire_color, vec3(1.0, 1.0, 1.0), is_edge * is_edge * 0.4);

    // 2. Evening Sunset Lighting & Subsurface Scattering (SSS)
    float vein = sin(v_uv.y * 36.0) * 0.02 * smoothstep(0.1, 0.7, v_uv.x);
    vec3 base_color = v_color + vec3(vein);

    // Warm setting sun key light (low on horizon, golden-amber)
    vec3 light_dir1 = normalize(vec3(0.35, 0.42, 0.85));
    vec3 light_col1 = vec3(1.00, 0.78, 0.52) * 1.05;

    // Cool twilight sky ambient fill (from top-back)
    vec3 light_dir2 = normalize(vec3(-0.45, 0.85, -0.40));
    vec3 light_col2 = vec3(0.40, 0.52, 0.72) * 0.75;

    vec3 ambient = vec3(0.24, 0.28, 0.35) * base_color;

    // Half-Lambert diffuse wrap for paper-thin floral translucency & lush grass
    float NdotL1 = dot(N, light_dir1);
    float wrap1 = max(0.0, NdotL1 * 0.6 + 0.4);
    float NdotL2 = max(0.0, dot(N, light_dir2));
    vec3 diffuse = (wrap1 * light_col1 + NdotL2 * light_col2 * 0.6) * base_color;

    // Specular highlight
    vec3 H1 = normalize(light_dir1 + V);
    float NdotH1 = max(0.0, dot(N, H1));
    float spec1 = pow(NdotH1, v_mat.z) * v_mat.y;
    vec3 specular = spec1 * vec3(1.0, 0.92, 0.78);

    // Subsurface Scattering (SSS) & Fresnel rim ONLY for delicate floral petals
    float is_petal = step(0.35, v_color.r);
    float is_grass = step(v_color.r * 1.15, v_color.g);

    float sss_factor = v_mat.x * is_petal;
    float back_scatter = pow(max(0.0, dot(-light_dir1, V)), 2.0) * sss_factor;
    vec3 sss_color = base_color * vec3(1.40, 0.42, 0.62) * back_scatter * 0.95;

    // Soft Fresnel rim glow (only on petals)
    float fresnel = pow(1.0 - max(0.0, dot(N, V)), 3.0) * is_petal;
    vec3 rim = fresnel * vec3(1.0, 0.80, 0.90) * 0.40;

    // Enhanced vibrant green grass lighting with soft organic meadow gradient
    float grass_dist = length(v_world_pos.xz);
    float grass_shade = 1.0 - smoothstep(1.0, 4.8, grass_dist) * 0.18;
    vec3 grass_base = base_color * grass_shade;
    vec3 grass_light = grass_base * (wrap1 * light_col1 * 1.30 + light_col2 * 0.90 + ambient * 1.40);
    vec3 standard_surface = ambient + diffuse + specular + sss_color + rim;

    vec3 shaded_surface = mix(standard_surface, grass_light, is_grass);

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
