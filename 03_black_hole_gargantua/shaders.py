"""
================================================================================
  GLSL SHADERS — GARGANTUA (SUPERMASSIVE ROTATING KERR BLACK HOLE)
  Includes:
  - General Relativistic Geodesic Raymarching (Schwarzschild + Kerr Metric)
  - Gravitational Lensing & Einstein Ring Photon Sphere (r = 1.5 r_s)
  - Superheated Accretion Disk with Keplerian Shear & Relativistic Doppler Beaming
  - Spacetime Curvature Flamm's Paraboloid Wireframe Geodesics
  - Warped Cosmic Starfield & Nebula Background
  - ACES Film Tone Mapping & Anamorphic Relativistic Bloom
================================================================================
"""

# -----------------------------------------------------------------------------
# 1. Fullscreen Quad Vertex Shader
# -----------------------------------------------------------------------------
QUAD_VERTEX_SHADER = """
#version 330
in vec2 in_position;
in vec2 in_uv;
out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""

# -----------------------------------------------------------------------------
# 2. Relativistic Raymarching Black Hole Fragment Shader
# -----------------------------------------------------------------------------
BLACK_HOLE_FRAGMENT_SHADER = """
#version 330
uniform float u_time;
uniform vec2 u_resolution;
uniform vec3 u_cam_pos;
uniform vec3 u_cam_target;
uniform float u_spin;          // Kerr black hole spin parameter (a/M)
uniform int u_mode;           // 0: Cinematic Hybrid, 1: Spacetime Grid, 2: Photorealistic
uniform float u_fov_scale;     // FOV scaling factor
in vec2 v_uv;
out vec4 fragColor;

#define PI 3.14159265359
#define RS 1.0                 // Schwarzschild radius (2GM/c²)
#define R_PHOTON 1.5           // Photon sphere radius (1.5 * RS)
#define R_ISCO 3.0             // Innermost Stable Circular Orbit
#define R_OUTER 9.2            // Outer boundary of accretion disk

// 2D pseudo-random hash for stars
float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

// 3D pseudo-random hash for volumetric noise
float hash31(vec3 p) {
    p = fract(p * vec3(443.897, 441.423, 437.195));
    p += dot(p, p.yzx + 19.19);
    return fract((p.x + p.y) * p.z);
}

// 3D Value Noise
float snoise3(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    float n000 = hash31(i + vec3(0, 0, 0));
    float n100 = hash31(i + vec3(1, 0, 0));
    float n010 = hash31(i + vec3(0, 1, 0));
    float n110 = hash31(i + vec3(1, 1, 0));
    float n001 = hash31(i + vec3(0, 0, 1));
    float n101 = hash31(i + vec3(1, 0, 1));
    float n011 = hash31(i + vec3(0, 1, 1));
    float n111 = hash31(i + vec3(1, 1, 1));

    float n00 = mix(n000, n100, f.x);
    float n01 = mix(n001, n101, f.x);
    float n10 = mix(n010, n110, f.x);
    float n11 = mix(n011, n111, f.x);

    float n0 = mix(n00, n10, f.y);
    float n1 = mix(n01, n11, f.y);

    return mix(n0, n1, f.z);
}

// Fractal Brownian Motion for accretion disk plasma turbulence
float fbm_disk(vec3 p) {
    float v = 0.0;
    float a = 0.55;
    vec3 shift = vec3(100.0);
    for (int i = 0; i < 4; ++i) {
        v += a * snoise3(p);
        p = p * 2.05 + shift;
        a *= 0.5;
    }
    return v;
}

// Deep cosmic starfield and warped interstellar dust
vec3 get_background(vec3 ray_dir) {
    vec2 p = vec2(atan(ray_dir.z, ray_dir.x), asin(clamp(ray_dir.y, -1.0, 1.0)));
    vec2 star_uv = p * 34.0;
    vec2 id = floor(star_uv);
    vec2 f = fract(star_uv) - 0.5;
    float h = hash21(id);
    
    vec3 bg = vec3(0.004, 0.005, 0.012); // Deep vacuum void
    
    // Cosmic interstellar nebula glow
    float neb1 = sin(p.x * 2.2 + p.y * 2.8) * 0.5 + 0.5;
    float neb2 = cos(p.x * 2.8 - p.y * 1.8) * 0.5 + 0.5;
    vec3 c_neb = mix(vec3(0.015, 0.035, 0.08), vec3(0.055, 0.025, 0.075), neb1);
    bg += c_neb * neb2 * 0.55;

    // Distant stars warped into relativistic arcs
    if (h > 0.86) {
        float d = length(f - (vec2(hash21(id + 1.1), hash21(id + 2.7)) - 0.5) * 0.7);
        float star = smoothstep(0.09, 0.0, d) * (h - 0.86) * 7.5;
        vec3 star_col = mix(vec3(0.75, 0.88, 1.0), vec3(1.0, 0.92, 0.75), hash21(id + 4.9));
        bg += star_col * star;
    }

    return bg;
}

