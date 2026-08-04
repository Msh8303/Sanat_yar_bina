"""
Smart Conveyor Controller for Webots
Integrates YOLOv8, Fuzzy Logic, and RL Q-Table for dynamic speed control.
Optimized for 256x256 Vision (Native Webots Camera Resolution) with 90-deg rotation fix.
"""

import sys
import os
import glob
import pickle
import cv2
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from ultralytics import YOLO
from controller import Supervisor

# ==========================================
# 1. Configs & Constants
# ==========================================
TIME_STEP = 32
MAX_SPEED = 0.4   
MIN_SPEED = 0.1  
START_X = -1.25  
END_X = 1.25     

PHYSICAL_SPEED_MULTIPLIER = 0.03 

IMG_WIDTH = 256
IMG_HEIGHT = 256
CAMERA_Z = 0.96
PLATE_SURFACE_Z = 0.520

DZ = CAMERA_Z - PLATE_SURFACE_Z
VISIBLE_WIDTH = 2.0 * DZ * 0.41421356237
METERS_PER_PIXEL = VISIBLE_WIDTH / float(IMG_WIDTH)

CAMERA_X = -0.3
CAMERA_Y = 0.06
PEN_X = 0.0
PEN_BASE_Y = 0.0
PEN_OFFSET_X = PEN_X - CAMERA_X

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(CURRENT_DIR, "validation_images")

YOLO_MODEL_PATH = os.path.join(CURRENT_DIR, "best.pt")
RL_MODEL_PATH = os.path.join(CURRENT_DIR, "hybrid_rl_model.pkl")

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
# 3. Hybrid RL Agent Class
# ==========================================
class HybridRLAgent:
    def __init__(self, model_path):
        with open(model_path, 'rb') as f:
            self.q_table = pickle.load(f)
        self.actions = {0: -0.1, 1: 0.0, 2: 0.1}

    def get_state(self, fuzzy_output, current_speed):
        if fuzzy_output < -0.1: fuzzy_state = 0
        elif fuzzy_output > 0.1: fuzzy_state = 2
        else: fuzzy_state = 1

        if current_speed < 0.3: speed_state = 0
        elif current_speed < 0.7: speed_state = 1
        else: speed_state = 2

        return (fuzzy_state, speed_state)

    def choose_action(self, state):
        action_idx = np.argmax(self.q_table[state])
        return self.actions[action_idx], action_idx

# ==========================================
# 4. Helper Functions (Vision & Risk)
# ==========================================
def calculate_weighted_risk(results, img_shape):
    h, w = img_shape[:2]
    total_weighted_risk = 0.0
    confidences = []
    
    if len(results.boxes) == 0: 
        return 0.0, 1.0
        
    for box in results.boxes:
        xyxy = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = map(int, xyxy)
        normalized_area = ((x2 - x1) * (y2 - y1)) / float(h * w)
        cls_id = int(box.cls)
        total_weighted_risk += (normalized_area * RISK_FACTORS.get(cls_id, 0.5)) * 10.0
        confidences.append(float(box.conf))
        
    mean_conf = sum(confidences) / len(confidences) if confidences else 1.0
    return min(total_weighted_risk, 1.0), mean_conf

