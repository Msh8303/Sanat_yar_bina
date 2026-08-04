# 👁️ Perception & Computer Vision Directory

## Overview
The `perception` directory is the sensory input layer of the cyber-physical system. It is strictly responsible for frame ingestion, preprocessing, and executing real-time object detection using YOLOv8. This module identifies steel surface defects, calculates bounding box geometries, and passes this data forward to instantiate `EventObject` payloads.

## Core Modules
To support both physical deployment and simulation, the perception logic is split between standard video processing and Webots integration:

* **`detector.py` & `selector.py` (Standard Pipeline):**
  * **`detector.py`:** The primary YOLOv8 inference script. It loads `best.pt`, processes incoming frames from a physical camera or local video file (e.g., `test_video.mp4`), and extracts bounding boxes, classes, and confidence scores.
  * **`selector.py`:** Handles Region of Interest (ROI) selection, frame filtering, and logic for determining which bounding boxes meet the threshold for further processing.

* **`detector_webots.py` & `selector_webots.py` (Simulation Pipeline):**
  * **`detector_webots.py`:** A specialized adaptation of the detection pipeline designed to ingest video frames directly from the Webots simulation environment (typically via TCP socket or shared memory) ensuring synchronized inference with the simulated conveyor belt.
  * **`selector_webots.py`:** Manages virtual camera selection and ROI logic specific to the Webots world coordinates and virtual sensor constraints.

## Integration
Once a defect is detected and validated by these scripts, the spatial and class data is immediately passed to the `controllers` (for fuzzy risk evaluation) and the `monitoring` module (for logging), acting as the trigger for the entire event lifecycle.