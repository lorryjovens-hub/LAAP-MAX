"""
LAAP Unified TTS Bridge — FishSpeech + CosyVoice + GPT-SoVITS Auto-Detect
"""
import json, base64, time, threading
from pathlib import Path

ENDPOINTS = {
    "fishspeech": "http://127.0.0.1:9991",
    "cosyvoice": "http://127.0.0.1:9992",
    "gptsovits": "http://127.0.0.1:9880",
}
VOICES_DIR = Path(__file__).parent / "voices"

# EdgeTTS fallback
from laap_web import tts_sync

def check_engines():
    """Return status of all TTS engines"""
    import requests
    results = {}
    for name, url in ENDPOINTS.items():
        try:
            r = requests.get(f"{url}/status" if name != "fishspeech" else f"{url}/v1/models", timeout=2)
            results[name] = {"online": True, "url": url}
        except:
            results[name] = {"online": False, "url": url}
    return results

def tts(text, preferred="fishspeech"):
    """TTS with auto-fallback: preferred → others → EdgeTTS"""
    import requests
    
    # Try preferred engine first
    engines = [preferred] + [e for e in ENDPOINTS if e != preferred]
    
    for eng in engines:
        try:
            url = ENDPOINTS[eng]
            if eng == "fishspeech":
                r = requests.post(f"{url}/v1/tts", json={
                    "input": text,
                    "voice": "default",
                    "response_format": "wav"
                }, timeout=30)
                if r.status_code == 200:
                    print(f"  TTS: FishSpeech ({len(r.content)} bytes)")
                    return r.content
                    
            elif eng == "cosyvoice":
                r = requests.post(f"{url}/tts", json={
                    "text": text,
                    "mode": "zero_shot",
                    "stream": False
                }, timeout=30)
                if r.status_code == 200:
                    print(f"  TTS: CosyVoice ({len(r.content)} bytes)")
                    return r.content
                    
            elif eng == "gptsovits":
                r = requests.post(f"{url}/tts", json={
                    "text": text,
                    "text_language": "zh",
                    "stream_chunk": False
                }, timeout=30)
                if r.status_code == 200:
                    print(f"  TTS: GPT-SoVITS ({len(r.content)} bytes)")
                    return r.content
        except:
            continue
    
    # Fallback
    print("  TTS: EdgeTTS (fallback)")
    return tts_sync(text)

def tts_stream(text, on_chunk, preferred="fishspeech"):
    """Streaming TTS with auto-fallback"""
    import websockets.sync.client as ws_client
    import requests
    
    try:
        url = ENDPOINTS.get(preferred)
        if preferred == "fishspeech" and url:
            with ws_client.connect(f"{url.replace('http','ws')}/v1/tts/stream") as ws:
                ws.send(json.dumps({"input": text, "voice": "default"}))
                for msg in ws:
                    data = json.loads(msg)
                    if "audio" in data:
                        on_chunk(base64.b64decode(data["audio"]))
                    elif data.get("done"):
                        break
            return
    except:
        pass
    
    # Fallback to sync TTS
    audio = tts(text)
    if audio:
        on_chunk(audio)
