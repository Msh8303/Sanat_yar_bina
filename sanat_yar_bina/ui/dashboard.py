from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from ui.video_widget import VideoWidget
from ui.log_widget import LogWidget
from ui.intelligence_widget import IntelligenceWidget

class IndustrialDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Sanat Yar Bina - AI Cyber-Physical Dashboard")
        self.resize(1300, 850) 
        self.setStyleSheet("background-color: #0f172a;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # پنل ویدیو
        self.video_panel = VideoWidget()
        self.main_layout.addWidget(self.video_panel, stretch=2)

        # لایه‌بندی افقی برای پنل‌های پایین (فقط 2 پنل)
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(15)
        
        # ۱. پنل لاگ زنده
        self.log_panel = LogWidget()
        self.bottom_layout.addWidget(self.log_panel, stretch=1)
        
        # ۲. پنل داده‌های تجمیع شده (لایه هوشمند)
        self.intel_panel = IntelligenceWidget()
        self.bottom_layout.addWidget(self.intel_panel, stretch=1)

        self.main_layout.addLayout(self.bottom_layout, stretch=1)

        # --- لایه کنترل دکمه‌ها ---
        self.control_layout = QHBoxLayout()
        
        self.btn_stop = QPushButton("⏹ توقف خط تولید و پردازش (YOLO)")
        self.btn_stop.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        
        self.btn_slm = QPushButton("📄 شروع گزارش‌گیری کامل (Qwen Batch Processing)")
        self.btn_slm.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_slm.setEnabled(False) 

        self.control_layout.addWidget(self.btn_stop)
        self.control_layout.addWidget(self.btn_slm)
        self.main_layout.addLayout(self.control_layout)

    def update_video(self, frame):
        self.video_panel.update_frame(frame)

    def update_log(self, event):
        self.log_panel.add_log(event)