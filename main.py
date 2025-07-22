import pygame
import random
import sys
import math

# Initialize
pygame.init()
pygame.mixer.init()

# Try to load sounds with error handling
try:
    pygame.mixer.music.load("./assets/bg_music.mp3")
    pygame.mixer.music.play(-1)
    crash_sound = pygame.mixer.Sound("./assets/crash-sound-effect.mp3")
    swap_sound = pygame.mixer.Sound("./assets/swap.mp3")
    sound_enabled = True
except:
    sound_enabled = False
    print("Sound files not found - running without audio")

# Try to load car images with fallback to colored rectangles
try:
    player_image = pygame.image.load("./assets/player_car.png")
    enemy_image = pygame.image.load("./assets/enemy_car.png")
    player_image = pygame.transform.scale(player_image, (40, 70))  # Rotated dimensions
    enemy_image = pygame.transform.scale(enemy_image, (40, 70))    # Rotated dimensions
    # Rotate images 90 degrees for vertical movement
    player_image = pygame.transform.rotate(player_image, 270)
    enemy_image = pygame.transform.rotate(enemy_image, 270)
    images_loaded = True
except:
    images_loaded = False
    print("Image files not found - using colored rectangles")

# Constants
WIDTH, HEIGHT = 1040, 500  # Swapped width and height
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Dodger")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 20)
BLUE = (30, 144, 255)
GREEN = (34, 139, 34)
GREY = (64, 64, 64)
DARK_GREY = (32, 32, 32)
YELLOW = (255, 215, 0)
ORANGE = (255, 165, 0)
PURPLE = (138, 43, 226)
ROAD_COLOR = (48, 48, 48)
GRASS_COLOR = (34, 139, 34)
CONTROL_COLOR = (100, 100, 100)
CONTROL_ACTIVE_COLOR = (150, 150, 150)

# Fonts
small_font = pygame.font.SysFont("Arial", 20)
font = pygame.font.SysFont("Arial", 28)
big_font = pygame.font.SysFont("Arial", 42)
title_font = pygame.font.SysFont("Arial", 60, bold=True)

# Game settings - Now vertical lanes
lane_height = HEIGHT // 5
lanes = [lane_height * i + lane_height // 2 for i in range(1, 5)]  # 4 lanes vertically
car_width, car_height = 80, 45  # Swapped for vertical orientation

# Visual elements
stripe_width, stripe_height, stripe_gap = 50, 8, 30  # Swapped for horizontal stripes
stripe_color = YELLOW

# Mobile controls settings
MOBILE_CONTROLS = True  # Set to False to disable mobile controls
control_button_size = 60
control_button_margin = 20
control_opacity = 180

# Touch control areas
up_button_rect = pygame.Rect(WIDTH - control_button_size - control_button_margin, 
                            HEIGHT//2 - control_button_size - 10, 
                            control_button_size, control_button_size)
down_button_rect = pygame.Rect(WIDTH - control_button_size - control_button_margin, 
                              HEIGHT//2 + 10, 
                              control_button_size, control_button_size)
pause_button_rect = pygame.Rect(WIDTH - control_button_size - control_button_margin, 
                               control_button_margin, 
                               control_button_size, control_button_size)

# Game state variables
state = "menu"
player_lane = 1
player_x = 120  # Now x position instead of y
enemy_cars = []
enemy_speed = 6
spawn_timer = 0
score = 0
high_score = 0
game_speed = 1.0
particles = []
road_offset = 0  # For moving road animation

# Animation variables
menu_animation = 0
button_hover_effects = {}

# Touch control variables
touch_up_pressed = False
touch_down_pressed = False
touch_pause_pressed = False

class Particle:
    def __init__(self, x, y, color, velocity):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.life = 60
        self.max_life = 60
    
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.life -= 1
        return self.life > 0
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color, alpha)
        size = int(4 * (self.life / self.max_life))
        if size > 0:
            pygame.draw.circle(surface, self.color[:3], (int(self.x), int(self.y)), size)

def create_explosion(x, y, color, count=15):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
        particles.append(Particle(x, y, color, velocity))

def update_particles():
    global particles
    particles = [p for p in particles if p.update()]

def draw_particles():
    for particle in particles:
        particle.draw(screen)

