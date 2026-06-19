import pickle
import numpy as np
from pathlib import Path

class RLAgent:
    def __init__(self, model_path: str = "models/hybrid_rl.pkl"):
        self.model_path = Path(model_path)
        
        # تعریف اکشن‌های در دسترس (تغییرات سرعت نوار نقاله به درصد)
        self.actions = [-20.0, -10.0, 0.0, 10.0]
        
        # بارگذاری ایمن مدل
        self.q_table = self._load_model()

    def _load_model(self) -> dict:
        """بارگذاری Q-Table از فایل پیکِل. اگر ساختار قدیمی/ناسازگار بود، جدول خالی می‌سازد."""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    
                    # بررسی اینکه آیا ساختار داده یک دیکشنری استاندارد (مثل نسخه جدید ما) است یا خیر
                    if isinstance(data, dict):
                        return data
                    else:
                        print("\n[!] هشدار: فرمت فایل PKL قدیمی یا ناسازگار است (آرایه نامپای یافت شد).")
                        print("[!] سیستم یک Q-Table جدید و خالی برای ادامه کار ایجاد کرد.\n")
                        return {}
            except Exception as e:
                print(f"[!] خطا در خواندن فایل PKL: {e}")
                return {}
                
        return {} # برگرداندن جدول خالی در صورت عدم وجود فایل

    def _discretize_state(self, risk_score: float, current_speed: float) -> tuple:
        """
        تبدیل مقادیر پیوسته به حالت‌های گسسته (State) برای Q-Table
        """
        discrete_risk = int(np.clip(risk_score * 10, 0, 9))
        discrete_speed = int(np.clip(current_speed // 10, 0, 10))
        return (discrete_risk, discrete_speed)

    def get_action(self, risk_score: float, current_speed: float) -> float:
        """
        استخراج بهترین اکشن (تغییر سرعت) بر اساس وضعیت فعلی
        """
        state = self._discretize_state(risk_score, current_speed)
        
        # اگر این وضعیت قبلا دیده شده و در دیکشنری وجود دارد
        if state in self.q_table:
            action_index = np.argmax(self.q_table[state])
            return self.actions[action_index]
        
        # اگر وضعیت جدید است، رویکرد ایمن (کاهش ملایم) پیش‌فرض است
        return -10.0