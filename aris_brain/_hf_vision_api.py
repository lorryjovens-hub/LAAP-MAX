"""
Try HuggingFace free Inference API for image captioning.
No local model needed - just an HTTP request.
"""
import base64, json, urllib.request, urllib.error

IMG_PATH = r'C:\Users\user\AppData\Local\hermes\profiles\laap-avatar-v4\image_cache\img_1cdd68034bd5.jpg'

# Read and encode image
with open(IMG_PATH, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Try different models on HF Inference API
models = [
    "Salesforce/blip-image-captioning-base",
    "microsoft/Florence-2-base",
    "nlpconnect/vit-gpt2-image-captioning",
]

for model in models:
    print(f"\nTrying {model}...")
    try:
        payload = json.dumps({
            "inputs": img_b64,
            "parameters": {"max_new_tokens": 50}
        }).encode()
        
        req = urllib.request.Request(
            f"https://api-inference.huggingface.co/models/{model}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        print(f"✅ Result: {result}")
        
        # Save result
        with open('D:/LAAP/aris_brain/_hf_caption.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False))
        break
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code}: {body[:200]}")
        continue
    except Exception as e:
        print(f"  Error: {e}")
        continue
else:
    print("\nAll HF models failed - trying free API endpoints...")
    # Try ollama if it's already got minicpm-v
    try:
        payload = json.dumps({
            "model": "minicpm-v",
            "prompt": "Describe this image in detail in Chinese.",
            "images": [img_b64],
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        print(f"Ollama: {result.get('response', 'no response')[:200]}")
        with open('D:/LAAP/aris_brain/_hf_caption.txt', 'w') as f:
            f.write(result.get('response', 'no response'))
    except Exception as e:
        print(f"Ollama local failed: {e}")
