# Carla_Simulation_Game

# CARLA Joystick-Controlled Simulation with Sensor and Collision Logging
This project is a Python-based CARLA simulation that integrates joystick control (e.g., Logitech G920), multi-camera visualization (including Bird's Eye View), autonomous vehicle and pedestrian spawning, real-time collision detection, dynamic weather changes, and video/data logging

# 🚘 CARLA Joystick-Controlled Simulation

> Full-featured manual driving simulation in [CARLA](https://carla.org/) with joystick support, 5 RGB cameras, dynamic weather, multi-town support, and collision logging.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![CARLA](https://img.shields.io/badge/CARLA-0.9.13%2B-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📦 Features

- ✅ Manual joystick control (Logitech G920/G29)
- 📷 Front / Rear / Left / Right / BEV RGB camera setup
- 🎥 BEV camera recording to `.mp4`
- 💥 Collision detection and logging to `.csv`
- 🌦️ Dynamic weather cycling
- 🧍 Spawns 30 autonomous vehicles + 10 pedestrians
- 🗺️ Live map switching (Town01–Town05)
- 🛞 Real-time gear, speed, and input feedback on-screen

---

## 🖥️ Demo

<img src="[https://user-images.githubusercontent.com/your-demo-gif.gif](https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.linkedin.com%2Fproducts%2Fcarla-simulator%2F&psig=AOvVaw0ajSySe3_A-4UN2ZlpQ0Ag&ust=1744419053042000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCNDhtcLhzowDFQAAAAAdAAAAABAE)" width="400" />

---

## 🧰 Requirements



## 🚀 Getting Started

### 🟢 Start CARLA Simulator

```bash
./CarlaUE4.sh

or on Windows:
```bash
CarlaUE4.exe



# Check outputs:
recordings/drive_output.mp4 – BEV camera footage
recordings/collision_log.csv – Collision events

