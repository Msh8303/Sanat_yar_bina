# 🏭 Webots Simulation Environment (Digital Twin)

## Overview
The `simulation` directory contains the complete Webots environment for the cyber-physical steel inspection system. This acts as a **Digital Twin** of the factory floor, allowing for safe, isolated testing of the YOLOv8 vision pipeline, the Fuzzy-RL hybrid controller, and the SQLite logging mechanisms without the need for physical hardware deployment.

## Directory Structure & Core Components

This directory strictly follows the standard Webots project architecture, compartmentalized into worlds, controllers, and plugins:

### 1. `worlds/` (Simulation Arenas)
This folder contains the 3D environment files defining the physics, lighting, virtual cameras, and mechanical constraints of the factory setup.
* **`steel_factory.wbt` & `foolad.wbt`:** The primary Webots world files containing the modeled conveyor belt system, lighting arrays, and the moving steel plates.
* **`.wbproj` files:** Project configuration files storing GUI layouts and scene tree states for Webots.
* **`protos/`:** Custom procedural nodes (assets) specific to the steel factory environment.

### 2. `controllers/smart_conveyor/` (The Cyber-Physical Bridge)
This is the active "brain" of the simulation, linking the 3D world to your Python AI engine.
* **`smart_conveyor.py`:** The main Webots robot controller. It captures frames from the virtual camera, executes the vision/control logic, and applies calculated velocities directly to the simulated conveyor motors. (Note: `smart_conveyor1.py` and `smart_conveyor111.py` act as backups or alternative configuration states).
* **AI Weights (`best.pt` & `hybrid_rl_model.pkl`):** Local copies of the YOLO and Reinforcement Learning weights, allowing the simulation controller to run inference immediately within the Webots environment.
* **`validation_images/`:** A repository of test frames and textures used to validate the virtual camera's capture quality and bounding box alignments.

### 3. `plugins/` & `libraries/`
* **`plugins/physics/` & `remote_controls/`:** Contains custom C/C++ or Python plugins to modify Webots' base physics engine (e.g., specific friction coefficients for steel on rollers) or handle external remote control APIs.
* **`robot_windows/`:** HTML/JS files for custom Webots graphical interfaces tailored to monitor the `smart_conveyor` in real-time.

## Execution Notes
To run the simulation:
1. Open `worlds/steel_factory.wbt` (or `foolad.wbt`) using the Webots application.
2. Ensure that Webots is configured to use the correct external Python environment (the one containing PyTorch, OpenCV, and your project dependencies) to successfully execute `smart_conveyor.py`.
3. The controller will automatically initialize the local `best.pt` and RL weights to begin autonomous inspection and motor control within the virtual factory.