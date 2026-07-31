import os
from ultralytics import YOLO
import cv2
class WebotsDefectDetector:
    def __init__(self, model_path=None, conf_thresh=0.25):
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "..", "simulation", "controllers", "smart_conveyor", "best.pt")
        print(f"[*] Loading Webots YOLO Model from: {model_path}")
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh

    def apply_clahe(self, img):
        """اعمال فیلتر کنتراست روی تصویری که از وباتز می‌آید"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe_enhancer = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        cl = clahe_enhancer.apply(gray)
        return cv2.cvtColor(cl, cv2.COLOR_GRAY2BGR)

    def detect(self, frame):
        # ۱. ابتدا بهبود کیفیت تصویر
        enhanced_frame = self.apply_clahe(frame)
        
        # ۲. سپس اجرای یولو روی فریم بهبود یافته
        results = self.model(enhanced_frame, conf=self.conf_thresh, verbose=False)[0]
        return results