"""
Try tiny vision models from HuggingFace for image captioning.
"""
import os, sys
from PIL import Image

IMG_PATH = r'C:\Users\user\AppData\Local\hermes\profiles\laap-avatar-v4\image_cache\img_1cdd68034bd5.jpg'

# Try to redirect cache to D: to save C: space
cache_dir = 'D:/hf_cache'
os.makedirs(cache_dir, exist_ok=True)

# Check disk
import shutil
total, used, free = shutil.disk_usage('D:/')
c_free = shutil.disk_usage('C:/').free
print(f"C: free: {c_free/1e9:.1f}GB")
print(f"D: free: {free/1e9:.1f}GB")

# Only attempt if enough space
MIN_REQUIRED = 1.5e9  # 1.5GB
if free < MIN_REQUIRED:
    print(f"Not enough space on D: (needs ~{MIN_REQUIRED/1e9:.1f}GB, has {free/1e9:.1f}GB)")
    sys.exit(0)

# Try to load a tiny captioning model
# microsoft/Florence-2-base-ft is good but ~1.2GB
# nlpconnect/vit-gpt2-image-captioning is ~500MB but older
try:
    from transformers import pipeline, AutoProcessor, AutoModelForCausalLM
    
    # Try several models in order of size
    models_to_try = [
        ("nlpconnect/vit-gpt2-image-captioning", "image-to-text"),
        # Fallbacks if we have more space
    ]
    
    for model_name, task in models_to_try:
        print(f"Trying {model_name}...")
        try:
            pipe = pipeline(task, model=model_name, cache_dir=cache_dir)
            img = Image.open(IMG_PATH)
            result = pipe(img)
            print(f"Result: {result}")
            # Save the result
            with open('D:/LAAP/aris_brain/_caption_result.txt', 'w', encoding='utf-8') as f:
                f.write(str(result))
            break
        except Exception as e:
            print(f"  Failed: {e}")
            continue
    else:
        print("All models failed")
except ImportError:
    print("transformers not installed properly")
except Exception as e:
    print(f"Error: {e}")