def draw_pred(img, results):
    for box in results.boxes:
        c = int(box.cls)
        conf = float(box.conf)
        xyxy = box.xyxy[0].cpu().numpy().astype(int)
        color = COLORS[c] if c < len(COLORS) else (255, 255, 255)
        
        cv2.rectangle(img, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 1)
        cv2.putText(img, f"{CLASSES[c]} {conf:.2f}", (xyxy[0], max(xyxy[1]-5, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    return img

def compute_marking_parameters(bbox_u, bbox_v, current_speed, physical_multiplier, time_step_ms, current_arm_y):
    offset_x_m = (bbox_u - (IMG_WIDTH / 2.0)) * METERS_PER_PIXEL
    offset_y_m = (bbox_v - (IMG_HEIGHT / 2.0)) * METERS_PER_PIXEL
    
    defect_world_y = CAMERA_Y + offset_y_m
    target_joint_y = defect_world_y - PEN_BASE_Y
    
    dist_x = PEN_OFFSET_X - offset_x_m
    v_conveyor_ms = (current_speed * physical_multiplier) / (time_step_ms / 1000.0)
    
    if v_conveyor_ms <= 0.0001:
        time_to_reach = 0.001
    else:
        time_to_reach = dist_x / v_conveyor_ms
        
    y_distance = target_joint_y - current_arm_y
    required_velocity = y_distance / max(time_to_reach, 0.001)
    
    return target_joint_y, required_velocity, time_to_reach, offset_x_m

# ==========================================
# 5. Main Webots Supervisor Script
# ==========================================
def main():
    supervisor = Supervisor()
    
    # 5.1 Load Models
    print("Loading YOLO model...")
    if not os.path.exists(YOLO_MODEL_PATH):
        print(f"Error: YOLO model not found at {YOLO_MODEL_PATH}")
        sys.exit(1)
    yolo_model = YOLO(YOLO_MODEL_PATH)
    
    print("Loading RL & Fuzzy Logic...")
    if not os.path.exists(RL_MODEL_PATH):
        print(f"Error: RL model not found at {RL_MODEL_PATH}")
        sys.exit(1)
    fuzzy_brain = AdvancedFuzzyController()
    rl_agent = HybridRLAgent(RL_MODEL_PATH)
    
    # 5.2 Initialize Images
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

    # 5.3 Initialize Webots Nodes
    camera = supervisor.getDevice('camera')
    if camera:
        camera.enable(TIME_STEP)
    else:
        print("Error: Camera not found!")
        sys.exit(1)

    marker_motor = supervisor.getDevice("marker_motor")
    marker_motor.setPosition(float('inf'))
    marker_motor.setVelocity(0.0)

    pen = supervisor.getDevice("pen")

    marker_position_sensor = marker_motor.getPositionSensor()
    if marker_position_sensor is None:
        marker_position_sensor = supervisor.getDevice("marker_motor_sensor")
    if marker_position_sensor is not None:
        marker_position_sensor.enable(TIME_STEP)

    marking_state = "IDLE"
    target_y_pos = 0.0
    target_x_defect = 0.0
    marking_timer = 0
    
    defect_detected_this_frame = False
    bbox_center_u = 0.0
    bbox_center_v = 0.0
    
    plates = []
    tex_fields = []
    plate_image_paths = []
    
    plate_names = ["STEEL_PLATE_1", "STEEL_PLATE_2", "STEEL_PLATE_3"]
    tex_names = ["PLATE_TEX_1", "PLATE_TEX_2", "PLATE_TEX_3"]
    
    for p_name, t_name in zip(plate_names, tex_names):
        node = supervisor.getFromDef(p_name)
        tex_node = supervisor.getFromDef(t_name)
        if node and tex_node:
            trans_field = node.getField("translation")
            url_field = tex_node.getField("url")
            plates.append(trans_field)
            tex_fields.append(url_field)
            img_p = get_next_image()
            url_field.setMFString(0, img_p)
            plate_image_paths.append(img_p)

    current_speed = 0.25  
    step_counter = 0
    
    print("--- Starting Smart Inspection Conveyor ---")

    # 5.4 Main Simulation Loop
    while supervisor.step(TIME_STEP) != -1:
        physical_step = current_speed * PHYSICAL_SPEED_MULTIPLIER 
        
        for i, trans_field in enumerate(plates):
            pos = trans_field.getSFVec3f()
            pos[0] += physical_step 
            if pos[0] > END_X:
                pos[0] = START_X 
                img_p = get_next_image()
                tex_fields[i].setMFString(0, img_p)
                plate_image_paths[i] = img_p
            trans_field.setSFVec3f(pos)

        current_arm_y = marker_position_sensor.getValue() if marker_position_sensor else 0.0

        if defect_detected_this_frame and marking_state == "IDLE":
            target_y_pos, req_vel, t_reach, def_x_off = compute_marking_parameters(
                bbox_center_u, bbox_center_v, current_speed, PHYSICAL_SPEED_MULTIPLIER, TIME_STEP, current_arm_y
            )
            marker_motor.setVelocity(abs(req_vel))
            marker_motor.setPosition(target_y_pos)
            marking_state = "TRACKING"
            target_x_defect = CAMERA_X + def_x_off
            defect_detected_this_frame = False

        if marking_state == "TRACKING":
            target_x_defect += physical_step
            if abs(target_x_defect - PEN_X) <= physical_step:
                pen.write(True)
                marking_timer = 5
                marking_state = "MARKING"

        elif marking_state == "MARKING":
            marking_timer -= 1
            if marking_timer <= 0:
                pen.write(False)
                marker_motor.setVelocity(0.5)
                marker_motor.setPosition(0.0)
                marking_state = "RETRACTING"

        elif marking_state == "RETRACTING":
            if abs(current_arm_y) < 0.005:
                marking_state = "IDLE"

        if step_counter % 8 == 0:
            camera_data = camera.getImage()
            if camera_data:
                orig_width, orig_height = camera.getWidth(), camera.getHeight()
                img = np.frombuffer(camera_data, np.uint8).reshape((orig_height, orig_width, 4))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                
                results = yolo_model(frame, conf=0.25, verbose=False)[0]
                defect_detected_this_frame = False
                if len(results.boxes) > 0:
                    box = results.boxes[0]
                    xyxy = box.xyxy[0].cpu().numpy()
                    bbox_center_u = float(xyxy[0] + xyxy[2]) / 2.0
                    bbox_center_v = float(xyxy[1] + xyxy[3]) / 2.0
                    defect_detected_this_frame = True

                # Logic
                risk, conf = calculate_weighted_risk(results, frame.shape)
                fuzzy_suggestion = fuzzy_brain.compute(risk, conf)
                state = rl_agent.get_state(fuzzy_suggestion, current_speed)
                speed_change, action_idx = rl_agent.choose_action(state)
                
                if marking_state == "IDLE":
                    current_speed = np.clip(current_speed + speed_change, MIN_SPEED, MAX_SPEED)

                closest_idx = min(range(len(plates)), key=lambda i: abs(plates[i].getSFVec3f()[0] - CAMERA_X))
                current_img_path = plate_image_paths[closest_idx]
                base_filename = os.path.basename(current_img_path)
                name_no_ext = os.path.splitext(base_filename)[0]
                gt_label = name_no_ext.split('_')[-1] if '_' in name_no_ext else name_no_ext

                # ==========================================
                # Visualizing Live Camera Output (Optimized for 256x256)
                # ==========================================
                annotated = draw_pred(frame.copy(), results)
                cv2.rectangle(annotated, (0, 0), (orig_width, 65), (0, 0, 0), -1)
                
                cv2.putText(annotated, f"GT: {gt_label}", (5, 18), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
                
                color_speed = (0, 255, 0) if current_speed > 0.25 else (0, 0, 255)
                cv2.putText(annotated, f"SPD:{current_speed*100:.0f}%", (5, 36), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_speed, 1)
                cv2.putText(annotated, f"RSK:{risk:.2f}", (130, 36), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                
                fuz_text = "BRK" if fuzzy_suggestion < -0.1 else "ACC" if fuzzy_suggestion > 0.1 else "HLD"
                cv2.putText(annotated, f"Fuz:{fuz_text}", (5, 54), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                
                action_name = "BRK" if action_idx == 0 else "HLD" if action_idx == 1 else "ACC"
                color_act = (0, 255, 255) if action_name == fuz_text else (0, 0, 255)
                cv2.putText(annotated, f"RL:{action_name}", (130, 54), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_act, 1)
                
                cv2.imshow("Smart Conveyor - Inspection Camera", annotated)

        cv2.waitKey(1)
        step_counter += 1

if __name__ == '__main__':
    main()