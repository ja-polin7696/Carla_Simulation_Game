# Weather Change -- Press- W
# Town change Press -- T
# Record Video of 5 Camera( BEV, Front, Rear, lef, Right)
# Traffic, Pedistrian, Vehicles Included
# Show speed, Driving status (Drive/Reverse)

import carla
import pygame
import sys
import numpy as np
import random
import os
import datetime
import cv2

# Initialize CARLA client
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)

available_towns = ['Town01', 'Town02', 'Town03', 'Town04', 'Town05']
town_index = 1  # Start from Town02

# Global actor handles
vehicle = None
av_vehicles = []
walkers = []
walker_controllers = []
cameras = []
camera_surfaces = [None] * 5
recordings = [None] * 5

# Create a directory for this recording session
session_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(f"recordings/{session_time}", exist_ok=True)

def reload_town():
    global world, blueprints, spawn_points, spawn_point
    global vehicle, av_vehicles, walkers, walker_controllers, cameras, recordings

    print("[Town Reload] Cleaning up actors...")

    for cam in cameras:
        if cam:
            cam.stop()
            cam.destroy()
    cameras.clear()

    for rec in recordings:
        if rec:
            rec.release()
    recordings = [None] * 5

    for c in walker_controllers:
        c.stop()
        c.destroy()
    walker_controllers.clear()

    for w in walkers:
        w.destroy()
    walkers.clear()

    for av in av_vehicles:
        av.destroy()
    av_vehicles.clear()

    if vehicle:
        vehicle.destroy()
        vehicle = None

    town_index = (reload_town.index + 1) % len(available_towns)
    reload_town.index = town_index
    print(f"[Town Reload] Loading {available_towns[town_index]}...")
    world = client.load_world(available_towns[town_index])

    blueprints = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()
    spawn_point = spawn_points[0] if spawn_points else carla.Transform()
    print("[Town Reload] Loaded successfully.")

reload_town.index = town_index
reload_town()

# Blueprint and spawn point setup
blueprints = world.get_blueprint_library()
vehicle_bp = blueprints.find('vehicle.tesla.model3')
spawn_point = spawn_points[0]

# Spawn Ego Vehicle
vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
vehicle.set_autopilot(False)

# Create RGB Cameras
def make_camera(transform, index, width, height):
    bp = blueprints.find('sensor.camera.rgb')
    bp.set_attribute('image_size_x', str(width))
    bp.set_attribute('image_size_y', str(height))
    bp.set_attribute('fov', '90')
    cam = world.spawn_actor(bp, transform, attach_to=vehicle)

    filename = f"recordings/{session_time}/camera_{index}.avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
    recordings[index] = out

    def callback(image):
        image.convert(carla.ColorConverter.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.uint8).reshape((image.height, image.width, 4))
        rgb_array = array[:, :, :3][:, :, ::-1]
        camera_surfaces[index] = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))
        out.write(rgb_array)

    cam.listen(callback)
    cameras.append(cam)
    return cam

make_camera(carla.Transform(carla.Location(x=1.5, z=1.5)), 0, 800, 600)  # Front
make_camera(carla.Transform(carla.Location(x=-2.5, z=1.5), carla.Rotation(yaw=180)), 1, 400, 300)  # Rear
make_camera(carla.Transform(carla.Location(y=-1.5, z=1.5), carla.Rotation(yaw=-90)), 2, 400, 300)  # Left
make_camera(carla.Transform(carla.Location(y=1.5, z=1.5), carla.Rotation(yaw=90)), 3, 400, 300)  # Right
make_camera(carla.Transform(carla.Location(z=50), carla.Rotation(pitch=-90)), 4, 400, 300)  # BEV

# Initialize Pygame
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No joystick detected.")
    pygame.quit()
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Detected joystick: {joystick.get_name()}")

screen = pygame.display.set_mode((1200, 900))
pygame.display.set_caption("CARLA Manual Drive")
font = pygame.font.SysFont(None, 36)
pygame.mouse.set_visible(False)

