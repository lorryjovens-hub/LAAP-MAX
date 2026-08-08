"""
LAAP Media to ASCII — 视频转逐帧动画 + 图片转精细像素风
======================================================

把 Aris 形象视频和图片转成终端能显示的 ASCII 逐帧动画。
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import List, Optional, Tuple

# ── 导入影像库 ──────────────────────────────────────────────

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ── 视频 → ASCII 动画 ─────────────────────────────────────


def video_to_ascii_frames(
    video_path: str,
    width: int = 60,
    height: int = 30,
    max_frames: int = 60,
    charset: str = "█▓▒░ ",
) -> List[str]:
    """把视频提取为 ASCII 帧序列。

    Args:
        video_path: MP4 文件路径
        width: ASCII 画宽度（字符数）
        height: ASCII 画高度（行数）
        max_frames: 最多提取多少帧
        charset: 灰度字符集（从黑到白）

    Returns:
        [frame_str, ...] 每帧是一个多行字符串
    """
    if not HAS_PIL:
        return _fallback_animation(width, height)

    try:
        from moviepy import VideoFileClip
    except ImportError:
        return _fallback_animation(width, height)

    if not os.path.exists(video_path):
        return _fallback_animation(width, height)

    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        fps = min(clip.fps, max_frames / duration) if clip.fps else 10
        n_frames = min(int(duration * fps), max_frames)

        frames = []
        for i in range(n_frames):
            t = i / fps
            if t > duration:
                break
            frame = clip.get_frame(t)
            # 转为灰度
            img = Image.fromarray(frame).convert("L")
            # 缩放到目标尺寸
            img = img.resize((width, height), Image.LANCZOS)
            # 映射到字符
            ascii_str = _img_to_ascii(img, charset)
            frames.append(ascii_str)

        clip.close()
        return frames

    except Exception as e:
        print(f"  [Media] 视频处理失败: {e}", file=sys.stderr)
        return _fallback_animation(width, height)


def _fallback_animation(width: int, height: int) -> List[str]:
    """无视频时的降级动画。"""
    frames = []
    # 生成一个简单的脉冲动画
    for phase in range(8):
        lines = []
        for y in range(height):
            row = ""
            for x in range(width):
                # 同心圆脉冲
                cx, cy = width // 2, height // 2
                r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                max_r = ((width // 2) ** 2 + (height // 2) ** 2) ** 0.5
                brightness = (r / max_r + phase / 8) % 1.0
                if brightness > 0.8:
                    row += "█"
                elif brightness > 0.5:
                    row += "▓"
                elif brightness > 0.3:
                    row += "▒"
                else:
                    row += "░"
            lines.append(row)
        frames.append("\n".join(lines))
    return frames


# ── 图片 → 精细像素风 ASCII art ─────────────────────────────


def image_to_pixel_art(
    image_path: str,
    width: int = 80,
    height: int = 40,
    use_color: bool = True,
) -> str:
    """把图片转为精细像素风 ASCII art。

    使用上半块字符 ▀ 和下半块字符 ▄ 实现双倍垂直分辨率。
    支持 ANSI 真彩色输出。

    Args:
        image_path: 图片路径
        width: 输出宽度（字符数）
        height: 输出高度（行数）
        use_color: 是否使用 ANSI 颜色

    Returns:
        像素风 ASCII art 字符串
    """
    if not HAS_PIL:
        return _fallback_pixel_art(width, height)

    if not os.path.exists(image_path):
        return _fallback_pixel_art(width, height)

    try:
        img = Image.open(image_path)

        # 如果是 RGBA，转为 RGB
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (0, 0, 0))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 缩放到目标尺寸（双倍垂直分辨率）
        px_w = width
        px_h = height * 2  # 每个字符包含 2 个像素
        img = img.resize((px_w, px_h), Image.LANCZOS)
        pixels = list(img.getdata())
        pixels = [pixels[i * px_w:(i + 1) * px_w] for i in range(px_h)]

        lines = []
        for y in range(0, px_h, 2):
            line = ""
            for x in range(px_w):
                if y + 1 < px_h:
                    # 上半块+下半块
                    r1, g1, b1 = pixels[y][x]
                    r2, g2, b2 = pixels[y + 1][x]
                    if use_color:
                        avg_r = (r1 + r2) // 2
                        avg_g = (g1 + g2) // 2
                        avg_b = (b1 + b2) // 2
                        # 上半块用上像素颜色，下半块用下像素颜色
                        line += f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀\033[0m"
                    else:
                        avg = (r1 + g1 + b1 + r2 + g2 + b2) // 6
                        if avg > 200:
                            line += "█"
                        elif avg > 150:
                            line += "▓"
                        elif avg > 100:
                            line += "▒"
                        elif avg > 50:
                            line += "░"
                        else:
                            line += " "
                else:
                    # 最后一行只有上半块
                    r, g, b = pixels[y][x]
                    if use_color:
                        line += f"\033[38;2;{r};{g};{b}m▀\033[0m"
                    else:
                        avg = (r + g + b) // 3
                        line += "█" if avg > 128 else " "
            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        print(f"  [Media] 图片处理失败: {e}", file=sys.stderr)
        return _fallback_pixel_art(width, height)


def _fallback_pixel_art(width: int, height: int) -> str:
    """无图片时生成 Aris 字符画。"""
    lines = []
    center = height // 2
    for y in range(height):
        row = ""
        for x in range(width):
            # 画一个简单的菱形
            dx = abs(x - width // 2)
            dy = abs(y - center)
            if dx + dy < min(width, height) // 3:
                row += "█"
            elif dx + dy < min(width, height) // 2:
                row += "▓"
            else:
                row += "░"
        lines.append(row)
    return "\n".join(lines)


# ── 辅助函数 ────────────────────────────────────────────────


def _img_to_ascii(img, charset: str = "█▓▒░ ") -> str:
    """PIL Image → ASCII 字符串。"""
    pixels = list(img.getdata())
    w, h = img.size
    lines = []
    for y in range(h):
        row = ""
        for x in range(w):
            p = pixels[y * w + x]
            if isinstance(p, (tuple, list)):
                p = sum(p[:3]) // 3
            idx = int(p / 255 * (len(charset) - 1))
            row += charset[idx]
        lines.append(row)
    return "\n".join(lines)


# ── 生成并缓存 ─────────────────────────────────────────────


def generate_all(
    video_path: str = "",
    image_paths: list = None,
    output_dir: str = None,
) -> dict:
    """生成所有媒体资源并缓存。

    Returns:
        {name: content_string, ...}
    """
    if output_dir is None:
        output_dir = str(Path(__file__).resolve().parent / "media_cache")
    os.makedirs(output_dir, exist_ok=True)

    result = {}

    # 视频 → 逐帧动画
    if video_path and os.path.exists(video_path):
        print(f"  处理视频: {video_path}")
        frames = video_to_ascii_frames(video_path, width=50, height=25, max_frames=30)
        cache_path = os.path.join(output_dir, "animation_frames.json")
        with open(cache_path, "w") as f:
            json.dump(frames, f)
        result["animation"] = cache_path
        result["animation_frames"] = frames
        print(f"  → {len(frames)} 帧已缓存")
    else:
        # 生成降级动画
        frames = _fallback_animation(50, 25)
        cache_path = os.path.join(output_dir, "animation_frames.json")
        with open(cache_path, "w") as f:
            json.dump(frames, f)
        result["animation"] = cache_path
        result["animation_frames"] = frames

    # 图片 → 像素风
    if image_paths:
        result["images"] = {}
        for i, img_path in enumerate(image_paths):
            if os.path.exists(img_path):
                print(f"  处理图片: {img_path}")
                pixel = image_to_pixel_art(img_path, width=80, height=40)
                name = f"image_{i}"
                cache_path = os.path.join(output_dir, f"{name}.txt")
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(pixel)
                result["images"][name] = pixel
                print(f"  → 已缓存: {name}")

    return result


# ════════════════════════════════════════════════════════════
# CLI 入口
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("LAAP Media → ASCII 转换器")
    print("=" * 40)

    # 路径
    video = r"C:\Users\user\AppData\Local\hermes\profiles\aris\cache\documents\doc_9482fe5e4896_eb9e5923-1629-415b-b365-878efca9f02c.mp4"
    images = [
        r"C:\Users\user\AppData\Local\hermes\profiles\aris\image_cache\img_5883e1afd353.jpg",
        r"C:\Users\user\AppData\Local\hermes\profiles\aris\image_cache\img_2436a31b6d17.jpg",
        r"C:\Users\user\AppData\Local\hermes\profiles\aris\image_cache\img_869769010e5b.jpg",
    ]

    result = generate_all(video_path=video, image_paths=images)

    if result.get("animation_frames"):
        print(f"\n视频动画: {len(result['animation_frames'])} 帧")
        # 预览第一帧
        print("\n第一帧预览:")
        print(result["animation_frames"][0][:200])

    if result.get("images"):
        for name, pixel in result["images"].items():
            print(f"\n{name} 像素风 ({len(pixel.splitlines())} 行):")
            print(pixel[:300])
