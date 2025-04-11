import carla
import pygame
import sys
import numpy as np
import random
import os
import datetime
import cv2
import csv

# Ask for driver name
driver_name = input("Enter driver name: ")

# Initialize CARLA client
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)

available_towns = ['Town01', 'Town02', 'Town03', 'Town04', 'Town05']
town_index = 4 # Change according to your town need

vehicle = None
av_vehicles = []
walkers = []
walker_controllers = []
cameras = []
camera_surfaces = [None] * 5
recordings = [None] * 5
collision_sensor = None
running = True
reverse_mode = False

# Session path
session_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
session_path = f"recordings/{session_time}"
os.makedirs(session_path, exist_ok=True)

# Log files
log_file_path = os.path.join(session_path, "drive_log.csv")
log_file = open(log_file_path, mode='w', newline='')
log_writer = csv.writer(log_file)
log_writer.writerow(["Driver", "Timestamp", "Speed_kmh", "Throttle", "Brake"])

collision_log_path = os.path.join(session_path, "collision_log.csv")
collision_file = open(collision_log_path, mode='w', newline='')
collision_writer = csv.writer(collision_file)
collision_writer.writerow(["Driver", "Timestamp", "Other Actor", "Location X", "Location Y", "Location Z"])

def on_collision(event):
    global vehicle
    other_actor = event.other_actor
    location = vehicle.get_location()
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")
    collision_writer.writerow([driver_name, timestamp, other_actor.type_id, location.x, location.y, location.z])
    print(f"[COLLISION] with {other_actor.type_id} at ({location.x:.2f}, {location.y:.2f}, {location.z:.2f})")

weather_presets = [
    carla.WeatherParameters.ClearNoon,
    carla.WeatherParameters.CloudyNoon,
    carla.WeatherParameters.WetNoon,
    carla.WeatherParameters.MidRainyNoon,
    carla.WeatherParameters.SoftRainNoon,
    carla.WeatherParameters.ClearSunset
]
weather_index = 0

def reload_world(town_name):
    global world, vehicle, cameras, camera_surfaces, recordings, collision_sensor, blueprints, spawn_points

    world = client.load_world(town_name)
    blueprints = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()

    if vehicle:
        vehicle.destroy()
    if collision_sensor:
        collision_sensor.stop()
        collision_sensor.destroy()
    for cam in cameras:
        cam.stop()
        cam.destroy()
    cameras.clear()
    camera_surfaces[:] = [None] * 5
    recordings[:] = [None] * 5

    vehicle_bp = blueprints.find('vehicle.tesla.model3')
    spawn_point = spawn_points[0] if spawn_points else carla.Transform()
    vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
    if vehicle:
        vehicle.set_autopilot(False)
        col_sensor_bp = blueprints.find('sensor.other.collision')
        collision_sensor = world.spawn_actor(col_sensor_bp, carla.Transform(), attach_to=vehicle)
        collision_sensor.listen(on_collision)

        make_camera(carla.Transform(carla.Location(x=1.5, z=1.5)), 0, 800, 600)
        make_camera(carla.Transform(carla.Location(x=-2.5, z=1.5), carla.Rotation(yaw=180)), 1, 400, 300)
        make_camera(carla.Transform(carla.Location(y=-1.5, z=1.5), carla.Rotation(yaw=-90)), 2, 400, 300)
        make_camera(carla.Transform(carla.Location(y=1.5, z=1.5), carla.Rotation(yaw=90)), 3, 400, 300)
        make_camera(carla.Transform(carla.Location(z=50), carla.Rotation(pitch=-90)), 4, 400, 300)

def make_camera(transform, index, width, height):
    global cameras, camera_surfaces, recordings
    bp = blueprints.find('sensor.camera.rgb')
    bp.set_attribute('image_size_x', str(width))
    bp.set_attribute('image_size_y', str(height))
    bp.set_attribute('fov', '90')
    cam = world.spawn_actor(bp, transform, attach_to=vehicle)

    filename = f"{session_path}/camera_{index}.avi"
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

