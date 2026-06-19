import sys
import cv2
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal

# وارد کردن تنظیمات کلان
from config.config import PATHS, VISION_SETTINGS, CONTROL_SETTINGS, REPORT_SETTINGS

# وارد کردن ماژول‌های توسعه داده شده
from perception.detector import DefectDetector
from perception.selector import TargetSelector
from controllers.hybrid import HybridController
from monitoring.event_model import DetectionEvent
from monitoring.database import DatabaseManager
from monitoring.logger import EventLogger
from monitoring.screenshot import ScreenshotManager
from reporting.report_generator import ReportGenerator
from ui.dashboard import IndustrialDashboard

# ==========================================
# Thread 1: پردازش تصویر و کنترلر بلادرنگ
# ==========================================
class VisionControlThread(QThread):
    # سیگنال‌ها برای ارسال داده از ترد پردازش به رابط کاربری
    new_frame_signal = pyqtSignal(object)
    new_log_signal = pyqtSignal(object)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.running = True
        
        # بارگذاری ماژول‌ها
        self.detector = DefectDetector(model_path=PATHS["yolo_model"], conf_thresh=VISION_SETTINGS["confidence_threshold"])
        self.selector = TargetSelector(min_risk_threshold=VISION_SETTINGS["risk_threshold"])
        self.controller = HybridController(rl_model_path=PATHS["rl_model"])
        self.logger = EventLogger(log_dir=PATHS["log_dir"])
        self.screenshot_mgr = ScreenshotManager(save_dir=PATHS["screenshot_dir"])
        
        self.current_speed = CONTROL_SETTINGS["max_conveyor_speed"]

    def run(self):
        # باز کردن ویدیو تستی
        cap = cv2.VideoCapture(PATHS["video_source"])
        frame_count = 0

        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # تکرار ویدیو در صورت اتمام
                continue

            # 1. پردازش یولو
            detections = self.detector.detect(frame)
            
            # 2. رسم کادرهای تشخیص روی فریم برای نمایش در داشبورد
            for det in detections:
                x1, y1, x2, y2 = map(int, det["bbox"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, det["class_name"], (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # ارسال فریم برای نمایش در UI
            self.new_frame_signal.emit(frame)

            # اجرای کنترلر فقط هر N فریم (برای جلوگیری از لرزش سرعت موتور)
            if frame_count % CONTROL_SETTINGS["frames_per_decision"] == 0:
                from datetime import datetime
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                target = self.selector.select_primary_target(detections)
                
                if target:
                    # عیب پیدا شده است
                    action_data = self.controller.compute_action(target, self.current_speed)
                    defect_class = target["detection"]["class_name"]
                    conf = target["detection"]["confidence"]
                    risk = target["risk_score"]
                else:
                    # خط تولید پاک است (وضعیت نرمال)
                    
                    # --- منطق بازیابی سرعت (پدال گاز) ---
                    # اگر خط پاک است یا ریسک عیب پایین‌تر از آستانه است، سرعت را پله‌پله بالا ببر
                    recovery_step = 10.0  # افزایش ۵ درصدی سرعت در هر تصمیم‌گیری
                    new_speed = min(CONTROL_SETTINGS["max_conveyor_speed"], self.current_speed + recovery_step)
                    
                    # تعیین اکشن: اگر سرعت در حال افزایش است بنویس ACCELERATE، در غیر این صورت MAX_SPEED
                    if self.current_speed < CONTROL_SETTINGS["max_conveyor_speed"]:
                        action_name = "ACCELERATE"
                    else:
                        action_name = "MAINTAIN_MAX_SPEED"

                    action_data = {
                        "fuzzy_output": 0.0, 
                        "rl_output": 0.0, 
                        "speed_before": self.current_speed, 
                        "speed_after": new_speed, 
                        "selected_action": action_name
                    }
                    defect_class = "NORMAL"
                    conf = 0.0
                    risk = 0.0

                # ساخت رویداد (چه عیب باشد چه نباشد)
                event = DetectionEvent(
                    timestamp=timestamp_str, frame_id=frame_count, defect_class=defect_class,
                    confidence=conf, severity_score=risk, fuzzy_output=action_data["fuzzy_output"],
                    rl_output=action_data["rl_output"], speed_before=action_data["speed_before"],
                    speed_after=action_data["speed_after"], selected_action=action_data["selected_action"]
                )

                # آپدیت متغیر سرعت
                self.current_speed = action_data["speed_after"]

                # ثبت در لاگ و دیتابیس (همیشه انجام می‌شود)
                self.logger.log(event)
                self.db.insert_event(event)
                
                # ذخیره اسکرین‌شات (فقط در صورت وجود عیب)
                if target:
                    self.screenshot_mgr.save_if_needed(frame, event)

                # ارسال لاگ به رابط کاربری (بدون تورفتگی اضافه، باید برای همه اجرا شود)
                self.new_log_signal.emit(event)

            # --- دقت کنید که else قبلی از اینجا حذف شد ---
            
            frame_count += 1
            # ایجاد یک تاخیر کوچک برای شبیه‌سازی سرعت واقعی (مثلا 30 فریم در ثانیه)
            time.sleep(0.03)

        cap.release()

    def stop(self):
        self.running = False
        self.wait()

# ==========================================
# Thread 2: پردازش هوش مصنوعی زبانی (SLM)
# ==========================================
class SLMReportingThread(QThread):
    new_report_signal = pyqtSignal(dict)

    def __init__(self, db_manager):
        super().__init__()
        self.running = True
        self.generator = ReportGenerator(db_manager=db_manager)

    def run(self):
        while self.running:
            # توقف برای N ثانیه (طبق تنظیمات)
            time.sleep(REPORT_SETTINGS["report_interval_seconds"])
            
            # تولید گزارش
            report = self.generator.create_periodic_report(window_seconds=REPORT_SETTINGS["report_interval_seconds"])
            
            # ارسال گزارش به رابط کاربری
            self.new_report_signal.emit(report)

    def stop(self):
        self.running = False
        self.wait()

# ==========================================
# Main App Execution
# ==========================================
if __name__ == "__main__":
    # 1. ساخت اپلیکیشن
    app = QApplication(sys.argv)

    # 2. راه‌اندازی دیتابیس مشترک
    db_manager = DatabaseManager(db_path=PATHS["database"])

    # 3. راه‌اندازی رابط کاربری
    dashboard = IndustrialDashboard()
    dashboard.show()

    # 4. راه‌اندازی Thread پردازش تصویر
    vision_thread = VisionControlThread(db_manager)
    vision_thread.new_frame_signal.connect(dashboard.update_video)
    vision_thread.new_log_signal.connect(dashboard.update_log)
    vision_thread.start()

    # 5. راه‌اندازی Thread گزارش‌گیر متنی
    slm_thread = SLMReportingThread(db_manager)
    slm_thread.new_report_signal.connect(dashboard.update_slm_report)
    slm_thread.start()

    # مدیریت خروج امن از برنامه
    sys.exit(app.exec_())
    
    # توقف تردها هنگام بستن برنامه
    vision_thread.stop()
    slm_thread.stop()