from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QLabel

class LogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)

        # عنوان پنل
        self.title = QLabel("Live Event Logs (YOLO & RL)")
        self.title.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 14px;")

        # مرورگر متن برای نمایش لاگ‌ها (فقط خواندنی)
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            background-color: #1e293b; 
            color: #a3be8c; 
            font-family: Consolas, monospace;
            font-size: 13px;
            border: 1px solid #334155;
            border-radius: 6px;
        """)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.text_browser)
        self.setLayout(self.layout)

    def add_log(self, event_data):
        """
        دریافت شیء رویداد و چاپ آن در ترمینال مجازی
        """
        # استخراج ساعت از رشته زمان
        time_str = event_data.timestamp.split()[1] if " " in event_data.timestamp else event_data.timestamp
        
        # فرمت‌دهی صنعتی برای نمایش
        color = "#ef4444" if event_data.severity_score > 0.8 else "#facc15"
        log_html = f"""
        <div style="margin-bottom: 5px; border-bottom: 1px dotted #475569; padding-bottom: 5px;">
            <span style="color: #94a3b8;">[{time_str}]</span> 
            <b style="color: {color};">{event_data.defect_class.upper()}</b> 
            | Risk: {event_data.severity_score:.2f} 
            | Action: <span style="color: #38bdf8;">{event_data.selected_action}</span> 
            | Speed: {event_data.speed_before}% &rarr; {event_data.speed_after}%
        </div>
        """
        self.text_browser.append(log_html)