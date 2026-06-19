import cv2
import os
from pathlib import Path
from monitoring.event_model import DetectionEvent

class ScreenshotManager:
    def __init__(self, save_dir: str = "data/screenshots"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def save_if_needed(self, frame, event: DetectionEvent):
        """
        بررسی شرایط و ذخیره تصویر فریم در صورت لزوم
        """
        # شرط ذخیره‌سازی صنعتی: فقط عیوب قطعی یا ریسک بالا
        if event.severity_score > 0.8 or event.confidence > 0.9:
            # فرمت‌دهی زمان برای نام فایل (حذف کاراکترهای غیرمجاز در نامگذاری فایل)
            safe_time = event.timestamp.replace(":", "").replace("-", "").replace(" ", "_").split(".")[0]
            filename = f"{safe_time}_{event.defect_class}.jpg"
            filepath = self.save_dir / filename
            
            # ذخیره تصویر با کتابخانه OpenCV
            cv2.imwrite(str(filepath), frame)