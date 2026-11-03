"""
Nokia 3310 Retro Dot-Matrix LCD Graphics Engine & Phone Chassis Renderer.
Simulates authentic monochrome liquid crystal response, subpixel grids,
battery/signal icons, and retro scanline vignette.
"""

import math
import numpy as np
import pygame

# Authentic Nokia 3310 LCD Color Palette
COLOR_LCD_BG = (142, 166, 102)        # Olive-green monochrome backlight
COLOR_LCD_PIXEL_ON = (22, 36, 18)     # Deep dark liquid crystal pixel
COLOR_LCD_PIXEL_GHOST = (118, 138, 86)# Ghosting trail / persistence of vision
COLOR_LCD_GRID = (130, 152, 92)       # Subpixel dot-matrix separation grid
COLOR_PHONE_BODY = (28, 42, 64)       # Iconic Navy Blue Nokia 3310 casing
COLOR_PHONE_BEZEL = (45, 60, 85)      # Beveled inner bezel
COLOR_CHROME = (180, 190, 205)        # Metallic Nokia logo & accents

class NokiaLCDRenderer:
    def __init__(self, grid_w=24, grid_h=14):
        self.grid_w = grid_w
        self.grid_h = grid_h
        
        # Pixel persistence buffer for LCD ghosting
        self.ghost_buffer = np.zeros((grid_w, grid_h), dtype=np.float32)
        
        # Load fonts
        pygame.font.init()
        font_names = ["Consolas", "Courier New", "Arial"]
        self.font_main = None
        self.font_bold = None
        self.font_tiny = None
        
        for name in font_names:
            try:
                self.font_main = pygame.font.SysFont(name, 16, bold=True)
                self.font_bold = pygame.font.SysFont(name, 22, bold=True)
                self.font_tiny = pygame.font.SysFont(name, 12, bold=True)
                break
            except Exception:
                continue
                
        if self.font_main is None:
            self.font_main = pygame.font.Font(None, 16)
            self.font_bold = pygame.font.Font(None, 22)
            self.font_tiny = pygame.font.Font(None, 12)

    def update_ghosting(self, snake_set, food_pos, dt=0.03):
        """Fade previous frames to simulate real monochrome LCD liquid crystal delay."""
        self.ghost_buffer *= max(0.0, 1.0 - dt * 3.5)
        for (x, y) in snake_set:
            self.ghost_buffer[x, y] = 1.0
        if food_pos:
            self.ghost_buffer[food_pos[0], food_pos[1]] = 1.0

    def draw_lcd_screen(self, surface, rect, game_state, is_ai=True):
        """
        Draw the authentic dot-matrix Nokia screen within `rect`.
        game_state: HamiltonianSnakeAI instance
        """
        x0, y0, screen_w, screen_h = rect
        
        # 1. Base LCD Glass with inner shadow
        pygame.draw.rect(surface, COLOR_LCD_BG, rect, border_radius=6)
        
        # 2. Header Status Bar (Battery, Signal, Title)
        header_h = int(screen_h * 0.16)
        header_rect = pygame.Rect(x0, y0, screen_w, header_h)
        
        # Signal strength (Left: 4 bars)
        sig_x = x0 + 12
        sig_y = y0 + 10
        for i in range(4):
            bar_h = 4 + i * 3
            pygame.draw.rect(surface, COLOR_LCD_PIXEL_ON, (sig_x + i * 4, sig_y + 12 - bar_h, 3, bar_h))
            
        # Battery strength (Right: 4 bars inside battery shell)
        bat_w, bat_h = 18, 10
        bat_x = x0 + screen_w - bat_w - 14
        bat_y = y0 + 8
        pygame.draw.rect(surface, COLOR_LCD_PIXEL_ON, (bat_x, bat_y, bat_w, bat_h), width=1)
        pygame.draw.rect(surface, COLOR_LCD_PIXEL_ON, (bat_x - 2, bat_y + 3, 2, 4)) # terminal
        for i in range(3):
            pygame.draw.rect(surface, COLOR_LCD_PIXEL_ON, (bat_x + 3 + i * 4, bat_y + 2, 2, bat_h - 4))
            
        # Header text
        mode_text = "AUTO [AI]" if is_ai else "MANUAL"
        title_surf = self.font_tiny.render(f"SNAKE II  {mode_text}", True, COLOR_LCD_PIXEL_ON)
        surface.blit(title_surf, (x0 + screen_w // 2 - title_surf.get_width() // 2, y0 + 7))
        
        # Divider line
        pygame.draw.line(surface, COLOR_LCD_GRID, (x0 + 8, y0 + header_h), (x0 + screen_w - 8, y0 + header_h), 1)

        # 3. Game Playing Matrix
        margin_x = 12
        margin_top = header_h + 6
        margin_bot = int(screen_h * 0.14)
        
        play_w = screen_w - 2 * margin_x
        play_h = screen_h - margin_top - margin_bot
        
        cell_size = min(play_w // self.grid_w, play_h // self.grid_h)
        grid_start_x = x0 + margin_x + (play_w - cell_size * self.grid_w) // 2
        grid_start_y = y0 + margin_top + (play_h - cell_size * self.grid_h) // 2
        
        # Border around play area
        border_rect = pygame.Rect(grid_start_x - 2, grid_start_y - 2, cell_size * self.grid_w + 4, cell_size * self.grid_h + 4)
        pygame.draw.rect(surface, COLOR_LCD_PIXEL_ON, border_rect, width=1)

        # Draw grid cells & liquid crystal pixels
        snake_head = game_state.snake[0] if game_state.snake else None
        
        for gx in range(self.grid_w):
            for gy in range(self.grid_h):
                px = grid_start_x + gx * cell_size
                py = grid_start_y + gy * cell_size
                
                # Ghosting pixel
                ghost_val = self.ghost_buffer[gx, gy]
                if ghost_val > 0.08 and (gx, gy) not in game_state.snake_set and (gx, gy) != game_state.food:
                    pygame.draw.rect(surface, COLOR_LCD_PIXEL_GHOST, (px + 1, py + 1, cell_size - 2, cell_size - 2))
                    
                # Active pixel
                if (gx, gy) in game_state.snake_set:
                    # Solid dark LCD block
                    pygame.draw.rect(surface, COLOR_LCD_PIXEL_ON, (px + 1, py + 1, cell_size - 2, cell_size - 2))
                    
                    # Distinguish Head with snake eyes
                    if (gx, gy) == snake_head:
                        eye_col = COLOR_LCD_BG
                        eye_size = max(1, cell_size // 4)
                        pygame.draw.rect(surface, eye_col, (px + 2, py + 2, eye_size, eye_size))
                        pygame.draw.rect(surface, eye_col, (px + cell_size - 2 - eye_size, py + 2, eye_size, eye_size))
                        
                elif (gx, gy) == game_state.food:
                    # Food pixel (apple/dot)
                    pygame.draw.rect(surface, COLOR_LCD_PIXEL_ON, (px + 2, py + 2, cell_size - 4, cell_size - 4))
                    # Little cross pixel
                    pygame.draw.rect(surface, COLOR_LCD_BG, (px + cell_size // 2, py + 2, 1, 1))

        # 4. Footer Telemetry (Score & Fill %)
        foot_y = y0 + screen_h - margin_bot + 2
        fill_pct = (len(game_state.snake) / float(game_state.total_cells)) * 100.0
        
        score_surf = self.font_main.render(f"SCORE:{game_state.score:04d}", True, COLOR_LCD_PIXEL_ON)
        fill_surf = self.font_main.render(f"FILL:{fill_pct:5.1f}%", True, COLOR_LCD_PIXEL_ON)
        
        surface.blit(score_surf, (x0 + margin_x + 4, foot_y))
        surface.blit(fill_surf, (x0 + screen_w - margin_x - fill_surf.get_width() - 4, foot_y))

        # Victory / 100% overlay
        if game_state.is_won:
            banner_w = int(screen_w * 0.8)
            banner_h = int(screen_h * 0.22)
            bx = x0 + (screen_w - banner_w) // 2
            by = y0 + (screen_h - banner_h) // 2
            
            pygame.draw.rect(surface, COLOR_LCD_PIXEL_ON, (bx, by, banner_w, banner_h), border_radius=4)
            pygame.draw.rect(surface, COLOR_LCD_BG, (bx + 2, by + 2, banner_w - 4, banner_h - 4), width=1)
            
            v_text = self.font_bold.render("100% COMPLETED!", True, COLOR_LCD_BG)
            s_text = self.font_tiny.render("ALL CELLS OCCUPIED", True, COLOR_LCD_BG)
            surface.blit(v_text, (bx + (banner_w - v_text.get_width()) // 2, by + 12))
            surface.blit(s_text, (bx + (banner_w - s_text.get_width()) // 2, by + 38))

    def draw_nokia_phone(self, surface, center_x, center_y, scale=1.0, game_state=None, is_ai=True):
        """
        Draw the iconic Nokia 3310 phone casing and embed the active LCD display.
        """
        phone_w = int(420 * scale)
        phone_h = int(720 * scale)
        px = center_x - phone_w // 2
        py = center_y - phone_h // 2
        
        # Outer phone silhouette (smooth pill shape)
        phone_rect = pygame.Rect(px, py, phone_w, phone_h)
        pygame.draw.rect(surface, COLOR_PHONE_BODY, phone_rect, border_radius=int(48 * scale))
        
        # Subtle rim highlight
        pygame.draw.rect(surface, (60, 80, 115), phone_rect, width=3, border_radius=int(48 * scale))

        # Earpiece speaker grille at top
        ear_w, ear_h = int(64 * scale), int(8 * scale)
        ear_rect = pygame.Rect(center_x - ear_w // 2, py + int(36 * scale), ear_w, ear_h)
        pygame.draw.rect(surface, (15, 20, 30), ear_rect, border_radius=int(4 * scale))

        # Metallic NOKIA logo at top
        logo_surf = self.font_bold.render("NOKIA", True, COLOR_CHROME)
        surface.blit(logo_surf, (center_x - logo_surf.get_width() // 2, py + int(56 * scale)))

        # Inner Screen Bezel
        bezel_w = int(320 * scale)
        bezel_h = int(240 * scale)
        bx = center_x - bezel_w // 2
        by = py + int(96 * scale)
        bezel_rect = pygame.Rect(bx, by, bezel_w, bezel_h)
        pygame.draw.rect(surface, COLOR_PHONE_BEZEL, bezel_rect, border_radius=int(14 * scale))
        pygame.draw.rect(surface, (20, 28, 40), bezel_rect, width=3, border_radius=int(14 * scale))

        # Active LCD Screen inside bezel
        pad = int(12 * scale)
        screen_rect = pygame.Rect(bx + pad, by + pad, bezel_w - 2 * pad, bezel_h - 2 * pad)
        if game_state:
            self.draw_lcd_screen(surface, screen_rect, game_state, is_ai=is_ai)

        # Buttons (Classic Navi key + keypad buttons)
        key_y = by + bezel_h + int(24 * scale)
        
        # Big central Navi-key
        navi_w = int(96 * scale)
        navi_h = int(28 * scale)
        navi_rect = pygame.Rect(center_x - navi_w // 2, key_y, navi_w, navi_h)
        pygame.draw.rect(surface, (70, 92, 130), navi_rect, border_radius=int(10 * scale))
        pygame.draw.rect(surface, COLOR_CHROME, navi_rect, width=1, border_radius=int(10 * scale))
        
        # Side functional keys ('C' on right, left soft key)
        c_rect = pygame.Rect(center_x + navi_w // 2 + int(14 * scale), key_y + int(4 * scale), int(42 * scale), int(22 * scale))
        pygame.draw.rect(surface, (55, 75, 105), c_rect, border_radius=int(8 * scale))
        
        l_rect = pygame.Rect(center_x - navi_w // 2 - int(56 * scale), key_y + int(4 * scale), int(42 * scale), int(22 * scale))
        pygame.draw.rect(surface, (55, 75, 105), l_rect, border_radius=int(8 * scale))

        # 12-key numeric pad
        pad_start_y = key_y + int(45 * scale)
        btn_w = int(58 * scale)
        btn_h = int(24 * scale)
        gap_x = int(18 * scale)
        gap_y = int(14 * scale)
        
        row_cols = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["*", "0", "#"]
        ]
        
        for r_idx, row in enumerate(row_cols):
            curr_y = pad_start_y + r_idx * (btn_h + gap_y)
            for c_idx, label in enumerate(row):
                curr_x = center_x - (3 * btn_w + 2 * gap_x) // 2 + c_idx * (btn_w + gap_x)
                b_rect = pygame.Rect(curr_x, curr_y, btn_w, btn_h)
                pygame.draw.rect(surface, (50, 70, 98), b_rect, border_radius=int(7 * scale))
                pygame.draw.rect(surface, (30, 45, 65), b_rect, width=1, border_radius=int(7 * scale))
                
                txt = self.font_tiny.render(label, True, COLOR_CHROME)
                surface.blit(txt, (curr_x + (btn_w - txt.get_width()) // 2, curr_y + (btn_h - txt.get_height()) // 2))
