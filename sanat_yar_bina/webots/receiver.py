import zmq
import cv2
import numpy as np

class WebotsStreamReceiver:
    """
    ماژول دریافت تصویر زنده از دوربین شبیه‌ساز Webots بر پایه ZeroMQ (IPC/TCP)
    """
    def __init__(self, host="127.0.0.1", port=5555, timeout_ms=300):
        self.host = host
        self.port = port
        self.timeout_ms = timeout_ms
        self.context = zmq.Context()
        self.socket = None
        self.is_connected = False

    def connect(self):
        """برقراری اتصال شبکه با کنترلر Webots"""
        if not self.is_connected:
            self.socket = self.context.socket(zmq.SUB)
            
            # جلوگیری از قفل شدن برنامه (در صورت قطع شدن ویباتز)
            self.socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms) 
            
            # 🔥 لغو صف شبکه و نگه داشتن فقط آخرین فریم (برای رفع مشکل کرش و کندی)
            self.socket.setsockopt(zmq.CONFLATE, 1)
            
            # دریافت تمام داده‌های ارسالی از سرور
            self.socket.setsockopt(zmq.SUBSCRIBE, b'')
            
            # برقراری اتصال
            self.socket.connect(f"tcp://{self.host}:{self.port}")
            self.is_connected = True
            
            print(f"[*] Webots Receiver connected to tcp://{self.host}:{self.port}")

    def get_frame(self):
        """
        دریافت یک فریم زنده از Webots و تبدیل آن به فرمت OpenCV (BGR)
        """
        if not self.is_connected:
            self.connect()

        try:
            # دریافت داده خام تصویر از شبکه
            raw_bytes = self.socket.recv()
            np_array = np.frombuffer(raw_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            return frame
        except zmq.Again:
            # اگر فریم جدیدی در مدت زمان مشخص دریافت نشد (مثلا ویباتز پاز است)
            return None
        except Exception as e:
            print(f"[!] WebotsStreamReceiver Error: {e}")
            return None

    def disconnect(self):
        """بستن ایمن سوکت و منابع ZeroMQ"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        self.is_connected = False
        print("[*] Webots Receiver disconnected cleanly.")