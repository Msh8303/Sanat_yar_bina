from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QLabel

class ReportWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)

        # عنوان پنل
        self.title = QLabel("SLM Periodic Reports (TinyLlama)")
        self.title.setStyleSheet("font-weight: bold; color: #c084fc; font-size: 14px;")

        # مرورگر متن برای نمایش گزارش‌های ساختاریافته
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            background-color: #1e293b; 
            color: #f8fafc; 
            font-family: 'Segoe UI', Tahoma, sans-serif;
            font-size: 14px;
            border: 1px solid #334155;
            border-radius: 6px;
        """)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.text_browser)
        self.setLayout(self.layout)

    def update_report(self, report_dict: dict):
        """
        دریافت دیکشنری گزارش از SLM و تبدیل آن به HTML گرافیکی
        """
        if "error" in report_dict:
            self.text_browser.setText(f"<h4 style='color: #a3be8c;'>{report_dict['error']}</h4>")
            return

        html_content = f"""
        <div style="padding: 10px;">
            <h3 style="color: #38bdf8; margin-top: 0;">Production Summary</h3>
            <table width="100%" style="margin-bottom: 15px;">
                <tr>
                    <td style="color: #94a3b8;">Total Defects:</td>
                    <td style="font-weight: bold;">{report_dict.get('total_defects', 0)}</td>
                </tr>
                <tr>
                    <td style="color: #94a3b8;">Critical Defects:</td>
                    <td style="font-weight: bold; color: #ef4444;">{report_dict.get('critical_defects', 0)}</td>
                </tr>
                <tr>
                    <td style="color: #94a3b8;">Most Frequent:</td>
                    <td style="font-weight: bold; color: #facc15;">{report_dict.get('most_frequent_defect', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="color: #94a3b8;">Avg Speed Drop:</td>
                    <td style="font-weight: bold;">{report_dict.get('average_speed_reduction', 0)}%</td>
                </tr>
            </table>
            
            <h4 style="color: #c084fc; border-top: 1px solid #475569; padding-top: 10px; margin-bottom: 5px;">AI Recommendation:</h4>
            <p style="color: #e2e8f0; line-height: 1.5; margin-top: 0;">
                {report_dict.get('recommendation', 'No recommendation provided.')}
            </p>
        </div>
        """
        self.text_browser.setText(html_content)