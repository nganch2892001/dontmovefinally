import pygame
import sys
import random
import numpy as np
import math

# ================= INITIALIZE =================
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DON'T MOVE")
clock = pygame.time.Clock()

# ================= FONTS =================
TITLE_FONT = pygame.font.SysFont(None, 96)
FONT = pygame.font.SysFont(None, 42)
SMALL_FONT = pygame.font.SysFont(None, 26)

# ================= COLORS =================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
DARK_RED = (120, 0, 0)
GRAY = (160, 160, 160)

# ================= SOUND =================
def generate_tone(freq, duration=0.12, volume=0.5):
    sr = 44100
    t = np.linspace(0, duration, int(sr * duration), False)
    wave = np.sin(freq * t * 2 * np.pi)
    audio = wave * (2**15 - 1) * volume
    return pygame.mixer.Sound(audio.astype(np.int16))

tick_sound = generate_tone(900, 0.08)
buzz_sound = generate_tone(120, 0.5)
start_sound = generate_tone(500, 0.25)

def heartbeat_sound(level):
    return generate_tone(60 + level * 6, 0.08, 0.4)

heartbeat = heartbeat_sound(1)
heartbeat_timer = 0

# ================= STATES =================
MENU = "menu"
SETUP = "setup"
INSTRUCTIONS = "instructions"
GAME = "game"
ENDING = "ending"
state = MENU

# ================= PLAYER INFO =================
player_name = ""
player_region = ""
active_input = "name"

# ================= LEVEL SYSTEM =================
level = 1
max_level = 13
LEVEL_TIME_LIMIT = 60  # 1 minute

def level_difficulty(lv):
    return {
        "speed": 3 + lv,
        "min_switch": max(280, 1000 - lv * 55),
        "max_switch": max(650, 1700 - lv * 75),
    }

diff = level_difficulty(level)

