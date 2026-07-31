from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QLabel

class IntelligenceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)

        # عنوان پنل با رنگ زرد/نارنجی صنعتی
        self.title = QLabel("Aggregated Data (Intelligence Layer)")
        self.title.setStyleSheet("font-weight: bold; color: #fbbf24; font-size: 14px;")

        # مرورگر متن
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            background-color: #1e293b; 
            color: #cbd5e1; 
            font-family: Consolas, monospace;
            font-size: 13px;
            border: 1px solid #334155;
            border-radius: 6px;
        """)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.text_browser)
        self.setLayout(self.layout)
    # این تابع را داخل کلاس IntelligenceWidget اضافه کنید
    def clear(self):
        """پاک کردن متن تحلیل هوش مصنوعی"""
        self.text_browser.clear()
        self.text_browser.setText("منتظر دریافت داده‌های جدید...")
    def update_data(self, text: str):
        """جایگزین کردن متن قبلی با داده‌های جدیدِ پنجره زمانی"""
        self.text_browser.setText(text)