import csv
import os
from pathlib import Path
from datetime import datetime
from monitoring.event_model import DetectionEvent
from config.config import PATHS

class EventLogger:
    
    def __init__(self, log_dir: str = None, csv_dir: str = None):
        try:
            actual_log_dir = log_dir if log_dir else os.path.join(PATHS["data_dir"], "logs")
            actual_csv_dir = csv_dir if csv_dir else PATHS["log_dir"]

            self.log_dir = Path(actual_log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "events.jsonl"

            self.csv_dir = Path(actual_csv_dir)
            self.csv_dir.mkdir(parents=True, exist_ok=True)
            
            session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.csv_file = self.csv_dir / f"log_{session_time}.csv"
            
            with open(self.csv_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Frame_ID", "Defect_Class", "Confidence", 
                    "Severity_Score", "Fuzzy_Output", "RL_Output", 
                    "Speed_Before", "Speed_After", "Selected_Action"
                ])
        except Exception as e:
            print(f"[!] Critical Error initializing EventLogger: {e}")
            self.log_file = None
            self.csv_file = None

    def log(self, event: DetectionEvent):
        """ثبت همزمان رویداد در لاگ JSONL و CSV با محافظت کامل در برابر خطای دیسک"""
        try:
            if self.log_file:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(event.to_json() + "\n")
        except Exception as e:
            print(f"[!] Error writing to JSONL log: {e}")
            
        try:
            if self.csv_file:
                with open(self.csv_file, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        event.timestamp,
                        event.frame_id,
                        event.defect_class.upper(),
                        f"{event.confidence:.4f}",
                        f"{event.severity_score:.4f}",
                        f"{event.fuzzy_output:.4f}",
                        f"{event.rl_output:.4f}",
                        f"{event.speed_before:.1f}",
                        f"{event.speed_after:.1f}",
                        event.selected_action
                    ])
        except Exception as e:
            print(f"[!] Error writing to CSV log: {e}")