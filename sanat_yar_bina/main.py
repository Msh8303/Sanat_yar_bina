import sys
import cv2
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import os
# وارد کردن تنظیمات کلان
from config.config import PATHS, VISION_SETTINGS, CONTROL_SETTINGS, REPORT_SETTINGS

# وارد کردن ماژول‌های توسعه داده شده
from perception.detector import DefectDetector
from perception.selector import TargetSelector
from controllers.fuzzy import AdvancedFuzzyController
from controllers.rl import InferenceRLAgent
import numpy as np
from monitoring.event_model import DetectionEvent
from monitoring.database import DatabaseManager
from monitoring.logger import EventLogger
from monitoring.screenshot import ScreenshotManager
from reporting.report_generator import ReportGenerator
from ui.dashboard import IndustrialDashboard
from ui.report_viewer import ReportViewerWindow
from ui.loading_dialog import LoadingScreen
# این خط را به بخش ایمپورت‌های بالای main.py اضافه کنید
from ui.auth import LoginDialog, WelcomeDialog
from webots.receiver import WebotsStreamReceiver
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
# ==========================================
# Thread 1: پردازش تصویر و کنترلر بلادرنگ
# ==========================================
# ==========================================
# Thread 1: پردازش تصویر و کنترلر بلادرنگ (Pure RL)
# ==========================================
class VisionControlThread(QThread):
    new_frame_signal = pyqtSignal(object)
    new_log_signal = pyqtSignal(object)
    motor_stopped_signal = pyqtSignal()

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.running = True
        self.input_mode = "video"
        
        self.webots_receiver = None
        self.webots_process = None  # 🔥 متغیر جدید برای کنترل برنامه Webots

        # بارگذاری سایر ماژول‌ها...
        self.detector = DefectDetector(model_path=PATHS["yolo_model"], conf_thresh=VISION_SETTINGS["confidence_threshold"])
        self.selector = TargetSelector() 
        self.logger = EventLogger(log_dir=PATHS["log_dir"])
        self.screenshot_mgr = ScreenshotManager(save_dir=PATHS["screenshot_dir"])
        self.fuzzy_brain = AdvancedFuzzyController()
        self.rl_agent = InferenceRLAgent(model_path=PATHS["rl_model"])
        self.current_speed = 0.5 
        self.target_speed = 0.5
        self.saved_speed = 0.5
        self.motor_state = "RUNNING"
        
    def request_smooth_stop(self):
        """درخواست توقف نرم از طریق دکمه UI"""
        if self.motor_state == "RUNNING":
            self.saved_speed = self.current_speed # ذخیره سرعت فعلی
            self.target_speed = 0.0
            self.motor_state = "STOPPING"

    def request_smooth_resume(self):
        """درخواست ادامه حرکت نرم"""
        if self.motor_state == "STOPPED":
            self.target_speed = self.saved_speed
            self.motor_state = "RESUMING"
            
            
    def run(self):
        cap = None
        
        if self.input_mode == "video":
            print("[*] اجرای پایپ‌لاین از روی ویدیو شبیه‌سازی...")
            cap = cv2.VideoCapture(PATHS["video_source"])
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
        elif self.input_mode == "webots":
            print("[*] اجرای خودکار شبیه‌ساز و اتصال به جریان زنده دوربین...")
            
            # 🔥 مسیر فایل اجرایی وباتز و دنیای شبیه‌سازی شما
            webots_exe = r"C:\Program Files\Webots\msys64\mingw64\bin\webots.exe"
            world_file = r"C:\Users\MSH8303\Sanat_yar_bina-1\simulation\worlds\steel_factory.wbt"
            
            # باز کردن خودکار وباتز (با حالت realtime برای استارت خودکار)
            if os.path.exists(world_file):
                self.webots_process = subprocess.Popen([webots_exe, "--mode=realtime", world_file])
            else:
                print(f"[!] خطا: فایل شبیه‌سازی در مسیر پیدا نشد: {world_file}")

            self.webots_receiver = WebotsStreamReceiver(port=5555)
            self.webots_receiver.connect()
            width, height = 640, 480 

        frame_count = 0
        
        while self.running:
            # --- منطق کنترل سرعت موتور ---
            if self.motor_state in ["STOPPING", "RESUMING"]:
                step = 0.1
                if self.current_speed > self.target_speed:
                    self.current_speed = max(self.current_speed - step, self.target_speed)
                elif self.current_speed < self.target_speed:
                    self.current_speed = min(self.current_speed + step, self.target_speed)
                
                if abs(self.current_speed - self.target_speed) < 0.01:
                    self.current_speed = self.target_speed
                    if self.motor_state == "STOPPING":
                        self.motor_state = "STOPPED"
                        self.motor_stopped_signal.emit()
                    elif self.motor_state == "RESUMING":
                        self.motor_state = "RUNNING"

            if self.motor_state == "STOPPED":
                time.sleep(0.05)
                continue

            # --- دریافت فریم بر اساس حالت ورودی ---
            frame = None
            if self.input_mode == "video" and cap and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
            elif self.input_mode == "webots" and self.webots_receiver:
                frame = self.webots_receiver.get_frame()
                
                # اگر سیگنالی از ویباتز دریافت نشد، صفحه انتظار نمایش داده می‌شود
                if frame is None:
                    frame = np.zeros((height, width, 3), dtype=np.uint8)
                    frame[:] = (42, 23, 15)
                    cv2.putText(frame, "Launching Webots Simulator...", (60, height // 2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
                    self.new_frame_signal.emit(frame)
                    time.sleep(0.05)
                    continue
            else:
                break

            # --- پردازش هوش مصنوعی (YOLO, Fuzzy, RL) ---
            detections = self.detector.detect(frame)
            
            for det in detections:
                x1, y1, x2, y2 = map(int, det["bbox"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, det["class_name"], (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            self.new_frame_signal.emit(frame)

            if frame_count % CONTROL_SETTINGS["frames_per_decision"] == 0:
                from datetime import datetime
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                risk, conf = self.selector.calculate_frame_risk(detections, width, height)
                fuzzy_suggestion = self.fuzzy_brain.compute(risk, conf)
                state = self.rl_agent.get_state(fuzzy_suggestion, self.current_speed)
                action_idx, speed_change = self.rl_agent.choose_best_action(state)
                
                speed_before = self.current_speed
                new_speed = np.clip(self.current_speed + speed_change, 0.1, 1.0)
                self.current_speed = new_speed
                
                f_label = self.fuzzy_brain.get_label(fuzzy_suggestion) if hasattr(self.fuzzy_brain, 'get_label') else str(round(fuzzy_suggestion,2))
                r_label = self.rl_agent.get_label(speed_change) if hasattr(self.rl_agent, 'get_label') else str(speed_change)
                action_label = f"RL: {r_label} | Fuzzy: {f_label}"

                primary_defect = detections[0]["class_name"] if detections else "NORMAL"

                event = DetectionEvent(
                    timestamp=timestamp_str, frame_id=frame_count, defect_class=primary_defect,
                    confidence=conf, severity_score=risk, 
                    fuzzy_output=fuzzy_suggestion, 
                    rl_output=speed_change, 
                    speed_before=speed_before * 100,
                    speed_after=self.current_speed * 100,
                    selected_action=action_label
                )

                self.logger.log(event)
                self.db.insert_event(event)
                if detections: 
                    self.screenshot_mgr.save_if_needed(frame, event)
                
                self.new_log_signal.emit(event)

            frame_count += 1
            time.sleep(0.03)

        if cap:
            cap.release()
        if self.webots_receiver:
            self.webots_receiver.disconnect()
            
    def stop(self):
        self.running = False
        if self.webots_receiver:
            self.webots_receiver.disconnect()
            
        # 🔥 بستن خودکار شبیه‌ساز هنگام توقف یا تغییر منبع
        if self.webots_process:
            print("[*] در حال بستن نرم‌افزار Webots...")
            self.webots_process.terminate()
            self.webots_process = None
            
        self.wait()

# ==========================================
# Thread 2: پردازش هوش مصنوعی زبانی (SLM)
# ==========================================
class DataAggregatorThread(QThread):
    new_intel_signal = pyqtSignal(str)

    def __init__(self, generator):
        super().__init__()
        self.running = True
        self.generator = generator

    def run(self):
        interval = REPORT_SETTINGS["report_interval_seconds"]
        elapsed_time = 0
        
        # حلقه به جای خواب 60 ثانیه‌ای، هر 1 ثانیه بیدار می‌شود تا در صورت توقف، فورا بسته شود
        while self.running:
            time.sleep(1)
            elapsed_time += 1
            
            if elapsed_time >= interval:
                elapsed_time = 0
                intel_text = self.generator.save_window_data_only(window_seconds=interval)
                if intel_text:
                    self.new_intel_signal.emit(intel_text)

    def stop(self):
        self.running = False
        self.wait()

# ==========================================
# Thread 3: پردازش دسته‌ای SLM (بعد از توقف)
# ==========================================
class BatchSLMThread(QThread):
    finished_signal = pyqtSignal(list)

    def __init__(self, generator):
        super().__init__()
        self.generator = generator

    def run(self):
        # اجرای تمام گزارش‌ها به صورت پشت سر هم
        reports = self.generator.process_all_batch()
        self.finished_signal.emit(reports)

# ==========================================
# Main App Execution
# ==========================================
# ==========================================
# Main App Execution
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginDialog()
    if login_window.exec_() != QDialog.Accepted:
        sys.exit(0)
    # +++ 2. اجرای صفحه خوش‌آمدگویی در صورت موفقیت +++
    user_data = login_window.logged_in_user
    welcome_window = WelcomeDialog(user_data)
    welcome_window.exec_() # برنامه اینجا ۳ ثانیه منتظر می‌ماند تا پاپ‌آپ خودش بسته شود
    # +++++++++++++++++++++++++++++++++++++++
    db_manager = DatabaseManager(db_path=PATHS["database"])
    
    # راه‌اندازی کلاس جنریتور
    generator = ReportGenerator(db_manager)

    dashboard = IndustrialDashboard()
    dashboard.show()

    # ایجاد تردها (اما هنوز استارت نمی‌زنیم!)
    vision_thread = VisionControlThread(db_manager)
    vision_thread.new_frame_signal.connect(dashboard.update_video)
    vision_thread.new_log_signal.connect(dashboard.update_log)
    
    aggregator_thread = DataAggregatorThread(generator)
    aggregator_thread.new_intel_signal.connect(dashboard.intel_panel.update_data) 

    # --- تنظیمات اولیه دکمه‌ها در زمان باز شدن نرم‌افزار ---
    dashboard.btn_start.setEnabled(True)   # دکمه شروع فعال است
    dashboard.btn_stop.setEnabled(False)   # دکمه توقف غیرفعال
    dashboard.btn_resume.setEnabled(False) # دکمه ادامه غیرفعال
    dashboard.btn_slm.setEnabled(False)    # دکمه گزارش‌گیری غیرفعال

    loading_screen = LoadingScreen()

    # --- توابع منطق دکمه‌ها ---
    
    def start_production_line():
        """شروع به کار خط تولید از حالت استندبای"""
        dashboard.btn_start.setEnabled(False)
        dashboard.btn_stop.setEnabled(True)
        dashboard.btn_start.setText("✅ خط در حال کار است")
        dashboard.radio_video.setEnabled(False)
        dashboard.radio_webots.setEnabled(False)
        if dashboard.radio_video.isChecked():
            vision_thread.input_mode = "video"
        elif dashboard.radio_webots.isChecked():
            vision_thread.input_mode = "webots"
        # تازه الان هوش مصنوعی و خط تولید روشن می‌شوند!
        vision_thread.start()
        aggregator_thread.start()

    def on_smooth_stop_requested():
        dashboard.btn_stop.setEnabled(False)
        dashboard.btn_stop.setText("⏳ در حال توقف موتور...")
        vision_thread.request_smooth_stop()

    def on_motor_fully_stopped():
        dashboard.btn_stop.setText("⏹ توقف کامل شد")
        dashboard.btn_resume.setEnabled(True)
        dashboard.btn_slm.setEnabled(True) 
        dashboard.btn_slm.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-family: Tahoma;") 
        dashboard.radio_video.setEnabled(True)
        dashboard.radio_webots.setEnabled(True)
    def on_smooth_resume_requested():
        dashboard.btn_resume.setEnabled(False)
        dashboard.btn_slm.setEnabled(False) 
        dashboard.btn_slm.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-family: Tahoma;")
        
        dashboard.btn_stop.setText("⏸ توقف نرم")
        dashboard.btn_stop.setEnabled(True)
        vision_thread.request_smooth_resume()

    def start_batch_slm():
        dashboard.btn_slm.setText("⏳ Qwen در حال پردازش است...")
        dashboard.btn_slm.setEnabled(False)
        dashboard.btn_resume.setEnabled(False) 
        
        loading_screen.show()
        global batch_thread 
        batch_thread = BatchSLMThread(generator)
        batch_thread.finished_signal.connect(show_report_viewer)
        batch_thread.start()

    def show_report_viewer(reports_data):
        loading_screen.accept()
        dashboard.btn_slm.setText("📄 شروع گزارش‌گیری کامل (Qwen)")
        dashboard.btn_slm.setEnabled(True)
        dashboard.btn_resume.setEnabled(True)
        
        global viewer_window
        viewer_window = ReportViewerWindow(reports_data)
        viewer_window.show()
        
    def reset_system():
        """بازگردانی کل سیستم به حالت اولیه هنگام تغییر ورودی"""
        global vision_thread, aggregator_thread
        
        # ۱. متوقف کردن کامل تردهای قبلی اگر در پس‌زمینه گیر کرده‌اند
        if vision_thread.isRunning():
            vision_thread.stop()
        if aggregator_thread.isRunning():
            aggregator_thread.stop()
            
        # ۲. بازسازی تردها برای اجرای تمیز و بدون خطای بعدی
        vision_thread = VisionControlThread(db_manager)
        vision_thread.new_frame_signal.connect(dashboard.update_video)
        vision_thread.new_log_signal.connect(dashboard.update_log)
        vision_thread.motor_stopped_signal.connect(on_motor_fully_stopped) # اتصال مجدد سیگنال توقف
        
        aggregator_thread = DataAggregatorThread(generator)
        aggregator_thread.new_intel_signal.connect(dashboard.intel_panel.update_data)
        
        # ۳. بازگردانی دکمه‌ها به حالت اولیه (استارت فعال، بقیه خاموش)
        dashboard.btn_start.setEnabled(True)
        dashboard.btn_start.setText("▶ شروع خط تولید")
        
        dashboard.btn_stop.setEnabled(False)
        dashboard.btn_stop.setText("⏸ توقف نرم")
        
        dashboard.btn_resume.setEnabled(False)
        
        dashboard.btn_slm.setEnabled(False)
        dashboard.btn_slm.setText("📄 شروع گزارش‌گیری کامل (صیب)")
        dashboard.btn_slm.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-family: Tahoma;")
        
        # ۴. خالی کردن کادر ویدیو (نمایش صفحه آماده به کار با تم رنگی شما)
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        blank_frame[:] = (42, 23, 15) # رنگ پس‌زمینه سرمه‌ای (#0f172a) در فرمت BGR
        cv2.putText(blank_frame, "Waiting for Input Signal...", (120, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
        dashboard.update_video(blank_frame)
        
        # ۵. پاک کردن پنل‌های لاگ و هوش مصنوعی
        if hasattr(dashboard.log_panel, 'clear'):
            dashboard.log_panel.clear()
        if hasattr(dashboard.intel_panel, 'clear'):
            dashboard.intel_panel.clear()
            
        print("[*] سیستم با موفقیت ریست شد و آماده دریافت ورودی جدید است.")

    

    # اتصال سیگنال‌ها و دکمه‌ها
    vision_thread.motor_stopped_signal.connect(on_motor_fully_stopped)
    dashboard.btn_start.clicked.connect(start_production_line)  # 🔥 اتصال دکمه شروع
    dashboard.btn_stop.clicked.connect(on_smooth_stop_requested)
    dashboard.btn_resume.clicked.connect(on_smooth_resume_requested)
    dashboard.btn_slm.clicked.connect(start_batch_slm)
    # +++ اتصال تغییر دکمه‌های رادیویی به تابع ریست +++
    dashboard.radio_video.clicked.connect(reset_system)
    dashboard.radio_webots.clicked.connect(reset_system)
    # +++++++++++++++++++++++++++++++++++++++++++++++++

    sys.exit(app.exec_())