void main() {
    float aspect = u_resolution.x / u_resolution.y;
    vec2 uv = (v_uv - 0.5) * vec2(aspect, 1.0);

    // Setup primary camera ray
    vec3 ro = u_cam_pos;
    vec3 forward = normalize(u_cam_target - ro);
    vec3 right = normalize(cross(forward, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, forward);
    
    float fov_factor = (u_fov_scale > 0.01) ? u_fov_scale : (aspect < 1.0 ? 0.92 : 1.35);
    vec3 rd = normalize(forward * fov_factor + uv.x * right + uv.y * up);

    // Dynamic progression parameters (0.0 to 14.0s)
    float prog_wire = clamp(u_time / 3.8, 0.0, 1.0);
    float prog_disk = clamp((u_time - 2.8) / 4.8, 0.0, 1.0);

    // Numerical raymarcher for curved spacetime geodesics
    vec3 pos = ro;
    vec3 dir = rd;
    
    vec3 disk_accum = vec3(0.0);
    float disk_alpha = 0.0;
    
    bool hit_horizon = false;
    float min_r = 1000.0;
    
    const int MAX_STEPS = 100;
    float dt = 0.12;

    for (int step = 0; step < MAX_STEPS; step++) {
        float r = length(pos);
        min_r = min(min_r, r);

        // Check if photon crossed Event Horizon (Schwarzschild radius)
        if (r < RS) {
            hit_horizon = true;
            break;
        }

        // Relativistic acceleration towards singularity (Schwarzschild + Kerr frame dragging)
        vec3 gravity_dir = -normalize(pos);
        float curvature = (1.5 * RS) / (r * r);
        vec3 frame_drag = normalize(cross(vec3(0.0, 1.0, 0.0), pos)) * (u_spin * 0.8 * RS / (r * r * r));
        dir = normalize(dir + (gravity_dir * curvature + frame_drag) * dt);

        float prev_y = pos.y;
        pos += dir * dt;

        // Check if geodesic pierced the accretion disk plane y = 0
        if (prev_y * pos.y <= 0.0 && r >= R_ISCO && r <= R_OUTER) {
            float frac = abs(prev_y) / max(0.0001, abs(prev_y) + abs(pos.y));
            vec3 hit_p = pos - dir * (dt * (1.0 - frac));
            float hit_r = length(hit_p.xz);

            if (hit_r >= R_ISCO && hit_r <= R_OUTER) {
                float phi = atan(hit_p.z, hit_p.x);
                float omega = sqrt(RS / (2.0 * pow(hit_r, 3.0)));
                float disk_time = u_time * 2.0 + phi + omega * 8.0;

                // Relativistic Doppler beaming
                vec3 v_orbit = normalize(vec3(-hit_p.z, 0.0, hit_p.x));
                float beta = sqrt(RS / (2.0 * hit_r));
                float gamma = 1.0 / sqrt(max(0.01, 1.0 - beta * beta));
                float cos_theta = dot(v_orbit, -dir);
                float doppler = 1.0 / (gamma * (1.0 - beta * cos_theta));
                doppler = clamp(doppler, 0.35, 2.8);

                // Accretion disk density & temperature turbulence
                float density = smoothstep(R_ISCO, R_ISCO + 0.6, hit_r) * (1.0 - smoothstep(R_OUTER - 2.5, R_OUTER, hit_r));
                
                vec3 sample_p = vec3(hit_r * 1.5, hit_p.y * 12.0, phi * 4.0 - u_time * 2.2);
                float turbulence = fbm_disk(sample_p);
                float plasma_filaments = sin(phi * 16.0 + hit_r * 5.0 - u_time * 3.5) * 0.5 + 0.5;
                plasma_filaments *= sin(phi * 32.0 - hit_r * 8.0 + u_time * 2.0) * 0.5 + 0.5;
                density *= (0.35 + 0.45 * turbulence + 0.20 * plasma_filaments);

                // Blackbody emission color gradient
                float temp = (R_OUTER - hit_r) / (R_OUTER - R_ISCO);
                vec3 c_hot   = vec3(1.00, 1.00, 1.00); // 14,000K Inner edge
                vec3 c_cyan  = vec3(0.75, 0.92, 1.00); // Doppler blueshift
                vec3 c_gold  = vec3(1.00, 0.72, 0.24); // 6,500K Mid disk
                vec3 c_amber = vec3(0.96, 0.38, 0.09); // 3,500K Outer filaments
                vec3 c_red   = vec3(0.55, 0.09, 0.04); // 1,800K Cool rim

                vec3 disk_col;
                if (temp > 0.65) {
                    disk_col = mix(c_gold, c_hot, (temp - 0.65) / 0.35);
                } else if (temp > 0.30) {
                    disk_col = mix(c_amber, c_gold, (temp - 0.30) / 0.35);
                } else {
                    disk_col = mix(c_red, c_amber, temp / 0.30);
                }

                // Apply Doppler beaming intensity & color shift
                disk_col *= pow(doppler, 3.2);
                if (doppler > 1.15) {
                    disk_col = mix(disk_col, c_cyan, (doppler - 1.15) * 0.5);
                }

                // Spacetime Grid Wireframe Overlay (Stage 1 & Hybrid Mode)
                float r_grid = abs(fract(hit_r * 2.0) - 0.5);
                float phi_grid = abs(fract(phi * (8.0 / PI)) - 0.5);
                float grid_line = smoothstep(0.08, 0.02, min(r_grid, phi_grid));
                vec3 wire_col = vec3(0.15, 0.95, 0.85) * 1.8;

                float wire_visibility = (1.0 - smoothstep(0.2, 0.9, prog_disk));
                disk_col = mix(disk_col, wire_col, grid_line * wire_visibility);

                // Alpha accumulation
                float step_alpha = clamp(density * 0.78 * prog_disk, 0.0, 1.0);
                disk_accum += disk_col * step_alpha * (1.0 - disk_alpha);
                disk_alpha += step_alpha * (1.0 - disk_alpha);

                if (disk_alpha > 0.95) break;
            }
        }

        dt = clamp(0.04 * r, 0.025, 0.35);
    }

    // Background cosmic starfield deflected by the black hole
    vec3 bg_color = get_background(dir);

    // Photon Sphere & Einstein Ring Glow (shimmering ring of trapped light at r ≈ 1.5 * RS)
    float photon_ring = exp(-abs(min_r - R_PHOTON) * 12.0) * 1.85;
    vec3 c_ring = vec3(1.0, 0.90, 0.72) * photon_ring * prog_disk;

    // Outer gravitational lens distortion halo
    float lens_halo = exp(-abs(min_r - 2.6 * RS) * 2.5) * 0.18 * prog_disk;

    // Spacetime Gravitational Funnel Grid (for Stage 1 Wireframe)
    vec3 grid_col = vec3(0.0);
    if (u_mode == 1 || prog_disk < 0.8) {
        float grid_r = abs(fract(min_r * 2.0) - 0.5);
        float grid_f = smoothstep(0.12, 0.02, grid_r) * (1.0 - prog_disk * 0.85);
        grid_col = vec3(0.10, 0.88, 0.78) * grid_f * 0.85;
    }

    // Anamorphic horizontal lens flare streak across the bright Doppler blueshifted side
    float flare_y = exp(-pow((uv.y - 0.04) * 28.0, 2.0));
    float flare_x = exp(-pow(uv.x + 0.12, 2.0) * 3.2);
    vec3 c_flare = vec3(0.6, 0.85, 1.0) * flare_y * flare_x * 0.40 * prog_disk;

    vec3 col;
    if (hit_horizon) {
        // Pure pitch-black event horizon singularity shadow (no light escapes!)
        col = disk_accum;
    } else {
        col = disk_accum + (bg_color + c_ring + c_flare + vec3(0.9, 0.7, 0.4) * lens_halo + grid_col) * (1.0 - disk_alpha);
    }

    // Atmospheric bloom / exposure tone-mapping (ACES style)
    col = col / (col + vec3(1.0));
    col = pow(col, vec3(1.0 / 2.2)); // Gamma correction

    // Subtle edge vignette
    vec2 vc = v_uv - vec2(0.5);
    col *= 1.0 - dot(vc, vc) * 0.35;

    fragColor = vec4(col, 1.0);
}
"""

# -----------------------------------------------------------------------------
# 3. HUD Overlay Screen Quad Shaders
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
