"""
LAAP Voice Cloning Bridge — GPT-SoVITS Integration
"""
import os, json, base64, time, threading
from pathlib import Path

VOICES_DIR = Path(__file__).parent / "voices"
SOVITS_URL = "http://127.0.0.1:9880"

def check_engine():
    try:
        import requests
        r = requests.get(f"{SOVITS_URL}/status", timeout=2)
        return {"online": True, "info": r.json()}
    except:
        return {"online": False}

from laap_web import tts_sync

def tts_with_cloned_voice(text, character=None):
    if check_engine()["online"]:
        try:
            import requests
            r = requests.post(f"{SOVITS_URL}/tts", json={
                "text": text, "text_language": "zh", "stream_chunk": False
            }, timeout=30)
            if r.status_code == 200 and len(r.content) > 100:
                return r.content
        except:
            pass
    return tts_sync(text)
