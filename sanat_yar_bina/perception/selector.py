from perception.risk import RiskAnalyzer

class TargetSelector:
    def __init__(self, min_risk_threshold: float = 0.4):
        """
        فقط عیوبی بررسی می‌شوند که ریسک آن‌ها از آستانه تعریف شده بیشتر باشد
        """
        self.risk_analyzer = RiskAnalyzer()
        self.min_risk_threshold = min_risk_threshold

    def select_primary_target(self, detections: list) -> dict:
        """
        دریافت تمام عیوب یک فریم و انتخاب خطرناک‌ترین مورد
        خروجی: دیکشنری شامل مشخصات عیب و ضریب ریسک آن (یا None در صورت عدم وجود هدف معتبر)
        """
        if not detections:
            return None

        evaluated_defects = []
        for det in detections:
            risk = self.risk_analyzer.calculate_risk(det)
            evaluated_defects.append({
                "detection": det,
                "risk_score": risk
            })

        # مرتب‌سازی لیست بر اساس ضریب ریسک به صورت نزولی
        evaluated_defects.sort(key=lambda x: x["risk_score"], reverse=True)

        # انتخاب مورد صدر جدول (بالاترین ریسک)
        primary_target = evaluated_defects[0]

        # اعتبارسنجی نهایی با آستانه ریسک سیستم
        if primary_target["risk_score"] >= self.min_risk_threshold:
            return primary_target
        
        return None