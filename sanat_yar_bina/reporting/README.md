# 📝 Reporting & Edge SLM Directory

## Overview
The `reporting` directory houses the automated natural language generation (NLG) pipeline of the inspection system. Instead of relying on cloud APIs, this module utilizes locally deployed, quantized Small Language Models (SLMs)—specifically Qwen3-4B—to analyze raw telemetry and generate structured, human-readable shift reports directly at the edge.

## Core Modules
The natural language pipeline is broken down into three primary scripts:

* **`prompt_builder.py`:**
  * **Role:** Context Engineering and Data Aggregation.
  * **Function:** Queries the SQLite database to extract key metrics (e.g., total defects, highest severity events, average conveyor speed). It formats this raw data into highly structured, strict system and user prompts designed to ground the SLM and prevent hallucinations.
* **`slm_engine.py`:**
  * **Role:** AI Inference Engine.
  * **Function:** Serves as the wrapper for loading and running quantized model weights (GGUF format via `llama.cpp` bindings). It handles hardware acceleration, token generation limits, and parameter constraints (Temperature, Top-P) defined in the main configuration.
* **`report_generator.py`:**
  * **Role:** Pipeline Orchestrator.
  * **Function:** Acts as the bridge between the database, the prompt builder, and the SLM engine. It triggers the reporting cycle (e.g., at the end of a shift or upon a critical failure), captures the SLM's text output, and saves the final documents into the `data/json_reports/` and `data/slm_report/` directories.