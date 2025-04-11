import carla
import pygame
import sys
import numpy as np

# -- Initialize CARLA client and world --
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)  # seconds
try:
    world = client.load_world('Town03')  # Load Town03 map
except Exception as e:
    print("Error connecting to CARLA. Make sure the simulator is running.")
    sys.exit(1)

# Get the blueprint library and spawn a Tesla Model 3
blueprints = world.get_blueprint_library()
vehicle_bp = blueprints.find('vehicle.tesla.model3')
if vehicle_bp is None:
    # Fallback: if Tesla blueprint not found, use any vehicle as backup
    vehicle_bp = blueprints.filter('vehicle.*')[0]

# Choose a spawn point (here we take the first available spawn point)
spawn_points = world.get_map().get_spawn_points()
if not spawn_points:
    print("No spawn points available in the map!")
    sys.exit(1)
spawn_point = spawn_points[0]

# Spawn the vehicle actor
vehicle = world.spawn_actor(vehicle_bp, spawn_point)
vehicle.set_autopilot(False)  # ensure vehicle is under manual control

# -- Set up the camera sensor --
camera_bp = blueprints.find('sensor.camera.rgb')
# Configure camera resolution and field of view
camera_bp.set_attribute('image_size_x', '800')
camera_bp.set_attribute('image_size_y', '600')
camera_bp.set_attribute('fov', '90')
# Position the camera in front of the vehicle (attach to the vehicle)
camera_transform = carla.Transform(carla.Location(x=1.5, z=1.5))
camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

# Prepare a variable to hold the latest camera image as a Pygame surface
camera_surface = None

# Define a callback to convert CARLA images to Pygame surfaces
def process_camera_image(image):
    """Convert the raw CARLA image to a Pygame surface."""
    global camera_surface
    # Convert the image to raw format (BGRA byte array)
    image.convert(carla.ColorConverter.Raw)
    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    # Reshape array to 2D array with BGRA channels
    array = array.reshape((image.height, image.width, 4))
    # Convert BGRA to RGB
    rgb_array = array[:, :, :3][:, :, ::-1]  # flip BGR to RGB
    # Create a Pygame surface from the numpy array (swap axes for correct orientation)
    camera_surface = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))

# Start the camera sensor listening in asynchronous mode
camera.listen(lambda image: process_camera_image(image))

# -- Initialize Pygame and Joystick --
pygame.init()
pygame.joystick.init()

# Check for joystick (wheel) presence
if pygame.joystick.get_count() == 0:
    print("No joystick detected. Please connect the Logitech G920 and try again.")
    vehicle.destroy()
    camera.destroy()
    pygame.quit()
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Detected joystick: {joystick.get_name()}")

# Set up Pygame display and font for the HUD overlay
display_width, display_height = 800, 600
window = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption("CARLA Manual Drive (Logitech G920)")
font = pygame.font.SysFont(None, 36)  # default font, size 36

# Hide mouse cursor on the display window
pygame.mouse.set_visible(False)

# -- Control state variables --
reverse_mode = False   # False = DRIVE (forward), True = REVERSE (backwards)

# Clock to manage loop frequency
clock = pygame.time.Clock()
running = True

# Deadzone for throttle, brake, and steering
def apply_deadzone(value, deadzone=0.1):
    if abs(value) < deadzone:
        return 0.0
    return value

try:
    while running:
        # Limit loop to ~60 frames per second
        clock.tick(60)

        # Process Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                # Toggle reverse gear when Button B (index 1) is pressed
                if event.button == 1:  # B button
                    reverse_mode = not reverse_mode
                    gear_state = "REVERSE" if reverse_mode else "DRIVE"
                    print(f"[Gear Toggle] Gear changed to: {gear_state}")
                # (Handbrake is handled continuously via button state, no toggle needed)

        # Read current state of joystick axes for steering, throttle, brake
        steer_axis = joystick.get_axis(0)   # Steering wheel
        throttle_axis = joystick.get_axis(1)  # Throttle (gas pedal)
        brake_axis = joystick.get_axis(2)     # Brake pedal

        # Normalize throttle and brake from [-1,1] to [0,1]
        throttle = apply_deadzone((-throttle_axis + 1) / 2.0)
        brake = apply_deadzone((-brake_axis + 1) / 2.0)

        # Steering value can be used directly (assuming axis gives -1 for left, 1 for right)
        steer = apply_deadzone(steer_axis)

        # Read handbrake button (A button index 0)
        handbrake_pressed = bool(joystick.get_button(0))

        # Create a VehicleControl with the computed values
        control = carla.VehicleControl()
        control.steer = steer
        control.throttle = throttle
        control.brake = brake
        control.hand_brake = handbrake_pressed
        control.reverse = reverse_mode

        # Apply the control to the vehicle
        vehicle.apply_control(control)

        # Print debug information for this tick
        gear_text = "REVERSE" if reverse_mode else "DRIVE"
        print(f"Steering={steer:.2f}, Throttle={throttle:.2f}, Brake={brake:.2f}, Gear={gear_text}")

        # -- Rendering the camera feed and overlay --
        window.fill((0, 0, 0))
        if camera_surface:
            window.blit(camera_surface, (0, 0))
        overlay_text = font.render(f"Gear: {gear_text}", True, (255, 255, 255))
        window.blit(overlay_text, (10, 10))
        pygame.display.flip()

except KeyboardInterrupt:
    # Allow graceful exit with Ctrl+C in terminal
    running = False

finally:
    # Cleanup: destroy actors and quit Pygame
    print("Shutting down...")
    if camera is not None:
        camera.stop()        # stop camera sensor
    if camera is not None:
        camera.destroy()
    if vehicle is not None:
        vehicle.destroy()
    pygame.quit()
