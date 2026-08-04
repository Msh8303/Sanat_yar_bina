"""
Smart Conveyor Controller for Webots
Integrates YOLOv8, Fuzzy Logic, and Deep RL (PPO) for dynamic speed control.
"""

import sys
import os
import glob
import cv2
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from ultralytics import YOLO
from controller import Supervisor

try:
    from stable_baselines3 import PPO
except ImportError:
    print("Error: stable-baselines3 is not installed.")
    print("Please run: pip install stable-baselines3")
    sys.exit(1)

# ==========================================
# 1. Configs & Constants
# ==========================================
TIME_STEP = 32
MAX_SPEED = 1.0  
MIN_SPEED = 0.1  

END_X = 0.75           
LOOP_DISTANCE = 1.68   

PHYSICAL_SPEED_MULTIPLIER = 0.03 

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "worlds", "validation_images"))

YOLO_MODEL_PATH = os.path.join(CURRENT_DIR, "best.pt")

PPO_MODEL_PATH = os.path.join(CURRENT_DIR, "ppo_final_model.zip")

CLASSES = ["crazing", "inclusion", "patches", "pitted_surface", "rolled-in_scale", "scratches"]
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

RISK_FACTORS = {
    0: 1.0,  # crazing (High Risk)
    1: 0.9,  # inclusion
    2: 0.6,  # patches
    3: 0.8,  # pitted_surface
    4: 0.5,  # rolled-in_scale
    5: 0.2   # scratches (Low Risk)
}

