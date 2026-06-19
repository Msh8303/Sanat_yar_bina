import sqlite3
from pathlib import Path
from monitoring.event_model import DetectionEvent

class DatabaseManager:
    def __init__(self, db_path: str = "data/factory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = self._create_connection()
        self._init_db()

    def _create_connection(self):
        # ایجاد اتصال با پشتیبانی از چند تردی
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        # فعال‌سازی حالت WAL برای جلوگیری از قفل شدن دیتابیس در خواندن/نوشتن همزمان
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        """ساخت جدول رویدادها در صورت عدم وجود"""
        query = """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            frame_id INTEGER,
            defect_class TEXT,
            confidence REAL,
            severity_score REAL,
            fuzzy_output REAL,
            rl_output REAL,
            speed_before REAL,
            speed_after REAL,
            selected_action TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def insert_event(self, event: DetectionEvent):
        """ثبت یک رویداد جدید در دیتابیس"""
        query = """
        INSERT INTO events (
            timestamp, frame_id, defect_class, confidence, severity_score, 
            fuzzy_output, rl_output, speed_before, speed_after, selected_action
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        data = (
            event.timestamp, event.frame_id, event.defect_class, event.confidence,
            event.severity_score, event.fuzzy_output, event.rl_output,
            event.speed_before, event.speed_after, event.selected_action
        )
        cursor = self.conn.cursor()
        cursor.execute(query, data)
        self.conn.commit()

    def get_recent_events(self, limit: int = 25) -> list:
        """دریافت N رویداد آخر برای ارسال به مدل زبانی (SLM)"""
        self.conn.row_factory = sqlite3.Row # برای دریافت خروجی به صورت دیکشنری
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows][::-1] # برگرداندن لیست به ترتیب زمان صعودی