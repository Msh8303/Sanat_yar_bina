from dataclasses import dataclass, asdict
import json

@dataclass
class DetectionEvent:
    timestamp: str
    frame_id: int
    defect_class: str
    confidence: float
    severity_score: float
    fuzzy_output: float
    rl_output: float
    speed_before: float
    speed_after: float
    selected_action: str

    def to_dict(self) -> dict:
        """تبدیل ایمن کلاس به دیکشنری برای ذخیره در JSON یا دیتابیس"""
        return asdict(self)

    def to_json(self) -> str:
        """تبدیل به رشته JSON"""
        return json.dumps(self.to_dict())