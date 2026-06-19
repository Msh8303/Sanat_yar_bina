from controllers.fuzzy import FuzzyController
from controllers.rl import RLAgent

class HybridController:
    def __init__(self, rl_model_path: str = "models/hybrid_rl.pkl"):
        self.fuzzy = FuzzyController()
        self.rl = RLAgent(model_path=rl_model_path)
        
        # سرعت پایه خط تولید (مثلا 100 متر بر دقیقه یا درصد)
        self.max_speed = 100.0

    def compute_action(self, target_data: dict, current_speed: float) -> dict:
        """
        ترکیب خروجی‌های Fuzzy و RL برای تولید فرمان نهایی.
        target_data خروجیِ کلاس TargetSelector است.
        """
        if not target_data:
            # اگر خط تولید پاک است، تلاش برای بازگشت به سرعت ماکزیمم
            speed_after = min(current_speed + 5.0, self.max_speed)
            return {
                "fuzzy_output": 0.0,
                "rl_output": 0.0,
                "speed_before": current_speed,
                "speed_after": speed_after,
                "selected_action": "MAINTAIN/ACCELERATE"
            }

        risk_score = target_data["risk_score"]

        # 1. محاسبه پیشنهاد فازی (درصد ترمز)
        brake_percent = self.fuzzy.compute_brake_percentage(risk_score)
        fuzzy_proposed_speed = current_speed * (1.0 - brake_percent)

        # 2. محاسبه پیشنهاد یادگیری تقویتی (تغییر سرعت)
        rl_speed_change = self.rl.get_action(risk_score, current_speed)
        rl_proposed_speed = current_speed + rl_speed_change

        # 3. منطق ترکیب (Fusion Logic)
        # سیستم فازی همیشه ناظر ایمنی است. اگر فازی تشخیص توقف/ترمز شدید بدهد، RL را لغو می‌کند.
        if risk_score > 0.85:
            # حالت بحرانی (Critical Override)
            final_speed = fuzzy_proposed_speed
            action_label = "EMERGENCY_BRAKE (Fuzzy Override)"
        else:
            # حالت نرمال: میانگین‌گیری یا اعتماد به RL برای حرکت نرم‌تر نوار نقاله
            final_speed = (fuzzy_proposed_speed * 0.3) + (rl_proposed_speed * 0.7)
            action_label = "HYBRID_ADJUST"

        # جلوگیری از توقف کامل مگر در شرایط فوق‌بحرانی (برای تحقق Zero-Downtime)
        final_speed = max(final_speed, 10.0) # حداقل سرعت 10

        return {
            "fuzzy_output": fuzzy_proposed_speed,
            "rl_output": rl_proposed_speed,
            "speed_before": current_speed,
            "speed_after": round(final_speed, 1),
            "selected_action": action_label
        }