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
        """دریافت دیکشنری گزارش و تبدیل خروجی ساختاریافته SLM به HTML"""
        
        if "error" in report_dict:
            self.text_browser.setText(f"<h4 style='color: #fca5a5;'>{report_dict['error']}</h4>")
            return

        # تبدیل خطوط جدید (Enter) در متن هوش مصنوعی به تگ <br> در HTML
        ai_raw_text = report_dict.get('ai_recommendation', 'No recommendation provided.')
        ai_formatted_html = ai_raw_text.replace("\n", "<br>")

        # تزریق مستقیم متن آماده‌ی هوش مصنوعی در یک کادر مجزا
        html_content = f"""
        <div style="padding: 10px;">
            <div style="background-color: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #475569;">
                <p style="color: #e2e8f0; line-height: 1.6; margin: 0; font-family: 'Segoe UI', sans-serif;">
                    {ai_formatted_html}
                </p>
            </div>
            
            <hr style="border: 0; border-top: 1px solid #334155; margin: 15px 0;">
            
            <h4 style="color: #64748b; margin-top: 0; font-size: 12px;">Data Backbone:</h4>
            <table width="100%" style="font-size: 12px; color: #94a3b8;">
                <tr>
                    <td>Total Evt: <b>{report_dict.get('total_defects', 0)}</b></td>
                    <td>Critical: <b style="color: #ef4444;">{report_dict.get('critical_defects', 0)}</b></td>
                    <td>Freq: <b style="color: #facc15;">{report_dict.get('most_frequent', 'N/A')}</b></td>
                </tr>
            </table>
        </div>
        """
        self.text_browser.setText(html_content)