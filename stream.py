# This code is running but giving blur video
import carla
import math
import random
import time
import numpy as np
import cv2
import subprocess

# Carla setup
client = carla.Client("localhost", 2000)
client.set_timeout(5.0)
world = client.get_world()
# Get the blueprint library
bp_lib =world.get_blueprint_library()

# Get the map's spawn points
spawn_points=world.get_map().get_spawn_points()

vehicle_bp=bp_lib.find('vehicle.lincoln.mkz_2020')
vehicle = world.try_spawn_actor(vehicle_bp, random.choice(spawn_points))

vehicle_pos =vehicle.get_transform()
print(vehicle_pos)

# Set the spectator with an empty transform
spectator=world.get_spectator()
transform=carla.Transform(vehicle.get_transform().transform(carla.Location(x=-4,z=2.5)),vehicle.get_transform().rotation)
spectator.set_transform(transform)

for v in world.get_actors().filter('*vehicle*'):
    v.set_autopilot(True)
    

# We create the camera through a blueprint that defines its properties
camera_bp=bp_lib.find('sensor.camera.rgb')
IM_WIDTH = 640
IM_HEIGHT = 480
camera_bp.set_attribute('image_size_x', str(IM_WIDTH))
camera_bp.set_attribute('image_size_y', str(IM_HEIGHT))

# Create a transform to place the camera on top of the vehicle
camera_init_trans=carla.Transform(carla.Location(z=1.6, x=0.4))

def camera_callback(image):
    image_array = np.array(image.raw_data)
    image_array = image_array.reshape((image.height, image.width, 4))
    image_array = image_array[:, :, :3]

    return image_array

# FFmpeg setup
ffmpeg_cmd = [
    "ffmpeg",
    "-y",
    "-f", "rawvideo",
    "-pixel_format", "rgb24",  
    "-video_size", "640x480",
    "-framerate", "30",
    "-i", "-",
    "-c:v", "libx264",
    "-preset", "fast",
    "-pix_fmt", "yuv420p",
    "-f", "rtsp",
    "rtsp://192.168.16.200:8554/mystream"   #Server IP address
]

ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

# Add camera sensor to Carla
camera = world.spawn_actor(camera_bp, camera_init_trans, attach_to=vehicle)
# camera.listen(camera_callback)
camera.listen(lambda image: ffmpeg_process.stdin.write(camera_callback(image).tobytes()))


try:
    # Simulation loop
    while True:
        # Advance the simulation time or perform control actions
        world.tick()

except KeyboardInterrupt:
    print("User interrupted the simulation.")
finally:
    # Clean up
    camera.stop()
    camera.destroy()
    ffmpeg_process.stdin.close()
    ffmpeg_process.wait()

# FFmpeg setup
# ffmpeg_cmd = [
#     "ffmpeg",
#     "-y",
#     "-f", "rawvideo",
#     "-pixel_format", "bgr24",
#     "-video_size", "640x480",
#     "-framerate", "15",
#     "-i", "-",
#     "-c:v", "libx264",
#     "-preset", "slow",
#     "-pix_fmt", "yuv420p",
#     "-f", "rtsp",
#     "rtsp://localhost:8554/mystream"
# ]

# ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

# # Camera sensor callback
# def camera_callback(image):
#     image_array = np.array(image.raw_data)
#     image_array = image_array.reshape((image.height, image.width, 4))
#     image_array = image_array[:, :, :3]
#     ffmpeg_process.stdin.write(image_array.tobytes())

# # Add camera sensor to Carla
# camera = world.spawn_actor(camera_bp, camera_init_trans, attach_to=vehicle)
# camera.listen(camera_callback)

# try:
#     # Simulation loop
#     while True:
#         # Advance the simulation time or perform control actions
#         world.tick()

# except KeyboardInterrupt:
#     print("User interrupted the simulation.")
# finally:
#     # Clean up
#     camera.stop()
#     camera.destroy()
#     ffmpeg_process.stdin.close()
#     ffmpeg_process.wait()