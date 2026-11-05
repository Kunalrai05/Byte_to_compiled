"""
GLSL Shaders for the Monochrome Coded & Binary Diamond Ring Simulation.
Episode 03: Byte to Compiled.

Includes:
1. RING_VERT_SRC & RING_FRAG_SRC (Pass 1):
   Renders 3D parametric ring band, 4 prongs, and brilliant-cut diamond to an offscreen FBO.
   Outputs [Luminance, Growth Coordinate, Material ID, Visibility].
2. CODED_VERT_SRC & CODED_FRAG_SRC (Pass 2):
   Rasterizes the 3D scene into a dense monochrome Black & White matrix grid of
   pixelated binary digits ('0', '1') and coded keywords ('def', 'vec', 'gem', 'void', '{}', '<>').
   Implements bottom-to-top growth ignition, concentric halo shockwave ripples, and 3D facet glints.
"""

# =============================================================================
# PASS 1: 3D PARAMETRIC RING RENDER TO OFFSCREEN FBO
# =============================================================================
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
uniform float u_growth; // 0.0 to 1.0 (materialization frontier)
uniform float u_time;
uniform float u_flash;

out vec4 frag_color;

void main() {
    float mat_id    = v_mat.x;
    float roughness = v_mat.y;
    float metallic  = v_mat.z;

    // Discard floor geometry if any, and discard unmaterialized ring fragments
    if (mat_id > 1.5) {
        discard;
    }
    if (v_growth > u_growth) {
        discard;
    }

    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world_pos);

    // Studio Lighting setup
    vec3 L_key = normalize(vec3(1.8, 3.2, 2.4) - v_world_pos);
    vec3 L_fill = normalize(vec3(-2.2, 1.8, 1.5) - v_world_pos);
    vec3 L_top  = normalize(vec3(0.0, 4.5, 0.0) - v_world_pos);

    vec3 H_key = normalize(L_key + V);
    vec3 H_top = normalize(L_top + V);

    float NdotV = max(dot(N, V), 0.0);
    float fresnel = pow(1.0 - NdotV, 3.0);

    float lum = 0.0;

    if (mat_id < 0.5) {
        // Platinum Band & Prongs: Sharp metallic specular highlights and diffuse
        float diff_key = max(dot(N, L_key), 0.0) * 0.65;
        float diff_fill = max(dot(N, L_fill), 0.0) * 0.30;
        float diff_top  = max(dot(N, L_top),  0.0) * 0.45;

        float spec_sharp = pow(max(dot(N, H_key), 0.0), 48.0) * 1.50
                         + pow(max(dot(N, H_top), 0.0), 64.0) * 1.80;
        float rim = fresnel * 0.70;

        lum = 0.15 + (diff_key + diff_fill + diff_top) * 0.55 + spec_sharp + rim;
        float micro = sin(v_uv.x * 64.0) * cos(v_uv.y * 64.0) * 0.02;
        lum += micro;
    } else {
        // Brilliant-cut Diamond Gemstone: High refractive index facet dispersion
        float diff_key = max(dot(N, L_key), 0.0) * 0.50;
        float spec_facet = pow(max(dot(N, H_key), 0.0), 96.0) * 2.80
                         + pow(max(dot(N, H_top), 0.0), 128.0) * 3.20;
        float facet_rim = pow(1.0 - NdotV, 2.0) * 1.10;

        lum = 0.30 + diff_key * 0.40 + spec_facet + facet_rim;

        if (u_flash > 0.01) {
            lum += u_flash * 2.5;
        }
    }

    // Ensure v_color contributes to output so GLSL attribute is preserved
    float color_weight = dot(v_color, vec3(0.299, 0.587, 0.114));
    lum = lum * max(0.5, color_weight);

    // Output: [Luminance, Growth Coordinate, Material ID, Visibility]
    frag_color = vec4(clamp(lum, 0.0, 2.5), v_growth, mat_id, 1.0);
}
"""

# =============================================================================
# PASS 2: FULLSCREEN BLACK & WHITE CODED & BINARY MATRIX SHADER
# =============================================================================
CODED_VERT_SRC = """
#version 330 core

