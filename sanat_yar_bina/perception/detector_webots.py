import os
from ultralytics import YOLO

class WebotsDefectDetector:
    def __init__(self, model_path=None, conf_thresh=0.25):
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = r"C:\Users\MSH8303\Sanat_yar_bina-1\simulation\controllers\smart_conveyor\best.pt"
            
        print(f"[*] Loading Webots YOLO Model from: {model_path}")
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh

    def detect(self, frame):
        # اجرای یولو روی فریم چرخیده شده‌ی Webots
        results = self.model(frame, conf=self.conf_thresh, verbose=False)[0]
        return results