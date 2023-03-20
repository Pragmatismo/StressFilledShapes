import pygame
import random
import math
import noise

import pygame.font
import numpy as np

# Constants
# Constants
WIDTH = 1200
HEIGHT = 1000

attack_text_width = int(0.25 * WIDTH)
attack_text_height = int(0.25 * HEIGHT)
attack_text_rect = pygame.Rect(0, 0, attack_text_width, attack_text_height)

game_text_width = WIDTH
game_text_height = int(0.25 * HEIGHT)

playarea_width = WIDTH - attack_text_width
playarea_height = HEIGHT - game_text_height

game_text_rect = pygame.Rect(0, playarea_height, game_text_width, game_text_height)
playarea_rect = pygame.Rect(attack_text_width, 0, playarea_width, playarea_height)


WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shape Fighter")
clock = pygame.time.Clock()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 30
        self.health = 100
        self.rage = 0
        self.level = 3
        self.speed = 5
        self.max_health = 100
        self.max_rage = 100
        self.max_level = 12
        self.projectiles = []
        self.last_direction = (0, 0)
        #
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (self.size // 2, self.size // 2), self.size // 2)
        self.radius = self.size // 2
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH // 2
        self.rect.y = HEIGHT // 2

        self.melee_attacks = self.generate_attacks("melee")
        self.ranged_attacks = self.generate_attacks("ranged")

    def update_last_direction(self, x_change, y_change):
        if x_change != 0 or y_change != 0:
            self.last_direction = (x_change, y_change)

    def move(self, x_change, y_change):
        self.rect.x += x_change
        self.rect.y += y_change
        self.update_last_direction(x_change, y_change)

    def perform_ranged_attack(self, power_level):
        fade_rate = (power_level * random.randint(3,10)) / 10
        projectile = Projectile(self.rect.x, self.rect.y, self.last_direction, fade_rate)
        self.projectiles.append(projectile)

    def generate_attacks(self, attack_type):
        attacks = []

        relaxation_techniques = [
            "Meditation", "Deep Breathing", "Progressive Muscle Relaxation", "Visualization", "Autogenic Training",
            "Biofeedback", "Cognitive Reframing", "Yoga", "Tai Chi", "Qigong", "Aromatherapy", "Massage",
            "Reflexology", "Reiki", "Acupuncture", "Hypnosis", "Music Therapy", "Art Therapy", "Dance Therapy",
            "Journaling", "Laughter Therapy", "Nature Walks", "Gardening", "Animal Therapy", "Reading", "Warm Bath",
            "Exercise", "Healthy Eating", "Adequate Sleep", "Social Support"
        ]

        relaxation_objects = [
            "Candles", "Blanket", "Incense", "Aromatherapy Diffuser", "Herbal Tea", "Massage Oil", "Pillow",
            "Eye Mask", "Ear Plugs", "Sound Machine", "Heating Pad", "Warm Socks", "Bath Salts", "Bubble Bath",
            "Essential Oils", "Face Mask", "Foot Spa", "Body Lotion", "Sleep Mask", "Humidifier", "Head Massager",
            "Yoga Mat", "Meditation Cushion", "Sleeping Bag", "Noise-cancelling Headphones", "Neck Pillow",
            "Bathrobe", "Tub Pillow", "Book", "Hammock", "Stress Ball"
        ]

        names = relaxation_techniques if attack_type == "melee" else relaxation_objects
        random.shuffle(names)

        for i in range(12):
            name = names[i]
            power_level = random.randint(1, 12)
            attack_cost = random.randint(power_level * 2, power_level * 4)
            rage_chance = power_level * 5

            attack = {
                "name": name,
                "type": attack_type,
                "power_level": power_level,
                "attack_cost": attack_cost,
                "rage_chance": rage_chance
            }
            attacks.append(attack)

        return attacks

class Enemy(pygame.sprite.Sprite):
    def __init__(self, corners, x, y):
        super().__init__()
        self.corners = corners
        self.health = corners * (random.randint(200,400) / 100)
        self.power_level = corners - 2
        self.speed = random.randint(1, 10) / 5
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.jagged_shape = self.generate_jagged_shape()
        self.available_attacks = self.get_available_attacks()

    def move_towards_player(self, player_x, player_y):
        dx = player_x - self.rect.x
        dy = player_y - self.rect.y
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance != 0:
            unit_vector_x = dx / distance
            unit_vector_y = dy / distance

            self.rect.x += unit_vector_x * self.speed
            self.rect.y += unit_vector_y * self.speed

    def generate_jagged_shape(self):
        angle_increment = 2 * math.pi / self.corners
        points = []

        for i in range(self.corners):
            angle = i * angle_increment
            random_length = random.uniform(0.3, 1) * self.rect.width // 2
            x = self.rect.width // 2 + random_length * math.cos(angle)
            y = self.rect.height // 2 + random_length * math.sin(angle)
            points.append((x, y))

        pygame.draw.polygon(self.image, self.get_random_color(), points)
        return points

    def get_available_attacks(self):
        return ['pointy', 'sharp', 'jagged']

    def get_random_color(self):
        while True:
            r = random.randint(100, 255)
            g = random.randint(100, 255)
            b = random.randint(100, 255)

            # Check if the color is not too close to blue
            if not (r < 100 and g < 100 and b > 200):
                break

        return (r, g, b)

def check_enemy_health(enemy, enemies_group):
    if enemy.health <= 0:
        enemies_group.remove(enemy)

    if not enemies_group:
        global mobs_defeated
        mobs_defeated += 1
        print(f"Mobs defeated: {mobs_defeated}")

        if mobs_defeated < total_mobs:
            generate_mob(2 * (mobs_defeated + 1), player, enemies_group)

class ExpandingCircle(pygame.sprite.Sprite):
    def __init__(self, player, attack):
        super().__init__()
        self.attack = attack
        self.player = player
        self.radius = player.size
        self.red_value = 255
        self.expanding = True
        self.initial_center = (self.player.rect.x + self.player.radius, self.player.rect.y + self.player.radius)

    def update(self, enemies_group):
        if self.expanding:
            self.radius += self.attack["power_level"]
            max_size = (self.attack["power_level"] * 6 * random.uniform(0.75, 1.25)) + self.player.size
            if self.radius >= max_size:
                self.expanding = False
        else:
            self.red_value -= 10
            if self.red_value <= 0:
                self.kill()
                return

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (self.red_value, 0, 0), (self.radius, self.radius), self.radius, 1)
        self.rect = self.image.get_rect()
        self.rect.center = self.initial_center

        if self.expanding:
            self.check_collision(enemies_group)

    def check_collision(self, enemies_group):
        for enemy in enemies_group:
            for corner in enemy.jagged_shape:
                corner_x = enemy.rect.x + corner[0]
                corner_y = enemy.rect.y + corner[1]
                distance = math.sqrt((self.rect.centerx - corner_x)**2 + (self.rect.centery - corner_y)**2)

                if distance <= self.radius:
                    enemy.health -= self.attack["power_level"]
                    print(f"Enemy hit! Health: {enemy.health}")
                    check_enemy_health(enemy, enemies_group)

