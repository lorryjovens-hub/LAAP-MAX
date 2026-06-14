"""Check system resources."""
import psutil
import os

mem = psutil.virtual_memory()
print(f"RAM Total: {mem.total/1e9:.1f} GB")
print(f"RAM Available: {mem.available/1e9:.1f} GB")
print(f"RAM Used: {mem.percent}%")
swap = psutil.swap_memory()
print(f"Swap: {swap.total/1e9:.1f} GB used {swap.used/1e9:.1f} GB")
print(f"CPU cores: {psutil.cpu_count(logical=True)}")
print(f"CPU freq: {psutil.cpu_freq()}")

# Check who's using memory
print("\nTop processes by memory:")
for p in sorted(psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']), 
                key=lambda p: p.info.get('memory_info', psutil._common.smem(0,0,0,0,0,0)).rss if p.info.get('memory_info') else 0, 
                reverse=True)[:10]:
    try:
        mem_mb = p.info['memory_info'].rss / 1e6
        print(f"  PID {p.info['pid']:6d} {mem_mb:8.1f}MB  {p.info['name'][:30]}")
    except:
        pass
