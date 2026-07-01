import pygame
import serial
import threading
import random
import time
import math

# Serial configuration
ser = serial.Serial('COM18', 9600)

# Global variables for joystick data
joystick_x = 512
joystick_y = 512
joystick_btn = 1
prev_joystick_btn = 1
pot_value = 0
pause_state = 0
prev_pause_state = 0

# New variables for better pause handling
arduino_paused = False
prev_arduino_paused = False
last_pause_change_time = 0
pause_cooldown = 500  # 500ms cooldown between pause changes

# --- RGB LED ---
def send_state(state):
    try:
        print(f"Sending: {state}")
        ser.write(f"STATE:{state}\n".encode())
    except Exception as e:
        print(f"Error: {e}")

# Function to read data from Arduino in separate thread
def read_joystick():
    global joystick_x, joystick_y, joystick_btn, pot_value, pause_state, arduino_paused
    while True:
        try:
            line = ser.readline().decode().strip()
            parts = line.split(',')
            if len(parts) == 5:
                joystick_x = int(parts[0])
                joystick_y = int(parts[1])
                joystick_btn = int(parts[2])
                pot_value = int(parts[3])
                pause_state = int(parts[4])
                arduino_paused = (pause_state == 1)  # Convert to boolean
        except:
            continue

# Start thread to read data from Arduino
threading.Thread(target=read_joystick, daemon=True).start()

# Wait for initial joystick data
while joystick_x == 512 and joystick_y == 512 and joystick_btn == 1:
    time.sleep(0.05)

# ------------------- TETRIS GAME -------------------

# Game parameters
CELL_SIZE = 30
COLS = 10
ROWS = 20
WIDTH = CELL_SIZE * COLS
HEIGHT = CELL_SIZE * ROWS

# Colors
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
COLORS = [
    (0, 255, 255),  # I
    (0, 0, 255),    # J
    (255, 165, 0),  # L
    (255, 255, 0),  # O
    (0, 255, 0),    # S
    (128, 0, 128),  # T
    (255, 0, 0)     # Z
]

