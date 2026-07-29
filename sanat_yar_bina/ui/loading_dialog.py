from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
import random

class LoadingScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("در حال پردازش")
        self.setFixedSize(650, 250)
        # حذف حاشیه‌های استاندارد ویندوز برای زیبایی بیشتر
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border: 2px solid #3b82f6;
                border-radius: 12px;
            }
            QLabel {
                color: #f8fafc;
                font-family: Tahoma, 'B Yekan', sans-serif;
            }
        """)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        
        # عنوان چشمک‌زن
        self.lbl_title = QLabel("⏳ هوش مصنوعی صیب در حال استخراج گزارش است...")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8;")
        
        # متن آموزشی که انیمیشن روی آن اجرا می‌شود
        self.lbl_info = QLabel("")
        self.lbl_info.setAlignment(Qt.AlignJustify | Qt.AlignVCenter)
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("font-size: 15px; line-height: 1.8; color: #cbd5e1;")
        
        self.layout.addWidget(self.lbl_title)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.lbl_info)

        # دیتابیس آموزشی عیوب ورق‌های فولادی
        self.facts = [
            "🔴 ناخالصی (Inclusion): \nاین عیب زمانی رخ می‌دهد که ذرات غیرفلزی (مثل اکسیدها یا سیلیکات‌ها) در حین ذوب درون فولاد محبوس می‌شوند. ناخالصی‌ها پیوستگی بافت را از بین برده و مقاومت قطعه را به شدت کاهش می‌دهند.",
            "🔴 پوسته نورد شده (Rolled-in Scale): \nاگر قبل از ورود شمش به دستگاه نورد، رسوب‌زدایی با آب پرفشار به درستی انجام نشود، پوسته‌های اکسیدی با فشار غلتک‌ها روی سطح ورق پرس شده و این عیب را می‌سازند.",
            "🔴 خط و خش (Scratch): \nیک آسیب مکانیکیِ خطی که معمولاً به خاطر اصطکاک ورق با غلتک‌های فرسوده، گیر کردن براده در مسیر حرکت، یا تنظیم نبودن راهنماهای دستگاه پدیدار می‌شود.",
            "🔴 ترک (Crack): \nخطرناک‌ترین عیب ساختاری! ترک‌ها معمولاً به دلیل تنش‌های حرارتی شدید، سرد شدن ناهمگون شمش، یا کششِ بیش از حدِ تحملِ فولاد در حین نورد ایجاد می‌شوند.",
            "🔴 سطح حفره‌دار (Pitted Surface): \nاین عیب شامل فرورفتگی‌های کوچک و نقطه‌ای است که عمدتاً به خاطر خوردگی شیمیایی و زنگ‌زدگیِ مقطعی قبل از عملیات نورد شکل گرفته و ظاهری آبله‌رو به ورق می‌دهد.",
            "🔴 وصله یا لکه (Patch): \nگاهی ذرات خارجی، روغن سوخته، یا پوسته‌های سرگردان در خط تولید، به سطح داغ ورق می‌چسبند و با عبور از زیر غلتک، به صورت لکه‌هایی تیره یا برآمده روی ورق تثبیت می‌شوند."
        ]
        
        # متغیرهای کنترل انیمیشن
        self.current_fact = ""
        self.typed_text = ""
        self.char_index = 0
        
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_char)
        
        self.delay_timer = QTimer()
        self.delay_timer.timeout.connect(self.start_new_fact)
        self.delay_timer.setSingleShot(True)

    def showEvent(self, event):
        """زمانی که پنجره باز می‌شود، انیمیشن شروع به کار می‌کند"""
        super().showEvent(event)
        self.start_new_fact()
        
    def start_new_fact(self):
        self.current_fact = random.choice(self.facts)
        self.typed_text = ""
        self.char_index = 0
        self.lbl_info.setText("")
        self.typing_timer.start(40) # سرعت تایپ: هر 40 میلی‌ثانیه یک حرف
        
    def type_next_char(self):
        if self.char_index < len(self.current_fact):
            self.typed_text += self.current_fact[self.char_index]
            self.lbl_info.setText(self.typed_text)
            self.char_index += 1
        else:
            self.typing_timer.stop()
            self.delay_timer.start(5000) # پس از اتمام جمله، 5 ثانیه مکث کن و بعدی را بیاور