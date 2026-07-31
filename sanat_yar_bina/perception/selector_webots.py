import numpy as np

# تعریف کلاس‌ها و رنگ‌های استاندارد مطابق مدل شما
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

class WebotsTargetSelector:
    def __init__(self):
        pass

    def calculate_frame_risk(self, results, img_shape):
        h, w = img_shape[:2]
        total_weighted_risk = 0
        confidences = []
        
        if len(results.boxes) == 0: 
            return 0.0, 1.0
            
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            normalized_area = ((x2 - x1) * (y2 - y1)) / (h * w)
            cls_id = int(box.cls)
            # استفاده از ضریب دقیق 10 مطابق کد مرجع شما
            total_weighted_risk += (normalized_area * RISK_FACTORS.get(cls_id, 0.5)) * 10
            confidences.append(float(box.conf))
            
        mean_conf = sum(confidences) / len(confidences)
        return min(total_weighted_risk, 1.0), mean_conf