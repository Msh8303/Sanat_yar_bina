import os
from pathlib import Path

# گرفتن مسیر اصلی پروژه (یک سطح بالاتر از پوشه config)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# مسیر یکپارچه پوشه data در داخل پروژه (برای جلوگیری از پراکندگی فایل‌ها)
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- تنظیمات مسیر فایل‌ها و پوشه‌ها ---
PATHS = {
    # پوشه اصلی داده‌ها
    "data_dir": DATA_DIR,
    
    # فایل‌های خروجی و ذخیره‌سازی
    "log_dir": os.path.join(DATA_DIR, "csv_log"), # اصلاح شده برای هدایت دقیق به csv_log
    "screenshot_dir": os.path.join(DATA_DIR, "screenshots"),
    "database": os.path.join(DATA_DIR, "factory.db"),
    "video_source": os.path.join(DATA_DIR, "test_video.mp4"),
    
    # مدل‌های اصلی (هوش مصنوعی)
    "yolo_model": os.path.join(BASE_DIR, "models", "best.pt"),
    "rl_model": os.path.join(BASE_DIR, "models", "hybrid_rl.pkl"),
    "slm_model": os.path.join(BASE_DIR, "models", "qwen2.5-3b-instruct-q4_k_m.gguf"),
    
    # مسیر فایل‌های مربوط به شبیه‌ساز Webots
    "webots_exe": r"C:\Program Files\Webots\msys64\mingw64\bin\webots.exe", # این مسیر به نصب وباتز در سیستم مقصد بستگی دارد
    "yolo_model_webot": os.path.join(BASE_DIR, "simulation", "controllers", "smart_conveyor", "best.pt"), # کاملا داینامیک شد
    "rl_model_webot": os.path.join(BASE_DIR, "simulation", "controllers", "smart_conveyor", "hybrid_rl_model.pkl") # کاملا داینامیک شد
}

# --- تنظیمات بینایی ماشین و کنترلر ---
VISION_SETTINGS = {
    "confidence_threshold": 0.60,  # حداقل اطمینان یولو برای قبول یک عیب
    "risk_threshold": 0.50         # حداقل ریسک برای ارسال به کنترلر
}

CONTROL_SETTINGS = {
    "max_conveyor_speed": 100.0,   # حداکثر سرعت خط تولید (درصد)
    "min_conveyor_speed": 10.0,    # حداقل سرعت (برای جلوگیری از توقف کامل)
    "frames_per_decision": 5       # تصمیم‌گیری کنترلر به ازای هر 5 فریم (برای جلوگیری از نوسان موتور)
}

# --- تنظیمات گزارش‌گیری مدل زبانی (SLM) ---
SLM_SETTINGS = {
    "repo_id": "Qwen/Qwen3-4B-Q4_K_M",
    "filename": "Qwen3-4B-Q4_K_M.gguf", 
    "local_path": os.path.join(BASE_DIR, "models", "Qwen3-4B-Q4_K_M.gguf")
}

REPORT_SETTINGS = {
    "report_interval_seconds": 40
}