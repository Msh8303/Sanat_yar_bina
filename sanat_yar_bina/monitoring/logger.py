from pathlib import Path
from monitoring.event_model import DetectionEvent

class EventLogger:
    def __init__(self, log_dir: str = "data/logs", log_filename: str = "events.jsonl"):
        """
        ایجاد پوشه لاگ در صورت عدم وجود و تنظیم مسیر فایل
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / log_filename

    def log(self, event: DetectionEvent):
        """
        اضافه کردن (Append) یک رویداد به انتهای فایل لاگ
        """
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")