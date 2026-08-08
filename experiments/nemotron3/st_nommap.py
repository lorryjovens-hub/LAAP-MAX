# ARIS-PATCH v2: lazy safetensors reader (no mmap, no full-memory load)
# - replaces safetensors.torch.load_file
# - replaces transformers.modeling_utils.safe_open with a lazy context manager
import json, struct, torch
import safetensors.torch as _st

_DTYPES = {
    "BF16": torch.bfloat16, "F16": torch.float16, "F32": torch.float32,
    "F64": torch.float64, "I64": torch.int64, "I32": torch.int32,
    "I16": torch.int16, "I8": torch.int8, "U8": torch.uint8, "BOOL": torch.bool,
}

def _read_tensor(f, base, start, end, dtype_name, shape, device):
    f.seek(base + start)
    raw = f.read(end - start)
    t = torch.frombuffer(bytearray(raw), dtype=_DTYPES[dtype_name]).reshape(shape)
    if device not in (None, "cpu"):
        t = t.to(device)
    return t

class _Slice:
    def __init__(self, f, base, v, device):
        self._f = f
        self._base = base
        self._v = v
        self._device = device

    def get_shape(self):
        return self._v["shape"]

    def get_dtype(self):
        return self._v["dtype"]

    def __getitem__(self, idx):
        start, end = self._v["data_offsets"]
        t = _read_tensor(self._f, self._base, start, end, self._v["dtype"], self._v["shape"], self._device)
        return t[idx]

class _LazySafeOpen:
    def __init__(self, filename, framework="pt", device="cpu"):
        self._f = open(filename, "rb")
        head_len = struct.unpack("<Q", self._f.read(8))[0]
        self._header = json.loads(self._f.read(head_len))
        self._base = 8 + head_len
        self._device = device

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self._f.close()

    def keys(self):
        return [k for k in self._header if k != "__metadata__"]

    def metadata(self):
        return self._header.get("__metadata__")

    def get_slice(self, k):
        v = self._header[k]
        return _Slice(self._f, self._base, v, self._device)

    def get_tensor(self, k):
        return self.get_slice(k)[:]

def load_file_no_mmap(filename, device="cpu"):
    with _LazySafeOpen(filename, device=device) as f:
        return {k: f.get_tensor(k) for k in f.keys()}

_st.load_file = load_file_no_mmap
try:
    import transformers.modeling_utils as _mu
    if hasattr(_mu, "safe_open"):
        _mu.safe_open = _LazySafeOpen
        print("ARIS-PATCH: modeling_utils.safe_open -> lazy reader", flush=True)
except Exception as e:
    print("ARIS-PATCH: modeling_utils patch skipped:", e, flush=True)
print("ARIS-PATCH: safetensors load_file -> plain-read (no mmap)", flush=True)
