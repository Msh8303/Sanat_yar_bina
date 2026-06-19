class FuzzyController:
    def __init__(self):
        """
        راه‌اندازی کنترلر فازی با قوانین پایه صنعتی
        """
        pass

    def _membership_low(self, x: float) -> float:
        # تابع عضویت مثلثی برای ریسک کم (0 تا 0.5)
        return max(0.0, min(1.0, (0.5 - x) / 0.5)) if x <= 0.5 else 0.0

    def _membership_medium(self, x: float) -> float:
        # تابع عضویت مثلثی برای ریسک متوسط (0.2 تا 0.8)
        return max(0.0, min((x - 0.2) / 0.3, (0.8 - x) / 0.3)) if 0.2 <= x <= 0.8 else 0.0

    def _membership_high(self, x: float) -> float:
        # تابع عضویت برای ریسک بالا (0.5 تا 1.0)
        return max(0.0, min(1.0, (x - 0.5) / 0.5)) if x >= 0.5 else 0.0

    def compute_brake_percentage(self, risk_score: float) -> float:
        """
        دریافت ضریب ریسک (0.0 تا 1.0) و محاسبه درصد کاهش سرعت
        خروجی: عددی بین 0.0 (بدون تغییر) تا 1.0 (توقف کامل)
        """
        # 1. فازی‌سازی (Fuzzification)
        u_low = self._membership_low(risk_score)
        u_med = self._membership_medium(risk_score)
        u_high = self._membership_high(risk_score)

        # 2. ارزیابی قوانین (Rule Evaluation)
        # قانون 1: اگر ریسک کم است، ترمز ضعیف (10%)
        brake_low = 0.10
        # قانون 2: اگر ریسک متوسط است، ترمز متوسط (40%)
        brake_med = 0.40
        # قانون 3: اگر ریسک بالا است، ترمز شدید (85%)
        brake_high = 0.85

        # 3. غیرفازی‌سازی (Defuzzification - میانگین وزن‌دار)
        numerator = (u_low * brake_low) + (u_med * brake_med) + (u_high * brake_high)
        denominator = u_low + u_med + u_high

        if denominator == 0:
            return 0.0

        final_brake = numerator / denominator
        return round(final_brake, 2)