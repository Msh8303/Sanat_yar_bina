import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # لایه‌بندی اصلی ویدیو
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # ساخت کادر نمایشگر
        self.video_label = QLabel("سیگنال ویدیو...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            background-color: #000000; 
            border-radius: 10px; 
            border: 2px solid #334155;
            color: #94a3b8;
            font-size: 16px;
        """)

        # ---------------------------------------------------------
        # قفل کردن ابعاد برای جلوگیری از بزرگ شدن بی‌نهایت پنجره
        # ---------------------------------------------------------
        self.video_label.setMinimumSize(640, 480)
        # Ignored به پایتون می‌گوید: "سایز عکس داخل کادر را برای تغییر سایز پنجره نادیده بگیر"
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.layout.addWidget(self.video_label)

    def update_frame(self, frame):
        """دریافت فریم از یولو و نمایش بهینه آن روی صفحه"""
        try:
            # 🔥 بررسی اعتبار فریم ورودی برای جلوگیری از کرش OpenCV
            if frame is None or not hasattr(frame, 'shape') or len(frame.shape) < 3:
                return
            # 1. تبدیل فرمت رنگ از OpenCV (BGR) به PyQt (RGB)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w

            # 2. تبدیل به فرمت تصویر گرافیکی
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)

            # ---------------------------------------------------------
            # 3. مقیاس‌دهی (Scale) عکس به اندازه دقیق کادر فعلی
            # ---------------------------------------------------------
            scaled_pixmap = pixmap.scaled(
                self.video_label.width(), 
                self.video_label.height(), 
                Qt.KeepAspectRatio,         # حفظ تناسب طول و عرض ویدیو (جلوگیری از کشیدگی)
                Qt.SmoothTransformation     # رندر نرم و باکیفیت پیکسل‌ها
            )

            # 4. قرار دادن عکس نهایی روی صفحه
            self.video_label.setPixmap(scaled_pixmap)
        except Exception as e:
            # در صورت بروز خطای گرافیکی، به جای بسته شدن برنامه فقط آن فریم رد می‌شود
            pass