# Weather setup
weather_presets = [
    carla.WeatherParameters.ClearNoon,
    carla.WeatherParameters.CloudyNoon,
    carla.WeatherParameters.WetNoon,
    carla.WeatherParameters.MidRainyNoon,
    carla.WeatherParameters.SoftRainNoon,
    carla.WeatherParameters.ClearSunset
]
weather_index = 0

reverse_mode = False
clock = pygame.time.Clock()
running = True

# Spawn 30 AVs
vehicle_bps = blueprints.filter('vehicle.*')
random.shuffle(spawn_points)
for i in range(30):
    if i + 1 < len(spawn_points):
        bp = random.choice(vehicle_bps)
        av = world.try_spawn_actor(bp, spawn_points[i + 1])
        if av:
            av.set_autopilot(True)
            av_vehicles.append(av)
print(f"[INFO] Spawned {len(av_vehicles)} autonomous vehicles.")

# Spawn 10 pedestrians
walker_bps = blueprints.filter('walker.pedestrian.*')
walker_controller_bp = blueprints.find('controller.ai.walker')
walker_spawn_points = [carla.Transform(world.get_random_location_from_navigation()) for _ in range(10)]

for i in range(10):
    walker_bp = random.choice(walker_bps)
    walker = world.try_spawn_actor(walker_bp, walker_spawn_points[i])
    if walker:
        controller = world.try_spawn_actor(walker_controller_bp, carla.Transform(), attach_to=walker)
        if controller:
            controller.start()
            controller.go_to_location(world.get_random_location_from_navigation())
            controller.set_max_speed(1 + random.random())
            walkers.append(walker)
            walker_controllers.append(controller)

# Main control loop
def apply_deadzone(value, deadzone=0.1):
    return 0.0 if abs(value) < deadzone else value

try:
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q)):
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    weather_index = (weather_index + 1) % len(weather_presets)
                    world.set_weather(weather_presets[weather_index])
                    print(f"[Weather] Changed to preset index: {weather_index}")
                elif event.key == pygame.K_t:
                    reload_town()
            elif event.type == pygame.JOYBUTTONDOWN and event.button == 1:
                reverse_mode = not reverse_mode

        steer = apply_deadzone(joystick.get_axis(0))
        throttle = apply_deadzone((-joystick.get_axis(1) + 1) / 2.0)
        brake = apply_deadzone((-joystick.get_axis(2) + 1) / 2.0)
        handbrake = joystick.get_button(0)

        control = carla.VehicleControl()
        control.steer = steer
        control.throttle = throttle
        control.brake = brake
        control.hand_brake = handbrake
        control.reverse = reverse_mode
        vehicle.apply_control(control)

        screen.fill((0, 0, 0))
        if camera_surfaces[0]:
            screen.blit(camera_surfaces[0], (0, 0))  # Front
            velocity = vehicle.get_velocity()
            speed_kmh = 3.6 * (velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2) ** 0.5
            speed_text = font.render(f"Speed: {speed_kmh:.1f} km/h", True, (255, 255, 255))
            screen.blit(speed_text, (10, 40))

        if camera_surfaces[1]:
            screen.blit(camera_surfaces[1], (800, 0))  # Rear
        if camera_surfaces[2]:
            screen.blit(camera_surfaces[2], (800, 300))  # Left
        if camera_surfaces[3]:
            screen.blit(camera_surfaces[3], (800, 600))  # Right
        if camera_surfaces[4]:
            screen.blit(camera_surfaces[4], (0, 600))  # BEV

        overlay = font.render(f"Gear: {'REVERSE' if reverse_mode else 'DRIVE'}", True, (255, 255, 255))
        screen.blit(overlay, (10, 10))
        pygame.display.flip()

except KeyboardInterrupt:
    running = False

finally:
    for cam in cameras:
        cam.stop()
        cam.destroy()
    for rec in recordings:
        if rec:
            rec.release()
    if vehicle:
        vehicle.destroy()
    for av in av_vehicles:
        av.destroy()
    for c in walker_controllers:
        c.stop()
        c.destroy()
    for w in walkers:
        w.destroy()
    pygame.quit()
