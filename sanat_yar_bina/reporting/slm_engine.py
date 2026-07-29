import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from llama_cpp import Llama
from openai import OpenAI

_global_llm = None

def _init_slm_process(model_path):
    """
    این تابع فقط یک‌بار در پراسسِ جداگانه اجرا می‌شود تا مدل را لود کند.
    نسخه بهینه‌شده برای پردازنده (CPU-Only).
    """
    global _global_llm
    
    num_cores = max(1, multiprocessing.cpu_count() - 2) 
    
    _global_llm = Llama(
        model_path=model_path,
        n_ctx=4096,
        n_batch=512,
        n_threads=num_cores,
        verbose=False
    )

def _generate_in_process(prompt):
    """تولید متن در پراسسِ جداگانه بدون درگیر کردن رشته اصلی برنامه"""
    global _global_llm
    
    # 🔥 مترجم هوشمند: تبدیل پرامپت دیکشنری به قالب استاندارد Qwen
    if isinstance(prompt, dict):
        sys_text = prompt.get("system", "")
        user_text = prompt.get("user", "")
        prompt_string = f"<|im_start|>system\n{sys_text}\n<|im_end|>\n<|im_start|>user\n{user_text}\n<|im_end|>\n<|im_start|>assistant\n"
    else:
        prompt_string = str(prompt)
        
    output = _global_llm(
        prompt_string,
        max_tokens=1500, # افزایش توکن برای جلوگیری از قطع شدن گزارش
        temperature=0.05,       
        top_p=0.7,
        top_k=40,
        min_p=0.05,
        repeat_penalty=1.05,     
        frequency_penalty=0.1,
        presence_penalty=0.0,
        seed=42,
        stop=[
            "<|im_end|>",
            "<|im_start|>user",
            "<|im_start|>system",
            "پایان گزارش.",        
            "پایان گزارش"
        ]
    )
    text = output["choices"][0]["text"].strip()
    return text.replace("<|im_end|>", "").replace("پایان گزارش.", "").strip()

class SLMEngine:
    def __init__(self, model_path: str):
        print(f"[*] Starting Isolated SLM Process on CPU...")
        
        # ساخت پراسس برای مدل لوکال
        self.executor = ProcessPoolExecutor(
            max_workers=1,
            initializer=_init_slm_process,
            initargs=(model_path,)
        )
        print("[+] SLM Isolated Process Ready. (CPU Mode)")
        
        # +++ متغیرهای جدید برای مدیریت API +++
        self.use_api = False
        self.api_key = ""
        self.api_model = ""

    def set_api_mode(self, use_api: bool, api_key: str = "", api_model: str = ""):
        """متدی برای فعال/غیرفعال کردن داینامیک API از طریق رابط کاربری"""
        self.use_api = use_api
        self.api_key = api_key
        self.api_model = api_model
        if self.use_api:
            print(f"[+] Switched to NVIDIA API Mode (Model: {api_model})")
        else:
            print("[+] Switched to Local CPU Mode")

    def _generate_via_api(self, prompt) -> str:
        """پردازش از طریق سرور انویدیا (این تابع نیاز به ProcessPool ندارد چون تحت شبکه است)"""
        try:
            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.api_key
            )
            
            # تبدیل هوشمند پرامپت به فرمت استاندارد OpenAI API
            if isinstance(prompt, dict):
                messages = [
                    {"role": "system", "content": prompt.get("system", "")},
                    {"role": "user", "content": prompt.get("user", "")}
                ]
            else:
                messages = [
                    {"role": "system", "content": "شما یک دستیار هوش مصنوعی متخصص در متالورژی هستید."},
                    {"role": "user", "content": str(prompt)}
                ]

            response = client.chat.completions.create(
                model=self.api_model,
                messages=messages,
                temperature=0.05,
                top_p=0.7,
                max_tokens=1500,
                frequency_penalty=0.1,
                presence_penalty=0.0
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"خطا در ارتباط با سرور انویدیا: {str(e)}\nلطفا اتصال اینترنت و اعتبار کلید API را بررسی کنید."


    def test_api_connection(self, api_key: str, api_model: str) -> tuple:
        """بررسی صحت اتصال به API با یک درخواست مینیمال"""
        try:
            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1", # یا آدرس انویدیا: https://integrate.api.nvidia.com/v1
                api_key=api_key,
                timeout=5.0 # تایم‌اوت ۵ ثانیه‌ای تا برنامه در صورت قطعی اینترنت هنگ نکند
            )
            
            # ارسال یک پرامپت بسیار کوتاه برای تست
            response = client.chat.completions.create(
                model=api_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True, "اتصال با موفقیت برقرار شد."
            
        except Exception as e:
            return False, str(e)
        
    def generate(self, prompt) -> str:
        """تابع اصلی تولید متن که درخواست را به مسیر درست هدایت می‌کند"""
        if self.use_api:
            # اگر حالت API فعال باشد، بدون درگیر کردن مدل محلی به سرور ریکوئست می‌زند
            return self._generate_via_api(prompt)
        else:
            # اگر محلی باشد، پرامپت را به پراسس دوم پرتاب می‌کند
            future = self.executor.submit(_generate_in_process, prompt)
            return future.result()
        #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