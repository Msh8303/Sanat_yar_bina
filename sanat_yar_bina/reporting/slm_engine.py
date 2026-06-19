import multiprocessing
from llama_cpp import Llama

class SLMEngine:
    def __init__(self, model_path: str):
        """بارگذاری مدل زبانی مستقیماً از روی فایل لوکال (آفلاین)"""
        num_cores = max(1, multiprocessing.cpu_count() - 2)
        
        print(f"[*] Loading SLM Model from local file: {model_path} ...")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,           
            n_threads=num_cores,  
            verbose=False         
        )
        print("[+] SLM Engine Ready.")

    def generate(self, prompt: str) -> str:
        output = self.llm(
            prompt,
            max_tokens=250,      
            temperature=0.1,     
            stop=["<|user|>"]    
        )
        return output['choices'][0]['text'].strip()