import pygame
import noise

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
