import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
CENTER = (WIDTH // 2, HEIGHT // 2)
BLACK_HOLE_RADIUS = 60
DISK_INNER_RADIUS = 80
DISK_OUTER_RADIUS = 200
NUM_DISK_PARTICLES = 500
NUM_STARS = 150
ROTATION_SPEED = 0.02

# Colors
BLACK = (0, 0, 0)
SPACE_BG = (5, 5, 20)
DISK_BRIGHT = (255, 140, 0)
DISK_DARK = (120, 50, 10)
STAR_COLOR = (255, 255, 255)

# Setup display
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Realistic Black Hole with Gravitational Lensing")

# Generate moving starfield background
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 4)) for _ in range(NUM_STARS)]

def draw_starfield():
    for i in range(len(stars)):
        x, y, size = stars[i]
        pygame.draw.circle(window, STAR_COLOR, (x, y), size)
        stars[i] = (x, (y + size) % HEIGHT, size)  # Move stars downward

# Generate accretion disk particles
disk_particles = [
    (random.uniform(DISK_INNER_RADIUS, DISK_OUTER_RADIUS), random.uniform(0, 2 * math.pi))
    for _ in range(NUM_DISK_PARTICLES)
]

def draw_accretion_disk(angle_offset, draw_front=False):
    """
    Draws the accretion disk while handling gravitational lensing.
    - If `draw_front == False`: Draw only the BACK part (behind the black hole)
    - If `draw_front == True`: Draw only the FRONT part (in front of the black hole, appearing lifted)
    """
    for r, theta in disk_particles:
        adjusted_theta = theta + angle_offset
        x = CENTER[0] + r * math.cos(adjusted_theta)
        y = CENTER[1] + r * math.sin(adjusted_theta)

        # Doppler Shift Effect (Redshift for far part, Blueshift for near part)
        shift_factor = 0.5 * (1 + math.sin(adjusted_theta))  # Shift based on orbit direction
        color = (
            int(DISK_BRIGHT[0] * (1 - shift_factor) + DISK_DARK[0] * shift_factor),
            int(DISK_BRIGHT[1] * (1 - shift_factor) + DISK_DARK[1] * shift_factor),
            int(DISK_BRIGHT[2] * (1 - shift_factor) + DISK_DARK[2] * shift_factor),
        )

        # Apply gravitational lens warping effect
        if y > CENTER[1]:  # Handle only the lower part of the disk
            if draw_front:
                # Lifting the lower part to simulate gravitational lensing
                y_lensed = CENTER[1] - abs(y - CENTER[1]) * 0.6
                pygame.draw.circle(window, color, (int(x), int(y_lensed)), 2)
        else:
            if not draw_front:
                pygame.draw.circle(window, color, (int(x), int(y)), 2)

# Function to simulate gravitational lensing (distortion effect around black hole)
def draw_gravitational_lensing():
    lens_radius = BLACK_HOLE_RADIUS * 1.5
    for i in range(360):
        angle = math.radians(i)
        d = lens_radius + math.sin(pygame.time.get_ticks() * 0.001 + i * 0.1) * 10
        x = int(CENTER[0] + d * math.cos(angle))
        y = int(CENTER[1] + d * math.sin(angle))
        
        # Dynamic curved light effect
        gradient_color = (255, 255, max(0, min(255, int(100 + 155 * math.cos(i * 0.1)))))
        
        pygame.draw.circle(window, gradient_color, (x, y), 1)

# Event horizon (black hole)
def draw_black_hole():
    pygame.draw.circle(window, BLACK, CENTER, BLACK_HOLE_RADIUS)


def main():
    clock = pygame.time.Clock()
    running = True
    angle_offset = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        angle_offset += ROTATION_SPEED

        # Clear screen
        window.fill(SPACE_BG)
        
        draw_starfield()

        # Draw the BACK accretion disk (behind black hole)
        draw_accretion_disk(angle_offset, draw_front=False)

        # Gravitational lensing halo effect
        draw_gravitational_lensing()

        # Draw black hole (occluding BACK disk)
        draw_black_hole()

        # Draw the FRONT accretion disk (with lifted part)
        draw_accretion_disk(angle_offset, draw_front=True)

        # Update screen
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()