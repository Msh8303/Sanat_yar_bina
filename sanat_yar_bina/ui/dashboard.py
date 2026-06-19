from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from ui.video_widget import VideoWidget
from ui.log_widget import LogWidget
from ui.report_widget import ReportWidget
from ui.intelligence_widget import IntelligenceWidget  # اضافه شدن ماژول جدید

class IndustrialDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Sanat Yar Bina - AI Cyber-Physical Dashboard")
        self.resize(1300, 850) # عرض را کمی بیشتر کردیم تا 3 پنل جا بشوند
        self.setStyleSheet("background-color: #0f172a;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        self.video_panel = VideoWidget()
        self.main_layout.addWidget(self.video_panel, stretch=2)

        # لایه‌بندی افقی برای ۳ پنل در پایین صفحه
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(15)
        
        # ۱. پنل سمت چپ: لاگ زنده
        self.log_panel = LogWidget()
        self.bottom_layout.addWidget(self.log_panel, stretch=1)
        
        # ۲. پنل وسط: داده‌های تجمیع شده (لایه هوشمند)
        self.intel_panel = IntelligenceWidget()
        self.bottom_layout.addWidget(self.intel_panel, stretch=1)

        # ۳. پنل سمت راست: گزارش هوش مصنوعی
        self.report_panel = ReportWidget()
        self.bottom_layout.addWidget(self.report_panel, stretch=1)

        self.main_layout.addLayout(self.bottom_layout, stretch=1)

    def update_video(self, frame):
        self.video_panel.update_frame(frame)

    def update_log(self, event):
        self.log_panel.add_log(event)

    def update_slm_report(self, report_dict):
        # آپدیت همزمان پنل گزارش و پنل هوشمند
        self.report_panel.update_report(report_dict)
        if "aggregated_data" in report_dict:
            self.intel_panel.update_data(report_dict["aggregated_data"])