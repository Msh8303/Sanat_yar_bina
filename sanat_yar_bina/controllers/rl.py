import pickle
import numpy as np
from pathlib import Path

class InferenceRLAgent:
    def __init__(self, model_path: str = "models/hybrid_rl_model.pkl"):
        self.model_path = Path(model_path)
        self.actions = {0: -0.1, 1: 0.0, 2: 0.1}
        self.q_table = self._load_model()

    def _load_model(self):
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, np.ndarray) and data.shape == (3, 3, 3):
                        return data
                    else:
                        print(f"[!] Warning: Invalid Q-Table format in {self.model_path}. Using default zero-table.")
            except Exception as e:
                print(f"[!] Error loading RL model PKL from {self.model_path}: {e}")
        else:
            print(f"[!] Notice: RL model file not found at {self.model_path}. Initializing empty Q-table.")
        return np.zeros((3, 3, 3))

    def get_state(self, fuzzy_output, current_speed):
        try:
            f_val = float(fuzzy_output)
            s_val = float(current_speed)
        except (TypeError, ValueError):
            f_val, s_val = 0.0, 0.5

        if f_val < -0.1: fuzzy_state = 0
        elif f_val > 0.1: fuzzy_state = 2
        else: fuzzy_state = 1

        if s_val < 0.3: speed_state = 0
        elif s_val < 0.7: speed_state = 1
        else: speed_state = 2

        return (fuzzy_state, speed_state)

    def choose_best_action(self, state):
        try:
            action_idx = int(np.argmax(self.q_table[state]))
            return action_idx, self.actions.get(action_idx, 0.0)
        except Exception as e:
            print(f"[!] Error choosing action in RL agent: {e}")
            return 1, 0.0  # پیش‌فرض: بدون تغییر سرعت (Maintain)
        
    def get_label(self, value):
        try:
            val = float(value)
        except (TypeError, ValueError):
            return "HOLD (0%)"

        if val < 0: return "DECELERATE (-10%)"
        elif val > 0: return "ACCELERATE (+10%)"
        return "HOLD (0%)"