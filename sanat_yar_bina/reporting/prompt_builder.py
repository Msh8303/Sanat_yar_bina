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
        پردازش رویدادها، تولید دیکشنری ساختاریافته (برای JSON) و ساخت پرامپت تحلیلی (برای Qwen)
        """
        if not events:
            return {}, "", {}

        # 1. استخراج زمان شروع و پایان بازه
        start_time = events[0].get("timestamp", "Unknown").split()[-1]
        end_time = events[-1].get("timestamp", "Unknown").split()[-1]

        # 2. متغیرهای تجمیع داده‌ها
        defect_counts = Counter()
        defect_risks = defaultdict(list)
        overall_risks = []
        overall_confs = []
        speed_changes = []

        # شمارنده‌های تحلیل رفتار هوش مصنوعی (RL vs Fuzzy)
        rl_agrees = 0
        rl_overrides_safety = 0  # زمانی که فازی می‌گوید ترمز اما RL گوش نمی‌کند
        rl_is_conservative = 0   # زمانی که فازی می‌گوید گاز بده اما RL ترمز می‌کند یا نگه می‌دارد

        # 3. حلقه پردازش فریم به فریم
        for e in events:
            defect = str(e.get("defect_class", "unknown")).upper()
            risk = float(e.get("severity_score", 0.0))
            conf = float(e.get("confidence", 0.0))
            s_before = float(e.get("speed_before", 0.0))
            s_after = float(e.get("speed_after", 0.0))
            time_str = e.get("timestamp", "").split()[-1]
            action_str = str(e.get("selected_action", ""))

            # الف) ثبت عیوب و ریسک/کانفیدنس
            if defect != "NORMAL":
                defect_counts[defect] += 1
                defect_risks[defect].append(risk)
                overall_risks.append(risk)
                overall_confs.append(conf)

            # ب) ثبت تغییرات سرعت موتور
            if s_before != s_after:
                speed_changes.append({"time": time_str, "from_speed": round(s_before, 1), "to_speed": round(s_after, 1)})

            # ج) کالبدشکافی تصمیمات کنترلر
            if "RL:" in action_str and "Fuzzy:" in action_str:
                parts = action_str.split("|")
                rl_action = parts[0].upper()
                fz_opinion = parts[1].upper()

                # منطق بررسی موافقت و مخالفت بین دو مغز سیستم
                if "BRAKE" in fz_opinion:
                    if "DECELERATE" in rl_action:
                        rl_agrees += 1
                    else:
                        rl_overrides_safety += 1 # ⚠️ نادیده گرفتن هشدار ایمنی
                        
                elif "ACCELERATE" in fz_opinion:
                    if "ACCELERATE" in rl_action:
                        rl_agrees += 1
                    else:
                        rl_is_conservative += 1  # 🐢 احتیاط بیش از حد RL
                        
                else: # MAINTAIN
                    if "HOLD" in rl_action:
                        rl_agrees += 1
                    elif "DECELERATE" in rl_action:
                        rl_is_conservative += 1
                    elif "ACCELERATE" in rl_action:
                        rl_overrides_safety += 1
        
        # 4. محاسبات آماری نهایی
        total_defects = sum(defect_counts.values())
        avg_overall_risk = sum(overall_risks) / len(overall_risks) if overall_risks else 0.0
        avg_overall_conf = sum(overall_confs) / len(overall_confs) if overall_confs else 0.0
        change_count = len(speed_changes)

        severity_breakdown = {}
        for d, risks in defect_risks.items():
            avg_risk = sum(risks) / len(risks)
            severity_breakdown[d] = {
                "level": self._determine_level(avg_risk),
                "average_score": round(avg_risk, 2)
            }

        # تعیین سطح ناپایداری موتور
        if change_count > 5: instab_level = "HIGH"
        elif change_count > 0: instab_level = "MEDIUM"
        else: instab_level = "LOW"

        # 5. ساختاردهی دیکشنری (برای فایل JSON که در لاگ‌ها ذخیره می‌شود)
        intelligence_dict = {
            "window_start": start_time,
            "window_end": end_time,
            "defect_summary": {
                "total_defects": total_defects,
                "average_confidence": round(avg_overall_conf, 2),
                "breakdown": dict(defect_counts)
            },
            "severity_breakdown": severity_breakdown,
            "ai_behavior_analysis": {
                "rl_fuzzy_agreements": rl_agrees,
                "rl_safety_overrides": rl_overrides_safety,
                "rl_conservative_actions": rl_is_conservative
            },
            "conveyor_control": {
                "instability_level": instab_level,
                "total_changes": change_count,
            },
            "overall_risk": {
                "score": round(avg_overall_risk, 2),
                "level": self._determine_level(avg_overall_risk)
            }
        }

        # 6. فرمت‌دهی به صورت متن (خوراکِ پرامپت کاربر)
        breakdown_str = "\n".join([f"   - {d}: {c}" for d, c in defect_counts.items()])
        severity_str = "\n".join([f"   - {d}: {info['level']} (Avg Risk: {info['average_score']})" for d, info in severity_breakdown.items()])

        formatted_text = f"""Time Window: {start_time} to {end_time}

