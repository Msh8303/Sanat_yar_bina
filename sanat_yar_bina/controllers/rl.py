import pickle
import numpy as np
from pathlib import Path

class InferenceRLAgent:
    def __init__(self, model_path: str = "models/hybrid_rl_model.pkl"):
        self.model_path = Path(model_path)
        self.actions = {0: -0.1, 1: 0.0, 2: 0.1} # درصد تغییرات (منهای 10، صفر، مثبت 10)
        self.q_table = self._load_model()

    def _load_model(self):
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, np.ndarray) and data.shape == (3, 3, 3):
                        return data
                    else:
                        print("[!] Warning: Invalid Q-Table format.")
            except Exception as e:
                print(f"[!] Error loading PKL: {e}")
        return np.zeros((3, 3, 3))

    def get_state(self, fuzzy_output, current_speed):
        # مپ کردن به 3 حالت گسسته دقیقا مشابه زمان آموزش
        if fuzzy_output < -0.1: fuzzy_state = 0
        elif fuzzy_output > 0.1: fuzzy_state = 2
        else: fuzzy_state = 1

        if current_speed < 0.3: speed_state = 0
        elif current_speed < 0.7: speed_state = 1
        else: speed_state = 2

        return (fuzzy_state, speed_state)

    def choose_best_action(self, state):
        # همیشه بهترین اکشن را انتخاب می‌کند (Epsilon = 0)
        action_idx = np.argmax(self.q_table[state])
        return action_idx, self.actions[action_idx]
        
    def get_label(self, value):
        if value < 0: return "DECELERATE (-10%)"
        elif value > 0: return "ACCELERATE (+10%)"
        return "HOLD (0%)"