# ================= PLAYER =================
player = pygame.Rect(50, HEIGHT // 2 - 20, 40, 40)
finish_line_x = WIDTH - 100

game_over = False
win = False

current_color = "GREEN"
next_switch_time = 0
level_start_time = 0

# ================= EFFECTS =================
shake_frames = 0
glitch_frames = 0
fade_alpha = 0
fading = False

def trigger_shake(frames=8):
    global shake_frames
    shake_frames = frames

def trigger_glitch(frames=20):
    global glitch_frames
    glitch_frames = frames

# ================= RESET =================
def reset_game():
    global game_over, win, current_color, next_switch_time
    global level_start_time, fading, fade_alpha
    global heartbeat, heartbeat_timer

    player.x = 50
    game_over = False
    win = False
    current_color = "GREEN"

    now = pygame.time.get_ticks()
    next_switch_time = now + random.randint(
        diff["min_switch"], diff["max_switch"]
    )
    level_start_time = now

    fading = False
    fade_alpha = 0

    heartbeat = heartbeat_sound(level)
    heartbeat_timer = 0

def switch_color():
    global current_color, next_switch_time
    current_color = "RED" if current_color == "GREEN" else "GREEN"
    next_switch_time = pygame.time.get_ticks() + random.randint(
        diff["min_switch"], diff["max_switch"]
    )
    tick_sound.play()

# ================= MAIN LOOP =================
tilt_angle = 0
tilt_dir = 1

while True:
    dt = clock.tick(60)
    screen.fill(BLACK)

    # Screen shake
    offset_x = offset_y = 0
    if shake_frames > 0:
        shake_frames -= 1
        offset_x = random.randint(-4, 4)
        offset_y = random.randint(-4, 4)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:

            # ===== MENU =====
            if state == MENU:
                if event.key == pygame.K_RETURN:
                    state = SETUP
                if event.key == pygame.K_i:
                    state = INSTRUCTIONS

            # ===== SETUP =====
            elif state == SETUP:
                if event.key == pygame.K_TAB:
                    active_input = "region" if active_input == "name" else "name"
                elif event.key == pygame.K_RETURN:
                    if player_name.strip() and player_region.strip():
                        level = 1
                        diff = level_difficulty(level)
                        reset_game()
                        start_sound.play()
                        state = GAME
                elif event.key == pygame.K_BACKSPACE:
                    if active_input == "name":
                        player_name = player_name[:-1]
                    else:
                        player_region = player_region[:-1]
                else:
                    if event.unicode.isprintable():
                        if active_input == "name" and len(player_name) < 14:
                            player_name += event.unicode
                        elif active_input == "region" and len(player_region) < 14:
                            player_region += event.unicode

            # ===== INSTRUCTIONS =====
            elif state == INSTRUCTIONS:
                if event.key == pygame.K_ESCAPE:
                    state = MENU

            # ===== GAME =====
            elif state == GAME:
                if event.key == pygame.K_ESCAPE:
                    state = MENU
                if event.key == pygame.K_RETURN and game_over:
                    trigger_glitch(30)
                    level = 1
                    diff = level_difficulty(level)
                    reset_game()

            # ===== ENDING =====
            elif state == ENDING:
                if event.key == pygame.K_RETURN:
                    state = MENU

    # ================= GAME LOGIC =================
    if state == GAME:
        now = pygame.time.get_ticks()
        elapsed = (now - level_start_time) / 1000
        time_left = max(0, LEVEL_TIME_LIMIT - elapsed)

        keys = pygame.key.get_pressed()
        moving = keys[pygame.K_SPACE]

        heartbeat_timer += dt
        if heartbeat_timer >= max(220 - level * 10, 80):
            heartbeat.play()
            heartbeat_timer = 0

        if now >= next_switch_time:
            switch_color()

        if not game_over and not win:
            if current_color == "GREEN" and moving:
                player.x += diff["speed"]
            elif current_color == "RED" and moving:
                buzz_sound.play()
                trigger_shake()
                trigger_glitch()
                game_over = True

        if time_left <= 0 and not win:
            trigger_glitch(25)
            game_over = True

        if player.right >= finish_line_x and not win:
            win = True
            fading = True

        if win and fading:
            fade_alpha += 5
            if fade_alpha >= 255:
                level += 1
                if level > max_level:
                    state = ENDING
                else:
                    diff = level_difficulty(level)
                    reset_game()

    # ================= RENDER =================
    if state == MENU:
        tilt_angle += 0.15 * tilt_dir
        if abs(tilt_angle) > 4:
            tilt_dir *= -1

        title = TITLE_FONT.render("DON'T MOVE", True, WHITE)
        rotated = pygame.transform.rotate(title, tilt_angle)
        screen.blit(rotated, rotated.get_rect(center=(WIDTH // 2, 120)))

        screen.blit(FONT.render("TIME IS WATCHING", True, RED),
                    (WIDTH // 2 - 170, 200))
        screen.blit(SMALL_FONT.render(
            "Survive all 13 levels to finish", True, WHITE),
            (WIDTH // 2 - 170, 240))
        screen.blit(SMALL_FONT.render(
            "ENTER — Start     I — Instructions", True, WHITE),
            (WIDTH // 2 - 200, 290))

    elif state == SETUP:
        screen.blit(FONT.render("ENTER YOUR IDENTITY", True, WHITE),
                    (WIDTH // 2 - 200, 80))

        name_color = WHITE if active_input == "name" else GRAY
        region_color = WHITE if active_input == "region" else GRAY

        screen.blit(SMALL_FONT.render("Username:", True, name_color), (200, 150))
        screen.blit(SMALL_FONT.render(player_name + "_", True, WHITE), (330, 150))

        screen.blit(SMALL_FONT.render("Region:", True, region_color), (200, 200))
        screen.blit(SMALL_FONT.render(player_region + "_", True, WHITE), (330, 200))

        screen.blit(SMALL_FONT.render(
            "TAB — Switch | ENTER — Confirm", True, GRAY),
            (WIDTH // 2 - 150, 270))

    elif state == INSTRUCTIONS:
        screen.blit(FONT.render("HOW TO PLAY", True, WHITE),
                    (WIDTH // 2 - 120, 60))
        lines = [
            "• HOLD SPACE to move",
            "• GREEN = Safe",
            "• RED = Do not move",
            "• Fail once → back to Level 1",
            "• 1 minute per level",
            "",
            "ESC — Back"
        ]
        for i, line in enumerate(lines):
            screen.blit(SMALL_FONT.render(line, True, WHITE),
                        (180, 140 + i * 30))

    elif state == GAME:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(70)
        overlay.fill(GREEN if current_color == "GREEN" else DARK_RED)
        screen.blit(overlay, (offset_x, offset_y))

        pygame.draw.rect(screen, WHITE, player.move(offset_x, offset_y))
        pygame.draw.line(screen, WHITE,
                         (finish_line_x + offset_x, 0),
                         (finish_line_x + offset_x, HEIGHT), 4)

        screen.blit(SMALL_FONT.render(
            f"LEVEL {level} / {max_level}", True, WHITE), (20, 20))

        color_text = FONT.render(current_color, True,
                                 GREEN if current_color == "GREEN" else RED)
        screen.blit(color_text,
                    (WIDTH // 2 - color_text.get_width() // 2, 20))

        # Stopwatch (bottom-left)
        cx, cy = 60, HEIGHT - 60
        pygame.draw.circle(screen, WHITE, (cx, cy), 28, 2)
        angle = -math.pi / 2 + ((LEVEL_TIME_LIMIT - time_left)
                                / LEVEL_TIME_LIMIT) * 2 * math.pi
        pygame.draw.line(screen, RED,
                         (cx, cy),
                         (cx + math.cos(angle) * 22,
                          cy + math.sin(angle) * 22), 3)

        if game_over:
            msg = FONT.render("TIME CAUGHT YOU", True, RED)
            tip = SMALL_FONT.render("PRESS ENTER TO RESTART", True, WHITE)
            screen.blit(msg,
                        (WIDTH // 2 - msg.get_width() // 2,
                         HEIGHT // 2 - 40))
            screen.blit(tip,
                        (WIDTH // 2 - tip.get_width() // 2,
                         HEIGHT // 2 + 10))

        if win:
            survive = FONT.render("SURVIVED", True, GREEN)
            screen.blit(survive,
                        (WIDTH // 2 - survive.get_width() // 2,
                         HEIGHT // 2 - 30))

        if fading:
            fade = pygame.Surface((WIDTH, HEIGHT))
            fade.set_alpha(fade_alpha)
            fade.fill(BLACK)
            screen.blit(fade, (0, 0))

    elif state == ENDING:
        screen.blit(FONT.render("LEADERBOARD", True, WHITE),
                    (WIDTH // 2 - 150, 90))
        screen.blit(SMALL_FONT.render(
            f"1. {player_name} — {player_region}", True, WHITE),
            (WIDTH // 2 - 200, 150))
        screen.blit(SMALL_FONT.render(
            "Completed all 13 levels", True, GRAY),
            (WIDTH // 2 - 200, 180))

        screen.blit(SMALL_FONT.render(
            "Congrats. This game shows time is precious.",
            True, WHITE),
            (WIDTH // 2 - 240, 230))
        screen.blit(SMALL_FONT.render(
            "Don't waste it.", True, RED),
            (WIDTH // 2 - 90, 260))

    # Glitch overlay
    if glitch_frames > 0:
        glitch_frames -= 1
        for _ in range(6):
            pygame.draw.rect(
                screen,
                random.choice([RED, WHITE]),
                (random.randint(0, WIDTH),
                 random.randint(0, HEIGHT),
                 random.randint(40, 120),
                 random.randint(4, 10))
            )

    # Instagram credit (safe position)
    credit = SMALL_FONT.render("@nagn._ch — Vietnam", True, GRAY)
    screen.blit(credit,
                (WIDTH - credit.get_width() - 20,
                 HEIGHT - credit.get_height() - 10))

    pygame.display.flip()