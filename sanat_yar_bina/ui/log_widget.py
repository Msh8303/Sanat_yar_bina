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

    def add_log(self, event):
        """قالب‌بندی صنعتی لاگ با تمایز بین فریم سالم و معیوب"""
        
        if event.defect_class.upper() == "NORMAL":
            # قالب خلوت و آرام برای فریم‌های بدون عیب (HTML برای تغییر رنگ)
            log_msg = (
                f"<span style='color: #4ade80;'>"
                f"[{event.timestamp}] [FRM: {event.frame_id:05d}] | STATUS: ALL CLEAR | SPD: {event.speed_after:.1f}%"
                f"</span>"
            )
        else:
            # قالب هشدار صنعتی برای تشخیص عیب
            log_msg = (
                f"<span style='color: #fca5a5;'>"
                f"[{event.timestamp}] [FRM: {event.frame_id:05d}] "
                f"| DEFECT: {event.defect_class.upper():<10} (Conf: {event.confidence:.2f}, Risk: {event.severity_score:.2f}) "
                f"| CTRL: [Fuzzy: {event.fuzzy_output:.2f}, RL: {event.rl_output:.2f}] -> {event.selected_action} "
                f"| SPD: {event.speed_before:.1f}% -> {event.speed_after:.1f}%"
                f"</span>"
            )
        
        self.text_browser.append(log_msg)