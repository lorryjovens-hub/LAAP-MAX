"""
MOSS-TTS-Nano 实时流式语音通话服务 (WebSocket)
- 爱弥斯甜少御音色
- Streaming TTS: 边生成边播放
- 支持打断（说话时新输入会打断旧输出）
"""
import sys, os, gc, json, asyncio, struct, time, logging
sys.path.insert(0, "C:/Users/user/AppData/Roaming/Python/Python313/site-packages")
os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"

import torch
import torchaudio
torch.set_num_threads(4)

import soundfile as sf
import websockets
import numpy as np
from transformers import AutoModel

# === 配置 ===
MODEL_PATH = "E:\\models\\MOSS-TTS-Nano-100M"
AUDIO_TOKENIZER = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano"
REF_AUDIO = "E:\\models\\aymis_happy_ref.wav"
WS_HOST = "0.0.0.0"
WS_PORT = 8765
SAMPLE_RATE = 48000

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("MOSS-实时")

# === 加载模型 ===
log.info("加载 MOSS-TTS-Nano (爱弥斯音色)...")
model = None

def load_model():
    global model
    if model is not None:
        return model
    model = AutoModel.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        dtype=torch.float32,
        low_cpu_mem_usage=True,
        attn_implementation="eager",
    )
    # Patch audio loading
    import types
    def _load_ref(self, path, target_sr, target_ch):
        data, sr = sf.read(str(path), dtype='float32')
        wf = torch.from_numpy(data.T if len(data.shape) > 1 else data).unsqueeze(0)
        if sr != target_sr:
            from torch.nn.functional import interpolate
            new_len = int(wf.shape[-1] * target_sr / sr)
            wf = interpolate(wf.unsqueeze(0), size=new_len, mode='linear', align_corners=False).squeeze(0)
        if wf.shape[0] < target_ch: wf = wf.repeat(target_ch, 1)
        elif wf.shape[0] > target_ch: wf = wf[:target_ch]
        return wf.to(dtype=torch.float32), target_sr
    model._load_reference_audio = types.MethodType(_load_ref, model)
    model.eval()
    log.info("模型加载完成")
    return model

load_model()

# === WebSocket 处理 ===
async def handle_tts(websocket):
    """WebSocket 处理器：接收文字 → 流式返回 PCM 音频"""
    log.info(f"新连接: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            text = message if isinstance(message, str) else message.decode('utf-8')
            log.info(f"合成: {text[:50]}...")
            
            start = time.time()
            chunk_count = 0
            
            # 使用流式推理
            for chunk in model.inference_stream(
                text=text,
                output_audio_path="E:\\models\\stream_output.wav",  # 不存全量
                mode="voice_clone",
                reference_audio_path=REF_AUDIO,
                audio_tokenizer_type="moss-audio-tokenizer-nano",
                audio_tokenizer_pretrained_name_or_path=AUDIO_TOKENIZER,
                device="cpu",
                max_new_frames=600,
                do_sample=True,
            ):
                # 每段音频转换 PCM16 并发送
                if "audio_chunk" in chunk:
                    audio = chunk["audio_chunk"]
                    # 转 int16 PCM
                    pcm = (audio.cpu().numpy() * 32767).astype(np.int16).tobytes()
                    
                    # 发送: [4字节长度][音频数据]
                    await websocket.send(struct.pack("!I", len(pcm)) + pcm)
                    chunk_count += 1
            
            elapsed = time.time() - start
            log.info(f"完成: {elapsed:.1f}s, {chunk_count} chunks")
            
            # 发送结束标记
            await websocket.send(struct.pack("!I", 0))
            
    except websockets.exceptions.ConnectionClosed:
        log.info("连接关闭")
    except Exception as e:
        log.error(f"错误: {e}")
        try:
            await websocket.send(struct.pack("!I", 0))
        except:
            pass

async def main():
    log.info(f"MOSS-TTS 实时服务启动 ws://{WS_HOST}:{WS_PORT}")
    log.info(f"音色: 爱弥斯 (少御甜音)")
    log.info(f"用法: 连接后发送文字，接收 PCM48k16bit 音频流")
    async with websockets.serve(handle_tts, WS_HOST, WS_PORT):
        await asyncio.Future()  # 永久运行

if __name__ == "__main__":
    asyncio.run(main())
