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
        self.builder = PromptBuilder()
        
        # بارگذاری SLM در یک پراسس جداگانه (فقط زمانی کار می‌کند که به آن دستور بدهیم)
        self.engine = SLMEngine(model_path=PATHS["slm_model"])
        
        # ایجاد پوشه‌های ذخیره‌سازی برای این جلسه
        base_log_dir = Path(PATHS.get("log_dir", "data/logs")).parent
        session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        self.json_session_dir = base_log_dir / "json_reports" / f"Session_{session_time}"
        self.txt_session_dir = base_log_dir / "slm_report" / f"Session_{session_time}"
        
        self.json_session_dir.mkdir(parents=True, exist_ok=True)
        self.txt_session_dir.mkdir(parents=True, exist_ok=True)

    def save_window_data_only(self, window_seconds=60):
        """این تابع هر X ثانیه اجرا می‌شود و فقط JSON و داده‌های خام را ذخیره می‌کند"""
        events = self.db.get_events_by_time_window(window_seconds)
        if not events:
            return None

        intelligence_dict, formatted_text, prompt = self.builder.process_events(events)
        
        # ذخیره پرامپت در داخل JSON تا در زمان گزارش‌گیری دسته‌جمعی از آن استفاده کنیم
        intelligence_dict["_prompt_text"] = prompt 

        start_safe = intelligence_dict["window_start"].replace(":", "-").replace(".", "-")
        end_safe = intelligence_dict["window_end"].replace(":", "-").replace(".", "-")
        filename = f"window_{start_safe}_to_{end_safe}.json"
        
        with open(self.json_session_dir / filename, "w", encoding="utf-8") as f:
            json.dump(intelligence_dict, f, indent=4, ensure_ascii=False)

        return formatted_text # فقط برای نمایش در پنل میانی داشبورد برمی‌گردد

    def process_all_batch(self):
        """این تابع زمانی اجرا می‌شود که دکمه گزارش‌گیری زده شود"""
        reports_data = []
        json_files = sorted(list(self.json_session_dir.glob("*.json")))

        for file_path in json_files:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            prompt = data.get("_prompt_text", "")
            window_str = f"{data.get('window_start', '')} تا {data.get('window_end', '')}"
            
            # 🔥 هوش مصنوعی جدید برای محاسبه ریسک کلی از روی دیتای فوق‌دقیق JSON
            risk_level = "NORMAL"
            detailed_breakdown = data.get("defect_analysis", {}).get("detailed_breakdown", {})
            
            for defect, stats in detailed_breakdown.items():
                r_level = stats.get("risk_level", "NORMAL")
                if r_level == "CRITICAL":
                    risk_level = "CRITICAL"
                    break # اگر حتی یک عیب بحرانی بود، کل وضعیت بحرانی است
                elif r_level == "WARNING":
                    risk_level = "WARNING"
            
            # ترجمه برای نمایش در رابط کاربری و فایل TXT
            if risk_level == "CRITICAL":
                risk_persian = "بحرانی 🔴"
            elif risk_level == "WARNING":
                risk_persian = "نیازمند توجه 🟠"
            else:
                risk_persian = "پایدار 🟢"

            # درخواست از Qwen برای تولید گزارش
            ai_text = self.engine.generate(prompt)

            # ذخیره گزارش به صورت فایل متنی TXT در پوشه slm_report
            txt_filename = file_path.stem + "_Report.txt"
            with open(self.txt_session_dir / txt_filename, "w", encoding="utf-8") as tf:
                tf.write(f"گزارش هوش مصنوعی - بازه: {window_str}\n")
                tf.write(f"وضعیت کلی خط: {risk_persian}\n")
                tf.write("="*50 + "\n\n")
                tf.write(ai_text)

            # ذخیره در رم برای ارسال به پنجره نمایش گرافیکی
            reports_data.append({
                "window": window_str,
                "risk": risk_persian,
                "text": ai_text
            })

        return reports_data