import pickle
import numpy as np

# آدرس دقیق فایل مدل آموزش دیده خود را اینجا بگذارید
model_path = r"C:\Users\MSH8303\Sanat_yar_bina-1\sanat_yar_bina\models\hybrid_rl.pkl" 

try:
    with open(model_path, 'rb') as f:
        data = pickle.load(f)
        
    print("✅ فایل با موفقیت خوانده شد.")
    print(f"نوع داده ذخیره شده: {type(data)}")
    
    if isinstance(data, np.ndarray):
        print(f"ابعاد ماتریس Q-Table شما: {data.shape}")
        
    elif isinstance(data, dict):
        print(f"تعداد ردیف‌های دیکشنری: {len(data)}")
        if len(data) > 0:
            sample_key = list(data.keys())[0]
            print(f"نمونه کلید: {sample_key} | نمونه مقادیر: {data[sample_key]}")
            
except Exception as e:
    print(f"❌ خطا در خواندن فایل: {e}")