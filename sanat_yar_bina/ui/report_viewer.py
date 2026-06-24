from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QTextBrowser, QHeaderView, QLabel
from PyQt5.QtCore import Qt

class ReportViewerWindow(QWidget):
    def __init__(self, reports_data):
        super().__init__()
        self.setWindowTitle("آرشیو گزارش‌های هوش مصنوعی (SLM)")
        self.resize(1100, 600)
        self.setStyleSheet("background-color: #0f172a; color: #f8fafc;")
        self.setLayoutDirection(Qt.RightToLeft) # راست‌چین برای فارسی

        self.layout = QHBoxLayout(self)
        
        # --- بخش راست: جدول گزارش‌ها ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["بازه زمانی (Window)", "سطح ریسک", "وضعیت بررسی"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e293b; border: 1px solid #334155; border-radius: 5px; }
            QHeaderView::section { background-color: #334155; padding: 5px; font-weight: bold; }
        """)
        
        # --- بخش چپ: نمایشگر متن کامل گزارش ---
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            background-color: #1e293b; border: 1px solid #334155; border-radius: 5px;
            font-family: Tahoma, 'B Yekan', sans-serif; font-size: 14px; line-height: 1.6; padding: 15px;
        """)
        
        self.layout.addWidget(self.table, stretch=1)
        self.layout.addWidget(self.text_browser, stretch=2)

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
            # تبدیل متن خام به HTML برای نمایش راست‌چین و زیباتر
            html = f"<div style='direction: rtl; text-align: right;'>{report_text.replace(chr(10), '<br>')}</div>"
            self.text_browser.setText(html)