import os
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSplashScreen, QApplication

class LogoSplashScreen(QSplashScreen):
    def __init__(self, logo_path):
        pixmap = QPixmap(logo_path)
        # تغییر اندازه لوگو در صورت نیاز (مثلاً 400 در 400 پیکسل)
        pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        self.setWindowOpacity(0.0) # شروع با شفافیت صفر (برای انیمیشن Fade In)
        
        # انیمیشن تغییر شفافیت (Opacity)
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(1500) # مدت زمان انیمیشن ورود (1.5 ثانیه)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        
        # تایمر برای مدیریت کل زمان نمایش (5 ثانیه)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.start_fade_out)

    def showEvent(self, event):
        super().showEvent(event)
        self.animation.start()
        self.timer.start(3500) # ماندن در حالت کامل تا قبل از فید آوت (جمعاً حدود 5 ثانیه)

    def start_fade_out(self):
        # انیمیشن خروج (Fade Out)
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(1500) # مدت زمان خروج (1.5 ثانیه)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.finished.connect(self.close)
        self.fade_out_anim.start()