def spawn_av_and_pedestrians():
    global av_vehicles, walkers, walker_controllers

    av_vehicles.clear()
    walkers.clear()
    walker_controllers.clear()

    vehicle_bps = blueprints.filter('vehicle.*')
    pedestrian_bps = blueprints.filter('walker.pedestrian.*')

    available_spawn_points = spawn_points[1:]
    random.shuffle(available_spawn_points)
    for i in range(min(30, len(available_spawn_points))):
        bp = random.choice(vehicle_bps)
        spawn = available_spawn_points[i]
        av = world.try_spawn_actor(bp, spawn)
        if av:
            av.set_autopilot(True)
            av_vehicles.append(av)

    walker_spawn_points = []
    for _ in range(10):
        loc = world.get_random_location_from_navigation()
        if loc:
            walker_spawn_points.append(carla.Transform(loc))

    batch = []
    for spawn_point in walker_spawn_points:
        walker_bp = random.choice(pedestrian_bps)
        walker_bp.set_attribute('is_invincible', 'false')
        batch.append(carla.command.SpawnActor(walker_bp, spawn_point))

    results = client.apply_batch_sync(batch, True)
    walker_ids = [r.actor_id for r in results if not r.error]

    for walker_id in walker_ids:
        walker = world.get_actor(walker_id)
        if walker:
            walkers.append(walker)
            controller_bp = blueprints.find('controller.ai.walker')
            controller = world.try_spawn_actor(controller_bp, carla.Transform(), attach_to=walker)
            if controller:
                walker_controllers.append(controller)
                controller.start()
                controller.go_to_location(world.get_random_location_from_navigation())
                controller.set_max_speed(1 + random.random())

reload_world(available_towns[town_index])
spawn_av_and_pedestrians()

# Pygame setup
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

pygame.mixer.init()
horn_sound = pygame.mixer.Sound('horn.wav')

def apply_deadzone(value, deadzone=0.1):
    return 0.0 if abs(value) < deadzone else value

clock = pygame.time.Clock()

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
                    town_index = (town_index + 1) % len(available_towns)
                    print(f"[Town] Changing to {available_towns[town_index]}")
                    reload_world(available_towns[town_index])
                    spawn_av_and_pedestrians()
            elif event.type == pygame.JOYBUTTONDOWN and event.button == 1:
                reverse_mode = not reverse_mode
            elif event.type == pygame.JOYBUTTONDOWN and event.button == 2:
                print("[HORN] Honk!")
                horn_sound.play()

        steer = apply_deadzone(joystick.get_axis(0))
        throttle = apply_deadzone((-joystick.get_axis(1) + 1) / 2.0)
        brake = apply_deadzone((-joystick.get_axis(2) + 1) / 2.0)
        handbrake = joystick.get_button(0)

        control = carla.VehicleControl(
            steer=steer,
            throttle=throttle,
            brake=brake,
            hand_brake=handbrake,
            reverse=reverse_mode
        )
        vehicle.apply_control(control)

        velocity = vehicle.get_velocity()
        speed_kmh = 3.6 * (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
        log_writer.writerow([driver_name, datetime.datetime.now().strftime("%H:%M:%S.%f"), f"{speed_kmh:.2f}", f"{throttle:.2f}", f"{brake:.2f}"])

        screen.fill((0, 0, 0))
        if camera_surfaces[0]:
            screen.blit(camera_surfaces[0], (0, 0))
            screen.blit(font.render("Front Camera", True, (255, 255, 0)), (300, 10))
            screen.blit(font.render(f"Speed: {speed_kmh:.1f} km/h", True, (255, 255, 255)), (10, 40))
            screen.blit(font.render(f"Hi,Virtual Driver: {driver_name}", True, (0, 255, 0)), (10, 80))

        if camera_surfaces[1]:
            screen.blit(camera_surfaces[1], (800, 0))
            screen.blit(font.render("Rear Camera", True, (255, 255, 0)), (1000, 10))
        if camera_surfaces[2]:
            screen.blit(camera_surfaces[2], (800, 300))
            screen.blit(font.render("Left Camera", True, (255, 255, 0)), (1000, 310))
        if camera_surfaces[3]:
            screen.blit(camera_surfaces[3], (800, 600))
            screen.blit(font.render("Right Camera", True, (255, 255, 0)), (1000, 610))
        if camera_surfaces[4]:
            screen.blit(camera_surfaces[4], (0, 600))
            screen.blit(font.render("BEV Camera", True, (255, 255, 0)), (300, 610))

        overlay = font.render(f"Gear: {'REVERSE' if reverse_mode else 'DRIVE'}", True, (255, 255, 255))
        screen.blit(overlay, (10, 10))
        pygame.display.flip()

except KeyboardInterrupt:
    running = False

finally:
    print("[Shutdown] Cleaning up resources...")
    for cam in cameras:
        cam.stop()
        cam.destroy()
    for rec in recordings:
        if rec:
            rec.release()
    if collision_sensor:
        collision_sensor.stop()
        collision_sensor.destroy()
    log_file.close()
    collision_file.close()
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
