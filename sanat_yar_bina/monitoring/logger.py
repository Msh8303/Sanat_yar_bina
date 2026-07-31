import csv
import os
from pathlib import Path
from datetime import datetime
from monitoring.event_model import DetectionEvent
from config.config import PATHS  # 🔥 اضافه کردن کانفیگ متمرکز

class EventLogger:
    # مقادیر پیش‌فرض را به None تغییر دادیم تا از کانفیگ خوانده شوند
    def __init__(self, log_dir: str = None, csv_dir: str = None):
        """
        راه‌اندازی سیستم لاگ‌گیری دوگانه (JSONL برای خواندن ماشینی و CSV برای تحلیل انسانی)
        """
        # اگر مقداری پاس داده نشد، مستقیماً از مسیرهای مطلق و امن config.py استفاده کن
        actual_log_dir = log_dir if log_dir else os.path.join(PATHS["data_dir"], "logs")
        actual_csv_dir = csv_dir if csv_dir else PATHS["log_dir"] # در کانفیگ به پوشه csv_log اشاره دارد

        # --- 1. تنظیمات فایل JSONL (پیوسته) ---
        self.log_dir = Path(actual_log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "events.jsonl"

        # --- 2. تنظیمات فایل CSV (جلسه‌ای / Session-based) ---
        self.csv_dir = Path(actual_csv_dir)
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        
        # ساخت نام فایل بر اساس تاریخ و ساعت دقیق استارت برنامه
        # مثال خروجی: log_2026-06-19_14-30-05.csv
        session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csv_file = self.csv_dir / f"log_{session_time}.csv"
        
        # ایجاد فایل CSV جدید برای این جلسه و نوشتن هدرها (ستون‌ها)
        with open(self.csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Timestamp", "Frame_ID", "Defect_Class", "Confidence", 
                "Severity_Score", "Fuzzy_Output", "RL_Output", 
                "Speed_Before", "Speed_After", "Selected_Action"
            ])

    def log(self, event: DetectionEvent):
        """
        ثبت همزمان رویداد در لاگ JSONL و CSV
        """
        # 1. اضافه کردن به فایل JSONL
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")
            
        # 2. اضافه کردن یک سطر به فایل CSV مخصوص این جلسه
        with open(self.csv_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                event.timestamp,
                event.frame_id,
                event.defect_class.upper(),
                f"{event.confidence:.4f}",
                f"{event.severity_score:.4f}",
                f"{event.fuzzy_output:.4f}",
                f"{event.rl_output:.4f}",
                f"{event.speed_before:.1f}",
                f"{event.speed_after:.1f}",
                event.selected_action
            ])