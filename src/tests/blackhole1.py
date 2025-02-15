import pygame
import numpy as np
import math
from random import randint, uniform
import colorsys

# Initialize Pygame
pygame.init()
WIDTH = 800
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Black Hole Simulation")

# Constants
BLACK_HOLE_RADIUS = 30
EVENT_HORIZON_RADIUS = 20
PARTICLE_COUNT = 1000
G = 0.5  # Gravitational constant (adjusted for visualization)

class Particle:
    def __init__(self):
        angle = uniform(0, 2 * math.pi)
        distance = uniform(100, 350)
        self.x = WIDTH/2 + math.cos(angle) * distance
        self.y = HEIGHT/2 + math.sin(angle) * distance
        self.vx = uniform(-1, 1)
        self.vy = uniform(-1, 1)
        self.trail = []
        self.trail_length = 20
        self.alive = True
        self.brightness = uniform(0.5, 1.0)

class BlackHole:
    def __init__(self):
        self.x = WIDTH/2
        self.y = HEIGHT/2
        self.radius = BLACK_HOLE_RADIUS
        
    def draw(self, screen):
        # Draw the accretion disk glow
        max_radius = self.radius * 4
        for r in range(int(self.radius), int(max_radius)):
            alpha = int(255 * (1 - (r - self.radius)/(max_radius - self.radius)))
            color = (0, int(100 * (1 - r/max_radius)), int(255 * (1 - r/max_radius)), alpha)
            surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r)
            screen.blit(surface, (0,0))
            
        # Draw the black hole
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.radius)



def calculate_gravitational_force(particle, black_hole):
    dx = black_hole.x - particle.x
    dy = black_hole.y - particle.y
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance < EVENT_HORIZON_RADIUS:
        particle.alive = False
        return 0, 0
        
    force = G * (BLACK_HOLE_RADIUS * 10) / (distance * distance)
    angle = math.atan2(dy, dx)
    
    return force * math.cos(angle), force * math.sin(angle)

def apply_gravitational_lensing(x, y, black_hole):
    dx = x - black_hole.x
    dy = y - black_hole.y
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance < EVENT_HORIZON_RADIUS:
        return x, y
        
    # Simplified gravitational lensing effect
    bend_factor = 1 + (BLACK_HOLE_RADIUS * 8) / (distance * distance)
    angle = math.atan2(dy, dx)
    
    new_distance = distance * bend_factor
    return (black_hole.x + math.cos(angle) * new_distance,
            black_hole.y + math.sin(angle) * new_distance)


def main():
    clock = pygame.time.Clock()
    black_hole = BlackHole()
    particles = [Particle() for _ in range(PARTICLE_COUNT)]
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        screen.fill((0, 0, 15))  # Dark blue background
        
        # Update and draw particles
        for particle in particles:
            if not particle.alive:
                particles.remove(particle)
                particles.append(Particle())
                continue
                
            # Apply gravitational force
            fx, fy = calculate_gravitational_force(particle, black_hole)
            particle.vx += fx
            particle.vy += fy
            
            # Update position
            particle.x += particle.vx
            particle.y += particle.vy
            
            # Apply gravitational lensing to trail
            particle.trail.append((particle.x, particle.y))
            if len(particle.trail) > particle.trail_length:
                particle.trail.pop(0)
            
            # Draw particle trail with lensing effect
            if len(particle.trail) > 1:
                points = []
                for i in range(len(particle.trail)):
                    x, y = particle.trail[i]
                    lensed_x, lensed_y = apply_gravitational_lensing(x, y, black_hole)
                    points.append((int(lensed_x), int(lensed_y)))
                    
                    # Calculate color based on position in trail
                    intensity = i / len(particle.trail)
                    color = (
                        int(255 * intensity * particle.brightness),
                        int(150 * intensity * particle.brightness),
                        int(50 * intensity * particle.brightness)
                    )
                    
                    if i > 0:
                        pygame.draw.line(screen, color, points[i-1], points[i], 2)
        
        # Draw black hole
        black_hole.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()