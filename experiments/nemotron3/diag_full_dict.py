# Diagnostic: can we materialize the full 8GB state dict at all right now?
import sys, time, tracemalloc
sys.path.insert(0, r"D:\LAAP\experiments\nemotron3")
from st_nommap import _LazySafeOpen
import psutil  # may not exist

p = r"D:\LAAP\models\nemotron-3-nano-4b-bf16\model.safetensors"
t0 = time.time()
peak = 0
with _LazySafeOpen(p) as f:
    d = {}
    for k in f.keys():
        d[k] = f.get_tensor(k)
print("dict size GB:", sum(v.numel()*2 for v in d.values())/1e9)
print("time:", round(time.time()-t0, 1))
try:
    import psutil
    print("current RSS GB:", round(psutil.Process().memory_info().rss/1e9, 2))
except ImportError:
    print("psutil not available")
print("FULL DICT OK")
