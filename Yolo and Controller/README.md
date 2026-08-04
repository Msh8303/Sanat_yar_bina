# 🔬 R&D: YOLO Training & Controller Experiments

## Overview
The `Yolo and Controller` directory serves as the Research and Development (R&D) archive for the cyber-physical inspection system. Unlike the deployment-focused directories, this folder houses the comprehensive training results, ablation studies, and comparative evaluations between different artificial intelligence architectures. 

It contains the evolutionary history of the models, documenting how the final production weights were achieved through various reinforcement learning algorithms and computer vision backbones.

## Directory Structure & Contents

### 1. `colab notebook/` (Training Environments)
This directory houses the cloud-based experiment configurations and Jupyter/Python scripts. It provides a fully reproducible environment for executing the heavy computational training tasks and hyperparameter tuning required for the YOLO and RL models.

### 2. Controller Ablation Studies (`Fuzzy-ppo/` & `Fuzzy-Qlearning/`)
These folders contain comparative studies evaluating two different Reinforcement Learning approaches (PPO vs. Q-Learning) paired with the Fuzzy logic controller. 
* Both algorithms were tested against multiple vision backbones to find the optimal synergy:
  * `for yolo8n` (Nano)
  * `for yolo8gse`
  * `for yolov8improvement` (Custom enhanced architecture)
  * `for yolo11m` (Medium)
* **`ppo-continue on yolo8n-Improvement/`:** Contains extended fine-tuning results and convergence graphs (e.g., `ppo_performance_plot.png`) for the most promising PPO configuration.

### 3. `Result of training yolo/` (Vision Metrics)
This folder is the repository for the pure computer vision training metrics. It includes the validation curves, confusion matrices, and loss graphs for all tested YOLO architectures (`Yolo8n`, `Yolo8-gse`, `Yolo8-Improvement`, and `Yolo11m`), justifying the final backbone selection.

### 4. `Result of training model soup/` (Ensemble Techniques)
This directory contains the results of advanced weight-averaging techniques (Model Soups) to increase detection robustness without adding inference latency.
* **`YOLO_expert_0` to `5`:** The individual fine-tuned expert models.
* **`model_soup_final.pt`:** The finalized, combined weight file resulting from the ensemble process.
* **`simulatedvideo/` & `smart_conveyor_simulation.mp4`:** Visual proofs and simulation exports demonstrating the model's real-time performance.
* **`speed_analysis_fuzzy.png`:** Analytical plots verifying the smoothing effect of the Fuzzy controller on the conveyor's mechanical speed.

### 5. `main model and controller/`
The staging area where the most successful, fully converged models (both Vision and RL) from the above experiments are extracted and packaged before being transferred to the edge deployment repository (the main system `models/` directory).

## Usage Notes
* **Reproducibility:** To replicate any of the results found in the subfolders, refer to the corresponding notebooks in the `colab notebook/` directory.