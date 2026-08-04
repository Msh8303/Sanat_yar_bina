# 📊 Monitoring & Logging Directory

## Overview
The `monitoring` directory is responsible for the end-to-end event lifecycle, data aggregation, and persistent logging. It bridges the gap between raw inference data and structured, immutable storage, ensuring that every critical event in the cyber-physical system is recorded reliably without bottlenecking the main execution threads.

## Core Modules
This directory contains the following scripts:

* **`event_model.py`:**
  * Defines the core `EventObject` data structure. It acts as the standard payload containing bounding box coordinates, defect classes, model confidence, and timestamps, which is passed between the vision, control, and logging modules.
* **`database.py`:**
  * Manages the connection and execution of queries for the SQLite database. It is optimized to support the Write-Ahead Logging (WAL) mode, ensuring concurrent read/write operations (e.g., YOLO writing telemetry while the SLM reads data for reporting) without database locks.
* **`logger.py`:**
  * Handles the generation of raw telemetry and flat-file logging. It formats incoming event data and writes it safely to `CSV` and `JSONL` files for redundancy and easy external parsing.
* **`screenshot.py`:**
  * The Selective Screenshot Manager. Utilizing OpenCV (`cv2.imwrite`), it captures and archives zero-latency frame dumps of critical anomalies. It applies OR-logic conditions (e.g., Confidence > 0.9 OR Severity > 0.8) to prevent storage saturation while retaining vital visual evidence.