# ==========================================
# 2. Fuzzy Controller Class
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
# 3. Helper Functions (Vision, Enhancement, Risk & PPO State)
# ==========================================
def apply_clahe(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    clahe_enhancer = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    cl = clahe_enhancer.apply(gray)
    
    return cv2.cvtColor(cl, cv2.COLOR_GRAY2BGR)

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
        
    mean_conf = sum(confidences) / len(confidences)
    return min(total_weighted_risk, 1.0), mean_conf

def extract_ppo_state(results, img_shape, current_speed, fuzzy_output):
   
    h, w = img_shape[:2]
    img_center_x = w / 2.0
    img_center_y = h / 2.0
    max_possible_dist = np.sqrt(img_center_x**2 + img_center_y**2)
    total_pixels = float(h * w)

    if len(results.boxes) == 0:
        return np.array([0.0, 0.0, current_speed, 0.0, 1.0, fuzzy_output], dtype=np.float32)

    confidences = []
    risk_scores = []
    center_distances = []

    for box in results.boxes:
        x1, y1, x2, y2 = map(float, box.xyxy[0])
        cls_id = int(box.cls)
        conf = float(box.conf)

        box_area = max(0.0, (x2 - x1)) * max(0.0, (y2 - y1))
        normalized_area = box_area / total_pixels
        risk_factor = RISK_FACTORS.get(cls_id, 0.5)
        risk_score = min(normalized_area * risk_factor * 10.0, 1.0)

        box_cx = (x1 + x2) / 2.0
        box_cy = (y1 + y2) / 2.0
        dist = np.sqrt((box_cx - img_center_x)**2 + (box_cy - img_center_y)**2)
        normalized_dist = dist / max_possible_dist if max_possible_dist > 0 else 1.0

        confidences.append(conf)
        risk_scores.append(risk_score)
        center_distances.append(normalized_dist)

    max_risk_score = float(max(risk_scores))
    mean_conf = float(np.mean(confidences))
    defect_count = min(float(len(results.boxes)) / 20.0, 1.0)
    closest_dist = float(min(center_distances))

    obs = np.array([
        max_risk_score,
        mean_conf,
        current_speed,
        defect_count,
        closest_dist,
        fuzzy_output
    ], dtype=np.float32)

    return obs

def draw_pred(img, results):
    for box in results.boxes:
        c = int(box.cls)
        conf = float(box.conf)
        xyxy = box.xyxy[0].cpu().numpy().astype(int)
        color = COLORS[c]
       
        cv2.rectangle(img, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 1)
       
        cv2.putText(img, f"{CLASSES[c]} {conf:.2f}", (xyxy[0], xyxy[1]-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    return img

# ==========================================
# 4. Main Webots Supervisor Script
# ==========================================
def main():
    supervisor = Supervisor()
    
    # 4.1 Load Models
    print("Loading YOLO model...")
    if not os.path.exists(YOLO_MODEL_PATH):
        print(f"Error: YOLO model not found at {YOLO_MODEL_PATH}")
        sys.exit(1)
    yolo_model = YOLO(YOLO_MODEL_PATH)
    
    print("Loading Deep RL (PPO) & Fuzzy Logic...")
    if not os.path.exists(PPO_MODEL_PATH):
        print(f"Error: PPO model not found at {PPO_MODEL_PATH}")
        sys.exit(1)
    
    fuzzy_brain = AdvancedFuzzyController()
    ppo_agent = PPO.load(PPO_MODEL_PATH)
    
    # 4.2 Initialize Images
    image_files = [f.replace('\\', '/') for f in glob.glob(os.path.join(IMAGES_DIR, "*.jpg"))]
    if not image_files:
        print(f"Error: No .jpg images found in '{IMAGES_DIR}' folder.")
        sys.exit(1)
    
    image_idx = 0
    def get_next_image():
        nonlocal image_idx
        img = image_files[image_idx % len(image_files)]
        image_idx += 1
        return img

    # 4.3 Initialize Webots Nodes
    camera = supervisor.getDevice('camera')
    if camera:
        camera.enable(TIME_STEP)
    else:
        print("Error: Camera not found!")
        sys.exit(1)
        
    plates = []
    tex_fields = []
    
    plate_names = ["STEEL_PLATE_1", "STEEL_PLATE_2", "STEEL_PLATE_3", "STEEL_PLATE_4"]
    tex_names = ["PLATE_TEX_1", "PLATE_TEX_2", "PLATE_TEX_3", "PLATE_TEX_4"]
    
    for p_name, t_name in zip(plate_names, tex_names):
        node = supervisor.getFromDef(p_name)
        tex_node = supervisor.getFromDef(t_name)
        
        if node and tex_node:
            trans_field = node.getField("translation")
            url_field = tex_node.getField("url")
            plates.append(trans_field)
            tex_fields.append(url_field)
            url_field.setMFString(0, get_next_image())

    current_speed = 0.55  
    step_counter = 0

    print("--- Starting Smart Inspection Conveyor (PPO Active) ---")

    # 4.4 Main Simulation Loop
    while supervisor.step(TIME_STEP) != -1:
       
        physical_step = current_speed * PHYSICAL_SPEED_MULTIPLIER 
        
        for i, trans_field in enumerate(plates):
            pos = trans_field.getSFVec3f()
            pos[0] += physical_step 
            
            if pos[0] > END_X:
                pos[0] -= LOOP_DISTANCE 
                tex_fields[i].setMFString(0, get_next_image())
                
            trans_field.setSFVec3f(pos)

        camera_data = camera.getImage()
        if camera_data:
            orig_width, orig_height = camera.getWidth(), camera.getHeight()
            img = np.frombuffer(camera_data, np.uint8).reshape((orig_height, orig_width, 4))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            
            frame = apply_clahe(frame)
            
            results = yolo_model(frame, conf=0.3, verbose=False)[0]
            
            # Logic: Fuzzy & Risk
            risk, conf = calculate_weighted_risk(results, frame.shape)
            fuzzy_suggestion = fuzzy_brain.compute(risk, conf)
            
            # Logic: PPO Network Inference
            obs = extract_ppo_state(results, frame.shape, current_speed, fuzzy_suggestion)
            action, _ = ppo_agent.predict(obs, deterministic=True)
            action = int(action)
            
            # Action Execution: 0 = Brake, 1 = Maintain, 2 = Accelerate
            if action == 0:
                speed_change = -0.1
            elif action == 1:
                speed_change = 0.0
            else:
                speed_change = 0.1
                
            current_speed = np.clip(current_speed + speed_change, MIN_SPEED, MAX_SPEED)
            
            # ==========================================
            # Visualizing Live Camera Output (Separated Dashboard)
            # ==========================================
            annotated = draw_pred(frame.copy(), results)
            
            frame_h, frame_w = annotated.shape[:2]
            
            dashboard = np.zeros((50, frame_w, 3), dtype=np.uint8)
            
            color_speed = (0, 255, 0) if current_speed > 0.55 else (0, 0, 255)
            cv2.putText(dashboard, f"SPD:{current_speed*100:.0f}%", (5, 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_speed, 1)
            
            cv2.putText(dashboard, f"RSK:{risk:.2f}", (130, 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            fuz_text = "BRK" if fuzzy_suggestion < -0.1 else "ACC" if fuzzy_suggestion > 0.1 else "HLD"
            cv2.putText(dashboard, f"Fuz:{fuz_text}", (5, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
            ppo_action_name = "BRK" if action == 0 else "HLD" if action == 1 else "ACC"
            color_act = (0, 255, 255) if ppo_action_name == fuz_text else (0, 0, 255)
            cv2.putText(dashboard, f"PPO:{ppo_action_name}", (130, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_act, 1)
            
            final_display = np.vstack((dashboard, annotated))
            
            cv2.imshow("Smart Conveyor - Inspection Camera", final_display)

        cv2.waitKey(1)
        step_counter += 1

if __name__ == '__main__':
    main()