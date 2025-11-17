import pygame
import random
import math
from background_generator import generate_background

import pygame.font
import numpy as np

# Constants
WIDTH = 1200
HEIGHT = 1000

attack_text_width = int(0.25 * WIDTH)
attack_text_height = int(0.25 * HEIGHT)
attack_text_rect = pygame.Rect(0, 0, attack_text_width, attack_text_height)
game_text_width = WIDTH
game_text_height = int(0.05 * HEIGHT)
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
        self.last_direction = pygame.math.Vector2(0, -1)
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
            direction = pygame.math.Vector2(x_change, y_change)
            if direction.length_squared() != 0:
                self.last_direction = direction.normalize()

    def move(self, x_change, y_change):
        self.rect.x += x_change
        self.rect.y += y_change
        self.update_last_direction(x_change, y_change)

    def perform_ranged_attack(self, power_level):
        projectile = Projectile(self.rect.center, self.last_direction, power_level, self.level)
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
            attack = {"name": name,
                      "type": attack_type,
                      "power_level": power_level,
                      "attack_cost": attack_cost,
                      "rage_chance": rage_chance}
            attacks.append(attack)
        return attacks

class Enemy(pygame.sprite.Sprite):
    def __init__(self, corners, x, y):
        super().__init__()
        self.corners = corners
        self.health = corners * (random.uniform(2, 4))
        self.power_level = corners - 2
        self.speed = random.uniform(0.2, 2)
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.jagged_shape = self.generate_jagged_shape()
        self.available_attacks = ['pointy', 'sharp', 'jagged']

    def move_towards_player(self, player_x, player_y):
        dx, dy = player_x - self.rect.x, player_y - self.rect.y
        distance = math.hypot(dx, dy)

        if distance:
            self.rect.x += (dx / distance) * self.speed
            self.rect.y += (dy / distance) * self.speed

    def generate_jagged_shape(self):
        angle_increment = 2 * math.pi / self.corners
        points = [
            (
                self.rect.width // 2 + random.uniform(0.3, 1) * self.rect.width // 2 * math.cos(i * angle_increment),
                self.rect.height // 2 + random.uniform(0.3, 1) * self.rect.height // 2 * math.sin(i * angle_increment),
            )
            for i in range(self.corners)
        ]

        pygame.draw.polygon(self.image, self.get_random_color(), points)
        return points

    def get_random_color(self):
        while True:
            r, g, b = (random.randint(100, 255) for _ in range(3))

            if not (r < 100 and g < 100 and b > 200):
                break

        return (r, g, b)

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
        self.radius += self.attack["power_level"] if self.expanding else -10
        self.red_value -= 10 if not self.expanding else 0
        if not self.expanding and self.red_value <= 0:
            self.kill()
            return
        if self.expanding and self.radius >= (self.attack["power_level"] * 6 * random.uniform(0.75, 1.25)) + self.player.size:
            self.expanding = False

        # Check if dimensions are valid
        if self.radius > 0:
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (self.red_value, 0, 0), (self.radius, self.radius), self.radius, 1)
            self.rect = self.image.get_rect(center=self.initial_center)
            if self.expanding:
                self.check_collision(enemies_group)
        else:
            self.kill()


    def check_collision(self, enemies_group):
        for enemy in enemies_group:
            for corner in enemy.jagged_shape:
                corner_x, corner_y = enemy.rect.x + corner[0], enemy.rect.y + corner[1]
                distance = math.hypot(self.rect.centerx - corner_x, self.rect.centery - corner_y)
                if distance <= self.radius:
                    enemy.health -= self.attack["power_level"]
                    print(f"Enemy hit! Health: {enemy.health}")
                    check_enemy_health(enemy, enemies_group)

class Projectile:
    def __init__(self, position, direction, power_level, player_level):
        self.hit = False
        self.position = pygame.math.Vector2(position)
        direction_vector = pygame.math.Vector2(direction)
        if direction_vector.length_squared() == 0:
            direction_vector = pygame.math.Vector2(0, -1)
        else:
            direction_vector = direction_vector.normalize()
        self.direction = direction_vector

        self.power_level = int(max(1, power_level) * max(1, player_level))
        self.size = int(6 + power_level * 2)
        self.speed = 5 + power_level * 0.5 + player_level * 0.5
        self.fade_rate = max(2, int(power_level * 1.5))
        self.color = [5, 5, 255]

        diameter = self.size * 2
        self.rect = pygame.Rect(0, 0, diameter, diameter)
        self.rect.center = (int(self.position.x), int(self.position.y))

    def move(self):
        self.position += self.direction * self.speed
        self.rect.center = (int(self.position.x), int(self.position.y))

    def fade(self):
        new_blue = max(0, self.color[2] - self.fade_rate)
        self.color[2] = int(new_blue)

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            (int(self.color[0]), int(self.color[1]), int(self.color[2])),
            self.rect.center,
            self.size,
        )

