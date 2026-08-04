# 📁 Assets Directory

## Overview
This directory serves as the central repository for all static files, graphical resources, and the visual identity of the system. The files located here are utilized across the Graphical User Interface (GUI), automated visual reports (such as PowerPoint exports), and system executable icons.

## Contents
Based on the current structure, this directory includes:
* **`logo.png` & `logo_png.png`**: The primary graphic logos used for report slides and GUI headers.
* **`logo.ico`**: The application's executable icon, displayed on the taskbar and main application window.

## Maintenance Notes
* If you need to update the system's theme or logo, replace the existing files using the exact same filenames to avoid updating directory paths in the main `config.py` file.
* To maintain optimal GUI performance, ensure all graphic files in this directory remain compressed and size-optimized.