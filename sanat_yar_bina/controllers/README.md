# 🧠 Controllers Directory (Cyber-Physical Engine)

## Overview
This directory houses the "Decision Engine" of your cyber-physical system. The modules here are responsible for ingesting structured data from the vision module (YOLO) and utilizing hybrid artificial intelligence to generate optimal mechanical commands (e.g., adjusting conveyor belt speed). 

This process is executed entirely at the Edge to ensure real-time responsiveness and actively prevent physical motor oscillations.

## Modules & Contents
The Python scripts developed in this directory include:

* **`fuzzy.py` (Mamdani Fuzzy Logic):**
  * **Role:** Receives bounding box geometries and defect density data, applying Mamdani fuzzy rules to calculate a robust "Severity Score".
  * **Function:** Smooths the inherent uncertainties of neural network predictions, providing a reliable, continuous risk metric for mechanical control.

* **`rl.py` (Reinforcement Learning):**
  * **Role:** Takes the fuzzy risk score as environmental state input and makes the final hardware control decision.
  * **Function:** The intelligent agent analyzes the current conveyor state and determines the optimal policy—whether to accelerate, decelerate, or maintain motor speed—preventing destructive mechanical oscillations (chattering).

## Dependencies & Communication
These modules transmit their operational outputs directly to the physical hardware or simulation environment (Webots) via TCP sockets (Port 555), while simultaneously logging all telemetry and control decisions to the central SQLite database for SLM analysis.