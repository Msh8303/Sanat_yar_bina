# 🤖 Webots Communication Interface Directory

## Overview
The `webots` directory serves as the dedicated Inter-Process Communication (IPC) bridge between the main Python inspection application and the external Webots simulation environment. It abstracts the networking and data transfer layers, ensuring the core AI and control pipelines remain decoupled from the simulation engine's specific API.

## Core Modules
This directory handles the ingestion of simulated sensor data:

* **`receiver.py`:**
  * **Role:** Telemetry & Media Stream Receiver.
  * **Function:** Listens for incoming data transmitted by the `smart_conveyor` controller running inside Webots (e.g., over TCP Port 555). It is responsible for capturing the virtual camera's video frames and physical state telemetry (conveyor speed, position), decoding them, and formatting them for seamless ingestion into the `perception` (YOLO) and `controllers` (Fuzzy/RL) modules.
* **`__init__.py`:**
  * Initializes the folder as a standard Python package, allowing the receiver functions to be easily imported across the system.

## Design Philosophy
By isolating the Webots communication logic in this directory, the system achieves "Simulation-to-Reality" (Sim2Real) transparency. The main application does not need to know whether the frames are coming from a physical industrial camera or the `receiver.py` module; the data payload format remains identical.