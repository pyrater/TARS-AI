import pygame
import cv2
import numpy as np
import os


# Initialize pygame
pygame.init()

# Load the video using OpenCV
video_path = "tesserac_1024.mp4"  # Change this to your video file
if not os.path.exists(video_path):
    print(f"Error: File '{video_path}' not found in {os.getcwd()}")
else:
    print("File found! Attempting to open...")

cap = cv2.VideoCapture(video_path)

# Check if video opened successfully
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

# Get video properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Create pygame window
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Looping Video Background")

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    # Read frame
    ret, frame = cap.read()
    
    if not ret:
        print("Restarting video...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # Convert OpenCV BGR to RGB format
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to Pygame surface
    frame_surface = pygame.surfarray.make_surface(np.flipud(frame))  # Flip to match Pygame's coordinates
    
    # Scale to fit screen
    frame_surface = pygame.transform.scale(frame_surface, (width, height))

    # Display frame
    screen.blit(frame_surface, (0, 0))
    pygame.display.update()

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Control frame rate
    clock.tick(fps)

# Clean up
cap.release()
pygame.quit()
