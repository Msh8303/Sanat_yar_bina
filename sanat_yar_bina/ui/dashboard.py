from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from ui.video_widget import VideoWidget
from ui.log_widget import LogWidget
from ui.report_widget import ReportWidget

class IndustrialDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # تنظیمات کلی پنجره نرم‌افزار
        self.setWindowTitle("Sanat Yar Bina - AI Cyber-Physical Dashboard")
        self.resize(1200, 850)
        self.setStyleSheet("background-color: #0f172a;") # تم دارک صنعتی

        # ویجت مرکزی
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # لایه‌بندی اصلی (عمودی)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # بخش بالایی: نمایشگر ویدیو (کشش 2 برابر نسبت به پایین)
        self.video_panel = VideoWidget()
        self.main_layout.addWidget(self.video_panel, stretch=2)

        # بخش پایینی: لایه‌بندی افقی برای لاگ‌ها و گزارش‌ها
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(15)
        
        # پنل لاگ زنده
        self.log_panel = LogWidget()
        self.bottom_layout.addWidget(self.log_panel, stretch=1)
        
        # پنل گزارش SLM
        self.report_panel = ReportWidget()
        self.bottom_layout.addWidget(self.report_panel, stretch=1)

        # اضافه کردن بخش پایینی به لایه اصلی
        self.main_layout.addLayout(self.bottom_layout, stretch=1)

    # توابع دسترسی سریع برای فراخوانی در فایل main.py
    def update_video(self, frame):
        self.video_panel.update_frame(frame)

    def update_log(self, event):
        self.log_panel.add_log(event)

    def update_slm_report(self, report_dict):
        self.report_panel.update_report(report_dict)