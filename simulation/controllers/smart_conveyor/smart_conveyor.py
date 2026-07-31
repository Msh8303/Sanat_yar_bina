"""
Smart Conveyor Controller for Webots (Streamer Mode)
Optimized for streaming Native Webots Camera (256x256) to SIB Dashboard via ZeroMQ.
"""

import sys
import os
import glob
import cv2
import numpy as np
import zmq
from controller import Supervisor

# ==========================================
# 1. Configs & Constants
# ==========================================
TIME_STEP = 32
START_X = -1.25  
END_X = 1.25     
PHYSICAL_SPEED_MULTIPLIER = 0.03 

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(CURRENT_DIR, "validation_images")

# ==========================================
# 2. Main Webots Supervisor Script
# ==========================================
def main():
    supervisor = Supervisor()
    
    # --- ZMQ SETUP (ارسال تصویر به داشبورد صیب) ---
    print("[*] Starting ZeroMQ Video Server on tcp://127.0.0.1:5555...")
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://127.0.0.1:5555")
    
    # --- Initialize Images ---
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

    # --- Initialize Webots Nodes ---
    camera = supervisor.getDevice('camera')
    if camera:
        camera.enable(TIME_STEP)
    else:
        print("Error: Camera not found!")
        sys.exit(1)
        
    plates = []
    tex_fields = []
    
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
            url_field.setMFString(0, get_next_image())

    current_speed = 0.5  # سرعت پیش‌فرض برای چرخش نوار نقاله در شبیه‌ساز
    step_counter = 0

    print("--- Webots Conveyor Streamer is Running ---")

    # --- Main Simulation Loop ---
    while supervisor.step(TIME_STEP) != -1:
        
        # 1. محاسبه فیزیک و حرکت پلیت‌ها
        physical_step = current_speed * PHYSICAL_SPEED_MULTIPLIER 
        
        for i, trans_field in enumerate(plates):
            pos = trans_field.getSFVec3f()
            pos[0] += physical_step 
            
            if pos[0] > END_X:
                pos[0] = START_X 
                tex_fields[i].setMFString(0, get_next_image())
                
            trans_field.setSFVec3f(pos)

        # 2. استخراج تصویر و ارسال از طریق شبکه (ZMQ)
        if step_counter % 2 == 0:  # استخراج فریم (جلوگیری از ارسال بیش از حد)
            camera_data = camera.getImage()
            if camera_data:
                orig_width, orig_height = camera.getWidth(), camera.getHeight()
                img = np.frombuffer(camera_data, np.uint8).reshape((orig_height, orig_width, 4))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # اعمال چرخش 90 درجه
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                
                # فشرده‌سازی فریم با کیفیت ۸۰ درصد برای ارسال روان روی شبکه
                _, encoded_img = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                
                # ارسال فریم به گیرنده در main.py
                socket.send(encoded_img.tobytes())

        step_counter += 1

if __name__ == '__main__':
    main()