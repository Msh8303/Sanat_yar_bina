import cv2
import time
from perception.detector import DefectDetector
from perception.selector import TargetSelector
from controllers.fuzzy import FuzzyController
from controllers.rl import RLAgent
from controllers.hybrid import HybridController
import cv2
import pickle
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from ultralytics import YOLO
# ==========================================
# 🔧 File Path Configurations (To be filled by you)
# ==========================================
VIDEO_PATH = r"C:\Users\MSH8303\Sanat_yar_bina-1\sanat_yar_bina\data\test_video.mp4"       # مثال: "data/test_video.mp4"
YOLO_MODEL_PATH = r"C:\Users\MSH8303\Sanat_yar_bina-1\sanat_yar_bina\models\best.pt"  # مثال: "models/best.pt"
RL_MODEL_PATH = r"C:\Users\MSH8303\Sanat_yar_bina-1\sanat_yar_bina\models\hybrid_rl.pkl"    # مثال: "models/hybrid_rl.pkl"
# ==========================================
# 🧠 Original Advanced Fuzzy Controller
# ==========================================
class AdvancedFuzzyController:
    def __init__(self):
        self.risk_score = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'risk_score')
        self.confidence = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'confidence')
        self.speed_change = ctrl.Consequent(np.arange(-1, 1.01, 0.01), 'speed_change')

        self.risk_score['Low']    = fuzz.gaussmf(self.risk_score.universe, 0, 0.15)
        self.risk_score['Medium'] = fuzz.gaussmf(self.risk_score.universe, 0.5, 0.15)
        self.risk_score['High']   = fuzz.gaussmf(self.risk_score.universe, 1, 0.15)

        self.confidence['Low']    = fuzz.gaussmf(self.confidence.universe, 0, 0.15)
        self.confidence['Medium'] = fuzz.gaussmf(self.confidence.universe, 0.5, 0.15)
        self.confidence['High']   = fuzz.gaussmf(self.confidence.universe, 1, 0.15)

        self.speed_change['Brake']      = fuzz.gaussmf(self.speed_change.universe, -1, 0.25)
        self.speed_change['Maintain']   = fuzz.gaussmf(self.speed_change.universe, 0, 0.15)
        self.speed_change['Accelerate'] = fuzz.gaussmf(self.speed_change.universe, 1, 0.25)

        self.rules = [
            ctrl.Rule(self.risk_score['Low'] & self.confidence['High'], self.speed_change['Accelerate']),
            ctrl.Rule(self.risk_score['Low'] & self.confidence['Medium'], self.speed_change['Accelerate']),
            ctrl.Rule(self.risk_score['Low'] & self.confidence['Low'], self.speed_change['Maintain']),
            ctrl.Rule(self.risk_score['Medium'] & self.confidence['High'], self.speed_change['Brake']),
            ctrl.Rule(self.risk_score['Medium'] & self.confidence['Medium'], self.speed_change['Maintain']),
            ctrl.Rule(self.risk_score['Medium'] & self.confidence['Low'], self.speed_change['Maintain']),
            ctrl.Rule(self.risk_score['High'] & self.confidence['High'], self.speed_change['Brake']),
            ctrl.Rule(self.risk_score['High'] & self.confidence['Medium'], self.speed_change['Brake']),
            ctrl.Rule(self.risk_score['High'] & self.confidence['Low'], self.speed_change['Brake']),
        ]

        self.control_system = ctrl.ControlSystem(self.rules)
        self.simulation = ctrl.ControlSystemSimulation(self.control_system)

    def compute(self, risk_val, conf_val):
        self.simulation.input['risk_score'] = np.clip(risk_val, 0, 1)
        self.simulation.input['confidence'] = np.clip(conf_val, 0, 1)
        self.simulation.compute()
        return self.simulation.output['speed_change']

