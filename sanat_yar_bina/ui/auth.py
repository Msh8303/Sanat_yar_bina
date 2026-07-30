import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# ==========================================
# 1. دیتابیس مشتریان (دیکشنری تنظیم شده توسط شما)
# ==========================================
CLIENTS_DB = {
    "admin": {
        "password": "123",
        "first_name": "محمدامین",
        "last_name": "شبستری",
        "company": "شرکت فولاد مبارکه",
        "phone": "09120000000"
    },
    "user1": {
        "password": "456",
        "first_name": "علی",
        "last_name": "رضایی",
        "company": "ذوب آهن",
        "phone": "09130000000"
    }
}

# ==========================================
# 2. پنجره لاگین
# ==========================================
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ورود به سیستم مانیتورینگ")
        self.setFixedSize(350, 200)
        self.setLayoutDirection(Qt.RightToLeft)
        
        # متغیر برای ذخیره اطلاعات کاربری که با موفقیت لاگین کرده
        self.logged_in_user = None 
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        font = QFont("Tahoma", 10)

        # عنوان
        title = QLabel("لطفاً نام کاربری و رمز عبور خود را وارد کنید")
        title.setFont(QFont("Tahoma", 10, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # فیلد یوزرنیم
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("نام کاربری")
        self.user_input.setFont(font)
        layout.addWidget(self.user_input)

        # فیلد پسورد
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("رمز عبور")
        self.pass_input.setEchoMode(QLineEdit.Password) # مخفی کردن تایپ رمز
        self.pass_input.setFont(font)
        layout.addWidget(self.pass_input)

        # دکمه ورود
        self.btn_login = QPushButton("ورود به سیستم")
        self.btn_login.setFont(QFont("Tahoma", 10, QFont.Bold))
        self.btn_login.setStyleSheet("background-color: #2563eb; color: white; padding: 8px; border-radius: 4px;")
        self.btn_login.clicked.connect(self.check_login)
        layout.addWidget(self.btn_login)

        self.setLayout(layout)

    def check_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if username in CLIENTS_DB and CLIENTS_DB[username]["password"] == password:
            self.logged_in_user = CLIENTS_DB[username]
            self.accept() # بستن پنجره با موفقیت
        else:
            QMessageBox.critical(self, "خطا", "نام کاربری یا رمز عبور اشتباه است!")

# ==========================================
# 3. پنجره خوش‌آمدگویی (بسته شدن خودکار)
# ==========================================
class WelcomeDialog(QDialog):
    def __init__(self, user_info):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) # بدون حاشیه و همیشه رو
        self.setFixedSize(400, 150)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("background-color: #1e293b; color: white; border: 2px solid #10b981; border-radius: 10px;")
        
        layout = QVBoxLayout()
        
        # ساخت پیام شخصی‌سازی شده
        welcome_msg = f"{user_info['first_name']} عزیز از {user_info['company']}\nبه سیستم مانیتورینگ هوشمند خوش آمدید"
        
        label = QLabel(welcome_msg)
        label.setFont(QFont("Tahoma", 12, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        self.setLayout(layout)
        
        # تنظیم تایمر برای بسته شدن خودکار بعد از 3 ثانیه (3000 میلی‌ثانیه)
        QTimer.singleShot(3000, self.accept)