class Projectile:
    def __init__(self, x, y, direction, fade_rate):
        self.hit = False
        self.power_level = random.randint(50, 2500) * player.level
        self.x = x
        self.y = y
        self.direction = direction
        self.color = (5, 5, 255)
        self.size = (random.randint(24, 24*8) * player.level) / 12
        self.speed = random.randint(5, 25) / 50
        self.fade_rate = fade_rate
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def move(self):
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed
        self.rect.x = self.x
        self.rect.y = self.y

    def fade(self):
        self.color = (self.color[0], self.color[1], max(0, self.color[2] - self.fade_rate))

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.size)



# Create player instance
player = Player()

def generate_background(playarea_rect):
    grass_color = (200, 230, 200)
    mud_color = (180, 150, 100)
    scale = 0.1
    octaves = 4

    width, height = playarea_rect.size
    playarea_background = pygame.Surface((width, height))

    for x in range(width):
        for y in range(height):
            n = noise.pnoise2(x * scale, y * scale, octaves)
            n = (n + 1) / 2

            if n < 0.5:
                color = lerp_color(grass_color, mud_color, n * 2)
            else:
                color = lerp_color(mud_color, grass_color, (n - 0.5) * 2)

            playarea_background.set_at((x, y), color)

    return playarea_background



def lerp_color(color1, color2, t):
    r = int(color1[0] + (color2[0] - color1[0]) * t)
    g = int(color1[1] + (color2[1] - color1[1]) * t)
    b = int(color1[2] + (color2[2] - color1[2]) * t)
    return (r, g, b)


