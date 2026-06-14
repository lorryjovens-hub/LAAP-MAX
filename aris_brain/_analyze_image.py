"""Analyze image metadata and colors."""
from PIL import Image
from collections import Counter

path = r'C:\Users\user\AppData\Local\hermes\profiles\laap-avatar-v4\image_cache\img_1cdd68034bd5.jpg'
img = Image.open(path)
print(f"Size: {img.size}")
print(f"Mode: {img.mode}")
print(f"Format: {img.format}")

# Reduce colors for analysis
p = img.quantize(colors=32)
palette = p.getpalette()
used = p.getcolors()
if used:
    used.sort(reverse=True)
    print(f"\nTotal color clusters: {len(used)}")
    print("Top palette colors:")
    for i, (count, idx) in enumerate(used[:20]):
        if count > 50:
            r, g, b = palette[idx*3:idx*3+3]
            print(f"  {count:5d}px  RGB({r:3d},{g:3d},{b:3d})")

# Check for text-like patterns - look for high contrast regions
pixels = list(img.getdata())
gray = [int(0.299*r + 0.587*g + 0.114*b) for r,g,b in pixels]
# Brightness distribution
bright = sum(1 for v in gray if v > 200)
dark = sum(1 for v in gray if v < 50)
mid = len(gray) - bright - dark
print(f"\nBrightness distribution:")
print(f"  Bright (>200): {bright}px ({bright*100/len(gray):.1f}%)")
print(f"  Mid range:     {mid}px ({mid*100/len(gray):.1f}%)")
print(f"  Dark (<50):    {dark}px ({dark*100/len(gray):.1f}%)")

# Average brightness
avg = sum(gray) / len(gray)
print(f"  Average:       {avg:.1f}")
