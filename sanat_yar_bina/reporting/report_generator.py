import json
import os
from datetime import datetime
from pathlib import Path
from reporting.slm_engine import SLMEngine
from reporting.prompt_builder import PromptBuilder
from config.config import PATHS

class ReportGenerator:
    def __init__(self, db_manager):
        self.db = db_manager
        self.engine = SLMEngine(model_path=PATHS["slm_model"])
        self.builder = PromptBuilder()
        
        # --- سیستم مدیریت پوشه‌ها برای ذخیره JSON ---
        # ایجاد پوشه اصلی json_reports در کنار پوشه logs
        base_log_dir = Path(PATHS.get("log_dir", "data/logs")).parent
        session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # ایجاد زیرپوشه با نام تاریخ و ساعت اجرای فعلی برنامه
        self.json_session_dir = base_log_dir / "json_reports" / f"Session_{session_time}"
        self.json_session_dir.mkdir(parents=True, exist_ok=True)

    def create_periodic_report(self, window_seconds=40):
        events = self.db.get_events_by_time_window(window_seconds)
        if not events:
            return {"total_defects": 0, "ai_recommendation": "خط تولید در وضعیت عادی است."}

        # دریافت همزمان دیکشنری تمیز و پرامپت متنی از بیلدر
        intelligence_dict, prompt = self.builder.process_events(events)

        # --- ۱. ذخیره دیکشنری به صورت فایل JSON ---
        # تبدیل کاراکترهای دو نقطه (:) در زمان به خط تیره (-) تا در نامگذاری فایل ویندوز خطا ندهد
        start_safe = intelligence_dict["window_start"].replace(":", "-").replace(".", "-")
        end_safe = intelligence_dict["window_end"].replace(":", "-").replace(".", "-")
        
        filename = f"window_{start_safe}_to_{end_safe}.json"
        filepath = self.json_session_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            # ذخیره با فرمت‌بندی مرتب و تورفتگی (Indent) برای خوانایی انسانی
            json.dump(intelligence_dict, f, indent=4, ensure_ascii=False)

        # --- ۲. دریافت پیشنهاد از هوش مصنوعی ---
        ai_json_str = self.engine.generate(prompt)
        
        try:
            ai_data = json.loads(ai_json_str.strip())
            recommendation = ai_data.get("recommendation", "بررسی دوره‌ای پیشنهاد می‌شود.")
        except:
            recommendation = "مدل در تولید فرمت JSON دچار خطا شد."

        # --- ۳. آماده‌سازی داده‌ها برای نمایش در داشبورد رابط کاربری ---
        defects = intelligence_dict["defect_summary"]["breakdown"]
        most_freq = max(defects, key=defects.get) if defects else "N/A"
        
        # استخراج میانگین افت سرعت از لیست لاگ تغییرات
        total_drop = sum(c["from_speed"] - c["to_speed"] for c in intelligence_dict["conveyor_control"]["change_log"])
        avg_drop = total_drop / len(events) if events else 0.0

        return {
            "total_defects": intelligence_dict["defect_summary"]["total_defects"],
            "critical_defects": sum(1 for v in intelligence_dict["severity_breakdown"].values() if v["level"] == "HIGH"),
            "most_frequent": most_freq,
            "avg_speed_drop": round(avg_drop, 1),
            "ai_recommendation": recommendation
        }