# ==========================================
# 🤖 Pure RL Agent (Inference Mode)
# ==========================================
class InferenceRLAgent:
    def __init__(self, model_path):
        self.actions = {0: -0.1, 1: 0.0, 2: 0.1}
        self.q_table = self._load_model(model_path)

    def _load_model(self, model_path):
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, np.ndarray) and data.shape == (3, 3, 3):
                    print("[+] Original Q-Table loaded successfully.")
                    return data
                else:
                    raise ValueError("Invalid Q-Table shape.")
        except Exception as e:
            print(f"[!] Error loading model: {e}")
            return np.zeros((3, 3, 3))

    def get_state(self, fuzzy_output, current_speed):
        # Match training discretization perfectly
        if fuzzy_output < -0.1: fuzzy_state = 0
        elif fuzzy_output > 0.1: fuzzy_state = 2
        else: fuzzy_state = 1

        if current_speed < 0.3: speed_state = 0
        elif current_speed < 0.7: speed_state = 1
        else: speed_state = 2

        return (fuzzy_state, speed_state)

    def choose_best_action(self, state):
        # Epsilon is 0 during inference (Always exploit)
        action_idx = np.argmax(self.q_table[state])
        return action_idx, self.actions[action_idx]

# ==========================================
# ⚙️ Helper Functions (From Training)
# ==========================================
RISK_FACTORS = {0: 1.0, 1: 0.9, 2: 0.6, 3: 0.8, 4: 0.5, 5: 0.2}

def calculate_weighted_risk(results, img_shape):
    h, w = img_shape[:2]
    total_weighted_risk = 0
    confidences = []
    
    if len(results.boxes) == 0: 
        return 0.0, 1.0
        
    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        normalized_area = ((x2 - x1) * (y2 - y1)) / (h * w)
        cls_id = int(box.cls)
        total_weighted_risk += (normalized_area * RISK_FACTORS.get(cls_id, 0.5)) * 10
        confidences.append(float(box.conf))
        
    return min(total_weighted_risk, 1.0), sum(confidences) / len(confidences)

def get_fuzzy_label(fuzzy_val):
    if fuzzy_val < -0.1: return "BRAKE (-)"
    elif fuzzy_val > 0.1: return "ACCELERATE (+)"
    return "MAINTAIN (=)"

def get_rl_label(action_val):
    if action_val < 0: return "DECELERATE (-10%)"
    elif action_val > 0: return "ACCELERATE (+10%)"
    return "HOLD SPEED (0%)"

# ==========================================
# 🚀 Main Test Execution
# ==========================================
def run_pure_rl_test():
    print("[*] Initializing Vision and Controllers...")
    model = YOLO(YOLO_MODEL_PATH)
    fuzzy_brain = AdvancedFuzzyController()
    rl_agent = InferenceRLAgent(RL_MODEL_PATH)

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("❌ Error: Video not found!")
        return

    # Start speed at 0.5 (50%) matching the training script
    current_speed = 0.5 
    frame_count = 0

    print("\n[+] Starting PURE RL control test...")
    print("=" * 70)

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Process every 5th frame for readable logs
        if frame_count % 5 == 0:
            results = model(frame, conf=0.25, verbose=False)[0]
            
            # 1. Vision Analysis
            risk, conf = calculate_weighted_risk(results, frame.shape)
            
            if len(results.boxes) > 0:
                print(f"\n🔴 Frame {frame_count} | Defects Detected: {len(results.boxes)} | Risk: {risk:.2f} | Conf: {conf:.2f}")
                
                # 2. Fuzzy Suggestion (Observer ONLY)
                fuzzy_suggestion = fuzzy_brain.compute(risk, conf)
                
                # 3. RL Final Decision (The Real Controller)
                state = rl_agent.get_state(fuzzy_suggestion, current_speed)
                action_idx, speed_change = rl_agent.choose_best_action(state)
                
                # 4. Apply Speed Change
                current_speed = np.clip(current_speed + speed_change, 0.1, 1.0)
                
                # 5. Logging the comparison
                print(f"   👁️‍🗨️ [Fuzzy Thinks]  Value: {fuzzy_suggestion:+.2f} -> {get_fuzzy_label(fuzzy_suggestion)}")
                print(f"   🧠 [RL Decides]    State: {state} | Change: {speed_change:+.1f} -> {get_rl_label(speed_change)}")
                print(f"   🏁 [Final Speed]   Set to: {current_speed * 100:.0f}%")
                print("-" * 70)
            
            else:
                # Normal condition recovery
                current_speed = np.clip(current_speed + 0.1, 0.1, 1.0)

        cv2.imshow("Pure RL Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if not VIDEO_PATH or not YOLO_MODEL_PATH:
        print("⚠️ Please provide paths for VIDEO, YOLO, and RL models.")
    else:
        run_pure_rl_test()