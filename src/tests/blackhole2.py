import pygame
import numpy as np
import math
from random import uniform
from pygame import gfxdraw
import colorsys

pygame.init()
WIDTH = 1200
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Black Hole Simulation")

# Constants
BLACK_HOLE_RADIUS = 60
EVENT_HORIZON_RADIUS = 50
PARTICLE_COUNT = 5000
G = 3.0
CENTER = (WIDTH/2, HEIGHT/2)

class Particle:
    def __init__(self, is_jet=False):
        self.is_jet = is_jet
        if is_jet:
            self._init_jet_particle()
        else:
            self._init_disk_particle()
        
    def _init_disk_particle(self):
        angle = uniform(0, 2 * math.pi)
        distance = uniform(70, 400)
        self.x = CENTER[0] + math.cos(angle) * distance
        self.y = CENTER[1] + math.sin(angle) * distance
        
        # Calculate initial orbital velocity
        orbital_speed = math.sqrt(G * BLACK_HOLE_RADIUS / distance) * 2.5
        self.vx = -math.sin(angle) * orbital_speed
        self.vy = math.cos(angle) * orbital_speed
        
        # Temperature increases closer to black hole
        temp_factor = 1 - (distance - 70) / 330
        hue = 0.05 - (temp_factor * 0.05)  # Red to yellow
        rgb = colorsys.hsv_to_rgb(hue, 1, 1)
        self.color = (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        self.alpha = 255
        
        self.alive = True
        self.trail = np.zeros((15, 2))
        self.trail_index = 0
        
    def _init_jet_particle(self):
        side = 1 if uniform(0, 1) > 0.5 else -1
        self.x = CENTER[0] + uniform(-10, 10)
        self.y = CENTER[1]
        angle = math.pi/2 * side + uniform(-0.2, 0.2)
        speed = uniform(15, 25)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = (255, 255, 255)
        self.alpha = 255
        self.alive = True
        self.trail = np.zeros((20, 2))
        self.trail_index = 0

def create_photon_sphere():
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    radius = BLACK_HOLE_RADIUS * 1.5
    for i in range(60):
        alpha = int(100 * math.sin(i/30 * math.pi))
        # Fix: Ensure all color values are integers
        color = (150, 200, 255, max(0, min(255, int(alpha))))
        pygame.draw.circle(surface, color, (int(CENTER[0]), int(CENTER[1])), int(radius + i), 1)
    return surface

class BlackHole:
    def __init__(self):
        self.x = CENTER[0]
        self.y = CENTER[1]
        self.radius = BLACK_HOLE_RADIUS
        self.photon_sphere = create_photon_sphere()
        self.glow_surfaces = self._create_glow_surfaces()
        
    def _create_glow_surfaces(self):
        surfaces = []
        max_radius = self.radius * 3
        for r in range(int(self.radius), int(max_radius), 2):
            alpha = int(200 * (1 - (r - self.radius)/(max_radius - self.radius)))
            # Fix: Ensure alpha is within valid range
            color = (0, 0, 0, max(0, min(255, alpha)))
            surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(r))
            surfaces.append(surface)
        return surfaces
        
    def draw(self, screen):
        # Draw photon sphere
        screen.blit(self.photon_sphere, (0,0))
        
        # Draw event horizon
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.radius)
        
        # Draw glow effects
        for surface in self.glow_surfaces:
            screen.blit(surface, (0,0))

def update_particle(particle, black_hole):
    if particle.is_jet:
        particle.x += particle.vx
        particle.y += particle.vy
        particle.alpha -= 2
        if particle.alpha <= 0:
            particle.alive = False
        return

    dx = black_hole.x - particle.x
    dy = black_hole.y - particle.y
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance < EVENT_HORIZON_RADIUS:
        particle.alive = False
        return
        
    force = G * BLACK_HOLE_RADIUS / (distance * distance)
    angle = math.atan2(dy, dx)
    
    particle.vx += force * math.cos(angle)
    particle.vy += force * math.sin(angle)
    
    # Apply relativistic effects (simplified)
    speed = math.sqrt(particle.vx**2 + particle.vy**2)
    if speed > 0:
        factor = 1 + (distance - EVENT_HORIZON_RADIUS) / 200
        particle.vx /= factor
        particle.vy /= factor
    
    particle.x += particle.vx
    particle.y += particle.vy
    
    # Update trail
    particle.trail[particle.trail_index] = [particle.x, particle.y]
    particle.trail_index = (particle.trail_index + 1) % len(particle.trail)


def main():
    clock = pygame.time.Clock()
    black_hole = BlackHole()
    particles = [Particle() for _ in range(PARTICLE_COUNT)]
    jet_particles = [Particle(is_jet=True) for _ in range(200)]
    
    # Create surface for particle trails
    trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        screen.fill((0, 0, 15))
        trail_surface.fill((0, 0, 0, 0))
        
        # Update and draw disk particles
        for particle in particles:
            if not particle.alive:
                particles.remove(particle)
                particles.append(Particle())
                continue
            
            update_particle(particle, black_hole)
            
            points = [(int(x), int(y)) for x, y in particle.trail]
            if len(points) > 1:
                for i in range(len(points) - 1):
                    intensity = i / len(points)
                    # Fix: Ensure color values are integers
                    color = (*particle.color, max(0, min(255, int(255 * intensity))))
                    gfxdraw.line(trail_surface, 
                                points[i][0], points[i][1],
                                points[i+1][0], points[i+1][1],
                                color)
        
        # Update and draw jet particles
        for particle in jet_particles:
            if not particle.alive:
                jet_particles.remove(particle)
                jet_particles.append(Particle(is_jet=True))
                continue
            
            update_particle(particle, black_hole)
            
            points = [(int(x), int(y)) for x, y in particle.trail]
            if len(points) > 1:
                for i in range(len(points) - 1):
                    intensity = i / len(points)
                    # Fix: Ensure color values are integers
                    color = (255, 255, 255, max(0, min(255, int(particle.alpha * intensity))))
                    gfxdraw.line(trail_surface, 
                                points[i][0], points[i][1],
                                points[i+1][0], points[i+1][1],
                                color)
        
        screen.blit(trail_surface, (0, 0))
        black_hole.draw(screen)
        
        pygame.display.flip()
        
    pygame.quit()

if __name__ == "__main__":
    main()