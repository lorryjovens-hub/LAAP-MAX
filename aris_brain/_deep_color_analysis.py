"""
Deep color analysis of the image - check for specific patterns.
"""
from PIL import Image
from collections import Counter

path = r'C:\Users\user\AppData\Local\hermes\profiles\laap-avatar-v4\image_cache\img_1cdd68034bd5.jpg'
img = Image.open(path)
pixels = list(img.getdata())

print(f"Image: {img.size[0]}x{img.size[1]} = {img.size[0]*img.size[1]} px")
print()

# 1. Check corners for background color
corners = {
    'top-left': pixels[0],
    'top-right': pixels[219],
    'bottom-left': pixels[-220],
    'bottom-right': pixels[-1],
}
print("Corner colors:")
for name, rgb in corners.items():
    print(f"  {name}: RGB{rgb}")

# 2. Check center region (rows 80-140, cols 80-140) 
center = []
for y in range(80, 141):
    for x in range(80, 141):
        center.append(pixels[y * 220 + x])
avg_r = sum(p[0] for p in center) / len(center)
avg_g = sum(p[1] for p in center) / len(center)
avg_b = sum(p[2] for p in center) / len(center)
print(f"\nCenter region (80..140,80..140):")
print(f"  Average: RGB({avg_r:.0f},{avg_g:.0f},{avg_b:.0f})")

# 3. Check top portion (first 60 rows) - could be sky vs ground
top = [px for y in range(60) for px in pixels[y*220:(y+1)*220]]
bottom = [px for y in range(160, 220) for px in pixels[y*220:(y+1)*220]]
top_avg = (sum(p[0] for p in top)/len(top), sum(p[1] for p in top)/len(top), sum(p[2] for p in top)/len(top))
bot_avg = (sum(p[0] for p in bottom)/len(bottom), sum(p[1] for p in bottom)/len(bottom), sum(p[2] for p in bottom)/len(bottom))
print(f"\nTop 60 rows avg: RGB({top_avg[0]:.0f},{top_avg[1]:.0f},{top_avg[2]:.0f})")
print(f"Bottom 60 rows avg: RGB({bot_avg[0]:.0f},{bot_avg[1]:.0f},{bot_avg[2]:.0f})")

# 4. Edge detection - check for strong horizontal lines
horiz_changes = 0
for y in range(1, 220):
    for x in range(1, 220):
        p1 = pixels[y*220 + x]
        p2 = pixels[y*220 + x - 1]
        diff = abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) + abs(p1[2]-p2[2])
        if diff > 100:
            horiz_changes += 1
print(f"\nEdge pixels (high contrast): {horiz_changes} ({horiz_changes*100/48400:.1f}%)")

# 5. Check for red/reddish areas (flowers maybe)
reddish = sum(1 for p in pixels if p[0] > 150 and p[1] < 100 and p[2] < 100)
warm_red = sum(1 for p in pixels if p[0] > 180 and p[0] > p[1] * 1.5 and p[0] > p[2] * 1.5)
print(f"Reddish pixels: {reddish}")
print(f"Warm red/orange: {warm_red}")

# 6. Green assessment
green_dominant = sum(1 for p in pixels if p[1] > p[0] * 1.2 and p[1] > p[2] * 1.2)
print(f"Green-dominant px: {green_dominant}")

# 7. Blue assessment  
blue_dominant = sum(1 for p in pixels if p[2] > p[0] * 1.1 and p[2] > p[1] * 1.1)
print(f"Blue-dominant px: {blue_dominant}")

# 8. Rough scene type estimation
total = len(pixels)
print(f"\nScene analysis:")
if green_dominant > total * 0.3:
    print("  Likely: NATURE / FOREST / PLANTS (30%+ green)")
if blue_dominant > total * 0.15:
    print("  Likely: SKY / WATER (15%+ blue)")
if reddish > total * 0.05:
    print(f"  Possible: FLOWERS / WARM OBJECTS ({reddish*100/total:.1f}% red)")
if warm_red > total * 0.03:
    print(f"  Possible: FLOWERS / ART ({warm_red*100/total:.1f}% warm red)")
if top_avg[2] > top_avg[0] and top_avg[2] > top_avg[1]:
    print("  Sky likely at top (blue dominant)")
if bot_avg[1] > bot_avg[0] and bot_avg[1] > bot_avg[2]:
    print("  Ground/plants likely at bottom (green dominant)")

# 9. Colorfulness score
import math
colorfulness = 0
for r, g, b in pixels:
    rg = abs(r - g)
    yb = abs(0.5*(r+g) - b)
    colorfulness += math.sqrt(rg*rg + yb*yb)
colorfulness /= total
print(f"Colorfulness score: {colorfulness:.1f} (higher = more colorful)")
