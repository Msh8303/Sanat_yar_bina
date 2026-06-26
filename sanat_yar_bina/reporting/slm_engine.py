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
        n_ctx=4096,
        n_batch=512,
        n_threads=num_cores,
        # n_gpu_layers حذف شده است چون نیازی به کارت گرافیک نداریم
        verbose=False
    )

def _generate_in_process(prompt):
    """تولید متن در پراسسِ جداگانه بدون درگیر کردن رشته اصلی برنامه"""
    global _global_llm
    
    # 🔥 مترجم هوشمند: اگر پرامپت دیکشنری بود، آن را به قالب استاندارد Qwen تبدیل کن
    if isinstance(prompt, dict):
        sys_text = prompt.get("system", "")
        user_text = prompt.get("user", "")
        prompt_string = f"<|im_start|>system\n{sys_text}\n<|im_end|>\n<|im_start|>user\n{user_text}\n<|im_end|>\n<|im_start|>assistant\n"
    else:
        prompt_string = str(prompt)
        
    output = _global_llm(
    prompt_string,

    max_tokens=240,          # خیلی مهم (جلوی تکرار را می‌گیرد)

    temperature=0.05,        # تقریباً deterministic

    top_p=0.9,

    top_k=30,

    min_p=0.05,

    repeat_penalty=1.18,     # کمی قوی‌تر برای جلوگیری از loop

    frequency_penalty=0.25,  # اگر پشتیبانی شود عالی است

    presence_penalty=0.0,

    seed=42,

    stop=[
        "<|im_end|>",
        "<|im_start|>user",
        "<|im_start|>system"
    ]
)
    text = output["choices"][0]["text"].strip()
    
    return text.replace("<|im_end|>", "").strip()

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