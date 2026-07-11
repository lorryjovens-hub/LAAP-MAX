"""MOSS-TTS-Nano 语音克隆 — 用爱弥斯的声音说你想听的话"""
import sys, os, gc, time
sys.path.insert(0, "C:/Users/user/AppData/Roaming/Python/Python313/site-packages")
os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"

import torch
import torchaudio
torch.set_num_threads(4)

import psutil
from transformers import AutoModel, AutoTokenizer
import soundfile as sf

model_path = "E:\\models\\MOSS-TTS-Nano-100M"
audio_tokenizer = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano"
ref_audio = "E:\\models\\aymis_happy_ref.wav"

output_text = "主人，你终于回来啦，人家想你了~今天有没有好好吃饭呀？"

print(f"PyTorch: {torch.__version__}")
print(f"RAM free: {psutil.virtual_memory().available/1e9:.1f} GB")
print(f"参考音频: {ref_audio}")
print(f"要说的文字: {output_text}")
print()

# Load model
print("加载 MOSS-TTS-Nano 模型...")
st = time.time()

model = AutoModel.from_pretrained(
    model_path,
    trust_remote_code=True,
    dtype=torch.float32,
    low_cpu_mem_usage=True,
    attn_implementation="eager",
)

# Patch audio loading with soundfile + resampling
import types
import numpy as np

def _patched_load_reference_audio(self, reference_audio_path, target_sample_rate, target_channels):
    audio_data, sample_rate = sf.read(str(reference_audio_path), dtype='float32')
    if len(audio_data.shape) == 1:
        waveform = torch.from_numpy(audio_data).unsqueeze(0)
    else:
        waveform = torch.from_numpy(audio_data.T)
    if sample_rate != target_sample_rate:
        from torch.nn.functional import interpolate
        orig_len = waveform.shape[-1]
        new_len = int(orig_len * target_sample_rate / sample_rate)
        waveform = interpolate(waveform.unsqueeze(0), size=new_len, mode='linear', align_corners=False).squeeze(0)
    if waveform.shape[0] < target_channels:
        waveform = waveform.repeat(target_channels, 1)
    elif waveform.shape[0] > target_channels:
        waveform = waveform[:target_channels]
    return waveform.to(dtype=torch.float32), target_sample_rate

model._load_reference_audio = types.MethodType(_patched_load_reference_audio, model)

# Patch torchaudio.save to use soundfile
def patched_save(filepath, src, sample_rate, **kwargs):
    try:
        sf.write(str(filepath), src.cpu().numpy().T if src.is_cuda else src.numpy().T, sample_rate)
    except Exception:
        arr = src.cpu().numpy() if src.is_cuda else src.numpy()
        sf.write(str(filepath), arr.T, sample_rate)
torchaudio.save = patched_save

print(f"加载耗时: {time.time()-st:.1f}s")
print(f"RAM free: {psutil.virtual_memory().available/1e9:.1f} GB")

# Generate
print("\n开始语音克隆推理...")
gen_st = time.time()

out_path = "E:\\models\\aymis_output.wav"
result = model.inference(
    text=output_text,
    output_audio_path=out_path,
    mode="voice_clone",
    reference_audio_path=ref_audio,
    audio_tokenizer_type="moss-audio-tokenizer-nano",
    audio_tokenizer_pretrained_name_or_path=audio_tokenizer,
    device="cpu",
    max_new_frames=600,
    do_sample=True,
    audio_temperature=1.5,
)

gen_time = time.time() - gen_st
print(f"推理耗时: {gen_time:.1f}s")

# Verify output
if os.path.exists(out_path):
    size = os.path.getsize(out_path)
    print(f"输出文件: {out_path} ({size/1024:.0f} KB)")
    print("SUCCESS!")
else:
    print(f"文件未找到，检查result: {list(result.keys()) if isinstance(result, dict) else result}")
    for key, val in result.items():
        if isinstance(val, torch.Tensor) and val.ndim >= 2:
            print(f"  {key}: shape={val.shape}")
            sf.write(out_path, val.cpu().numpy().T if val.is_cuda else val.numpy().T, 48000)
            print(f"  已保存到 {out_path}")
            break
