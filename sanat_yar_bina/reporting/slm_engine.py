import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from llama_cpp import Llama

# متغیر گلوبال برای بارگذاری مدل فقط در پراسسِ دوم (ایزوله)
_global_llm = None

def _init_slm_process(model_path):
    """
    این تابع فقط یک‌بار در پراسسِ جداگانه اجرا می‌شود تا مدل را لود کند.
    نسخه بهینه‌شده برای پردازنده (CPU-Only).
    """
    global _global_llm
    
    # اختصاص تمام هسته‌های CPU منهای ۲ (برای اینکه ویندوز و بقیه برنامه‌ها هنگ نکنند)
    num_cores = max(1, multiprocessing.cpu_count() - 2) 
    
    _global_llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=num_cores,
        # n_gpu_layers حذف شده است چون نیازی به کارت گرافیک نداریم
        verbose=False
    )

def _generate_in_process(prompt):
    """تولید متن در پراسسِ جداگانه بدون درگیر کردن رشته اصلی برنامه"""
    global _global_llm
    output = _global_llm(
        prompt,
        max_tokens=1200,           # 🔥 توکن بالا برای جلوگیری از نصفه ماندن گزارش‌های طولانی فارسی
        temperature=0.05,
        top_p=0.8,
        top_k=15,
        repeat_penalty=1.2,
        stop=[
            "<|im_end|>",
            "<|im_start|>user",
            "<|im_start|>system"
        ] # 🔥 تگ‌های توقف مخصوص Qwen
    )
    return output['choices'][0]['text'].strip()

class SLMEngine:
    def __init__(self, model_path: str):
        print(f"[*] Starting Isolated SLM Process on CPU...")
        
        # ساخت یک پراسس (OS Process) کاملاً مستقل از برنامه اصلی
        self.executor = ProcessPoolExecutor(
            max_workers=1,
            initializer=_init_slm_process,
            initargs=(model_path,)
        )
        print("[+] SLM Isolated Process Ready. (CPU Mode)")

    def generate(self, prompt: str) -> str:
        """
        پرامپت را به پراسس دوم پرتاب می‌کند و منتظر جواب می‌ماند.
        """
        future = self.executor.submit(_generate_in_process, prompt)
        return future.result()