layout (location = 0) in vec2 in_pos;
out vec2 v_uv;

void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

CODED_FRAG_SRC = """
#version 330 core

in vec2 v_uv;

uniform sampler2D u_ring_tex;
uniform sampler2D u_font_atlas;
uniform vec2 u_resolution;
uniform vec2 u_cell_size;
uniform float u_time;
uniform float u_growth;
uniform float u_shock_radius;
uniform float u_shock_alpha;
uniform vec2 u_shock_center;
uniform int u_mode;          // 0 = Coded & Binary, 1 = Pure Binary, 2 = ASCII Density
uniform float u_bg_noise;    // Subtle background ambient noise

out vec4 frag_color;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main() {
    // 1. Calculate cell grid coordinates
    vec2 pixel_pos = gl_FragCoord.xy;
    vec2 cell_idx = floor(pixel_pos / u_cell_size);
    vec2 in_cell = fract(pixel_pos / u_cell_size);

    // Invert Y for OpenGL font texture coordinates
    in_cell.y = 1.0 - in_cell.y;

    // 2. Cell center in UV coordinates
    vec2 cell_uv = (cell_idx * u_cell_size + u_cell_size * 0.5) / u_resolution;

    // Multi-sample the 3D ring buffer within the cell for antialiasing
    vec4 s0 = texture(u_ring_tex, (cell_idx * u_cell_size + u_cell_size * vec2(0.25, 0.25)) / u_resolution);
    vec4 s1 = texture(u_ring_tex, (cell_idx * u_cell_size + u_cell_size * vec2(0.75, 0.25)) / u_resolution);
    vec4 s2 = texture(u_ring_tex, (cell_idx * u_cell_size + u_cell_size * vec2(0.25, 0.75)) / u_resolution);
    vec4 s3 = texture(u_ring_tex, (cell_idx * u_cell_size + u_cell_size * vec2(0.75, 0.75)) / u_resolution);
    vec4 ring_data = (s0 + s1 + s2 + s3) * 0.25;

    float lum = ring_data.r;
    float growth_coord = ring_data.g;
    float mat_id = ring_data.b;
    float is_ring = ring_data.a;

    // 3. Concentric Hollow Halo Shockwave Burst
    float aspect = u_resolution.x / u_resolution.y;
    vec2 p_shock = cell_uv - u_shock_center;
    p_shock.x *= aspect;
    float shock_dist = length(p_shock);

    float halo_intensity = 0.0;
    if (u_shock_alpha > 0.005) {
        float radii[3] = float[3](u_shock_radius, u_shock_radius * 0.82, u_shock_radius * 0.65);
        float weights[3] = float[3](1.0, 0.70, 0.40);
        float thick[3] = float[3](0.045, 0.038, 0.030);

        for (int i = 0; i < 3; ++i) {
            float r = radii[i];
            if (r > 0.01) {
                float d = abs(shock_dist - r);
                if (d < thick[i]) {
                    float edge = 1.0 - d / thick[i];
                    halo_intensity += pow(edge, 2.0) * weights[i] * u_shock_alpha;
                }
            }
        }
        // Central radiant burst when first igniting
        if (u_shock_radius < 0.45) {
            float core = exp(-pow(shock_dist, 2.0) * 25.0) * (1.0 - u_shock_radius / 0.45);
            halo_intensity += core * 1.8 * u_shock_alpha;
        }
    }

    // 4. Growth frontier glow & flicker
    float frontier_glow = 0.0;
    if (is_ring > 0.05 && u_growth < 0.999) {
        float d_front = u_growth - growth_coord;
        if (d_front >= 0.0 && d_front < 0.045) {
            frontier_glow = (1.0 - d_front / 0.045) * 2.2;
        }
    }

    // 5. Total cell illumination
    float total_lum = lum * is_ring + halo_intensity * 1.8 + frontier_glow;
    float cell_rnd = hash21(cell_idx);

    int glyph_idx = 0;

    if (total_lum < 0.02) {
        // Outside ring: subtle ambient binary rain background
        if (u_bg_noise > 0.001 && cell_rnd < 0.22) {
            glyph_idx = (cell_rnd < 0.11) ? 16 : 17; // '0' or '1'
            total_lum = u_bg_noise;
        } else {
            frag_color = vec4(0.0, 0.0, 0.0, 1.0);
            return;
        }
    } else {
        // Cell is active!
        if (frontier_glow > 0.1) {
            // High-speed machine code binary flicker at materialization frontier
            float fast_tick = fract(u_time * 11.0 + cell_rnd);
            glyph_idx = (fast_tick > 0.5) ? 17 : 16; // '1' or '0'
            total_lum = clamp(total_lum + 0.5, 0.0, 1.6);
        }
        else if (u_mode == 1) {
            // Pure Binary Matrix ('0' and '1')
            glyph_idx = (cell_rnd > 0.48) ? 17 : 16;
        }
        else if (u_mode == 2) {
            // ASCII Density Ramp
            int ramp_idx = int(clamp(total_lum * 9.0, 0.0, 9.0));
            glyph_idx = ramp_idx;
        }
        else {
            // Coded Words & Binary Matrix (Viral Instagram Reel aesthetic)
            if (mat_id > 0.5 && is_ring > 0.5) {
                // Diamond Gemstone: Crystalline code symbols & facet tokens
                if (total_lum > 0.85) {
                    // High specular glints: dense glowing characters
                    int hi_glyphs[4] = int[4](9, 7, 57, 73); // '@', '#', 'gem', '1111'
                    glyph_idx = hi_glyphs[int(cell_rnd * 4.0) % 4];
                } else if (total_lum > 0.45) {
                    int mid_glyphs[6] = int[6](32, 33, 34, 35, 38, 39); // '{', '}', '[', ']', '<', '>'
                    glyph_idx = mid_glyphs[int(cell_rnd * 6.0) % 6];
                } else {
                    int lo_glyphs[4] = int[4](6, 5, 22, 17); // '*', '+', '101', '1'
                    glyph_idx = lo_glyphs[int(cell_rnd * 4.0) % 4];
                }
            } else {
                // Platinum Band & Prongs: Stream of binary digits and coded words
                if (cell_rnd < 0.45) {
                    int bin_glyphs[4] = int[4](16, 17, 20, 21); // '0', '1', '01', '10'
                    glyph_idx = bin_glyphs[int(cell_rnd * 10.0) % 4];
                } else if (cell_rnd < 0.80) {
                    int kw_glyphs[7] = int[7](48, 51, 53, 58, 64, 65, 61); // 'def', 'vec', 'rot', 'void', 'byte', 'math', '0x1'
                    glyph_idx = kw_glyphs[int(cell_rnd * 15.0) % 7];
                } else {
                    int sym_glyphs[5] = int[5](32, 33, 40, 7, 6); // '{', '}', ';', '#', '*'
                    glyph_idx = sym_glyphs[int(cell_rnd * 8.0) % 5];
                }
            }
        }
    }

    // 6. Sample Font Atlas (16x16 grid of 32x32 tiles in 512x512 texture)
    float tile_x = float(glyph_idx % 16);
    float tile_y = float(glyph_idx / 16);
    vec2 atlas_uv = (vec2(tile_x, tile_y) + clamp(in_cell, 0.001, 0.999)) / 16.0;

    float glyph_alpha = texture(u_font_atlas, atlas_uv).r;

    // 7. Pure Monochrome Black & White Color Tone
    float boost = pow(clamp(total_lum, 0.0, 3.0), 0.65) * 1.55;
    float white_val = clamp(glyph_alpha * boost, 0.0, 1.0);

    // Shockwave ripple boost
    if (halo_intensity > 0.05) {
        white_val = max(white_val, halo_intensity * glyph_alpha * 2.2);
    }

    frag_color = vec4(vec3(white_val), 1.0);
}
"""