class ScreenRenderer:
    def __init__(self, screen, playarea_background, playarea_rect, player, attack_text_rect, game_text_rect):
        self.screen = screen
        self.playarea_background = playarea_background
        self.playarea_rect = playarea_rect
        self.player = player
        self.attack_text_rect = attack_text_rect
        self.game_text_rect = game_text_rect

    def draw_screen(self, enemies_group, expanding_circle_group, wave_number):
        # Clear the screen
        self.screen.fill((205, 235, 205))
        self.screen.blit(self.playarea_background, (self.playarea_rect.left, self.playarea_rect.top))

        padding = int(self.playarea_rect.width * 0.03)
        start_x = self.playarea_rect.x + padding
        bar_width = (self.playarea_rect.width - 4 * padding) // 3
        bar_height = int(self.game_text_rect.height * 0.8)
        bar_spacing = padding
        status_bar_y = self.playarea_rect.y + self.playarea_rect.height

        self.draw_status_bar(start_x, status_bar_y, bar_width, bar_height, self.player.health, self.player.max_health, (255, 0, 0), "Health")
        self.draw_status_bar(start_x + bar_width + bar_spacing, status_bar_y, bar_width, bar_height, self.player.rage, self.player.max_rage, (255, 140, 0), "Rage")
        self.draw_status_bar(start_x + (bar_width + bar_spacing) * 2, status_bar_y, bar_width, bar_height, self.player.level, self.player.max_level, (0, 255, 0), "Level")

        self.draw_wave_text(wave_number)
        self.display_attacks()
        enemies_group.draw(self.screen)
        expanding_circle_group.draw(self.screen)

        # Update projectiles
        for projectile in self.player.projectiles[:]:
            projectile.move()
            projectile.fade()
            projectile.draw(self.screen)

            if projectile.color[2] == 0:
                self.player.projectiles.remove(projectile)

        self.screen.blit(self.player.image, self.player.rect)
        pygame.display.flip()

    @staticmethod
    def lerp_color(color1, color2, t):
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        return (r, g, b)


    def draw_wave_text(self, wave_number):
        font = pygame.font.SysFont("Arial", 36)  # You can replace "Arial" with any available system font.
        text = font.render(f"Wave: {wave_number}", True, (190, 20, 20))

        # Create the outline by rendering the same text in a larger size
        outline_font = pygame.font.SysFont("Arial", 36)
        outline_text = outline_font.render(f"Wave: {wave_number}", True, (0, 0, 0))

        text_width, text_height = text.get_size()
        x = self.playarea_rect.right - text_width - 10  # 10 pixels padding from the right side of the playarea_rect
        y = 10  # 10 pixels padding from the top

        # First, draw the outline, then draw the main text on top of it.
        self.screen.blit(outline_text, (x - 1, y - 1))
        self.screen.blit(outline_text, (x + 1, y - 1))
        self.screen.blit(outline_text, (x - 1, y + 1))
        self.screen.blit(outline_text, (x + 1, y + 1))
        self.screen.blit(text, (x, y))


    def draw_status_bar(self, x, y, width, height, value, max_value, color, label):
        # Draw the background of the status bar
        background_color = (255, 255, 255)
        pygame.draw.rect(self.screen, background_color, (x, y, width, height))
        # Calculate the filled part of the status bar
        filled_width = int(width * (value / max_value))
        # Draw the filled part of the status bar
        pygame.draw.rect(self.screen, color, (x, y, filled_width, height))
        # Render the label text
        font = pygame.font.Font(None, int(height * 0.8))
        label_surface = font.render(label, True, self.lerp_color(color, background_color, 0.5))
        # Position the label on the status bar
        label_x = x + (width - label_surface.get_width()) // 2
        label_y = y + (height - label_surface.get_height()) // 2
        # Draw the label on the screen
        self.screen.blit(label_surface, (label_x, label_y))


    def display_attacks(self):
        font_size = (self.attack_text_rect.height // (len(player.melee_attacks) + len(self.player.ranged_attacks)) ) * 4
        melee_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        ranged_keys = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']
        attacks = self.player.melee_attacks[:10] + self.player.ranged_attacks[:10]
        keys = melee_keys + ranged_keys
        font = pygame.font.Font(None, font_size)

        for i, attack in enumerate(attacks):
            rage_color = int(attack['rage_chance'] * 255 / 100)
            level_color = int(attack['power_level'] * 255 / 12)
            color = (rage_color, 100, level_color)
            key = keys[i % len(keys)]  # Use modulus to ensure a valid index
            text = font.render(f"{key} - {attack['name']}", True, color)
            y = i * font_size
            self.screen.blit(text, (self.attack_text_rect.x, y))

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

def check_enemy_health(enemy, enemies_group):
    if enemy.health <= 0:
        enemies_group.remove(enemy)

    if not enemies_group:
        global mobs_defeated
        mobs_defeated += 1
        print(f"Mobs defeated: {mobs_defeated}")

        if mobs_defeated < total_mobs:
            generate_mob(2 * (mobs_defeated + 1), player, enemies_group)


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
player = Player()
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
enemies_group = pygame.sprite.Group()
mob = generate_mob(3, player, enemies_group)
renderer = ScreenRenderer(screen, playarea_background, playarea_rect, player, attack_text_rect, game_text_rect)

while running:
    clock.tick(60)

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

    renderer.draw_screen(enemies_group, expanding_circle_group, wave_number)

pygame.quit()
