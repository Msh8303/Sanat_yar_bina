from collections import defaultdict
from datetime import datetime

class PromptBuilder:
    def __init__(self):
        pass

    def _determine_level(self, score: float) -> str:
        """تبدیل عدد ریسک به سطح کیفی"""
        if score >= 0.8: return "CRITICAL"
        if score >= 0.5: return "WARNING"
        return "NORMAL"

    def process_events(self, events: list):
        """پردازش رویدادها، تولید JSON فوق‌دقیق و ساخت پرامپت برای Qwen"""
        
        # 🔥 جلوگیری از ارور در زمان توقف کامل خط (خالی بودن لیست ایونت‌ها)
        if not events:
            now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            # برگرداندن کلیدهای حیاتی برای جلوگیری از کرش کردن report_generator
            return {"window_start": now_str, "window_end": now_str}, "", {}

        # 1. استخراج زمان شروع و پایان بازه
        start_time = events[0].get("timestamp", "Unknown").split()[-1]
        end_time = events[-1].get("timestamp", "Unknown").split()[-1]

        # 2. متغیرهای تجمیع داده‌های دقیق
        defect_stats = defaultdict(lambda: {"count": 0, "risks": [], "confs": []})
        speed_changes_log = []
        
        rl_agrees = 0
        rl_overrides_safety = 0
        rl_is_conservative = 0

        last_recorded_speed = None

        # 3. حلقه پردازش فریم به فریم
        for e in events:
            defect = str(e.get("defect_class", "NORMAL")).upper()
            risk = float(e.get("severity_score", 0.0))
            conf = float(e.get("confidence", 0.0))
            s_before = float(e.get("speed_before", 0.0))
            s_after = float(e.get("speed_after", 0.0))
            time_str = e.get("timestamp", "").split()[-1]
            action_str = str(e.get("selected_action", ""))

            if defect != "NORMAL":
                defect_stats[defect]["count"] += 1
                defect_stats[defect]["risks"].append(risk)
                defect_stats[defect]["confs"].append(conf)

            if s_before != s_after and s_after != last_recorded_speed:
                speed_changes_log.append({
                    "time": time_str,
                    "from_speed_percent": round(s_before, 1),
                    "to_speed_percent": round(s_after, 1)
                })
                last_recorded_speed = s_after

            if "RL:" in action_str and "Fuzzy:" in action_str:
                parts = action_str.split("|")
                rl_action = parts[0].upper()
                fz_opinion = parts[1].upper()

                if "BRAKE" in fz_opinion:
                    if "DECELERATE" in rl_action: rl_agrees += 1
                    else: rl_overrides_safety += 1 
                        
                elif "ACCELERATE" in fz_opinion:
                    if "ACCELERATE" in rl_action: rl_agrees += 1
                    else: rl_is_conservative += 1  
                        
                else: 
                    if "HOLD" in rl_action: rl_agrees += 1
                    elif "DECELERATE" in rl_action: rl_is_conservative += 1
                    elif "ACCELERATE" in rl_action: rl_overrides_safety += 1
        
        # 4. تدوین گزارش تفصیلی عیوب
        detailed_defects_json = {}
        total_defects = 0
        
        for d_name, stats in defect_stats.items():
            c = stats["count"]
            total_defects += c
            avg_r = sum(stats["risks"]) / c if c > 0 else 0
            max_r = max(stats["risks"]) if c > 0 else 0
            avg_c = sum(stats["confs"]) / c if c > 0 else 0
            
            detailed_defects_json[d_name] = {
                "count": c,
                "average_risk": round(avg_r, 3),
                "max_risk": round(max_r, 3),
                "average_confidence": round(avg_c, 3),
                "risk_level": self._determine_level(avg_r)
            }

        # 5. ساختاردهی دیکشنری 
        intelligence_dict = {
            "window_start": start_time,  # 🔥 بازگرداندن این کلید برای سازگاری با کدهای شما
            "window_end": end_time,      # 🔥 بازگرداندن این کلید برای سازگاری با کدهای شما
            "window_info": {
                "start_time": start_time,
                "end_time": end_time
            },
            "defect_analysis": {
                "total_defects_detected": total_defects,
                "detailed_breakdown": detailed_defects_json
            },
            "controller_behavior": {
                "rl_fuzzy_agreements": rl_agrees,
                "rl_safety_overrides": rl_overrides_safety,
                "rl_conservative_actions": rl_is_conservative
            },
            "speed_profile": {
                "total_speed_changes": len(speed_changes_log),
                "changes_log": speed_changes_log
            }
        }

        # 6. فرمت‌دهی متن خلاصه
        defects_str_list = []
        for d_name, info in detailed_defects_json.items():
            defects_str_list.append(
                f"   - {d_name}: {info['count']} times | Max Risk: {info['max_risk']} | Avg Conf: {info['average_confidence']*100:.1f}%"
            )
        breakdown_str = "\n".join(defects_str_list) if defects_str_list else "   - No defects detected."

        speed_str_list = []
        for log in speed_changes_log:
            speed_str_list.append(f"   - At {log['time']}: {log['from_speed_percent']}% -> {log['to_speed_percent']}%")
        speed_changes_str = "\n".join(speed_str_list) if speed_str_list else "   - Constant speed maintained."

        formatted_text = f"""Time Window: {start_time} to {end_time}

[1] Defect Stats (Total: {total_defects}):
{breakdown_str}

[2] RL Behavior vs Fuzzy Safety:
   - Agreements: {rl_agrees}
   - Overrides (Ignored Brake): {rl_overrides_safety}
   - Conservative (Unnecessary Brake): {rl_is_conservative}

[3] Speed Changes ({len(speed_changes_log)}):
{speed_changes_str}
"""

        # 7. پرامپت اختصاصی و بهینه‌شده برای Qwen 2.5 3B (کاملا دستوری و سخت‌گیرانه)
        system_prompt = f"""
You are an industrial AI monitoring assistant for a steel conveyor system.

You MUST follow all rules strictly.

RULES:
- Use ONLY the provided data.
- Do NOT guess, infer, or hallucinate.
- If data is missing, explicitly write: "اطلاعات کافی موجود نیست."
- Do NOT repeat phrases.
- Do NOT explain reasoning.
- Output MUST be in Persian.
- Keep output compact and structured.
- Maximum 8–10 sentences total.

TERMS (IMPORTANT):
- RL = عامل یادگیری تقویتی
- Fuzzy = کنترل‌کننده فازی
- Override = نادیده گرفتن تصمیم فازی
- Risk = سطح ریسک

FORMAT (STRICT):

🕒 شیفت گزارش: {start_time} تا {end_time}

🔴 وضعیت کلی خط:
- [پایدار | نیازمند توجه | بحرانی]

🤖 بیشترین عیب یافت شده:
- Name: ...
- Max Risk: ...
- Count: ...

📝 تحلیل رفتار کنترلر هوشمند (RL):
- Bullet 1 (رفتار RL)
- Bullet 2 (رعایت/عدم رعایت Fuzzy و Override)

📊 پروفایل سرعت موتور:
- تعداد تغییرات: ...
- تحلیل: (یک خط کوتاه، یکنواخت یا نوسانی بودن)

⚠️ اقدام پیشنهادی:
- فقط یک جمله کوتاه مهندسی

IMPORTANT RULES:
- If no defect exists, say: "هیچ عیبی شناسایی نشد."
- Do NOT fabricate explanations.
- Do NOT repeat words or phrases.
"""

        prompt_dict = {
            "system": system_prompt,
            "user": f"Monitoring Data (JSON): {formatted_text.strip()}"
        }

        return intelligence_dict, formatted_text, prompt_dict