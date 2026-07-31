import os
from ultralytics import YOLO
import cv2
class WebotsDefectDetector:
    def __init__(self, model_path=None, conf_thresh=0.25):
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "..", "simulation", "controllers", "smart_conveyor", "best.pt")
        print(f"[*] Loading Webots YOLO Model from: {model_path}")
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            print(f"[!] Critical Error: Failed to load Webots YOLO model. Error: {e}")
            self.model = None
            
        self.conf_thresh = conf_thresh

    def apply_clahe(self, img):
        """اعمال فیلتر کنتراست روی تصویری که از وباتز می‌آید"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe_enhancer = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            cl = clahe_enhancer.apply(gray)
            return cv2.cvtColor(cl, cv2.COLOR_GRAY2BGR)
        except Exception as e:
            print(f"[!] Image enhancement error: {e}")
            return img # در صورت خطا، همان فریم اصلی برگردانده شود

    def detect(self, frame):
        if self.model is None or frame is None:
            return None # یا بازگرداندن شیء خالی متناسب با ساختار یولو
            
        try:
            # ۱. ابتدا بهبود کیفیت تصویر
            enhanced_frame = self.apply_clahe(frame)
            
            # ۲. سپس اجرای یولو روی فریم بهبود یافته
            results = self.model(enhanced_frame, conf=self.conf_thresh, verbose=False)[0]
            return results
        except Exception as e:
            print(f"[!] YOLO inference error in Webots detector: {e}")
            return None