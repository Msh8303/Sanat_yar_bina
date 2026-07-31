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
        if not isinstance(report_dict, dict):
            self.text_browser.setText("<h4 style='color: #fca5a5;'>Critical Error: Invalid report format received from SLM.</h4>")
            return
        """دریافت دیکشنری گزارش و تبدیل خروجی ساختاریافته SLM به HTML"""
        
        if "error" in report_dict:
            self.text_browser.setText(f"<h4 style='color: #fca5a5;'>{report_dict['error']}</h4>")
            return

        # تبدیل خطوط جدید (Enter) در متن هوش مصنوعی به تگ <br> در HTML
        # تبدیل خطوط جدید به تگ HTML
        ai_raw_text = report_dict.get('ai_recommendation', 'هیچ پیشنهادی ارائه نشده است.')
        ai_formatted_html = ai_raw_text.replace("\n", "<br>")

        # تزریق متن در کادر راست‌چین و فارسی‌سازی لیبل‌ها
        html_content = f"""
        <div style="padding: 10px; direction: rtl; text-align: right; font-family: Tahoma, 'B Yekan', sans-serif;">
            <div style="background-color: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #475569;">
                <p style="color: #e2e8f0; line-height: 1.8; margin: 0; font-size: 14px;">
                    {ai_formatted_html}
                </p>
            </div>
            
            <hr style="border: 0; border-top: 1px solid #334155; margin: 15px 0;">
            
            <h4 style="color: #64748b; margin-top: 0; font-size: 13px;">داده‌های پشتیبان (بازه زمانی):</h4>
            <table width="100%" style="font-size: 13px; color: #94a3b8; direction: rtl; text-align: right;">
                <tr>
                    <td>کل عیوب: <b style="color: #f8fafc;">{report_dict.get('total_defects', 0)}</b></td>
                    <td>موارد بحرانی: <b style="color: #ef4444;">{report_dict.get('critical_defects', 0)}</b></td>
                    <td>شایع‌ترین: <b style="color: #facc15;">{report_dict.get('most_frequent', 'هیچ')}</b></td>
                </tr>
            </table>
        </div>
        """
        self.text_browser.setText(html_content)