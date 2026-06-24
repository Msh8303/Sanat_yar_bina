import os
from pathlib import Path

# گرفتن مسیر اصلی پروژه (پوشه sanat_yar_bina)
BASE_DIR = Path(__file__).resolve().parent.parent

# --- تنظیمات مسیر فایل‌ها و پوشه‌ها ---
PATHS = {
    "yolo_model": os.path.join(BASE_DIR, "models", "best.pt"),
    "rl_model": os.path.join(BASE_DIR, "models", "hybrid_rl.pkl"),
    "slm_model": os.path.join(BASE_DIR, "models", "qwen2.5-3b-instruct-q4_k_m.gguf"),
    "video_source": os.path.join(BASE_DIR, "data", "test_video.mp4"), # ویدیو تستی خط تولید
    "log_dir": os.path.join(BASE_DIR, "data", "logs"),
    "screenshot_dir": os.path.join(BASE_DIR, "data", "screenshots"),
    "database": os.path.join(BASE_DIR, "data", "factory.db")
}

# --- تنظیمات بینایی ماشین و کنترلر ---
VISION_SETTINGS = {
    "confidence_threshold": 0.50,  # حداقل اطمینان یولو برای قبول یک عیب
    "risk_threshold": 0.40         # حداقل ریسک برای ارسال به کنترلر
}

CONTROL_SETTINGS = {
    "max_conveyor_speed": 100.0,   # حداکثر سرعت خط تولید (درصد)
    "min_conveyor_speed": 10.0,    # حداقل سرعت (برای جلوگیری از توقف کامل)
    "frames_per_decision": 5       # تصمیم‌گیری کنترلر به ازای هر 5 فریم (برای جلوگیری از نوسان موتور)
}

# --- تنظیمات گزارش‌گیری مدل زبانی (SLM) ---
# --- تنظیمات گزارش‌گیری مدل زبانی (SLM) ---
SLM_SETTINGS = {
    "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
    "filename": "qwen2.5-3b-instruct-q4_k_m.gguf", 
    "local_path": os.path.join(BASE_DIR, "models", "qwen2.5-3b-instruct-q4_k_m.gguf")
}

REPORT_SETTINGS = {
    "report_interval_seconds": 40,
    "events_per_report": 15
}