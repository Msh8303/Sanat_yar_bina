import json

class PromptBuilder:
    def __init__(self):
        pass

    def build_prompt(self, events: list) -> str:
        """
        تبدیل لیست رویدادهای خام به یک پرامپت استاندارد برای TinyLlama
        """
        simplified_events = []
        
        # استخراج داده‌های کلیدی برای کاهش حجم متن ارسالی به مدل
        for e in events:
            # فقط زمان را استخراج می‌کنیم (بدون تاریخ کامل)
            time_only = e.get("timestamp", "").split()[-1] if "timestamp" in e else ""
            
            # محاسبه میزان افت سرعت نوار نقاله
            speed_drop = e.get("speed_before", 0.0) - e.get("speed_after", 0.0)
            
            simplified_events.append({
                "time": time_only,
                "defect": e.get("defect_class", ""),
                "risk": round(e.get("severity_score", 0.0), 2),
                "speed_drop": round(speed_drop, 1)
            })

        events_json = json.dumps(simplified_events)

        # ساختار استاندارد پرامپت TinyLlama (استفاده از تگ‌های system, user, assistant)
        prompt = f"""<|system|>
You are an expert industrial data analyst for a steel manufacturing plant.
Analyze the production events and output ONLY valid JSON. Do not add introductory or concluding texts.
Use this exact JSON format:
{{
    "total_defects": <int>,
    "critical_defects": <int>,
    "most_frequent_defect": "<string>",
    "average_speed_reduction": <float>,
    "recommendation": "<string>"
}}
<|user|>
Analyze these recent events:
{events_json}
<|assistant|>
"""
        return prompt