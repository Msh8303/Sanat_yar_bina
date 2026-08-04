# ⚙️ Configuration Directory

## Overview
The `config` directory is the core parameter management hub of the system. To avoid hard-coding variables within the executable scripts, all hyperparameters, directory paths, and decision-making thresholds are centralized here.

## Contents
This directory contains the main configuration script:
* **`config.py`**: The comprehensive project configuration file.

**Key parameters managed within this file include:**
1. **Vision Settings:** Paths to the YOLO weight files (e.g., `best.pt`), and minimum confidence thresholds for frame archiving.
2. **Control Settings:** Fuzzy logic risk thresholds, Reinforcement Learning (RL) hyperparameters, and communication ports for Webots (e.g., TCP Port 555).
3. **Edge SLM Settings:** Text generation parameters for the Qwen language model (e.g., `Temperature`, `Top-K`, `Top-P`, and `Repetition Penalty`) to control hallucination.
4. **Database & IO Settings:** Paths and configurations for the SQLite database (WAL mode) and JSONL log directories.

## Usage
To modify system behavior (such as making the language model stricter or adjusting the base conveyor speed), simply edit the respective values within `config.py`. There is no need to modify the core application source code.