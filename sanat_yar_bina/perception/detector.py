import cv2
import numpy as np
from ultralytics import YOLO

class DefectDetector:
    def __init__(self, model_path: str = "models/best.pt", conf_thresh: float = 0.5):
        """
        راه‌اندازی مدل یولو با استفاده از پردازنده گرافیکی (در صورت وجود)
        """
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            print(f"[!] Critical Error: Failed to load YOLO model from {model_path}. Error: {e}")
            self.model = None
        self.conf_thresh = conf_thresh

    def detect(self, frame: np.ndarray) -> list:
        """
        اجرای استنتاج روی فریم ورودی و استخراج لیست عیوب
        """
        
        detections = []
        if self.model is None or frame is None:
            return detections
            
        try:
            # اجرای مدل با مخفی کردن لاگ‌های اضافه در ترمینال
            results = self.model.predict(source=frame, conf=self.conf_thresh, verbose=False)

            if len(results) > 0:
                result = results[0]
                boxes = result.boxes
                
                # بررسی تک تک عیوب پیدا شده در این فریم
                for box in boxes:
                    # استخراج مختصات
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].item()
                    cls_id = int(box.cls[0].item())
                    cls_name = self.model.names[cls_id]

                    # محاسبه مساحت (به پیکسل)
                    area = (x2 - x1) * (y2 - y1)

                    detections.append({
                        "class_id": cls_id,
                        "class_name": cls_name,
                        "confidence": conf,
                        "bbox": (x1, y1, x2, y2),
                        "area_px": area
                    })
        except Exception as e:
            print(f"[!] YOLO inference error in detector: {e}")

        return detections