def divide_power_level(power_level, num_enemies):
    power_levels = np.random.randint(1, power_level, size=num_enemies - 1)
    power_levels = np.sort(power_levels)
    power_levels = np.insert(power_levels, 0, 0)
    power_levels = np.append(power_levels, power_level)

    return np.diff(power_levels)

def generate_mob(power_level, player, enemies_group):
    num_enemies = random.randint(1, power_level // 3 + 1)
    enemy_powers = divide_power_level(power_level, num_enemies)

    for power in enemy_powers:
        corners = power + 3
        created = False
        while not created:
            x = random.randint(playarea_rect.left, playarea_rect.right - 50)  # Subtract 50 (enemy width) to prevent enemies from spawning outside the play area horizontally
            y = random.randint(playarea_rect.top, playarea_rect.bottom - 50)  # Subtract 50 (enemy height) to prevent enemies from spawning outside the play area vertically
            enemy = Enemy(corners, x, y)
            distance = math.sqrt((player.rect.x - x)**2 + (player.rect.y - y)**2)

            if distance > player.radius * 3:
                enemies_group.add(enemy)
                created = True

    print(f"Generated a mob with a power level of {power_level} containing {num_enemies}")


def draw_wave_text(screen, wave_number):
    font = pygame.font.Font(None, 36)
    text = font.render(f"Wave: {wave_number}", True, BLACK)
    screen.blit(text, (WIDTH - 100, 10))


def lerp_color(color1, color2, t):
    r = int(color1[0] + (color2[0] - color1[0]) * t)
    g = int(color1[1] + (color2[1] - color1[1]) * t)
    b = int(color1[2] + (color2[2] - color1[2]) * t)
    return (r, g, b)


def divide_power_level(power_level, num_enemies):
    power_levels = np.random.randint(1, power_level, size=num_enemies - 1)
    power_levels = np.sort(power_levels)
    power_levels = np.insert(power_levels, 0, 0)
    power_levels = np.append(power_levels, power_level)

    return np.diff(power_levels)

def generate_mob(power_level, player, enemies_group):
    num_enemies = random.randint(1, power_level // 3 + 1)
    enemy_powers = divide_power_level(power_level, num_enemies)

    for power in enemy_powers:
        corners = power + 3
        created = False
        while not created:
            x = random.randint(playarea_rect.left, playarea_rect.right - 50)  # Subtract 50 (enemy width) to prevent enemies from spawning outside the play area horizontally
            y = random.randint(playarea_rect.top, playarea_rect.bottom - 50)  # Subtract 50 (enemy height) to prevent enemies from spawning outside the play area vertically
            enemy = Enemy(corners, x, y)
            distance = math.sqrt((player.rect.x - x)**2 + (player.rect.y - y)**2)

            if distance > player.radius * 3:
                enemies_group.add(enemy)
                created = True

    print(f"Generated a mob with a power level of {power_level} containing {num_enemies}")


def draw_wave_text(screen, wave_number):
    font = pygame.font.Font(None, 36)
    text = font.render(f"Wave: {wave_number}", True, BLACK)
    screen.blit(text, (WIDTH - 100, 10))

def display_attacks(screen, player, attack_text_rect):
    font_size = (attack_text_rect.height // (len(player.melee_attacks) + len(player.ranged_attacks)) ) * 4

    melee_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    ranged_keys = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']

    attacks = player.melee_attacks[:10] + player.ranged_attacks[:10]
    keys = melee_keys + ranged_keys

    font = pygame.font.Font(None, font_size)

    for i, attack in enumerate(attacks):
        rage_color = int(attack['rage_chance'] * 255 / 100)
        level_color = int(attack['power_level'] * 255 / 12)
        color = (rage_color, 100, level_color)
        key = keys[i % len(keys)]  # Use modulus to ensure a valid index
        text = font.render(f"{key} - {attack['name']}", True, color)
        y = i * font_size
        screen.blit(text, (attack_text_rect.x, y))

def draw_status_bar(screen, x, y, width, height, value, max_value, color, label):
    # Draw the background of the status bar
    pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height))

    # Calculate the filled part of the status bar
    filled_width = int(width * (value / max_value))

    # Draw the filled part of the status bar
    pygame.draw.rect(screen, color, (x, y, filled_width, height))

    # Render the label text
    font = pygame.font.Font(None, 24)
    label_surface = font.render(label, True, (255, 255, 255))

    # Position the label under the status bar
    label_x = x + (width - label_surface.get_width()) // 2
    label_y = y + height + 5

    # Draw the label on the screen
    screen.blit(label_surface, (label_x, label_y))



def perform_attack(attack):
    print(f"Attack Name: {attack['name']}, Type: {attack['type']}, Power Level: {attack['power_level']}")
    if random.randint(0, 101) > attack['rage_chance']:
        player.rage += 1
        if player.rage >= player.max_rage:
            player.rage = 0
            if player.level > 1:
                player.level -= 1

    if attack['type'] == "melee":
        perform_melee_attack(attack)

def perform_melee_attack(attack):
    expanding_circle = ExpandingCircle(player, attack)
    expanding_circle_group.add(expanding_circle)

def check_collision(player, enemies_group):
    for enemy in enemies_group.sprites():
        for corner in enemy.jagged_shape:
            corner_x = enemy.rect.x + corner[0]
            corner_y = enemy.rect.y + corner[1]
            distance = math.sqrt((player.rect.x + player.radius - corner_x)**2 + (player.rect.y + player.radius - corner_y)**2)

            if distance <= player.radius:
                player.health -= enemy.power_level

                # Calculate push direction
                push_x = (player.rect.x + player.radius) - corner_x
                push_y = (player.rect.y + player.radius) - corner_y
                push_distance = math.sqrt(push_x**2 + push_y**2)

                # Normalize push direction
                push_x /= push_distance
                push_y /= push_distance

                # Apply push force
                push_force = 20
                player.rect.x += push_x * push_force
                player.rect.y += push_y * push_force
                player.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT - 150))

                break  # No need to check other corners for this enemy


