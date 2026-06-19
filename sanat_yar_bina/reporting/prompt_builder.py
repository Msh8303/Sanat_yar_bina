from collections import Counter, defaultdict

class PromptBuilder:
    def __init__(self):
        pass

    def _determine_level(self, score: float) -> str:
        """تبدیل عدد ریسک به سطح کیفی (متنی)"""
        if score >= 0.8: return "HIGH"
        if score >= 0.5: return "MEDIUM"
        return "LOW"

    def process_events(self, events: list):
        """
        پردازش رویدادها، تولید دیکشنری ساختاریافته (برای فایل JSON) و ساخت پرامپت (برای مدل)
        """
        if not events:
            return {}, ""

        # 1. استخراج زمان شروع و پایان بازه
        start_time = events[0].get("timestamp", "Unknown").split()[-1]
        end_time = events[-1].get("timestamp", "Unknown").split()[-1]

        # 2. تحلیل و تجمیع داده‌ها
        total_defects = len(events)
        defect_counts = Counter()
        defect_risks = defaultdict(list)
        overall_risks = []
        speed_changes = []

        # در بخش حلقه for e in events این تغییرات را بدهید:
        for e in events:
            defect = str(e.get("defect_class", "unknown")).upper()
            risk = float(e.get("severity_score", 0.0))
            s_before = float(e.get("speed_before", 0.0))
            s_after = float(e.get("speed_after", 0.0))
            time_str = e.get("timestamp", "").split()[-1]

            # تفاوت: فقط عیوب واقعی شمرده شوند
            if defect != "NORMAL":
                defect_counts[defect] += 1
                defect_risks[defect].append(risk)
                overall_risks.append(risk)

            # ثبت تغییرات سرعت (حتی اگر نرمال باشد، ممکن است سرعت تغییر کند)
            if s_before != s_after:
                speed_changes.append({"time": time_str, "from_speed": round(s_before, 1), "to_speed": round(s_after, 1)})
        
        # مجموع عیوب واقعی
        total_defects = sum(defect_counts.values())

        # --- ساختاردهی دیکشنری (دقیقاً برای ذخیره در قالب JSON) ---
        severity_breakdown = {}
        for d, risks in defect_risks.items():
            avg_risk = sum(risks) / len(risks)
            severity_breakdown[d] = {
                "level": self._determine_level(avg_risk),
                "average_score": round(avg_risk, 2)
            }

        change_count = len(speed_changes)
        if change_count > 5: instab_level = "HIGH"
        elif change_count > 0: instab_level = "MEDIUM"
        else: instab_level = "LOW"

        avg_overall_risk = sum(overall_risks) / len(overall_risks) if overall_risks else 0.0

        intelligence_dict = {
            "window_start": start_time,
            "window_end": end_time,
            "defect_summary": {
                "total_defects": total_defects,
                "breakdown": dict(defect_counts)
            },
            "severity_breakdown": severity_breakdown,
            "conveyor_control": {
                "instability_level": instab_level,
                "total_changes": change_count,
                "change_log": speed_changes
            },
            "overall_risk": {
                "score": round(avg_overall_risk, 2),
                "level": self._determine_level(avg_overall_risk)
            }
        }

        # --- فرمت‌دهی به صورت متن برای پرامپت TinyLlama ---
        breakdown_str = "\n".join([f"   - {d}: {c}" for d, c in defect_counts.items()])
        severity_str = "\n".join([f"   - {d}: {info['level']} (Avg: {info['average_score']})" for d, info in severity_breakdown.items()])
        speed_log_str = "\n".join([f"     - Change: {c['from_speed']}% -> {c['to_speed']}% at {c['time']}" for c in speed_changes])
        speed_str = f"Instability: {instab_level} ({change_count} changes)\n{speed_log_str}"

        formatted_text = f"""Window: {start_time} to {end_time}

1. Defect Summary:
   - Total defects: {total_defects}
{breakdown_str}

2. Severity Breakdown:
{severity_str}

3. Conveyor Control:
   - {speed_str}

4. Overall Window Risk: {avg_overall_risk:.2f} -> {self._determine_level(avg_overall_risk)}
"""

        prompt = f"""<|system|>
You are an expert industrial AI analyst. Read the aggregated production window data below.
Output ONLY valid JSON. Do not output anything else.
Required JSON format: {{"recommendation": "Your 2-sentence advice"}}
<|user|>
{formatted_text.strip()}
<|assistant|>
"""
        return intelligence_dict, formatted_text, prompt