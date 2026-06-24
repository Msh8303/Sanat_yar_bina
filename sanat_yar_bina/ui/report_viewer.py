from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser, QHeaderView
from PyQt5.QtCore import Qt

class ReportViewerWindow(QWidget):
    def __init__(self, reports_data):
        super().__init__()
        self.setWindowTitle("آرشیو گزارش‌های هوش مصنوعی (SLM)")
        self.resize(1100, 600)
        self.setStyleSheet("background-color: #0f172a; color: #f8fafc;")
        self.setLayoutDirection(Qt.RightToLeft) # راست‌چین برای فارسی

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 🔥 استفاده از QSplitter برای ایجاد Handler (خط جا‌به‌جاکننده)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #475569;
                width: 4px;
                border-radius: 2px;
                margin: 0px 5px;
            }
            QSplitter::handle:hover {
                background-color: #3b82f6; /* تغییر رنگ هنگام رفتن موس روی هندلر */
            }
        """)

        # --- بخش راست: جدول گزارش‌ها ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["بازه زمانی (Window)", "سطح ریسک", "وضعیت"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e293b; border: 1px solid #334155; border-radius: 5px; }
            QHeaderView::section { background-color: #334155; padding: 5px; font-weight: bold; }
        """)
        
        # --- بخش چپ: نمایشگر متن کامل گزارش ---
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            background-color: #1e293b; border: 1px solid #334155; border-radius: 5px;
            padding: 10px;
        """)
        
        # اضافه کردن ویجت‌ها به Splitter به جای Layout
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.text_browser)
        
        # تنظیم نسبت اندازه پیش‌فرض (مثلاً جدول کوچکتر و متن بزرگتر باشد)
        self.splitter.setSizes([350, 750])

        self.main_layout.addWidget(self.splitter)

        # پر کردن جدول با داده‌ها
        self.reports_data = reports_data
        self.populate_table()

        # اتصال رویداد کلیک روی جدول به نمایش متن
        self.table.itemSelectionChanged.connect(self.display_selected_report)

    def populate_table(self):
        self.table.setRowCount(len(self.reports_data))
        for row, data in enumerate(self.reports_data):
            self.table.setItem(row, 0, QTableWidgetItem(data["window"]))
            
            risk_item = QTableWidgetItem(data["risk"])
            if data["risk"] == "HIGH": risk_item.setForeground(Qt.red)
            elif data["risk"] == "MEDIUM": risk_item.setForeground(Qt.yellow)
            else: risk_item.setForeground(Qt.green)
            self.table.setItem(row, 1, risk_item)
            
            self.table.setItem(row, 2, QTableWidgetItem("✅ تکمیل شده"))

    def display_selected_report(self):
        selected_rows = self.table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            report_text = self.reports_data[row]["text"]
            
            # 🔥 استفاده از div و align برای اجبار PyQt به راست‌چین کردن
            html = f"""
            <div dir="rtl" align="right" style="
                font-family: Tahoma, 'B Yekan', sans-serif;
                font-size: 15px;
                line-height: 1.8;
                color: #f8fafc;
                background-color: #1e293b;
                padding: 10px;
                text-align: right;
            ">
                {report_text.replace(chr(10), '<br>')}
            </div>
            """
            self.text_browser.setHtml(html)