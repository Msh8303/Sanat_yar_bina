import sys
import os
import glob
import cv2
import numpy as np
import zmq
from controller import Supervisor

TIME_STEP = 32
START_X = -1.25  
END_X = 1.25     
PHYSICAL_SPEED_MULTIPLIER = 0.01
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(CURRENT_DIR, "validation_images")

def main():
    supervisor = Supervisor()
    context = zmq.Context()
    
    # فرستنده تصویر به داشبورد
    vid_socket = context.socket(zmq.PUB)
    vid_socket.bind("tcp://127.0.0.1:5555")
    
    # گیرنده فرمان سرعت از داشبورد
    cmd_socket = context.socket(zmq.SUB)
    cmd_socket.bind("tcp://127.0.0.1:5556")
    cmd_socket.setsockopt_string(zmq.SUBSCRIBE, "")

    image_files = [f.replace('\\', '/') for f in glob.glob(os.path.join(IMAGES_DIR, "*.jpg"))]
    if not image_files: sys.exit(1)
    
    image_idx = 0
    def get_next_image():
        nonlocal image_idx
        img = image_files[image_idx % len(image_files)]
        image_idx += 1
        return img

    camera = supervisor.getDevice('camera')
    if camera: camera.enable(TIME_STEP)
        
    plates = []
    tex_fields = []
    plate_names = ["STEEL_PLATE_1", "STEEL_PLATE_2", "STEEL_PLATE_3"]
    tex_names = ["PLATE_TEX_1", "PLATE_TEX_2", "PLATE_TEX_3"]
    
    for p_name, t_name in zip(plate_names, tex_names):
        node = supervisor.getFromDef(p_name)
        tex_node = supervisor.getFromDef(t_name)
        if node and tex_node:
            plates.append(node.getField("translation"))
            url_f = tex_node.getField("url")
            tex_fields.append(url_f)
            url_f.setMFString(0, get_next_image())

    current_speed = 0.5 
    step_counter = 0

    while supervisor.step(TIME_STEP) != -1:
        # دریافت بلادرنگ سرعت از داشبورد
        try:
            while True:  
                msg = cmd_socket.recv_string(flags=zmq.NOBLOCK)
                if msg.startswith("SPEED:"):
                    current_speed = float(msg.split(":")[1])
        except zmq.Again: pass 

        physical_step = current_speed * PHYSICAL_SPEED_MULTIPLIER 
        
        for i, trans_field in enumerate(plates):
            pos = trans_field.getSFVec3f()
            pos[0] += physical_step 
            if pos[0] > END_X:
                pos[0] = START_X 
                tex_fields[i].setMFString(0, get_next_image())
            trans_field.setSFVec3f(pos)

        # استخراج و ارسال تصویر (فقط چرخش 90 درجه، بدون پردازش یولو)
        if step_counter % 8 == 0:  
            camera_data = camera.getImage()
            if camera_data:
                orig_width, orig_height = camera.getWidth(), camera.getHeight()
                img = np.frombuffer(camera_data, np.uint8).reshape((orig_height, orig_width, 4))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                _, encoded_img = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                vid_socket.send(encoded_img.tobytes())

        step_counter += 1

if __name__ == '__main__':
    main()