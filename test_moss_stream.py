"""测试 MOSS-TTS-Nano 流式推理"""
import sys, os, gc, time
sys.path.insert(0, "C:/Users/user/AppData/Roaming/Python/Python313/site-packages")
os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"

import torch
import torchaudio
torch.set_num_threads(4)

import soundfile as sf
import numpy as np
from transformers import AutoModel

MODEL_PATH = "E:\\models\\MOSS-TTS-Nano-100M"
AUDIO_TOKENIZER = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano"
AUDIO_TOKENIZER="OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano"
REF_AUDIO = "E:\\models\\aymis_happy_ref.wav"

# Patch torchaudio save
def patched_save(filepath, src, sample_rate, **kwargs):
    try:
        sf.write(str(filepath), src.cpu().numpy().T if src.is_cuda else src.numpy().T, sample_rate)
    except Exception as e:
        print(f"save error: {e}, trying alt...")
        arr = src.cpu().numpy() if src.is_cuda else src.numpy()
        sf.write(str(filepath), arr.T, sample_rate)
torchaudio.save = patched_save

# Load model
import types
model = AutoModel.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
    dtype=torch.float32,
    low_cpu_mem_usage=True,
    attn_implementation="eager",
)

def _load_ref(self, path, target_sr, target_ch):
    data, sr = sf.read(str(path), dtype='float32')
    # data shape: (samples,) for mono, (samples, channels) for stereo
    if len(data.shape) == 1:
        wf = torch.from_numpy(data).unsqueeze(0)  # [1, samples]
    else:
        wf = torch.from_numpy(data).T  # [channels, samples]
    
    if sr != target_sr:
        from torch.nn.functional import interpolate
        orig_len = wf.shape[-1]
        new_len = int(orig_len * target_sr / sr)
        # interpolate needs [N, C, T]
        wf = interpolate(wf.unsqueeze(0), size=new_len, mode='linear', align_corners=False)
        wf = wf.squeeze(0)  # [C, T]
    
    if wf.shape[0] < target_ch:
        wf = wf.expand(target_ch, -1).contiguous()
    elif wf.shape[0] > target_ch:
        wf = wf[:target_ch]
    return wf.to(dtype=torch.float32), target_sr
model._load_reference_audio = types.MethodType(_load_ref, model)
model.eval()

# Test streaming
print("\n=== 测试流式推理 ===")
text = "主人，你终于回来啦~人家想你了！"
chunks = []
start = time.time()

for i, chunk in enumerate(model.inference_stream(
    text=text,
    output_audio_path="E:\\models\\stream_test.wav",
    mode="voice_clone",
    reference_audio_path=REF_AUDIO,
    audio_tokenizer_type="moss-audio-tokenizer-nano",
    audio_tokenizer_pretrained_name_or_path=AUDIO_TOKENIZER,
    device="cpu",
    max_new_frames=600,
    do_sample=True,
)):
    print(f"  Chunk {i}: type={chunk.get('type','?')}, ", end="")
    if "waveform" in chunk and chunk.get('type') != 'result':
        audio = chunk["waveform"]
        print(f"waveform shape={audio.shape}")
        chunks.append(audio.cpu())
    elif chunk.get('type') == 'result':
        print(f"result: sample_rate={chunk.get('sample_rate')}, path={chunk.get('audio_path','')}")
    elif "decoded_sample_rate" in chunk:
        print(f"sample_rate={chunk['decoded_sample_rate']}")
    elif "generated" in chunk:
        print(f"generated={chunk['generated']}")
    else:
        print(str(chunk)[:80])

elapsed = time.time() - start
print(f"\n总耗时: {elapsed:.1f}s")
print(f"音频块数: {len(chunks)}")

if chunks:
    full_audio = torch.cat(chunks, dim=-1)
    print(f"完整音频: {full_audio.shape}, {full_audio.numel()/full_audio.shape[-1]*40:.0f}ms")
    out = "E:\\models\\stream_final.wav"
    sf.write(out, full_audio.numpy().T, 48000)
    print(f"保存到: {out}")
