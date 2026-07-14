#!/usr/bin/env python3
"""
Aris 离线语音识别 — Windows SAPI 适配器
=========================================
使用 Windows 内置语音识别引擎，完全离线。

优势：
  - 零下载：Windows 自带，无需任何模型文件
  - 支持中文：系统级中文语音识别
  - 完全离线：不依赖任何网络服务
  - 免配置：即装即用

用法：
  python sapi_stt.py                    # 聆听一次
  python sapi_stt.py --once             # 聆听一次（同默认）
  python sapi_stt.py --loop             # 持续聆听（测试用）
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("aris.sapi_stt")


def listen(timeout: int = 5, phrase_time: int = 5) -> Optional[str]:
    """
    通过 Windows SAPI 聆听一次
    
    Args:
        timeout: 等待说话的超时（秒）
        phrase_time: 一句话的最大时长（秒）
        
    Returns:
        识别文本，失败返回 None
    """
    try:
        import pythoncom
        pythoncom.CoInitialize()
        
        import win32com.client
        from win32com.client import constants
        
        # 创建识别器
        recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
        
        # 创建识别上下文
        context = recognizer.CreateRecoContext()
        
        # 设置音频输入（默认麦克风）
        audio = win32com.client.Dispatch("SAPI.SpAudioFormat")
        audio.Type = constants.SAFTDefault
        
        # 创建语法（自由听写模式）
        grammar = context.CreateGrammar()
        grammar.DictationSetState(1)  # 启用听写
        
        # 事件标志
        result_event = threading.Event()
        recognized_text = [""]
        
        def on_recognition(stream_number, stream_position, recognition_type, result):
            """识别结果回调"""
            try:
                phrase = result.PhraseInfo
                text = phrase.GetText()
                recognized_text[0] = text
                result_event.set()
            except Exception as e:
                logger.debug(f"SAPI 回调错误: {e}")
        
        # 注册事件
        from win32com.client import with_events
        from win32comext.speech import constants as speech_consts
        
        # 创建事件接收器
        class RecognitionHandler:
            def OnRecognition(self, stream_number, stream_position, recognition_type, result):
                on_recognition(stream_number, stream_position, recognition_type, result)
        
        handler = RecognitionHandler()
        conn = win32com.client.WithEvents(grammar, handler)
        
        # 等待结果（带超时）
        result_event.wait(timeout=timeout)
        
        # 清理
        grammar.DictationSetState(0)
        pythoncom.CoUninitialize()
        
        text = recognized_text[0].strip()
        return text if text else None
        
    except Exception as e:
        logger.error(f"SAPI 聆听失败: {e}")
        return None


def listen_with_vad(timeout: int = 10) -> Optional[str]:
    """
    带 VAD 的 SAPI 聆听（使用 speech_recognition 库捕获音频，
    然后用 SAPI 识别，实现离线识别）
    
    先录制音频，再用 SAPI 识别——离线、无网络、零配置。
    """
    try:
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 200
        recognizer.pause_threshold = 0.5
        
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
        
        # 用 SAPI 识别（离线）
        return _recognize_sapi(audio)
        
    except sr.WaitTimeoutError:
        return None
    except Exception as e:
        logger.error(f"VAD+SAPI 聆听失败: {e}")
        return None


def _recognize_sapi(audio) -> Optional[str]:
    """
    用 Windows SAPI 识别音频
    
    Args:
        audio: speech_recognition AudioData 对象
        
    Returns:
        识别文本
    """
    try:
        import wave
        import tempfile
        import os
        
        # 保存音频到临时 WAV 文件
        wav_data = audio.get_wav_data()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(wav_data)
        
        try:
            # 用 SAPI 识别
            import pythoncom
            pythoncom.CoInitialize()
            
            import win32com.client
            from win32com.client import constants
            
            # 创建文件输入流
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            stream.Open(temp_path, constants.SSFMOpenForRead)
            
            # 创建识别器
            recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
            context = recognizer.CreateRecoContext()
            grammar = context.CreateGrammar()
            grammar.DictationSetState(1)
            
            # 识别
            result = recognizer.Recognize(stream)
            text = ""
            if result:
                text = result.PhraseInfo.GetText()
            
            stream.Close()
            pythoncom.CoUninitialize()
            
            return text.strip() if text.strip() else None
            
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    except Exception as e:
        logger.error(f"SAPI 识别失败: {e}")
        return None


def test_sapi():
    """测试 SAPI 是否可用"""
    try:
        import pythoncom
        pythoncom.CoInitialize()
        import win32com.client
        recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
        voices = win32com.client.Dispatch("SAPI.SpVoice")
        print(f"✅ Windows SAPI 可用")
        print(f"   TTS 声音数: {voices.GetVoices().Count}")
        for v in voices.GetVoices():
            print(f"   - {v.GetDescription()}")
        pythoncom.CoUninitialize()
        return True
    except Exception as e:
        print(f"❌ SAPI 不可用: {e}")
        return False


if __name__ == "__main__":
    import threading  # needed for the event system
    
    if "--test" in sys.argv or "-t" in sys.argv:
        test_sapi()
    elif "--listen" in sys.argv or "-l" in sys.argv:
        print("🎤 聆听中（说一句话）...")
        text = listen()
        if text:
            print(f"✅ 识别: {text}")
        else:
            print("❌ 未识别")
    elif "--vad" in sys.argv:
        print("🎤 VAD+离线识别模式（说一句话）...")
        text = listen_with_vad()
        if text:
            print(f"✅ 识别: {text}")
        else:
            print("❌ 未识别或超时")
    else:
        print("Aris 离线 STT (SAPI)")
        print("用法:")
        print("  python sapi_stt.py --test    # 测试 SAPI 可用性")
        print("  python sapi_stt.py --listen  # 聆听一次")
        print("  python sapi_stt.py --vad     # VAD+SAPI 模式")
