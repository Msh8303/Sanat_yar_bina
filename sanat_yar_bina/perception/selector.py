class TargetSelector:
    def __init__(self):
        # ضرایب خطر دقیقا مشابه زمان آموزش RL
        self.risk_factors = {
            0: 1.0,  # crazing
            1: 0.9,  # inclusion
            2: 0.6,  # patches
            3: 0.8,  # pitted_surface
            4: 0.5,  # rolled-in_scale
            5: 0.2   # scratches
        }

    def calculate_frame_risk(self, detections: list, frame_width: int, frame_height: int) -> tuple:
        """
        محاسبه ریسک وزن‌دار و میانگین اطمینان برای کل فریم (تجمیع تمام عیوب)
        """
        if not detections:
            return 0.0, 1.0 # ریسک صفر، اطمینان 100 درصد

        total_weighted_risk = 0.0
        confidences = []
        total_pixels = frame_width * frame_height

        for det in detections:
            # دیکشنری خروجی از detector.py
            normalized_area = det["area_px"] / total_pixels
            cls_id = det["class_id"]
            conf = det["confidence"]

            risk_factor = self.risk_factors.get(cls_id, 0.5)
            # فرمول دقیق زمان آموزش:
            total_weighted_risk += (normalized_area * risk_factor) * 10
            confidences.append(conf)

        final_risk = min(total_weighted_risk, 1.0)
        mean_conf = sum(confidences) / len(confidences)

        return final_risk, mean_conf