[1] Defect & Vision Stats:
   - Total defects detected: {total_defects}
   - Average AI Confidence (YOLO): {avg_overall_conf*100:.1f}%
{breakdown_str}

[2] Severity Breakdown:
{severity_str}
   - Overall Window Risk: {avg_overall_risk:.2f} -> {self._determine_level(avg_overall_risk)}

[3] RL Agent Behavior vs Fuzzy Safety Observer:
   - RL aligned with Fuzzy safety recommendations: {rl_agrees} times.
   - RL ignored safety (Sped up / Held speed while Fuzzy warned to brake): {rl_overrides_safety} times.
   - RL was extra cautious (Braked while Fuzzy said it's safe): {rl_is_conservative} times.

[4] Conveyor Motor:
   - Speed Instability: {instab_level} ({change_count} speed changes)
"""

        # 7. --- پرامپت سیستم (نقشِ Qwen به عنوان بازرس رفتار AI) ---
        system_prompt = f"""You are a senior AI safety auditor and industrial control engineer in a steel plant.
Your task is to analyze monitoring data and evaluate the performance of our Reinforcement Learning (RL) conveyor controller.

Style requirements:
- Professional, analytical, and objective industrial tone.
- Keep output concise and strictly follow the required format.
- DO NOT hallucinate. Base your analysis ONLY on the provided data.

Output must strictly follow this format:

🕒 شیفت گزارش: {start_time} تا {end_time}
🔴 وضعیت کلی خط: [بحرانی / نیازمند توجه / پایدار]
🤖 دقت بینایی ماشین (YOLO): [درصد میانگین اطمینان]

📝 تحلیل رفتار کنترلر هوشمند (RL Analysis):
Explain how the RL agent behaved during this window. Did it respect the Fuzzy logic's safety warnings? If the RL agent ignored safety overrides (rl_safety_overrides > 0), analyze the potential risk to the production line. If it was conservative, mention that it prioritized safety over throughput.

📊 وضعیت عیوب و موتور:
- عیوب غالب: [نام عیب و سطح ریسک]
- پایداری موتور نقاله: [تحلیل تغییرات سرعت]

⚠️ اقدام پیشنهادی:
Provide 1 precise engineering adjustment (e.g., "Retrain RL agent to heavily penalize safety overrides" or "Inspect camera due to low YOLO confidence" or "Normal operation, no action needed").
"""

        prompt_dict = {
            "system": system_prompt,
            "user": f"Monitoring dataset for this time window:\n{formatted_text.strip()}"
        }

        # برای اینکه کدهای `report_generator.py` به مشکل نخورند، ما prompt_dict را برمی‌گردانیم
        return intelligence_dict, formatted_text, prompt_dict