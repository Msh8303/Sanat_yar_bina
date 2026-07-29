import json
import csv
from pathlib import Path
from config.config import PATHS

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTabWidget, QSplitter, QTreeWidget, 
                             QTreeWidgetItem, QTableWidget, QTextEdit, QStackedWidget,
                             QHeaderView, QLabel, QTableWidgetItem, QCheckBox, QLineEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from ui.video_widget import VideoWidget
from ui.log_widget import LogWidget
from ui.intelligence_widget import IntelligenceWidget

import json
import csv
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QSplitter, QTreeWidget, 
                             QTreeWidgetItem, QTableWidget, QTextEdit, QStackedWidget,
                             QHeaderView, QLabel, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ArchivePanel(QWidget):
    """Archive panel to display history, CSV Excel tables, and SLM reports"""
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)

        # ==========================================
        # 1. Tree Menu (Right Panel)
        # ==========================================
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("📂 Extracted Files")
        self.tree.setCursor(Qt.PointingHandCursor)
        self.tree.setStyleSheet("""
            QTreeWidget { 
                background-color: #1e293b; color: #cbd5e1; 
                border: 1px solid #334155; border-radius: 5px; 
                padding: 5px; font-family: Tahoma; font-size: 13px;
            }
            QTreeWidget::item { padding: 4px; }
            QTreeWidget::item:hover { background-color: #334155; border-radius: 3px; }
            QTreeWidget::item:selected { background-color: #3b82f6; color: white; border-radius: 3px; font-weight: bold;}
        """)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_refresh = QPushButton("🔄 Refresh Files")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #334155; color: white; padding: 10px; 
                font-family: Tahoma; font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #475569; }
            QPushButton:pressed { background-color: #1e293b; }
        """)
        self.btn_refresh.clicked.connect(self.load_real_data)
        
        right_layout.addWidget(self.btn_refresh)
        right_layout.addWidget(self.tree)

        # ==========================================
        # 2. Content Viewer (Stacked Widget)
        # ==========================================
        self.viewer = QStackedWidget()
        
        # Text Viewer (For JSON & SLM)
        self.text_viewer = QTextEdit()
        self.text_viewer.setReadOnly(True)
        self.text_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a; color: #38bdf8; 
                font-size: 14px; border: 2px solid #334155; 
                border-radius: 5px; padding: 15px; font-family: Consolas, Tahoma;
            }
        """)
        
        # Professional Table Viewer (For CSV)
        self.table_viewer = QTableWidget()
        self.table_viewer.setEditTriggers(QAbstractItemView.NoEditTriggers) # Make it read-only
        self.table_viewer.setSelectionBehavior(QAbstractItemView.SelectRows) # Select entire row
        self.table_viewer.setAlternatingRowColors(True) # Alternate row colors
        self.table_viewer.viewport().setCursor(Qt.PointingHandCursor) # Hand cursor on hover
        self.table_viewer.setStyleSheet("""
            QTableWidget { 
                background-color: #1e293b; 
                alternate-background-color: #0f172a; /* Beautiful striped effect */
                color: #e2e8f0; 
                border: 2px solid #334155; 
                border-radius: 5px;
                gridline-color: #475569; 
                font-family: Tahoma; 
                font-size: 13px;
            }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:hover { 
                background-color: #2563eb; /* Blue highlight on mouse hover */
                color: white; 
            }
            QTableWidget::item:selected { background-color: #1d4ed8; color: white; }
            
            QHeaderView::section { 
                background-color: #0f172a; color: #38bdf8; 
                padding: 8px; border: 1px solid #334155; 
                font-weight: bold; font-size: 14px;
            }
            QTableCornerButton::section { background-color: #0f172a; }
        """)

        # Empty State Label
        self.empty_label = QLabel("Please select an item from the right panel to view its contents...")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #64748b; font-size: 18px; font-family: Tahoma; font-weight: bold;")

        self.viewer.addWidget(self.empty_label)
        self.viewer.addWidget(self.text_viewer)
        self.viewer.addWidget(self.table_viewer)

        self.splitter.addWidget(self.viewer)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([950, 250]) 

        layout.addWidget(self.splitter)
        self.tree.itemClicked.connect(self.on_item_clicked)

    def load_real_data(self):
        """Read actual files from directories using absolute paths"""
        self.tree.clear()
        
        # 🔥 FIX: Using exact absolute paths for all directories
        base_absolute_path_csv = r"C:\Users\MSH8303\Sanat_yar_bina-1\data"
        base_absolute_path = r"C:\Users\MSH8303\Sanat_yar_bina-1\sanat_yar_bina\data"
        csv_dir = Path(rf"{base_absolute_path_csv}\csv_log")
        json_dir = Path(rf"{base_absolute_path}\json_reports")
        txt_dir = Path(rf"{base_absolute_path}\slm_report")
        
        
        # 1. Load CSV Files
        if csv_dir.exists():
            csv_root = QTreeWidgetItem(self.tree, ["📊 Production Logs (CSV)"])
            csv_root.setData(0, Qt.UserRole, "folder")
            for f in sorted(csv_dir.glob("*.csv"), reverse=True): 
                it = QTreeWidgetItem(csv_root, [f.name])
                it.setData(0, Qt.UserRole, "csv")
                it.setData(1, Qt.UserRole, str(f)) 

        # 2. Load JSON Files
        if json_dir.exists():
            j_root = QTreeWidgetItem(self.tree, ["⏱ 40-Sec Summaries (JSON)"])
            j_root.setData(0, Qt.UserRole, "folder")
            for folder in sorted(json_dir.iterdir(), reverse=True):
                if folder.is_dir():
                    sess = QTreeWidgetItem(j_root, [folder.name])
                    sess.setData(0, Qt.UserRole, "folder")
                    for jf in sorted(folder.glob("*.json")):
                        it = QTreeWidgetItem(sess, [jf.name])
                        it.setData(0, Qt.UserRole, "json")
                        it.setData(1, Qt.UserRole, str(jf))

        # 3. Load TXT Files (SLM Reports)
        if txt_dir.exists():
            t_root = QTreeWidgetItem(self.tree, ["🧠 AI Analysis (Qwen SLM)"])
            t_root.setData(0, Qt.UserRole, "folder")
            for folder in sorted(txt_dir.iterdir(), reverse=True):
                if folder.is_dir():
                    sess = QTreeWidgetItem(t_root, [folder.name])
                    sess.setData(0, Qt.UserRole, "folder")
                    for tf in sorted(folder.glob("*.txt")):
                        it = QTreeWidgetItem(sess, [tf.name])
                        it.setData(0, Qt.UserRole, "text")
                        it.setData(1, Qt.UserRole, str(tf))
        
        self.tree.expandAll()

    def on_item_clicked(self, item, column):
        item_type = item.data(0, Qt.UserRole)
        file_path = item.data(1, Qt.UserRole)
        
        if not file_path:
            self.viewer.setCurrentWidget(self.empty_label)
            return

        try:
            if item_type == "csv":
                self.viewer.setCurrentWidget(self.table_viewer)
                # Load CSV into Table
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    reader = list(csv.reader(f))
                    if reader:
                        self.table_viewer.setRowCount(len(reader)-1)
                        self.table_viewer.setColumnCount(len(reader[0]))
                        self.table_viewer.setHorizontalHeaderLabels(reader[0])
                        
                        for r_idx, row in enumerate(reader[1:]):
                            for c_idx, val in enumerate(row):
                                cell_item = QTableWidgetItem(val)
                                cell_item.setTextAlignment(Qt.AlignCenter) # Center align text
                                self.table_viewer.setItem(r_idx, c_idx, cell_item)
                                
                        self.table_viewer.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                        
            elif item_type == "json":
                self.viewer.setCurrentWidget(self.text_viewer)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.text_viewer.setText(json.dumps(data, indent=4, ensure_ascii=False))
                    
            elif item_type == "text":
                self.viewer.setCurrentWidget(self.text_viewer)
                with open(file_path, "r", encoding="utf-8") as f:
                    self.text_viewer.setText(f.read())
                    
        except Exception as e:
            self.viewer.setCurrentWidget(self.text_viewer)
            self.text_viewer.setText(f"Error reading file:\n{str(e)}")

class IndustrialDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Sanat Yar Bina - AI Cyber-Physical Dashboard")
        self.resize(1350, 900) 
        self.setStyleSheet("background-color: #0f172a;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # ==========================================
        # تب‌بندی اصلی سیستم
        # ==========================================
        self.tabs = QTabWidget()
        self.tabs.setCursor(Qt.PointingHandCursor)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; border-radius: 5px; }
            QTabBar::tab { background-color: #1e293b; color: #94a3b8; padding: 10px 20px; font-weight: bold; font-family: Tahoma; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px;}
            QTabBar::tab:selected { background-color: #3b82f6; color: white; }
            QTabBar::tab:hover { background-color: #334155; }
        """)

        # تب اول: مانیتورینگ زنده
        self.tab_live = QWidget()
        self.setup_live_monitoring_tab()
        self.tabs.addTab(self.tab_live, "🔴 مانیتورینگ زنده")

        # تب دوم: آرشیو واقعی
        self.tab_archive = ArchivePanel()
        self.tab_archive.load_real_data() # 🔥 لود کردن فایل‌های واقعی
        self.tabs.addTab(self.tab_archive, "📂 آرشیو و فایل‌های استخراج شده")

        self.main_layout.addWidget(self.tabs)

    def setup_live_monitoring_tab(self):
        layout = QVBoxLayout(self.tab_live)
        layout.setContentsMargins(10, 10, 10, 10)

        self.v_splitter = QSplitter(Qt.Vertical)

        # پنل بالا (ویدیو)
        self.video_panel = VideoWidget()
        self.v_splitter.addWidget(self.video_panel)

        # پنل پایین (اسپلیتر افقی بین لاگ و تحلیل هوشمند)
        self.h_splitter = QSplitter(Qt.Horizontal)
        self.log_panel = LogWidget()
        self.intel_panel = IntelligenceWidget()
        self.h_splitter.addWidget(self.log_panel)
        self.h_splitter.addWidget(self.intel_panel)
        
        self.v_splitter.addWidget(self.h_splitter)
        self.v_splitter.setSizes([600, 300]) # نسبت 2 به 1

        layout.addWidget(self.v_splitter)

        # ==========================================
        # دکمه‌های کنترلی موتور و گزارش‌گیری
        # ==========================================
        self.control_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶ شروع خط تولید")
        self.btn_start.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-family: Tahoma;")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setEnabled(False)
        
        self.btn_stop = QPushButton("⏸ توقف نرم")
        self.btn_stop.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-family: Tahoma;")
        self.btn_stop.setCursor(Qt.PointingHandCursor)

        self.btn_resume = QPushButton("⏯ ادامه حرکت")
        self.btn_resume.setStyleSheet("background-color: #14b8a6; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-family: Tahoma;")
        self.btn_resume.setCursor(Qt.PointingHandCursor)
        self.btn_resume.setEnabled(False)
        
        self.btn_slm = QPushButton("📄 شروع گزارش‌گیری کامل (صیب)")
        self.btn_slm.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-family: Tahoma;")
        self.btn_slm.setCursor(Qt.PointingHandCursor)
        self.btn_slm.setEnabled(False)

        # --- NEW API CONTROLS ---
        self.chk_api = QCheckBox("Use NVIDIA API")
        self.chk_api.setStyleSheet("color: white; font-family: Tahoma; font-weight: bold; padding: 0 10px;")
        
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("NVIDIA API Key")
        self.txt_api_key.setEchoMode(QLineEdit.Password) # Masks the API key for security
        self.txt_api_key.setEnabled(False)
        self.txt_api_key.setStyleSheet("background-color: #1e293b; color: white; padding: 8px; border-radius: 4px; border: 1px solid #334155;")
        
        self.txt_api_model = QLineEdit()
        self.txt_api_model.setPlaceholderText("Model (e.g., meta/llama-3.1-8b-instruct)")
        self.txt_api_model.setEnabled(False)
        self.txt_api_model.setStyleSheet("background-color: #1e293b; color: white; padding: 8px; border-radius: 4px; border: 1px solid #334155;")

        # Enable/Disable input fields based on checkbox state
        self.chk_api.toggled.connect(self.txt_api_key.setEnabled)
        self.chk_api.toggled.connect(self.txt_api_model.setEnabled)
        # ------------------------

        # Adding widgets to the layout
        self.control_layout.addWidget(self.btn_start)
        self.control_layout.addWidget(self.btn_stop)
        self.control_layout.addWidget(self.btn_resume)
        
        self.control_layout.addStretch() # Pushes the following widgets to the right
        
        # Add the new API widgets to the layout before the SLM button
        self.control_layout.addWidget(self.chk_api)
        self.control_layout.addWidget(self.txt_api_key)
        self.control_layout.addWidget(self.txt_api_model)
        
        self.control_layout.addWidget(self.btn_slm)

        layout.addLayout(self.control_layout)

    def update_video(self, frame):
        self.video_panel.update_frame(frame)

    def update_log(self, event):
        self.log_panel.add_log(event)