# 🏭 Sanat Yar Bina (SIB) 
**Edge-Deployed Cyber-Physical Steel Inspection System**

## 📖 Overview
**Sanat Yar Bina (SIB)** is an advanced industrial cyber-physical system designed for real-time steel surface defect detection, hardware orchestration, and automated natural language reporting. Engineered specifically for **serverless edge environments**, the system integrates a multi-threaded architecture to ensure zero-latency computer vision, continuous mechanical control, and immutable database logging.

The system features a **Digital Twin** integration via Webots, allowing seamless transitions between simulated factory environments and physical production lines.

## ✨ Core Architecture & Features
* **👁️ Real-Time Perception:** YOLOv8-based vision pipeline for microsecond defect detection.
* **🧠 Hybrid Cyber-Physical Control:** A combined Mamdani Fuzzy Logic and Reinforcement Learning (RL) controller to dynamically adjust conveyor belt speeds and prevent motor chattering.
* **📝 Edge SLM Reporting:** Autonomous shift reporting using locally deployed, quantized Small Language Models (Qwen3-4B).
* **🗄️ Concurrent Storage:** SQLite backend utilizing Write-Ahead Logging (WAL) to ensure AI inference and database I/O run asynchronously without blocking threads.
* **🖥️ Asynchronous GUI:** A highly responsive PyQt5 dashboard featuring real-time telemetry, visual monitoring, and strict operator authentication.

---

## 📂 Repository Structure
Click on any directory below to navigate to its specific `README.md` and read detailed documentation about its underlying modules:

* 📁 **[`assets/`](./assets/)** — Static files, GUI graphics, application icons, and visual branding.
* ⚙️ **[`config/`](./config/)** — Global parameters, AI confidence thresholds, and system paths (`config.py`).
* 🧠 **[`controllers/`](./controllers/)** — The decision engine containing the `fuzzy.py` and `rl.py` modules for hardware orchestration.
* 🗄️ **[`data/`](./data/)** — Local infrastructure backend housing the SQLite WAL database, JSONL logs, generated reports, and critical anomaly screenshots.
* 🤖 **[`models/`](./models/)** — Storage for all quantized AI weights (`.pt`, `.pkl`, `.gguf`) for Vision, Control, and SLM execution.
* 📊 **[`monitoring/`](./monitoring/)** — Event lifecycle managers, database I/O handlers, and the Selective Screenshot Manager.
* 👁️ **[`perception/`](./perception/)** — Computer vision pipeline handling standard and simulation-based frame ingestion, ROI selection, and YOLOv8 inference.
* 📝 **[`reporting/`](./reporting/)** — The Natural Language Generation (NLG) pipeline orchestrating the Qwen SLM and prompt engineering.
* 🏭 **[`simulation/`](./simulation/)** — The Webots Digital Twin environment, containing 3D worlds and simulated hardware controllers.
* 🖥️ **[`ui/`](./ui/)** — Modular PyQt5 front-end components, including dashboards, real-time widgets, and authentication dialogs.
* 🔌 **[`webots/`](./webots/)** — The ZeroMQ/TCP communication bridge linking the Python core to the external simulation engine.

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.10+ installed. Since this is an edge-optimized AI system, a CUDA-compatible GPU is highly recommended for real-time inference.

### 2. Installation
Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/your-username/sanat_yar_bina.git](https://github.com/your-username/sanat_yar_bina.git)
cd sanat_yar_bina
pip install -r requirements.txt

### 3. Model Weights
Ensure that all required model weights (`best.pt`, `hybrid_rl.pkl`, and Qwen `.gguf` files) are placed inside the `models/` directory before execution.

### 4. Execution
Run the main orchestrator script to launch the application:

```bash
python main.py

## ⚙️ Application Lifecycle (`main.py`)
The `main.py` script acts as the central hub of the system. It orchestrates three primary `QThread` classes to guarantee non-blocking operations:

* **`VisionControlThread`:** Manages video/Webots frame ingestion, YOLO inference, Fuzzy-RL control computation, and ZeroMQ (Port 5556) motor command broadcasting.
* **`DataAggregatorThread`:** Silently aggregates telemetry data in the background based on defined time intervals.
* **`BatchSLMThread`:** Safely triggers the resource-intensive SLM reporting pipeline only when the mechanical systems undergo a "Smooth Stop."