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

<img src="https://i.ytimg.com/vi/u2TxYhv3UKE/maxresdefault.jpg" alt="Simulation Output" width="500"/>


---

## 🧰 Requirements
```bash
CARLA Simulator (0.9.13+)
Python 3.7+
```
Install dependencies:
```bash
pip install pygame numpy opencv-python
```
### Note: Ensure your joystick is plugged in before launching the script.

## 🚀 Getting Started

### 1. Start CARLA Simulator

```bash
./CarlaUE4.sh
```

or on Windows:
```bash
CarlaUE4.exe
```

### 2. Run the simulation:
```bash
python carla_joystick_drive.py
```

# Check outputs:
recordings/drive_output.mp4 – BEV camera footage
recordings/collision_log.csv – Collision events

## 🧠 How It Works

- 🚗 Spawns a **Tesla Model 3** as the ego vehicle
- 📷 Attaches **5 RGB cameras**, including a **Bird's Eye View (BEV)** camera
- 🚙 Spawns **30 autonomous vehicles** with autopilot enabled
- 🧍 Spawns **10 AI-controlled pedestrians**
- 💥 Listens for **collision events** and logs them to a `.csv` file
- 🎮 Provides real-time **joystick control** for throttle, steering, gear shift, and braking
- 🖥️ Displays **speed, gear status, and BEV footage** live on a Pygame window
- 🧹 On shutdown, the script **cleans up all actors** and **saves logs + video**

---

## 📌 Notes

- 🎮 Joystick mapping may vary by OS. This script is tested with **Logitech G920** on **Windows 10**.
- 🛑 If no joystick is detected, the script **exits gracefully** with a message.
- 🧪 For advanced research (e.g., integrating **YOLO**, **LiDAR**, or **V2V communication**), feel free
