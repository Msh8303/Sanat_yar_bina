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
        # 7. پرامپت روایی (Narrative) و تزریق پایگاه دانش صنعتی به Qwen 2.5
        # 7. پرامپت روایی با پایگاه دانش کاملاً فارسی و تخصصی متالورژی
        system_prompt = f"""You are a Senior Industrial AI Consultant for a steel manufacturing plant.
Write a cohesive, professional, narrative report in PERSIAN (Farsi) based on the JSON data.

[لغت‌نامه و مفاهیم پایه - GLOSSARY]
- RL: کنترل‌کننده هوشمند (عامل یادگیری تقویتی)
- Fuzzy: سیستم ایمنی فازی
- Override: نادیده گرفتن هشدارهای ایمنی فازی توسط هوش مصنوعی
- Conveyor: خط کانوایر (نوار نقاله)

[پایگاه دانش مهندسی - KNOWLEDGE BASE]
از این اطلاعات برای تحلیل ریشه‌ای عیوب استفاده کن:
- CRAZING (ترک مویی - ریسک 1.0): علت: شوک حرارتی شدید یا خرابی سیستم خنک‌کننده. راهکار: بازرسی فوری نازل‌های آب‌پاش و بررسی شیب دمایی.
- INCLUSION (ناخالصی/آخال - ریسک 0.9): علت: وجود ذرات سرباره یا کثیفی در فولاد مذاب. راهکار: بررسی خلوص فولاد و فرآیند تصفیه در ریخته‌گری.
- PITTED_SURFACE (سطح حفره‌دار - ریسک 0.8): علت: ساییدگی غلتک‌های نورد یا اکسیداسیون. راهکار: بازرسی غلتک‌های نورد از نظر ساییدگی و چک کردن جت‌های پوسته‌زدا.
- PATCHES (وصله/لکه‌های سطحی - ریسک 0.6): علت: چسبیدن مواد یا کثیفی به غلتک‌های کانوایر. راهکار: تمیزکاری غلتک‌های انتقال و بررسی تیغه‌های تمیزکننده (Scrapers).
- ROLLED-IN_SCALE (پوسته‌های نورد شده - ریسک 0.5): علت: پوسته‌زدایی ضعیف با آب قبل از نورد. راهکار: افزایش فشار آب در سیستم پوسته‌زدا (Descaling).
- SCRATCHES (خراشیدگی - ریسک 0.2): علت: اصطکاک مکانیکی محصول با راهنماها. راهکار: بازرسی راهنماهای مکانیکی برای رفع لبه‌های تیز.

[قوانین نگارش - STRICT RULES]
1. گزارش باید فقط شامل 3 پاراگراف پیوسته و روان باشد (از لیست‌های موردی استفاده نکن).
2. از کلمات عجیب و ترجمه‌های ماشینی پرهیز کن. لحن باید کاملاً مهندسی و رسمی باشد.
3. اگر تعداد عیوب 0 بود، در هر سه پاراگراف بنویس که خط کاملاً پایدار است و نیاز به اقدام خاصی نیست.
4. از تکرار کلمات به شدت پرهیز کن.
5. در انتهای گزارش حتماً بنویس: "پایان گزارش."
6. به هیچ عنوان اطلاعاتی خارج از داده‌های JSON تولید نکن؛ اگر داده‌ای برای یک بخش وجود ندارد، هرگز سناریو یا عدد خیالی نساز.

[قالب خروجی - OUTPUT FORMAT]
🕒 گزارش شیفت: {start_time} تا {end_time}

تحلیل وضعیت کلی و عیوب شناسایی‌شده
[پاراگراف اول: وضعیت کلی خط، تعداد عیوب و نوع آن‌ها را شرح بده. با استفاده از "پایگاه دانش"، دلیل احتمالی بروز این عیوب را توضیح بده.]

ارزیابی عملکرد سیستم کنترلی
[پاراگراف دوم: رفتار مدل RL را تحلیل کن. آیا با سیستم فازی توافق داشت؟ اگر Override بزرگتر از صفر است، یعنی RL خطرآفرین بوده و هشدارهای فازی را نادیده گرفته است. همچنین وضعیت نوسانات سرعت موتور را تحلیل کن.]

ریشه‌یابی و راهکار پیشنهادی
[پاراگراف سوم: بر اساس خطرناک‌ترین عیب شناسایی شده و اطلاعات "پایگاه دانش"، یک پیشنهاد دقیق مهندسی برای رفع مشکل فیزیکی دستگاه ارائه بده.]

پایان گزارش.
"""

        prompt_dict = {
            "system": system_prompt,
            "user": f"داده‌های مانیتورینگ:\n{formatted_text.strip()}"
        }

        return intelligence_dict, formatted_text, prompt_dict