def draw_mobile_controls():
    """Draw mobile control buttons"""
    if not MOBILE_CONTROLS:
        return
    
    # Only show controls during gameplay
    if state != "playing" and state != "paused":
        return
    
    # Create surfaces with alpha for transparency
    control_surface = pygame.Surface((control_button_size, control_button_size))
    control_surface.set_alpha(control_opacity)
    
    # Draw UP button
    up_color = CONTROL_ACTIVE_COLOR if touch_up_pressed else CONTROL_COLOR
    control_surface.fill(up_color)
    screen.blit(control_surface, up_button_rect)
    pygame.draw.rect(screen, WHITE, up_button_rect, 2)
    
    # Draw up arrow
    arrow_points = [
        (up_button_rect.centerx, up_button_rect.centery - 15),
        (up_button_rect.centerx - 12, up_button_rect.centery + 8),
        (up_button_rect.centerx + 12, up_button_rect.centery + 8)
    ]
    pygame.draw.polygon(screen, WHITE, arrow_points)
    
    # Draw DOWN button
    down_color = CONTROL_ACTIVE_COLOR if touch_down_pressed else CONTROL_COLOR
    control_surface.fill(down_color)
    screen.blit(control_surface, down_button_rect)
    pygame.draw.rect(screen, WHITE, down_button_rect, 2)
    
    # Draw down arrow
    arrow_points = [
        (down_button_rect.centerx, down_button_rect.centery + 15),
        (down_button_rect.centerx - 12, down_button_rect.centery - 8),
        (down_button_rect.centerx + 12, down_button_rect.centery - 8)
    ]
    pygame.draw.polygon(screen, WHITE, arrow_points)
    
    # Draw PAUSE button
    pause_color = CONTROL_ACTIVE_COLOR if touch_pause_pressed else CONTROL_COLOR
    control_surface.fill(pause_color)
    screen.blit(control_surface, pause_button_rect)
    pygame.draw.rect(screen, WHITE, pause_button_rect, 2)
    
    # Draw pause symbol (two vertical bars)
    bar_width = 8
    bar_height = 20
    bar_spacing = 6
    left_bar_x = pause_button_rect.centerx - bar_spacing//2 - bar_width
    right_bar_x = pause_button_rect.centerx + bar_spacing//2
    bar_y = pause_button_rect.centery - bar_height//2
    
    pygame.draw.rect(screen, WHITE, (left_bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, WHITE, (right_bar_x, bar_y, bar_width, bar_height))

def handle_touch_input(mouse_pos, mouse_pressed):
    """Handle touch/mouse input for mobile controls"""
    global touch_up_pressed, touch_down_pressed, touch_pause_pressed
    global player_lane, state
    
    if not MOBILE_CONTROLS:
        return
    
    # Reset touch states
    old_touch_up = touch_up_pressed
    old_touch_down = touch_down_pressed
    old_touch_pause = touch_pause_pressed
    
    touch_up_pressed = mouse_pressed and up_button_rect.collidepoint(mouse_pos)
    touch_down_pressed = mouse_pressed and down_button_rect.collidepoint(mouse_pos)
    touch_pause_pressed = mouse_pressed and pause_button_rect.collidepoint(mouse_pos)
    
    # Handle lane changes (trigger on press, not hold)
    if state == "playing":
        if touch_up_pressed and not old_touch_up and player_lane > 0:
            if sound_enabled:
                swap_sound.play()
            player_lane -= 1
        elif touch_down_pressed and not old_touch_down and player_lane < 3:
            if sound_enabled:
                swap_sound.play()
            player_lane += 1
        elif touch_pause_pressed and not old_touch_pause:
            state = "paused"
    elif state == "paused":
        if touch_pause_pressed and not old_touch_pause:
            state = "playing"

def draw_text_centered(text, font_obj, y, color=WHITE, shadow=False):
    if shadow:
        shadow_surface = font_obj.render(text, True, BLACK)
        shadow_rect = shadow_surface.get_rect(center=(WIDTH//2 + 2, y + 2))
        screen.blit(shadow_surface, shadow_rect)
    
    text_surface = font_obj.render(text, True, color)
    rect = text_surface.get_rect(center=(WIDTH//2, y))
    screen.blit(text_surface, rect)
    return rect

def draw_text(text, font_obj, x, y, color=WHITE, shadow=True):
    if shadow:
        shadow_surface = font_obj.render(text, True, BLACK)
        screen.blit(shadow_surface, (x + 1, y + 1))
    
    text_surface = font_obj.render(text, True, color)
    screen.blit(text_surface, (x, y))

def button(text, x, y, w, h, inactive, active, action=None, button_id="default"):
    global button_hover_effects
    
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    
    # Hover effect
    is_hovered = x < mouse[0] < x+w and y < mouse[1] < y+h
    
    if button_id not in button_hover_effects:
        button_hover_effects[button_id] = 0
    
    if is_hovered:
        button_hover_effects[button_id] = min(button_hover_effects[button_id] + 0.2, 1.0)
    else:
        button_hover_effects[button_id] = max(button_hover_effects[button_id] - 0.1, 0)
    
    # Interpolate colors
    hover_factor = button_hover_effects[button_id]
    color = [
        int(inactive[i] + (active[i] - inactive[i]) * hover_factor)
        for i in range(3)
    ]
    
    # Draw button with rounded corners effect
    pygame.draw.rect(screen, color, (x, y, w, h))
    pygame.draw.rect(screen, WHITE, (x, y, w, h), 2)
    
    # Add glow effect when hovered
    if hover_factor > 0:
        glow_surface = pygame.Surface((w + 10, h + 10))
        glow_surface.set_alpha(int(50 * hover_factor))
        glow_surface.fill(active)
        screen.blit(glow_surface, (x - 5, y - 5))
    
    draw_text_centered(text, font, y + h // 2, BLACK)
    
    if click[0] and is_hovered and action:
        pygame.time.wait(100)
        action()

def draw_road():
    # Draw grass on top and bottom with moving texture
    grass_pattern_offset = int(road_offset * 0.3) % 20
    for side_y in [0, lanes[-1] + lane_height//2]:
        side_height = lanes[0] - lane_height//2 if side_y == 0 else HEIGHT - side_y
        pygame.draw.rect(screen, GRASS_COLOR, (0, side_y, WIDTH, side_height))
        
        # Add grass texture lines
        for x in range(-20, WIDTH + 20, 10):
            grass_x = x + grass_pattern_offset
            if 0 <= grass_x <= WIDTH:
                darker_green = (max(0, GRASS_COLOR[0] - 20), max(0, GRASS_COLOR[1] - 30), max(0, GRASS_COLOR[2] - 20))
                pygame.draw.line(screen, darker_green, (grass_x, side_y), (grass_x, side_y + side_height), 1)
    
    # Draw road
    road_top = lanes[0] - lane_height//2
    road_bottom = lanes[-1] + lane_height//2
    pygame.draw.rect(screen, ROAD_COLOR, (0, road_top, WIDTH, road_bottom - road_top))
    
    # Draw road edges
    pygame.draw.line(screen, WHITE, (0, road_top), (WIDTH, road_top), 4)
    pygame.draw.line(screen, WHITE, (0, road_bottom), (WIDTH, road_bottom), 4)
    
    # Draw moving lane dividers (horizontal)
    stripe_total_width = stripe_width + stripe_gap
    for i in range(len(lanes) - 1):
        y = (lanes[i] + lanes[i+1]) // 2
        # Calculate offset based on road movement
        offset = road_offset % stripe_total_width
        
        # Draw stripes from left to right with offset
        start_x = -stripe_width - offset
        for x in range(int(start_x), WIDTH + stripe_width, stripe_total_width):
            stripe_x = x
            if stripe_x < WIDTH and stripe_x + stripe_width > 0:
                pygame.draw.rect(screen, stripe_color, (stripe_x, y - stripe_height//2, stripe_width, stripe_height))

def temp_draw_road_on_surface(surface):
    # Draw grass on top and bottom with moving texture
    grass_pattern_offset = int(road_offset * 0.3) % 20
    for side_y in [0, lanes[-1] + lane_height//2]:
        side_height = lanes[0] - lane_height//2 if side_y == 0 else HEIGHT - side_y
        pygame.draw.rect(surface, GRASS_COLOR, (0, side_y, WIDTH, side_height))
        
        # Add grass texture lines
        for x in range(-20, WIDTH + 20, 10):
            grass_x = x + grass_pattern_offset
            if 0 <= grass_x <= WIDTH:
                darker_green = (max(0, GRASS_COLOR[0] - 20), max(0, GRASS_COLOR[1] - 30), max(0, GRASS_COLOR[2] - 20))
                pygame.draw.line(surface, darker_green, (grass_x, side_y), (grass_x, side_y + side_height), 1)
    
    # Draw road
    road_top = lanes[0] - lane_height//2
    road_bottom = lanes[-1] + lane_height//2
    pygame.draw.rect(surface, ROAD_COLOR, (0, road_top, WIDTH, road_bottom - road_top))
    
    # Draw road edges
    pygame.draw.line(surface, WHITE, (0, road_top), (WIDTH, road_top), 4)
    pygame.draw.line(surface, WHITE, (0, road_bottom), (WIDTH, road_bottom), 4)
    
    # Draw moving lane dividers (horizontal)
    stripe_total_width = stripe_width + stripe_gap
    for i in range(len(lanes) - 1):
        y = (lanes[i] + lanes[i+1]) // 2
        # Calculate offset based on road movement
        offset = road_offset % stripe_total_width
        
        # Draw stripes from left to right with offset
        start_x = -stripe_width - offset
        for x in range(int(start_x), WIDTH + stripe_width, stripe_total_width):
            stripe_x = x
            if stripe_x < WIDTH and stripe_x + stripe_width > 0:
                pygame.draw.rect(surface, stripe_color, (stripe_x, y - stripe_height//2, stripe_width, stripe_height))

def draw_player():
    y = lanes[player_lane] - car_height // 2
    
    if images_loaded:
        screen.blit(player_image, (player_x, y))
    else:
        # Draw a nice looking car with rectangles (horizontal orientation)
        pygame.draw.rect(screen, BLUE, (player_x, y, car_width, car_height))
        pygame.draw.rect(screen, WHITE, (player_x, y, car_width, car_height), 2)
        # Add windows
        pygame.draw.rect(screen, WHITE, (player_x + 10, y + 5, 15, car_height - 10))
        pygame.draw.rect(screen, WHITE, (player_x + car_width - 25, y + 5, 15, car_height - 10))

def spawn_enemy():
    for _ in range(10):
        lane = random.randint(0, 3)
        lane_y = lanes[lane] - car_height // 2
        too_close = any(car[3] == lane and car[0] < WIDTH + 150 for car in enemy_cars)
        if not too_close:
            enemy_color = random.choice([RED, ORANGE, PURPLE, GREEN])
            return [WIDTH, lane_y, lane, enemy_color]  # Spawn from right side
    return None

def draw_enemies():
    for enemy in enemy_cars:
        x, y, lane, color = enemy
        if images_loaded:
            screen.blit(enemy_image, (x, y))
        else:
            # Draw colored enemy cars (horizontal orientation)
            pygame.draw.rect(screen, color, (x, y, car_width, car_height))
            pygame.draw.rect(screen, WHITE, (x, y, car_width, car_height), 2)
            # Add windows
            pygame.draw.rect(screen, WHITE, (x + 10, y + 5, 12, car_height - 10))
            pygame.draw.rect(screen, WHITE, (x + car_width - 20, y + 5, 12, car_height - 10))

def move_enemies():
    for enemy in enemy_cars:
        enemy[0] -= enemy_speed * game_speed  # Move left instead of down

def detect_collision():
    player_rect = pygame.Rect(player_x, lanes[player_lane] - car_height // 2, car_width, car_height)
    for enemy in enemy_cars:
        enemy_rect = pygame.Rect(enemy[0], enemy[1], car_width, car_height)
        if player_rect.colliderect(enemy_rect):
            return True, enemy
    return False, None

def reset_game():
    global enemy_cars, score, player_lane, spawn_timer, game_speed, particles, road_offset
    enemy_cars.clear()
    particles.clear()
    score = 0
    player_lane = 1
    spawn_timer = 0
    game_speed = 1.0
    road_offset = 0

def main_menu():
    global state
    state = "menu"

def game_loop():
    global player_lane, spawn_timer, score, state, game_speed, high_score, road_offset

    # Update road movement
    road_offset += enemy_speed * game_speed

    # Clean up off-screen enemies (now checking x position)
    enemy_cars[:] = [car for car in enemy_cars if car[0] > -car_width - 50]

    # Spawn enemies
    spawn_timer += 1
    spawn_rate = max(20, 60 - score // 100)  # Faster spawning as score increases
    if spawn_timer >= spawn_rate:
        new_enemy = spawn_enemy()
        if new_enemy:
            enemy_cars.append(new_enemy)
        spawn_timer = 0

    # Update game speed
    game_speed = 1.0 + score / 1000

    move_enemies()
    
    # Check collision
    collision, hit_enemy = detect_collision()
    if collision:
        if sound_enabled:
            crash_sound.play()
        # Create explosion effect
        player_y = lanes[player_lane]
        create_explosion(player_x + car_width//2, player_y, RED, 20)
        create_explosion(hit_enemy[0] + car_width//2, hit_enemy[1] + car_height//2, hit_enemy[3], 15)
        
        if score > high_score:
            high_score = score
        state = "gameover"

    # Update score
    score += int(game_speed)

def pause_menu():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(128)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    draw_text_centered("PAUSED", big_font, HEIGHT // 2 - 60, YELLOW)
    
    # Different instructions for mobile vs desktop
    if MOBILE_CONTROLS:
        draw_text_centered("Touch pause button to resume", font, HEIGHT // 2 - 20, WHITE)
    else:
        draw_text_centered("Press P to resume", font, HEIGHT // 2 - 20, WHITE)
    
    button("Resume", WIDTH//2 - 75, HEIGHT // 2 + 20, 150, 50, GREY, GREEN, lambda: set_state("playing"), "resume")
    button("Reset", WIDTH//2 - 75, HEIGHT // 2 + 80, 150, 50, GREY, ORANGE, lambda: (reset_game(), set_state("playing")), "reset")

def set_state(new_state):
    global state
    state = new_state

def gameover_screen():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    # Game over box
    box_width, box_height = 350, 280
    box_x, box_y = WIDTH//2 - box_width//2, HEIGHT//2 - box_height//2
    pygame.draw.rect(screen, DARK_GREY, (box_x, box_y, box_width, box_height))
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 3)
    
    center_x = box_x + box_width // 2
    
    draw_text_centered("GAME OVER", big_font, box_y + 60, RED)
    draw_text_centered(f"Final Score: {score}", font, box_y + 110, WHITE)
    
    if score == high_score and score > 0:
        draw_text_centered("NEW HIGH SCORE!", font, box_y + 140, YELLOW)
    else:
        draw_text_centered(f"High Score: {high_score}", font, box_y + 140, YELLOW)
    
    # Center buttons horizontally with spacing
    button_width, button_height = 120, 45
    spacing = 40
    total_width = button_width * 2 + spacing
    start_x = center_x - total_width // 2
    
    def draw_button_text_centered(text, x, y, w, h, font_obj, color=BLACK):
        text_surface = font_obj.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x + w // 2, y + h // 2 + 3))  # Adjust vertical offset by +3 pixels
        screen.blit(text_surface, text_rect)
    
    # Override button function locally to adjust text vertical alignment
    def button_with_adjusted_text(text, x, y, w, h, inactive, active, action=None, button_id="default"):
        global button_hover_effects
        
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        
        # Hover effect
        is_hovered = x < mouse[0] < x+w and y < mouse[1] < y+h
        
        if button_id not in button_hover_effects:
            button_hover_effects[button_id] = 0
        
        if is_hovered:
            button_hover_effects[button_id] = min(button_hover_effects[button_id] + 0.2, 1.0)
        else:
            button_hover_effects[button_id] = max(button_hover_effects[button_id] - 0.1, 0)
        
        # Interpolate colors
        hover_factor = button_hover_effects[button_id]
        color = [
            int(inactive[i] + (active[i] - inactive[i]) * hover_factor)
            for i in range(3)
        ]
        
        # Draw button with rounded corners effect
        pygame.draw.rect(screen, color, (x, y, w, h))
        pygame.draw.rect(screen, WHITE, (x, y, w, h), 2)
        
        # Add glow effect when hovered
        if hover_factor > 0:
            glow_surface = pygame.Surface((w + 10, h + 10))
            glow_surface.set_alpha(int(50 * hover_factor))
            glow_surface.fill(active)
            screen.blit(glow_surface, (x - 5, y - 5))
        
        draw_button_text_centered(text, x, y, w, h, font)
        
        if click[0] and is_hovered and action:
            pygame.time.wait(100)
            action()
    
    button_with_adjusted_text("Play Again", start_x+90, box_y + 200, button_width+30, button_height+10, WHITE, GREEN, 
           lambda: (reset_game(), set_state("playing")), "retry")
 

def start_menu():
    global menu_animation, road_offset, screen
    menu_animation += 1
    
    # Animate road even in menu for visual appeal
    road_offset += 3
    
    # Gradient background
    for y in range(HEIGHT):
        color_ratio = y / HEIGHT
        r = int(DARK_GREY[0] + (GREY[0] - DARK_GREY[0]) * color_ratio)
        g = int(DARK_GREY[1] + (GREY[1] - DARK_GREY[1]) * color_ratio)
        b = int(DARK_GREY[2] + (GREY[2] - DARK_GREY[2]) * color_ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    
    # Draw road in background (semi-transparent)
    road_surface = pygame.Surface((WIDTH, HEIGHT))
    road_surface.set_alpha(100)
    
    # Draw road on the temporary surface
    current_screen = screen
    temp_draw_road_on_surface(road_surface)
    screen.blit(road_surface, (0, 0))
    
    # Animated title
    title_y = HEIGHT//2 - 180 + math.sin(menu_animation * 0.05) * 10
    draw_text_centered("CAR DODGER", title_font, title_y, YELLOW)
    
    # Subtitle with animation
    subtitle_alpha = int(128 + 127 * math.sin(menu_animation * 0.1))
    subtitle_color = (*WHITE[:3], subtitle_alpha)
    draw_text_centered("Made With Pygame", font, title_y + 70, BLUE)
    
    # Buttons
    button("START GAME", WIDTH//2 - 100, HEIGHT//2 - 30, 200, 60, WHITE, GREEN, 
           lambda: set_state("playing"), "start")
    
    
    # High score display
    if high_score > 0:
        draw_text_centered(f"High Score: {high_score}", small_font, HEIGHT - 50, YELLOW)
    
    # Instructions (updated for mobile controls)
    if MOBILE_CONTROLS:
        draw_text_centered("Touch controls on right side during game", small_font, HEIGHT - 100, WHITE)
        draw_text_centered("Or use UP/DOWN arrows • Touch pause button", small_font, HEIGHT - 75, WHITE)
    else:
        draw_text_centered("Use UP/DOWN arrows to move lanes", small_font, HEIGHT - 100, WHITE)
        draw_text_centered("Press P to pause during game", small_font, HEIGHT - 75, WHITE)

# Main game loop
running = True
while running:
    # Get mouse/touch input
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]
    
    # Handle touch controls
    handle_touch_input(mouse_pos, mouse_pressed)
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if state == "playing":
                # Changed to UP/DOWN keys for vertical lane movement
                if event.key == pygame.K_UP and player_lane > 0:
                    if sound_enabled:
                        swap_sound.play()
                    player_lane -= 1
                elif event.key == pygame.K_DOWN and player_lane < 3:
                    if sound_enabled:
                        swap_sound.play()
                    player_lane += 1
                elif event.key == pygame.K_p:
                    state = "paused"
            elif state == "paused":
                if event.key == pygame.K_p:
                    state = "playing"

    # Clear screen
    screen.fill(DARK_GREY)
    
    # Update particles
    update_particles()

    # Game state handling
    if state == "menu":
        start_menu()
    elif state == "playing":
        draw_road()
        draw_player()
        draw_enemies()
        game_loop()
        
        # HUD
        draw_text(f"Score: {score}", font, 15, 15, YELLOW)
        draw_text(f"Speed: {game_speed:.1f}x", font, 15, 50, WHITE)
        if high_score > 0:
            text = f"Best: {high_score}"
            text_surface = font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(topright=(WIDTH - 15, 15))
            screen.blit(text_surface, text_rect)
        
        # Draw mobile controls
        draw_mobile_controls()
        
    elif state == "paused":
        draw_road()
        draw_player()
        draw_enemies()
        # HUD (dimmed)
        draw_text(f"Score: {score}", font, 15, 15, GREY)
        draw_text(f"Speed: {game_speed:.1f}x", font, 15, 50, GREY)
        pause_menu()
        
        # Draw mobile controls (dimmed)
        draw_mobile_controls()
        
    elif state == "gameover":
        draw_road()
        draw_enemies()
        gameover_screen()
    
    # Draw particles on top
    draw_particles()
    
    pygame.display.flip()
    clock.tick(60)  # Increased to 60 FPS for smoother animation

pygame.quit()
print(f"Game ended. Final Score: {score}, High Score: {high_score}")