def display_attacks(screen, player, attack_text_rect):
    font_size = (attack_text_rect.height // (len(player.melee_attacks) + len(player.ranged_attacks)) ) * 4

    melee_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    ranged_keys = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']

    attacks = player.melee_attacks[:10] + player.ranged_attacks[:10]
    keys = melee_keys + ranged_keys

    font = pygame.font.Font(None, font_size)

    for i, attack in enumerate(attacks):
        rage_color = int(attack['rage_chance'] * 255 / 100)
        level_color = int(attack['power_level'] * 255 / 12)
        color = (rage_color, 100, level_color)
        key = keys[i % len(keys)]  # Use modulus to ensure a valid index
        text = font.render(f"{key} - {attack['name']}", True, color)
        y = i * font_size
        screen.blit(text, (attack_text_rect.x, y))

def draw_status_bar(screen, x, y, width, height, value, max_value, color, label):
    # Draw the background of the status bar
    pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height))

    # Calculate the filled part of the status bar
    filled_width = int(width * (value / max_value))

    # Draw the filled part of the status bar
    pygame.draw.rect(screen, color, (x, y, filled_width, height))

    # Render the label text
    font = pygame.font.Font(None, 24)
    label_surface = font.render(label, True, (255, 255, 255))

    # Position the label under the status bar
    label_x = x + (width - label_surface.get_width()) // 2
    label_y = y + height + 5

    # Draw the label on the screen
    screen.blit(label_surface, (label_x, label_y))



def perform_attack(attack):
    print(f"Attack Name: {attack['name']}, Type: {attack['type']}, Power Level: {attack['power_level']}")
    if random.randint(0, 101) > attack['rage_chance']:
        player.rage += 1
        if player.rage >= player.max_rage:
            player.rage = 0
            if player.level > 1:
                player.level -= 1

    if attack['type'] == "melee":
        perform_melee_attack(attack)
    elif attack['type'] == "ranged":
        player.perform_ranged_attack(attack['power_level'])

def perform_melee_attack(attack):
    expanding_circle = ExpandingCircle(player, attack)
    expanding_circle_group.add(expanding_circle)

