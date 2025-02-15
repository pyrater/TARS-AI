import pygame
import threading
import queue
from typing import Dict, Any, List
import time
from datetime import datetime
import random
import math

class Star:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.reset()
        
    def reset(self):
        # Initialize star at random position
        self.x = random.randrange(-self.width, self.width)
        self.y = random.randrange(-self.height, self.height)
        self.z = random.randrange(1, self.width)
        self.speed = random.uniform(2, 5)
        
    def move(self):
        # Move star toward viewer
        self.z -= self.speed
        # Reset star if it's too close
        if self.z <= 0:
            self.reset()
    
    def draw(self, screen):
        # Project 3D position to 2D screen coordinates
        factor = 200.0 / self.z
        x = self.x * factor + self.width // 2
        y = self.y * factor + self.height // 2
        
        # Calculate star size based on distance
        size = max(1, min(5, 200.0 / self.z))
        
        # Adjust brightness from dark to bright as it moves closer
        brightness = int(255 * (1 - self.z / self.width))  
        brightness = max(10, min(255, brightness))  # Keep brightness in a visible range

        # Add color variation for a cosmic effect
        if self.z > self.width * 0.75:  # Distant stars - bluish tint
            color = (brightness // 2, brightness // 2, brightness)  
        elif self.z > self.width * 0.5:  # Mid-range stars - neutral white
            color = (brightness, brightness, brightness)
        else:  # Closer stars - slight yellow tint
            color = (brightness, brightness * 0.9, brightness * 0.7)

        # Add slight flicker effect for realism
        flicker = random.randint(-20, 20)  
        color = tuple(max(0, min(255, c + flicker)) for c in color)

        # Only draw if star is on screen
        if 0 <= x < self.width and 0 <= y < self.height:
            pygame.draw.circle(screen, color, (int(x), int(y)), int(size))


class UIManager(threading.Thread):
    def __init__(self, width: int = 1024, height: int = 768):
        super().__init__()
        self.width = width
        self.height = height
        self.running = True
        self.data_queue = queue.Queue()
        self.data_store: Dict[str, Any] = {}
        
        # UI state
        self.scroll_offset = 0
        self.max_lines = 10
        self.font_size = 16
        self.line_height = self.font_size
        
        # Console dimensions
        self.console_width = self.width // 2
        
        # Starfield
        self.stars: List[Star] = [Star(width, height) for _ in range(2800)]
        
        # Colors for different message types
        self.colors = {
            'INFO': (200, 200, 200),    # Light gray
            'DEBUG': (100, 200, 100),    # Light green
            'ERROR': (255, 100, 100),    # Light red
            'SYSTEM': (100, 100, 255),   # Light blue
            'default': (200, 200, 200)   # Default light gray
        }
        
    def update_data(self, key: str, value: Any, msg_type: str = 'INFO') -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.data_queue.put((timestamp, key, value, msg_type))
        
    def draw_starfield(self, screen):
        # Move and draw all stars
        for star in self.stars:
            star.move()
            star.draw(screen)

    def draw_console(self, screen, font):
        # Create a semi-transparent surface for the console
        console_surface = pygame.Surface((self.console_width, self.height), pygame.SRCALPHA)
        console_background = (40, 40, 50, 180)  # RGBA with alpha for transparency
        pygame.draw.rect(console_surface, console_background, (0, 0, self.console_width, self.height))
        
        # Draw console border
        border_color = (60, 60, 70, 255)  # Solid border
        pygame.draw.rect(console_surface, border_color, (0, 0, self.console_width, self.height), 2)
        
        # Draw title
        title = font.render("System Console", True, (150, 150, 150))
        console_surface.blit(title, (10, 5))
        
        # Draw console content
        y_pos = 40
        visible_items = list(self.data_store.items())[self.scroll_offset:]
        
        for i, (key, (value, msg_type)) in enumerate(visible_items):
            if i >= self.max_lines:
                break
                
            timestamp = key.split('_')[0]
            actual_key = '_'.join(key.split('_')[1:])
            text = f"{timestamp} | {actual_key}: {str(value)}"
            
            # Word wrap text
            words = text.split()
            line = ''
            for word in words:
                test_line = line + word + ' '
                if font.size(test_line)[0] < (self.console_width - 40):
                    line = test_line
                else:
                    color = self.colors.get(msg_type, self.colors['default'])
                    text_surface = font.render(line, True, color)
                    console_surface.blit(text_surface, (10, y_pos))
                    y_pos += self.line_height
                    line = word + ' '
            
            if line:
                color = self.colors.get(msg_type, self.colors['default'])
                text_surface = font.render(line, True, color)
                console_surface.blit(text_surface, (10, y_pos))
                y_pos += self.line_height
        
        # Draw scroll indicator
        if len(self.data_store) > self.max_lines:
            scroll_pct = self.scroll_offset / (len(self.data_store) - self.max_lines)
            indicator_height = (self.height * self.max_lines) / len(self.data_store)
            indicator_pos = scroll_pct * (self.height - indicator_height)
            pygame.draw.rect(console_surface, (100, 100, 100, 255),
                           (self.console_width - 15, indicator_pos, 5, indicator_height))
    
        # Blit the console surface onto the main screen
        screen.blit(console_surface, (0, 0))


    def run(self) -> None:
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("TARS-AI Monitor")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Courier New", self.font_size, bold=True)

        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll_offset = max(0, min(
                        len(self.data_store) - self.max_lines,
                        self.scroll_offset - event.y
                    ))
            
            # Process data updates
            while not self.data_queue.empty():
                try:
                    timestamp, key, value, msg_type = self.data_queue.get_nowait()
                    self.data_store[f"{timestamp}_{key}"] = (value, msg_type)

                    # Auto-scroll to the bottom when a new message arrives
                    self.scroll_offset = max(0, len(self.data_store) - self.max_lines)
                except queue.Empty:
                    break
                        
            # Clear screen with dark background
            screen.fill((0, 0, 20))
            
            # Draw starfield
            self.draw_starfield(screen)
            
            # Draw console overlay
            self.draw_console(screen, font)
            
            pygame.display.flip()
            clock.tick(60)  # Increased to 60 FPS for smoother animation
        
        pygame.quit()
    
    def stop(self) -> None:
        self.running = False