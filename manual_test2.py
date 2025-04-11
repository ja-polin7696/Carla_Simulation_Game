#Dynamic Weather --- Press W
#BEV
# Town Hall Change ---- Press T
import carla
import pygame
import sys
import numpy as np
import random

# -- Initialize CARLA client and world --
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)

available_towns = ['Town01', 'Town02', 'Town03', 'Town04', 'Town05']
town_index = 1  # Start with Town02

try:
    world = client.load_world(available_towns[town_index])
except Exception as e:
    print("Error connecting to CARLA:", e)
    sys.exit(1)

blueprints = world.get_blueprint_library()
vehicle_bp = blueprints.find('vehicle.tesla.model3')
if vehicle_bp is None:
    vehicle_bp = blueprints.filter('vehicle.*')[0]

# Function to reload town
def reload_town():
    global world, blueprints, spawn_points, spawn_point
    town_index = (reload_town.index + 1) % len(available_towns)
    reload_town.index = town_index
    print(f"[Town Reload] Loading {available_towns[town_index]}...")
    world = client.load_world(available_towns[town_index])
    blueprints = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()
    spawn_point = spawn_points[0] if spawn_points else carla.Transform()
    print("[Town Reload] Loaded successfully.")
reload_town.index = town_index

# Initial spawn points
spawn_points = world.get_map().get_spawn_points()
if not spawn_points:
    print("No spawn points available in the map!")
    sys.exit(1)
spawn_point = spawn_points[0]

# Spawn ego vehicle
vehicle = world.spawn_actor(vehicle_bp, spawn_point)
vehicle.set_autopilot(False)

# ---------- Setup Four RGB Cameras ----------
camera_surfaces = [None] * 5  # Added one for BEV

def make_camera(name, transform, index):
    bp = blueprints.find('sensor.camera.rgb')
    bp.set_attribute('image_size_x', '800')
    bp.set_attribute('image_size_y', '600')
    bp.set_attribute('fov', '90')
    cam = world.spawn_actor(bp, transform, attach_to=vehicle)

    def callback(image):
        image.convert(carla.ColorConverter.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((image.height, image.width, 4))
        rgb_array = array[:, :, :3][:, :, ::-1]
        camera_surfaces[index] = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))

    cam.listen(callback)
    return cam

camera_front = make_camera("Front", carla.Transform(carla.Location(x=1.5, z=1.5)), 0)
camera_rear = make_camera("Rear", carla.Transform(carla.Location(x=-2.5, z=1.5), carla.Rotation(yaw=180)), 1)
camera_left = make_camera("Left", carla.Transform(carla.Location(y=-1.5, z=1.5), carla.Rotation(yaw=-90)), 2)
camera_right = make_camera("Right", carla.Transform(carla.Location(y=1.5, z=1.5), carla.Rotation(yaw=90)), 3)
# Bird’s Eye View (top-down)
camera_bev = make_camera("BEV", carla.Transform(carla.Location(z=50), carla.Rotation(pitch=-90)), 4)

cameras = [camera_front, camera_rear, camera_left, camera_right, camera_bev]

# ---------- Initialize Pygame ----------
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No joystick detected.")
    vehicle.destroy()
    for cam in cameras:
        cam.destroy()
    pygame.quit()
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Detected joystick: {joystick.get_name()}")

display_width, display_height = 800, 600
window = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption("CARLA Manual Drive (Logitech G920)")
font = pygame.font.SysFont(None, 36)
pygame.mouse.set_visible(False)

reverse_mode = False
clock = pygame.time.Clock()
running = True

# Dynamic Weather Settings
weather_presets = [
    carla.WeatherParameters.ClearNoon,
    carla.WeatherParameters.CloudyNoon,
    carla.WeatherParameters.WetNoon,
    carla.WeatherParameters.MidRainyNoon,
    carla.WeatherParameters.SoftRainNoon,
    carla.WeatherParameters.ClearSunset
]
weather_index = 0

def apply_deadzone(value, deadzone=0.1):
    return 0.0 if abs(value) < deadzone else value

# ---------- Spawn 30 Autonomous Vehicles ----------
vehicle_bps = blueprints.filter('vehicle.*')
spawn_points_av = spawn_points[1:]
random.shuffle(spawn_points_av)

av_vehicles = []
for i in range(30):
    if i < len(spawn_points_av):
        av_bp = random.choice(vehicle_bps)
        av = world.try_spawn_actor(av_bp, spawn_points_av[i])
        if av:
            av.set_autopilot(True)
            av_vehicles.append(av)
print(f"[INFO] Spawned {len(av_vehicles)} autonomous vehicles.")

# ---------- Spawn 10 Pedestrians ----------
walker_bps = blueprints.filter('walker.pedestrian.*')
walker_controller_bp = blueprints.find('controller.ai.walker')
walker_spawn_points = []

for _ in range(10):
    loc = world.get_random_location_from_navigation()
    if loc:
        walker_spawn_points.append(carla.Transform(loc))

walkers = []
walker_controllers = []
for i in range(min(10, len(walker_spawn_points))):
    walker_bp = random.choice(walker_bps)
    walker = world.try_spawn_actor(walker_bp, walker_spawn_points[i])
    controller = world.try_spawn_actor(walker_controller_bp, walker_spawn_points[i])
    if walker and controller:
        controller.start()
        controller.go_to_location(world.get_random_location_from_navigation())
        controller.set_max_speed(1 + random.random())
        walkers.append(walker)
        walker_controllers.append(controller)
print(f"[INFO] Spawned {len(walkers)} pedestrians.")

# --------------------- Main Control Loop ---------------------
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
                print(f"[Gear Toggle] {'REVERSE' if reverse_mode else 'DRIVE'}")

        steer = apply_deadzone(joystick.get_axis(0))
        throttle = apply_deadzone((-joystick.get_axis(1) + 1) / 2.0)
        brake = apply_deadzone((-joystick.get_axis(2) + 1) / 2.0)
        handbrake = bool(joystick.get_button(0))

        control = carla.VehicleControl()
        control.steer = steer
        control.throttle = throttle
        control.brake = brake
        control.hand_brake = handbrake
        control.reverse = reverse_mode
        vehicle.apply_control(control)

        gear_text = "REVERSE" if reverse_mode else "DRIVE"
        print(f"Steering={steer:.2f}, Throttle={throttle:.2f}, Brake={brake:.2f}, Gear={gear_text}")

        window.fill((0, 0, 0))
        if camera_surfaces[4]:
            window.blit(camera_surfaces[4], (0, 0))  # Bird's Eye View
        overlay = font.render(f"Gear: {gear_text}", True, (255, 255, 255))
        window.blit(overlay, (10, 10))
        pygame.display.flip()

except KeyboardInterrupt:
    running = False

finally:
    print("Shutting down...")
    for cam in cameras:
        if cam:
            cam.stop()
            cam.destroy()
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