def check_collision(player, enemies_group):
    for enemy in enemies_group.sprites():
        for corner in enemy.jagged_shape:
            corner_x = enemy.rect.x + corner[0]
            corner_y = enemy.rect.y + corner[1]
            distance = math.sqrt((player.rect.x + player.radius - corner_x)**2 + (player.rect.y + player.radius - corner_y)**2)

            if distance <= player.radius:
                player.health -= enemy.power_level

                # Calculate push direction
                push_x = (player.rect.x + player.radius) - corner_x
                push_y = (player.rect.y + player.radius) - corner_y
                push_distance = math.sqrt(push_x**2 + push_y**2)

                # Normalize push direction
                push_x /= push_distance
                push_y /= push_distance

                # Apply push force
                push_force = 20
                player.rect.x += push_x * push_force
                player.rect.y += push_y * push_force
                player.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT - 150))

                break  # No need to check other corners for this enemy




# Main game loop
wave_number = 1
mobs_defeated = 0
total_mobs = 1  # Change this to the number of mobs in a wave
melee_keys = [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
ranged_keys = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t, pygame.K_y, pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_p]
key_delays = {}
bar_width = 250
bar_height = 50
bar_spacing = 10
num_bars = 3
total_width = (bar_width * num_bars) + (bar_spacing * (num_bars - 1))
start_x = game_text_rect.x + (game_text_rect.width - total_width) // 2

playarea_background = generate_background(playarea_rect)
expanding_circle_group = pygame.sprite.Group()
running = True
FPS = 60
enemies_group = pygame.sprite.Group()
mob = generate_mob(3, player, enemies_group)
print(mob)


while running:
    clock.tick(FPS)

    # Process input (events)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    x_change = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
    y_change = keys[pygame.K_DOWN] - keys[pygame.K_UP]

    player.move(x_change * player.speed, y_change * player.speed)

    check_collision(player, enemies_group)

    for projectile in player.projectiles:
        for enemy in enemies_group:
            if projectile.rect.colliderect(enemy.rect):
                # Collision detected, deduct health from the enemy
                enemy.health -= projectile.power_level
                # Remove the projectile from the list
                projectile.hit = True
                check_enemy_health(enemy, enemies_group)

    player.projectiles = [projectile for projectile in player.projectiles if not projectile.hit]




    # Update key delays and remove keys with zero delay
    for key in list(key_delays.keys()):
        key_delays[key] -= 1
        if key_delays[key] == 0:
            del key_delays[key]


    for i, key in enumerate(melee_keys + ranged_keys):
        if keys[key] and key not in key_delays:
            delay = random.randint(25,100)  # Set the desired delay value here
            key_delays[key] = delay
            print(key_delays)

            if i < len(melee_keys):
                attack = player.melee_attacks[i]
                perform_attack(attack)
                player.melee_attacks[i] = player.generate_attacks("melee")[i]
            else:
                ranged_index = i - len(melee_keys)
                attack = player.ranged_attacks[ranged_index]
                perform_attack(attack)
                player.ranged_attacks[ranged_index] = player.generate_attacks("ranged")[ranged_index]

    for enemy in enemies_group:
        enemy.move_towards_player(player.rect.x, player.rect.y)



    if mobs_defeated >= total_mobs:
        wave_number += 1
        mobs_defeated = 0
        power_level = int(wave_number * 3 * random.uniform(0.75, 1.25))
        mob = generate_mob(power_level, player, enemies_group)
        print(mob)


    expanding_circle_group.update(enemies_group)
    # Clear the screen
    screen.fill((205,235,205))
    screen.blit(playarea_background, (playarea_rect.left, playarea_rect.top))
    draw_status_bar(screen, start_x, game_text_rect.y, bar_width, bar_height, player.health, player.max_health, (255, 0, 0), "Health")
    draw_status_bar(screen, start_x + bar_width + bar_spacing, game_text_rect.y, bar_width, bar_height, player.rage, player.max_rage, (255, 140, 0), "Rage")
    draw_status_bar(screen, start_x + (bar_width + bar_spacing) * 2, game_text_rect.y, bar_width, bar_height, player.level, player.max_level, (0, 255, 0), "Level")
    draw_wave_text(screen, wave_number)
    display_attacks(screen, player, attack_text_rect)
    enemies_group.draw(screen)
    expanding_circle_group.draw(screen)

    # Update projectiles
    for projectile in player.projectiles[:]:
        projectile.move()
        projectile.fade()
        projectile.draw(screen)

        if projectile.color[2] == 0:
            player.projectiles.remove(projectile)

    screen.blit(player.image, player.rect)
    pygame.display.flip()
    #clock.tick(60)

pygame.quit()
