import sqlite3
from pathlib import Path
from monitoring.event_model import DetectionEvent

class DatabaseManager:
    def __init__(self, db_path: str = "data/factory.db"):
        self.db_path = Path(db_path)
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = self._create_connection()
            self._init_db()
        except Exception as e:
            print(f"[!] Critical Database Initialization Error: {e}")
            self.conn = None

    def _create_connection(self):
        try:
            # ایجاد اتصال با پشتیبانی از چند تردی
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            # فعال‌سازی حالت WAL برای جلوگیری از قفل شدن دیتابیس در خواندن/نوشتن همزمان
            conn.execute("PRAGMA journal_mode=WAL;")
            return conn
        except sqlite3.Error as e:
            print(f"[!] Database connection error: {e}")
            raise

    def _init_db(self):
        """ساخت جدول رویدادها در صورت عدم وجود"""
        if not self.conn:
            return
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
        try:
            self.conn.execute(query)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[!] Error creating database tables: {e}")

    def insert_event(self, event: DetectionEvent):
        """ثبت یک رویداد جدید در دیتابیس با مدیریت خطا"""
        if not self.conn:
            return
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
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, data)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[!] Error inserting event into database: {e}")

    def get_recent_events(self, limit: int = 25) -> list:
        """دریافت N رویداد آخر برای ارسال به مدل زبانی (SLM)"""
        if not self.conn:
            return []
        try:
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows][::-1]
        except sqlite3.Error as e:
            print(f"[!] Error fetching recent events: {e}")
            return []
    
    def get_events_by_time_window(self, seconds: int) -> list:
        """دریافت تمام رویدادهای X ثانیه گذشته بر اساس Timestamp"""
        if not self.conn:
            return []
        from datetime import datetime, timedelta
        try:
            time_threshold = datetime.now() - timedelta(seconds=seconds)
            time_str = time_threshold.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM events WHERE timestamp >= ? ORDER BY id ASC", (time_str,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[!] Error fetching events by time window: {e}")
            return []