# Enhanced multi-stage line clear effect with FIXED TIMING
class SpectacularLineClearEffect:
    def __init__(self, row_indices, board):
        self.row_indices = row_indices
        self.start_time = pygame.time.get_ticks()  # Use absolute time instead of dt
        self.total_duration = 1500  # Total effect duration in milliseconds
        self.board_snapshot = [row[:] for row in board]
        
        # Stage timings (in milliseconds) - these are now ABSOLUTE timings
        self.stage_1_duration = 200   # Charge up
        self.stage_2_duration = 100   # Flash
        self.stage_3_duration = 400   # Disintegration
        self.stage_4_duration = 600   # Particle explosion
        self.stage_5_duration = 200   # Final fade
        
        # Charge particles (stage 1)
        self.charge_particles = []
        for _ in range(30):
            self.charge_particles.append({
                'x': random.uniform(-50, WIDTH + 50),
                'y': random.uniform(-50, HEIGHT + 50),
                'target_row': random.choice(row_indices),
                'speed': random.uniform(3, 8),
                'color': (random.randint(100, 255), random.randint(200, 255), random.randint(150, 255)),
                'size': random.uniform(2, 5)
            })
        
        # Block fragments for disintegration
        self.fragments = []
        for row in row_indices:
            for col in range(COLS):
                if board[row][col] != BLACK:
                    # Create multiple fragments per block
                    for _ in range(random.randint(8, 12)):
                        fragment = {
                            'x': col * CELL_SIZE + random.uniform(5, CELL_SIZE - 5),
                            'y': row * CELL_SIZE + random.uniform(5, CELL_SIZE - 5),
                            'vx': random.uniform(-6, 6),
                            'vy': random.uniform(-8, -2),
                            'color': board[row][col],
                            'size': random.uniform(2, 6),
                            'rotation': random.uniform(0, 360),
                            'rot_speed': random.uniform(-10, 10),
                            'gravity': random.uniform(0.2, 0.5),
                            'life': 1.0,
                            'bounce_factor': random.uniform(0.3, 0.7)
                        }
                        self.fragments.append(fragment)
        
        # Energy waves
        self.energy_waves = []
        for row in row_indices:
            self.energy_waves.append({
                'y': row * CELL_SIZE + CELL_SIZE // 2,
                'width': 0,
                'max_width': WIDTH + 100,
                'speed': 8,
                'color': (255, 255, 100),
                'intensity': 1.0
            })
        
        # Lightning bolts
        self.lightning_bolts = []
        for row in row_indices:
            for _ in range(3):
                points = []
                start_x = random.uniform(0, WIDTH)
                current_x = start_x
                current_y = row * CELL_SIZE
                
                # Generate zigzag lightning path
                for i in range(8):
                    current_x += random.uniform(-30, 30)
                    current_y += random.uniform(3, 8)
                    points.append((current_x, current_y))
                
                self.lightning_bolts.append({
                    'points': points,
                    'width': random.uniform(2, 5),
                    'color': (200 + random.randint(0, 55), 200 + random.randint(0, 55), 255),
                    'life': 1.0
                })

    def update(self, dt=None):  # dt parameter is now ignored
        # Use absolute time for consistent animation speed
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        progress = elapsed / self.total_duration
        
        # Stage 1: Charge particles converging
        if elapsed < self.stage_1_duration:
            for particle in self.charge_particles:
                target_y = particle['target_row'] * CELL_SIZE + CELL_SIZE // 2
                target_x = WIDTH // 2
                
                dx = target_x - particle['x']
                dy = target_y - particle['y']
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist > 5:
                    particle['x'] += (dx / dist) * particle['speed']
                    particle['y'] += (dy / dist) * particle['speed']
        
        # Stage 3: Fragment physics - using fixed time step
        elif elapsed > self.stage_1_duration + self.stage_2_duration:
            # Use a fixed time step for consistent physics
            fixed_dt = 16.67  # ~60fps equivalent
            
            for fragment in self.fragments:
                # Apply physics with fixed time step
                fragment['x'] += fragment['vx'] * (fixed_dt / 1000)
                fragment['y'] += fragment['vy'] * (fixed_dt / 1000)
                fragment['vy'] += fragment['gravity'] * (fixed_dt / 10)  # Adjust gravity scaling
                fragment['rotation'] += fragment['rot_speed'] * (fixed_dt / 100)
                
                # Bounce off edges
                if fragment['x'] <= 0 or fragment['x'] >= WIDTH:
                    fragment['vx'] *= -fragment['bounce_factor']
                    fragment['x'] = max(0, min(WIDTH, fragment['x']))
                
                if fragment['y'] >= HEIGHT:
                    fragment['vy'] *= -fragment['bounce_factor']
                    fragment['y'] = HEIGHT
                    fragment['vx'] *= 0.8  # Friction
                
                # Fade out based on elapsed time, not dt
                fade_duration = self.stage_3_duration + self.stage_4_duration
                fade_elapsed = elapsed - (self.stage_1_duration + self.stage_2_duration)
                fragment['life'] = max(0, 1 - (fade_elapsed / fade_duration))
        
        # Update energy waves with fixed speed
        for wave in self.energy_waves:
            if elapsed > self.stage_1_duration:
                wave['width'] += wave['speed']
                wave['intensity'] = max(0, 1 - (wave['width'] / wave['max_width']))
        
        # Update lightning with fixed timing
        for bolt in self.lightning_bolts:
            if self.stage_1_duration < elapsed < self.stage_1_duration + self.stage_2_duration + 100:
                bolt['life'] = random.uniform(0.3, 1.0)  # Flickering effect
            else:
                lightning_fade_start = self.stage_1_duration + self.stage_2_duration + 100
                if elapsed > lightning_fade_start:
                    fade_elapsed = elapsed - lightning_fade_start
                    bolt['life'] = max(0, 1 - (fade_elapsed / 200))
        
        return elapsed < self.total_duration

    def draw(self, surface):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        progress = elapsed / self.total_duration
        
        # Stage 1: Draw charge particles
        if elapsed < self.stage_1_duration:
            for particle in self.charge_particles:
                # Glow effect
                glow_size = int(particle['size'] * 3)
                glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                glow_color = (*particle['color'], 100)
                pygame.draw.circle(glow_surface, glow_color, (glow_size, glow_size), glow_size)
                surface.blit(glow_surface, (int(particle['x'] - glow_size), int(particle['y'] - glow_size)))
                
                # Main particle
                pygame.draw.circle(surface, particle['color'], 
                                 (int(particle['x']), int(particle['y'])), int(particle['size']))
        
        # Stage 2: Massive flash
        elif elapsed < self.stage_1_duration + self.stage_2_duration:
            flash_intensity = 255
            for row in self.row_indices:
                # Multi-colored flash layers
                colors = [(255, 255, 255), (255, 255, 100), (255, 150, 255)]
                for i, color in enumerate(colors):
                    flash_rect = pygame.Rect(-20, row * CELL_SIZE - 5, WIDTH + 40, CELL_SIZE + 10)
                    flash_surface = pygame.Surface((WIDTH + 40, CELL_SIZE + 10), pygame.SRCALPHA)
                    alpha = flash_intensity // (i + 1)
                    flash_surface.fill((*color, alpha))
                    surface.blit(flash_surface, flash_rect)
        
        # Stage 3 & 4: Draw energy waves
        if elapsed > self.stage_1_duration:
            for wave in self.energy_waves:
                if wave['intensity'] > 0:
                    # Multiple wave layers for depth
                    for i in range(3):
                        wave_width = wave['width'] - i * 20
                        if wave_width > 0:
                            alpha = int(wave['intensity'] * 255 / (i + 1))
                            wave_surface = pygame.Surface((int(wave_width * 2), 40), pygame.SRCALPHA)
                            
                            # Gradient effect
                            for y in range(40):
                                gradient_alpha = alpha * (1 - abs(y - 20) / 20)
                                color = (*wave['color'], int(gradient_alpha))
                                pygame.draw.line(wave_surface, color, (0, y), (int(wave_width * 2), y))
                            
                            surface.blit(wave_surface, (WIDTH//2 - wave_width, wave['y'] - 20))
        
        # Draw lightning bolts
        for bolt in self.lightning_bolts:
            if bolt['life'] > 0:
                alpha = int(bolt['life'] * 255)
                
                # Draw multiple lightning layers
                for thickness in [5, 3, 1]:
                    if len(bolt['points']) > 1:
                        lightning_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        
                        for i in range(len(bolt['points']) - 1):
                            start_pos = bolt['points'][i]
                            end_pos = bolt['points'][i + 1]
                            
                            # Clamp positions to screen
                            start_pos = (max(0, min(WIDTH, start_pos[0])), max(0, min(HEIGHT, start_pos[1])))
                            end_pos = (max(0, min(WIDTH, end_pos[0])), max(0, min(HEIGHT, end_pos[1])))
                            
                            if thickness == 1:
                                color = (255, 255, 255, alpha)
                            else:
                                color = (*bolt['color'], alpha // thickness)
                            
                            pygame.draw.line(lightning_surface, color, start_pos, end_pos, thickness)
                        
                        surface.blit(lightning_surface, (0, 0))
        
        # Stage 3 & 4: Draw fragments
        if elapsed > self.stage_1_duration + self.stage_2_duration:
            for fragment in self.fragments:
                if fragment['life'] > 0:
                    # Calculate fragment properties
                    alpha = int(255 * fragment['life'])
                    size = max(1, int(fragment['size'] * fragment['life']))
                    
                    # Create rotated square fragment
                    fragment_surface = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
                    
                    # Draw fragment with rotation
                    points = []
                    center_x, center_y = size * 1.5, size * 1.5
                    angle_rad = math.radians(fragment['rotation'])
                    
                    for i in range(4):
                        angle = angle_rad + i * math.pi / 2
                        x = center_x + size * math.cos(angle)
                        y = center_y + size * math.sin(angle)
                        points.append((x, y))
                    
                    # Fragment color with fading
                    r, g, b = fragment['color']
                    frag_color = (r, g, b, alpha)
                    
                    if len(points) >= 3:
                        pygame.draw.polygon(fragment_surface, frag_color, points)
                        
                        # Add bright core
                        core_color = (255, 255, 255, alpha // 2)
                        pygame.draw.circle(fragment_surface, core_color, 
                                         (int(center_x), int(center_y)), max(1, size // 2))
                    
                    surface.blit(fragment_surface, 
                               (int(fragment['x'] - size * 1.5), int(fragment['y'] - size * 1.5)))
        
        # Stage 5: Final screen flash
        if elapsed > self.total_duration - self.stage_5_duration:
            fade_start = self.total_duration - self.stage_5_duration
            fade_elapsed = elapsed - fade_start
            fade_progress = fade_elapsed / self.stage_5_duration
            flash_alpha = int(100 * (1 - fade_progress))
            if flash_alpha > 0:
                flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash_surface.fill((255, 255, 255, flash_alpha))
                surface.blit(flash_surface, (0, 0))

def draw_block_3d(surface, base_color, x, y, size):
    # Base colors
    highlight = tuple(min(255, c + 80) for c in base_color)  # Lighter
    shadow = tuple(max(0, c - 80) for c in base_color)       # Darker
    dark_shadow = tuple(max(0, c - 120) for c in base_color) # Even darker

    # Main block
    pygame.draw.rect(surface, base_color, (x, y, size, size))

    # Left and top highlights
    pygame.draw.polygon(surface, highlight, [
        (x, y),
        (x + size - 1, y),
        (x + size - 4, y + 4),
        (x + 4, y + 4),
        (x + 4, y + size - 4),
        (x, y + size - 1)
    ])

    # Right and bottom shadows
    pygame.draw.polygon(surface, shadow, [
        (x + size - 1, y),
        (x + size - 1, y + size - 1),
        (x, y + size - 1),
        (x + 4, y + size - 4),
        (x + size - 4, y + size - 4),
        (x + size - 4, y + 4)
    ])

    # Outer border
    pygame.draw.rect(surface, dark_shadow, (x, y, size, size), 2)

SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 0, 0],
     [1, 1, 1]],
    [[0, 0, 1],
     [1, 1, 1]],
    [[1, 1],
     [1, 1]],
    [[0, 1, 1],
     [1, 1, 0]],
    [[0, 1, 0],
     [1, 1, 1]],
    [[1, 1, 0],
     [0, 1, 1]]
]

class Tetromino:
    def __init__(self):
        self.shape = random.choice(SHAPES)
        self.color = random.choice(COLORS)
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

    def get_cells(self):
        cells = []
        for i, row in enumerate(self.shape):
            for j, val in enumerate(row):
                if val:
                    cells.append((self.x + j, self.y + i))
        return cells

class Tetris:
    def __init__(self):
        self.board = [[BLACK for _ in range(COLS)] for _ in range(ROWS)]
        self.tetromino = Tetromino()
        self.game_over = False
        self.score = 0
        self.paused = False
        self.line_clear_effects = []  # Changed from explosion_effects

    def can_move(self, dx, dy, shape=None):
        if shape is None:
            shape = self.tetromino.shape
        for i, row in enumerate(shape):
            for j, val in enumerate(row):
                if val:
                    x = self.tetromino.x + j + dx
                    y = self.tetromino.y + i + dy
                    if x < 0 or x >= COLS or y >= ROWS or (y >= 0 and self.board[y][x] != BLACK):
                        return False
        return True

    def freeze(self):
        for x, y in self.tetromino.get_cells():
            if y < 0:
                self.game_over = True
            else:
                self.board[y][x] = self.tetromino.color
        
        lines_cleared, cleared_rows = self.clear_lines()
        if lines_cleared > 0:
            self.score += lines_cleared * 100
            send_state(f"SCORE:{self.score}")
            send_state("BUZZ:LINE")
            
            # Create spectacular line clear effect
            if cleared_rows:
                board_copy = [row[:] for row in self.board]
                self.line_clear_effects.append(SpectacularLineClearEffect(cleared_rows, board_copy))
        
        send_state("BUZZ:DROP")
        self.tetromino = Tetromino()

        if any(self.board[0][x] != BLACK for x in range(COLS)):
            self.game_over = True

    def clear_lines(self):
        lines_cleared = 0
        cleared_rows = []
        new_board = []
        
        for i, row in enumerate(self.board):
            if all(c != BLACK for c in row):
                lines_cleared += 1
                cleared_rows.append(i)
            else:
                new_board.append(row)

        while len(new_board) < ROWS:
            new_board.insert(0, [BLACK for _ in range(COLS)])

        self.board = new_board
        return lines_cleared, cleared_rows

    def update(self, dt=0):
        if not self.paused:
            if self.can_move(0, 1):
                self.tetromino.y += 1
            else:
                self.freeze()
        
        # Update line clear effects - no longer pass dt since it's not used
        self.line_clear_effects = [effect for effect in self.line_clear_effects if effect.update()]

    def move_left(self):
        if not self.paused and self.can_move(-1, 0):
            self.tetromino.x -= 1

    def move_right(self):
        if not self.paused and self.can_move(1, 0):
            self.tetromino.x += 1

    def rotate(self):
        if not self.paused:
            new_shape = [list(row) for row in zip(*self.tetromino.shape[::-1])]
            if self.can_move(0, 0, new_shape):
                self.tetromino.shape = new_shape
                send_state("BUZZ:ROTATE")

    def set_pause_state(self, paused):
        """Set pause state directly from Arduino"""
        if self.paused != paused:
            self.paused = paused
            if paused:
                print("Game PAUSED (from Arduino)")
            else:
                print("Game RESUMED (from Arduino)")

    def draw_effects(self, surface):
        """Draw all active line clear effects"""
        for effect in self.line_clear_effects:
            effect.draw(surface)

def show_pause_overlay(surface):
    """Display pause overlay on game"""
    # Semi-transparent background
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    surface.blit(overlay, (0, 0))
    
    # Pause text
    pause_font = pygame.font.Font("pressstart2p.ttf", 32)
    instruction_font = pygame.font.Font("pressstart2p.ttf", 16)
    
    pause_text = pause_font.render("PAUZA", True, (255, 255, 0))
    pause_shadow = pause_font.render("PAUZA", True, (100, 100, 0))
    
    instruction_text = instruction_font.render("Nacisnij przycisk", True, (255, 255, 255))
    instruction_text2 = instruction_font.render("aby wznowic", True, (255, 255, 255))
    
    # Center text
    surface.blit(pause_shadow, (WIDTH // 2 - pause_text.get_width() // 2 + 3, HEIGHT // 2 - 60 + 3))
    surface.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 60))
    
    surface.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 2 + 20))
    surface.blit(instruction_text2, (WIDTH // 2 - instruction_text2.get_width() // 2, HEIGHT // 2 + 45))

def handle_arduino_pause(game):
    """Handle pause state changes from Arduino"""
    global arduino_paused, prev_arduino_paused, last_pause_change_time
    
    current_time = pygame.time.get_ticks()
    
    # Check if Arduino pause state changed
    if arduino_paused != prev_arduino_paused:
        # Apply cooldown to prevent rapid changes
        if current_time - last_pause_change_time > pause_cooldown:
            game.set_pause_state(arduino_paused)
            last_pause_change_time = current_time
            print(f"Arduino pause state changed to: {arduino_paused}")
        
        prev_arduino_paused = arduino_paused

# ------------------- Main game loop -------------------

pygame.init()
pygame.mixer.init()
pygame.mixer.music.load("bloons_soundtrack.mp3")
pygame.mixer.music.play(-1, 0.0)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris z Arduino")
clock = pygame.time.Clock()
game = Tetris()
fall_time = 0
move_cooldown = 0

font = pygame.font.Font("pressstart2p.ttf", 16)
game_over_font = pygame.font.Font("pressstart2p.ttf", 32)
welcome_font = pygame.font.Font("pressstart2p.ttf", 42)

player_name = ""
name_input_active = True

def show_game_over_screen():
    screen.fill((20, 20, 30))

    # Gradient background effect
    for i in range(HEIGHT):
        color = (30 + i // 10, 10 + i // 15, 30 + i // 12)
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))

    # Title with shadow
    game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
    shadow_text = game_over_font.render("GAME OVER", True, (100, 0, 0))
    screen.blit(shadow_text, (WIDTH // 2 - game_over_text.get_width() // 2 + 4, HEIGHT // 4 + 4))
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 4))

    # Score
    score_text = font.render(f"Punkty: {game.score}", True, (255, 255, 255))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))

    # "Close" Button
    button_rect = pygame.Rect(WIDTH // 2 - 100, int(HEIGHT * 0.65), 200, 50)
    pygame.draw.rect(screen, (50, 50, 70), button_rect)
    pygame.draw.rect(screen, (180, 180, 255), button_rect, 2)

    close_button_text = font.render("Zamknij", True, (255, 255, 255))
    close_shadow = font.render("Zamknij", True, (80, 80, 100))
    screen.blit(close_shadow, (button_rect.x + (button_rect.width - close_button_text.get_width()) // 2 + 2,
                               button_rect.y + (button_rect.height - close_button_text.get_height()) // 2 + 2))
    screen.blit(close_button_text, (button_rect.x + (button_rect.width - close_button_text.get_width()) // 2,
                                    button_rect.y + (button_rect.height - close_button_text.get_height()) // 2))

    pygame.display.flip()

def show_welcome_screen():
    global player_name, name_input_active

    screen.fill((20, 20, 30))

    for i in range(HEIGHT):
        color = (20 + i // 10, 20 + i // 20, 30 + i // 15)
        pygame.draw.line(screen, color, (0, i), (WIDTH, i))

    title_text = welcome_font.render("TETRIS", True, (255, 255, 0))
    shadow_text = welcome_font.render("TETRIS", True, (100, 100, 0))
    screen.blit(shadow_text, (WIDTH // 2 - title_text.get_width() // 2 + 4, HEIGHT // 4 + 4))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

    prompt_text = font.render("Wpisz nazwe", True, (255, 255, 255))
    prompt_text2 = font.render("gracza:", True, (255, 255, 255))

    screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 60))
    screen.blit(prompt_text2, (WIDTH // 2 - prompt_text2.get_width() // 2, HEIGHT // 2 - 40))

    # Input box
    box_width = WIDTH - 60
    input_box_rect = pygame.Rect((WIDTH - box_width) // 2, HEIGHT // 2 - 10, box_width, 40)
    pygame.draw.rect(screen, (50, 50, 70), input_box_rect)
    pygame.draw.rect(screen, (180, 180, 255), input_box_rect, 2)

    player_name_text = font.render(player_name, True, (255, 255, 255))
    text_y = input_box_rect.y + (40 - player_name_text.get_height()) // 2
    screen.blit(player_name_text, (input_box_rect.x + 10, text_y))

    if name_input_active and (pygame.time.get_ticks() // 500) % 2 == 0:
        cursor = font.render("|", True, (255, 255, 255))
        screen.blit(cursor, (input_box_rect.x + 10 + player_name_text.get_width(), text_y))

    hint_line1 = font.render("Nacisnij ENTER", True, (150, 255, 150))
    hint_line2 = font.render("aby rozpoczac", True, (150, 255, 150))

    screen.blit(hint_line1, (WIDTH // 2 - hint_line1.get_width() // 2, HEIGHT - 100))
    screen.blit(hint_line2, (WIDTH // 2 - hint_line2.get_width() // 2, HEIGHT - 70))

    pygame.display.flip()

# Main game loop - welcome screen
running = True
send_state("START")
send_state("BUZZ:START")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if name_input_active:
                if event.key == pygame.K_RETURN:
                    running = False
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    player_name += event.unicode

    show_welcome_screen()
    clock.tick(30)

send_state("PLAY")

# Start the game
while not game.game_over:
    screen.fill(BLACK)
    dt = clock.tick(30)
    
    # Handle Arduino pause state
    handle_arduino_pause(game)
    
    # Update time only when game is not paused
    if not game.paused:
        fall_time += dt
        move_cooldown += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game.game_over = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:  # P key for pause (optional)
                game.paused = not game.paused

    # Handle joystick only when game is not paused
    if not game.paused:
        if move_cooldown > 150:
            if joystick_x < 300:
                game.move_right()
                move_cooldown = 0
            elif joystick_x > 700:
                game.move_left()
                move_cooldown = 0
            if joystick_y > 700:
                game.update(dt)
                move_cooldown = 0
            if prev_joystick_btn == 1 and joystick_btn == 0:
                game.rotate()
                move_cooldown = 0

            prev_joystick_btn = joystick_btn

        if fall_time > (500 - pot_value // 2):
            game.update(dt)
            fall_time = 0
    else:
        # Still update effects even when paused
        game.update(dt)

    # Draw board
    for y in range(ROWS):
        for x in range(COLS):
            color = game.board[y][x]
            draw_block_3d(screen, color, x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE)   
    
    # Draw tetromino
    for x, y in game.tetromino.get_cells():
        if y >= 0:
            draw_block_3d(screen, game.tetromino.color, x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE)

    # Draw spectacular line clear effects
    game.draw_effects(screen)

    # Display score
    score_text = font.render(f"Punkty: {game.score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    
    # Display pause overlay
    if game.paused:
        show_pause_overlay(screen)

    pygame.display.flip()

# Game over sequence
send_state("SCORE:" + str(game.score))
time.sleep(0.1)
send_state("OVER")
time.sleep(0.1)
send_state("BUZZ:GAMEOVER")
time.sleep(0.1)

show_game_over_screen()

# Wait for click to close game
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if (WIDTH // 2 - 100 < mouse_pos[0] < WIDTH // 2 + 100 and
                HEIGHT // 1.5 < mouse_pos[1] < HEIGHT // 1.5 + 40):
                running = False

pygame.quit()