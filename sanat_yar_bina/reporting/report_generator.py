from collections import Counter
from reporting.slm_engine import SLMEngine
from config.config import PATHS
import json
from reporting.prompt_builder import PromptBuilder
class ReportGenerator:
    def __init__(self, db_manager):
        self.db = db_manager
        self.engine = SLMEngine(model_path=PATHS["slm_model"])
        self.builder = PromptBuilder()

    def create_periodic_report(self, limit=25):
        events = self.db.get_recent_events(limit)
        if not events:
            return {"total_defects": 0, "ai_recommendation": "Normal"}

        # ۱. محاسبات عددی دقیق با پایتون
        total = len(events)
        critical = sum(1 for e in events if float(e.get('severity_score', 0)) > 0.5)
        defects = [e.get('defect_class', 'unknown').lower() for e in events]
        most_freq = Counter(defects).most_common(1)[0][0] if defects else "N/A"
        drops = [(float(e.get('speed_before', 0)) - float(e.get('speed_after', 0))) for e in events]
        avg_drop = sum(drops) / len(drops) if drops else 0.0

        # ۲. استفاده از PromptBuilder برای ساخت یک پرامپت استاندارد JSON
        # (این متد در فایل prompt_builder شما وجود دارد)
        prompt = self.builder.build_prompt(events) 
        
        # ۳. دریافت پاسخ از مدل
        ai_json_str = self.engine.generate(prompt)
        
        # ۴. پارس کردن خروجی مدل
        try:
            # پاکسازی خروجی از تگ‌های احتمالی مدل
            ai_data = json.loads(ai_json_str.strip())
            recommendation = ai_data.get("recommendation", "No specific advice.")
        except:
            recommendation = "AI failed to generate JSON structure."

        return {
            "total_defects": total,
            "critical_defects": critical,
            "most_frequent": most_freq.upper(),
            "avg_speed_drop": round(avg_drop, 1),
            "ai_recommendation": recommendation
        }