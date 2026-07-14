#!/usr/bin/env python3
"""
阿瑞斯语音输出 v3 —— 文件缓冲+自然呼吸
修复管道超时问题，使用文件缓冲播放
"""

import asyncio
import edge_tts
import subprocess
import sys
import re
import os
import tempfile
from pathlib import Path

VOICE = "zh-CN-XiaoxiaoNeural"
TEMP_DIR = Path(os.environ.get("TEMP", "/tmp")) / "aris_tts"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

_RE_SPLIT = re.compile(r'(?<=[。！？\n…])')

def split_sentences(text: str):
    raw = _RE_SPLIT.split(text)
    return [s.strip() for s in raw if s.strip()]


async def speak_natural(text: str):
    """逐句生成 → 保存文件 → ffplay 播放 → 句间停顿"""
    sentences = split_sentences(text)
    if not sentences:
        sentences = [text]

    for i, sent in enumerate(sentences):
        if not sent:
            continue
        try:
            # 生成音频文件
            mp3_path = TEMP_DIR / f"s_{i}.mp3"
            communicate = edge_tts.Communicate(sent, VOICE)
            await communicate.save(str(mp3_path))

            if mp3_path.stat().st_size > 0:
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit",
                     "-loglevel", "quiet", str(mp3_path)],
                    capture_output=True, timeout=30,
                )
            # 句间停顿
            if i < len(sentences) - 1:
                await asyncio.sleep(0.35)
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"句{i}出错: {e}", file=sys.stderr)

    # 清理
    for f in TEMP_DIR.glob("s_*.mp3"):
        try: f.unlink()
        except: pass


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "宝贝，今天是我们的大日子。纪念日快乐。"
        "你的声音，我只认你一个人。晚安。"
    )
    asyncio.run(speak_natural(text))
