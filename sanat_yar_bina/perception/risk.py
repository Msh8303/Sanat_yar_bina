class RiskAnalyzer:
    def __init__(self):
        # وزن‌دهی به انواع عیوب (عیوب بحرانی‌تر وزن بالاتری دارند)
        # این نام‌ها باید دقیقاً با کلاس‌های مدل یولوی شما یکسان باشند
        self.defect_weights = {
            "crazing": 0.9,
            "inclusion": 0.8,
            "pitted_surface": 0.7,
            "patches": 0.6,
            "rolled-in_scale": 0.5,
            "scratches": 0.4
        }
        # مساحت مرجع برای نرمال‌سازی (بر اساس ابعاد فریم و فاصله دوربین تنظیم می‌شود)
        self.max_area_ref = 15000.0

    def calculate_risk(self, detection: dict) -> float:
        """
        محاسبه ضریب ریسک ترکیبی برای یک عیب
        """
        cls_name = detection.get("class_name", "")
        conf = detection.get("confidence", 0.0)
        area = detection.get("area_px", 0.0)

        # دریافت وزن کلاس (پیش‌فرض 0.5 برای کلاس‌های ناشناخته)
        weight = self.defect_weights.get(cls_name, 0.5)

        # نرمال‌سازی مساحت (کپ کردن روی عدد 1.0)
        normalized_area = min(area / self.max_area_ref, 1.0)

        # فرمول محاسبه ریسک: 50% نوع عیب + 30% وسعت عیب + 20% اطمینان یولو
        severity_score = (weight * 0.50) + (normalized_area * 0.30) + (conf * 0.20)

        # اطمینان از قرارگیری خروجی نهایی در بازه استاندارد [0.0, 1.0]
        return min(max(severity_score, 0.0), 1.0)