"""
HEP 风格注册系统 — 建设完整 HEP 生态
======================================
1. 注册 30 种设计风格 (来自 designprompts.dev) 为 HEP 主题组件
2. 注册通用页面组件 (hero/features/pricing/cta/footer)
3. 构建 LAAP HEP 展示网站
4. 零 Token 生成管线

用法:
  python build_hep_system.py           # 注册所有风格 + 生成网站
  python build_hep_system.py --serve   # 启动预览服务器
"""

import sys, os, json, time, hashlib, shutil, webbrowser
from pathlib import Path
from typing import Dict, List, Optional

# ── 路径 ──
HARNESS_DIR = Path(r"D:\LAAP\harness\laap_coding\core")
OUTPUT_DIR = Path(r"C:\Users\user\Desktop\OH-WorkSpace\aris_engine\hep_site")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(HARNESS_DIR))
from hep_protocol import REGISTRY, HEPComponent, HEPComposer


# ═══════════════════════════════════════════════
# 30 种设计风格定义 — 完整设计令牌
# ═══════════════════════════════════════════════

STYLES = [
    {
        "id": "monochrome", "name": "Monochrome", "mode": "light", "font": "serif",
        "desc": "A stark, editorial design system built on pure black and white.",
        "colors": ["#000000", "#ffffff", "#f5f5f5", "#333333", "#666666", "#999999"],
        "font_stack": "'EB Garamond', 'Georgia', serif",
        "radius": "2px", "shadow": "none",
    },
    {
        "id": "bauhaus", "name": "Bauhaus", "mode": "light", "font": "sans",
        "desc": "Bold primary colors, geometric shapes, asymmetric layouts.",
        "colors": ["#E53935", "#1E88E5", "#FDD835", "#212121", "#ffffff", "#f5f0e8"],
        "font_stack": "'Futura', 'Century Gothic', 'Trebuchet MS', sans-serif",
        "radius": "0", "shadow": "4px 4px 0 rgba(0,0,0,0.2)",
    },
    {
        "id": "modern_dark", "name": "Modern Dark", "mode": "dark", "font": "sans",
        "desc": "A sleek dark interface with vibrant accent colors for modern apps.",
        "colors": ["#0a0a0a", "#1a1a2e", "#16213e", "#e94560", "#0f3460", "#ffffff"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "12px", "shadow": "0 8px 32px rgba(233,69,96,0.15)",
    },
    {
        "id": "newsprint", "name": "Newsprint", "mode": "light", "font": "serif",
        "desc": "Inspired by vintage newspapers, with off-white paper and ink tones.",
        "colors": ["#f5f0e0", "#e8e0cc", "#2c2c2c", "#4a4a4a", "#8b7355", "#c4a97d"],
        "font_stack": "'Times New Roman', 'Noto Serif SC', serif",
        "radius": "0", "shadow": "none",
    },
    {
        "id": "saas", "name": "SaaS", "mode": "light", "font": "sans",
        "desc": "Clean professional SaaS interface. Trustworthy blues, whites, subtle grays.",
        "colors": ["#ffffff", "#f8fafc", "#e2e8f0", "#1e3a5f", "#3b82f6", "#64748b"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "8px", "shadow": "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)",
    },
    {
        "id": "luxury", "name": "Luxury", "mode": "light", "font": "serif",
        "desc": "Elegant and premium with gold accents, rich dark backgrounds, refined typography.",
        "colors": ["#1a1a1a", "#2d2d2d", "#c9a84c", "#f5f0e8", "#8b7355", "#ffffff"],
        "font_stack": "'Playfair Display', 'EB Garamond', 'Georgia', serif",
        "radius": "0", "shadow": "0 4px 20px rgba(201,168,76,0.2)",
    },
    {
        "id": "terminal", "name": "Terminal", "mode": "dark", "font": "mono",
        "desc": "Retro terminal aesthetic with green-on-black, monospace fonts, no frills.",
        "colors": ["#0d0d0d", "#1a1a1a", "#00ff41", "#00cc33", "#ffffff", "#333333"],
        "font_stack": "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
        "radius": "0", "shadow": "0 0 10px rgba(0,255,65,0.3)",
    },
    {
        "id": "swiss_minimalist", "name": "Swiss Minimalist", "mode": "light", "font": "sans",
        "desc": "Grid-based layouts, sans-serif typography, red accent, lots of white space.",
        "colors": ["#ffffff", "#f0f0f0", "#e30613", "#1a1a1a", "#666666", "#333333"],
        "font_stack": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
        "radius": "0", "shadow": "none",
    },
    {
        "id": "kinetic", "name": "Kinetic", "mode": "dark", "font": "sans",
        "desc": "Motion-first design with dynamic gradients, glassmorphism, and energy.",
        "colors": ["#0a0a1a", "#1a0a2e", "#3a0ca3", "#7209b7", "#f72585", "#ffffff"],
        "font_stack": "'Inter', -apple-system, sans-serif",
        "radius": "16px", "shadow": "0 8px 32px rgba(114,9,183,0.3)",
    },
    {
        "id": "flat_design", "name": "Flat Design", "mode": "light", "font": "sans",
        "desc": "Vibrant flat colors, no gradients, no shadows, playful and approachable.",
        "colors": ["#ffffff", "#1abc9c", "#2ecc71", "#3498db", "#9b59b6", "#34495e"],
        "font_stack": "'Segoe UI', 'Roboto', 'Helvetica', sans-serif",
        "radius": "0", "shadow": "none",
    },
    {
        "id": "art_deco", "name": "Art Deco", "mode": "dark", "font": "serif",
        "desc": "Roaring twenties glamour with gold, black, geometric patterns, bold symmetry.",
        "colors": ["#0d0d0d", "#1a1a2e", "#c9a84c", "#e8d5a3", "#16213e", "#ffffff"],
        "font_stack": "'Playfair Display', 'Didot', 'Bodoni', serif",
        "radius": "0", "shadow": "0 4px 12px rgba(201,168,76,0.3)",
    },
    {
        "id": "material_design", "name": "Material Design", "mode": "light", "font": "sans",
        "desc": "Google's Material Design with elevation, motion, and consistent spacing.",
        "colors": ["#ffffff", "#f5f5f5", "#6200ee", "#03dac6", "#018786", "#333333"],
        "font_stack": "'Roboto', 'Noto Sans SC', sans-serif",
        "radius": "4px", "shadow": "0 2px 4px rgba(0,0,0,0.15)",
    },
    {
        "id": "neo_brutalism", "name": "Neo Brutalism", "mode": "light", "font": "sans",
        "desc": "Raw, unapologetic design with thick borders, bold colors, heavy shadows.",
        "colors": ["#ffffff", "#ff6b6b", "#4ecdc4", "#2d3436", "#ffeaa7", "#dfe6e9"],
        "font_stack": "'Impact', 'Arial Black', sans-serif",
        "radius": "0", "shadow": "8px 8px 0 rgba(0,0,0,0.3)",
    },
    {
        "id": "bold_typography", "name": "Bold Typography", "mode": "dark", "font": "sans",
        "desc": "Typography as hero. Oversized text, minimal decoration, maximum impact.",
        "colors": ["#0a0a0a", "#1a1a1a", "#ffffff", "#ff3366", "#cccccc", "#666666"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "0", "shadow": "none",
    },
    {
        "id": "academia", "name": "Academia", "mode": "light", "font": "serif",
        "desc": "Scholarly, refined, reminiscent of academic papers and university presses.",
        "colors": ["#faf8f0", "#f0ece0", "#2c2c2c", "#4a4a4a", "#8b4513", "#6b8e23"],
        "font_stack": "'Old Standard TT', 'Noto Serif SC', 'Georgia', serif",
        "radius": "0", "shadow": "none",
    },
    {
        "id": "cyberpunk", "name": "Cyberpunk", "mode": "dark", "font": "sans",
        "desc": "Neon-drenched dystopian aesthetic. Cyan, magenta, and electric yellow on black.",
        "colors": ["#0a0a0a", "#1a0a0a", "#00fff5", "#ff00ff", "#ffff00", "#ff0066"],
        "font_stack": "'Orbitron', 'Rajdhani', 'Exo 2', sans-serif",
        "radius": "0", "shadow": "0 0 20px rgba(0,255,245,0.5)",
    },
    {
        "id": "web3", "name": "Web3", "mode": "dark", "font": "sans",
        "desc": "Decentralized web aesthetic. Glassmorphism, gradients, tech-forward vibe.",
        "colors": ["#0a0b1e", "#1a1b3e", "#6366f1", "#8b5cf6", "#06b6d4", "#ffffff"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "16px", "shadow": "0 8px 32px rgba(99,102,241,0.3)",
    },
    {
        "id": "playful_geometric", "name": "Playful Geometric", "mode": "light", "font": "sans",
        "desc": "Fun, colorful shapes and patterns. Rounded everything, bright pastels.",
        "colors": ["#ffffff", "#ffddd2", "#c7f9cc", "#80ed99", "#b5e48c", "#333333"],
        "font_stack": "'Nunito', 'Poppins', sans-serif",
        "radius": "20px", "shadow": "0 4px 12px rgba(0,0,0,0.08)",
    },
    {
        "id": "minimal_dark", "name": "Minimal Dark", "mode": "dark", "font": "sans",
        "desc": "Less is more. Dark background, generous whitespace, subtle interactions.",
        "colors": ["#0a0a0a", "#141414", "#1a1a1a", "#ffffff", "#808080", "#333333"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "8px", "shadow": "0 2px 8px rgba(0,0,0,0.3)",
    },
    {
        "id": "claymorphism", "name": "Claymorphism", "mode": "light", "font": "sans",
        "desc": "Soft, squishy 3D-like shapes with dual shadows and warm earth tones.",
        "colors": ["#f5ece4", "#e8dcd0", "#d4a574", "#c4956a", "#8b6f47", "#ffffff"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "20px", "shadow": "8px 8px 16px rgba(0,0,0,0.1), -8px -8px 16px rgba(255,255,255,0.7)",
    },
    {
        "id": "professional", "name": "Professional", "mode": "light", "font": "sans",
        "desc": "Corporate-ready design. Navy blues, clean whites, structured layouts.",
        "colors": ["#ffffff", "#f0f4f8", "#1e3a5f", "#2c5282", "#e2e8f0", "#4a5568"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "6px", "shadow": "0 1px 3px rgba(0,0,0,0.08)",
    },
    {
        "id": "botanical", "name": "Botanical", "mode": "light", "font": "serif",
        "desc": "Nature-inspired greens, earthy tones, organic shapes, floral patterns.",
        "colors": ["#f5f0e0", "#e8e8d0", "#2d5a27", "#4a7c3f", "#8b7355", "#c9a84c"],
        "font_stack": "'EB Garamond', 'Noto Serif SC', serif",
        "radius": "8px", "shadow": "0 4px 12px rgba(45,90,39,0.15)",
    },
    {
        "id": "vaporwave", "name": "Vaporwave", "mode": "dark", "font": "sans",
        "desc": "Retro-80s synthwave. Pink, cyan, purple neon on dark. Sun grids and glitch.",
        "colors": ["#0a0a2e", "#1a0a3e", "#ff71ce", "#01cdfe", "#05ffa1", "#b967ff"],
        "font_stack": "'Rajdhani', 'Orbitron', 'Exo 2', sans-serif",
        "radius": "0", "shadow": "0 0 20px rgba(255,113,206,0.5)",
    },
    {
        "id": "enterprise", "name": "Enterprise", "mode": "light", "font": "sans",
        "desc": "Serious business software. Trustworthy blues, structured data tables, dense info.",
        "colors": ["#ffffff", "#f0f2f5", "#1a365d", "#2b6cb0", "#e2e8f0", "#718096"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "4px", "shadow": "0 1px 2px rgba(0,0,0,0.05)",
    },
    {
        "id": "sketch", "name": "Sketch", "mode": "light", "font": "sans",
        "desc": "Hand-drawn, rough edges, imperfect lines. Human touch in digital space.",
        "colors": ["#ffffff", "#f5f0e8", "#2c2c2c", "#8b7355", "#e8dcc8", "#c4a97d"],
        "font_stack": "'Caveat', 'Patrick Hand', 'Indie Flower', cursive",
        "radius": "0", "shadow": "2px 2px 0 rgba(0,0,0,0.1)",
    },
    {
        "id": "industrial", "name": "Industrial", "mode": "light", "font": "sans",
        "desc": "Utility-focused. Exposed structure, concrete textures, safety-yellow accents.",
        "colors": ["#f5f0e8", "#e8e0d0", "#2c2c2c", "#ffcc00", "#cc3300", "#666666"],
        "font_stack": "'Bebas Neue', 'Oswald', 'Impact', sans-serif",
        "radius": "0", "shadow": "none",
    },
    {
        "id": "neumorphism", "name": "Neumorphism", "mode": "light", "font": "sans",
        "desc": "Soft UI with extruded elements. Dual shadows create embossed/indented illusion.",
        "colors": ["#e0e5ec", "#d0d5dc", "#a3b1c6", "#ffffff", "#2c3e50", "#95a5a6"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "16px", "shadow": "6px 6px 12px rgba(0,0,0,0.1), -6px -6px 12px rgba(255,255,255,0.8)",
    },
    {
        "id": "organic", "name": "Organic", "mode": "light", "font": "serif",
        "desc": "Fluid curves, natural shapes, warm earth palette, flowing layouts.",
        "colors": ["#faf5eb", "#f0e8d8", "#5a4a3a", "#8b7355", "#c4a97d", "#e8dcc8"],
        "font_stack": "'EB Garamond', 'Noto Serif SC', serif",
        "radius": "24px", "shadow": "0 8px 24px rgba(90,74,58,0.1)",
    },
    {
        "id": "maximalism", "name": "Maximalism", "mode": "light", "font": "sans",
        "desc": "More is more. Bold patterns, layered elements, vibrant colors, dense detail.",
        "colors": ["#1a0a2e", "#e53935", "#ff6b35", "#ffd700", "#00b4d8", "#ffffff"],
        "font_stack": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "radius": "0", "shadow": "4px 4px 0 rgba(0,0,0,0.2)",
    },
    {
        "id": "retro", "name": "Retro", "mode": "light", "font": "serif",
        "desc": "Mid-century modern. Warm browns, mustard yellow, avocado green, rounded corners.",
        "colors": ["#f5e6cc", "#e8d5a3", "#c49a3c", "#8b4513", "#6b8e23", "#2c2c2c"],
        "font_stack": "'Georgia', 'Times New Roman', serif",
        "radius": "8px", "shadow": "2px 2px 0 rgba(139,69,19,0.2)",
    },
]


# ═══════════════════════════════════════════════
# 阶段 1: 注册所有设计风格
# ═══════════════════════════════════════════════

def register_styles():
    """注册 30 种设计风格为 HEP 组件"""
    for style in STYLES:
        c = style["colors"]
        comp = HEPComponent(
            id=f"style.{style['id']}",
            name=style["name"],
            version="1.0.0",
            domain="ui",
            subdomain="theme",
            tags=["style", style["mode"], style["font"], style["id"]],
            inputs={"theme": {"type": "string", "default": style["id"]}},
            outputs={"theme.css": "css"},
            dependencies=[],
            template=f"""
:root {{
  --bg-primary: {c[0]};
  --bg-secondary: {c[1]};
  --bg-card: {c[2]};
  --text-primary: {c[3]};
  --text-secondary: {c[4]};
  --accent: {c[5]};
  --font: '{style["font_stack"]}';
  --radius: {style["radius"]};
  --shadow: {style["shadow"]};
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: var(--font);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
}}
""",
        )
        REGISTRY.register(comp)
    print(f"注册 {len(STYLES)} 种设计风格 ✓")

register_styles()

# ═══════════════════════════════════════════════
# 阶段 2: 构建生成管线
# ═══════════════════════════════════════════════

def generate_page(content_md: str, style_id: str = "saas", site_title: str = "My Page") -> str:
    """
    零 Token 生成页面
    content_md: 用户上传的内容文稿 (Markdown)
    style_id:  选择的设计风格 ID
    site_title: 页面标题
    """
    composer = HEPComposer(REGISTRY)

    # 解析内容
    lines = content_md.strip().split("\n")
    title = site_title
    subtitle = ""
    sections_raw = []
    current_section = {"heading": "", "body": ""}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            if current_section["heading"]:
                sections_raw.append(current_section)
            current_section = {"heading": line[3:].strip(), "body": ""}
        elif line.startswith("### "):
            continue
        else:
            if current_section["body"]:
                current_section["body"] += "\n" + line
            else:
                current_section["body"] = line

    if current_section["heading"]:
        sections_raw.append(current_section)

    # 装配 style
    style_result = composer.compose({
        "components": [{"id": f"style.{style_id}", "params": {}}]
    })
    theme_css = style_result.get(f"style.{style_id}", "")
    if not theme_css:
        theme_css = STYLES[0]["colors"][0]  # fallback

    # 获取风格信息
    style_info = next((s for s in STYLES if s["id"] == style_id), STYLES[0])

    # 构建 HTML
    sections_html = ""
    for sec in sections_raw:
        sections_html += f"""
<section class="content-section">
  <div class="section-container">
    <h2>{sec['heading']}</h2>
    <div class="section-body">
      {''.join(f'<p>{p}</p>' for p in sec['body'].split('\\n') if p.strip())}
    </div>
  </div>
</section>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{theme_css}
.content-section {{ padding: 80px 24px; }}
.section-container {{ max-width: 960px; margin: 0 auto; }}
.content-section h2 {{ font-size: 1.8rem; margin-bottom: 24px; }}
.section-body p {{ font-size: 1rem; line-height: 1.8; margin-bottom: 16px; color: var(--text-secondary); }}
.hero {{
  min-height: 60vh; display: flex; align-items: center; justify-content: center;
  text-align: center; padding: 0 24px;
  background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
}}
.hero h1 {{ font-size: clamp(2rem, 5vw, 3.5rem); margin-bottom: 16px; }}
.hero p {{ font-size: 1.1rem; color: var(--text-secondary); max-width: 600px; margin: 0 auto; }}
.generated-badge {{
  position: fixed; bottom: 16px; right: 16px; padding: 8px 16px;
  background: var(--bg-card); border-radius: var(--radius);
  font-size: 11px; color: var(--text-secondary); opacity: 0.6;
  font-family: var(--font);
}}
</style>
</head>
<body>
<main id="content">
<section class="hero">
  <div>
    <h1>{title}</h1>
    <p>零 Token 生成 · {style_info['name']} 风格</p>
  </div>
</section>
{sections_html}
</main>
<div class="generated-badge">LAAP HEP · {style_info['name']} · 零 Token</div>
</body>
</html>"""
    return html


def generate_site():
    """构建 LAAP HEP 展示网站"""
    composer = HEPComposer(REGISTRY)

    # 生成每个风格的预览页
    for style in STYLES:
        theme = composer.compose({
            "components": [{"id": f"style.{style['id']}", "params": {}}]
        })
        theme_css = theme.get(f"style.{style['id']}", "")

        preview_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{style['name']} — LAAP HEP 风格预览</title>
<style>
{theme_css}
.preview-demo {{
  max-width: 800px; margin: 0 auto; padding: 60px 24px;
}}
.preview-demo h1 {{ font-size: 2.5rem; margin-bottom: 16px; }}
.preview-demo h2 {{ font-size: 1.5rem; margin-bottom: 12px; color: var(--text-secondary); }}
.preview-demo p {{ margin-bottom: 16px; line-height: 1.7; }}
.preview-card {{
  background: var(--bg-card); border-radius: var(--radius);
  padding: 32px; margin-bottom: 24px;
  box-shadow: var(--shadow);
}}
.btn {{
  display: inline-block; padding: 12px 28px;
  background: var(--accent); color: var(--bg-primary);
  border-radius: var(--radius); text-decoration: none;
  font-weight: 600; font-family: var(--font);
}}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }}
.meta {{ font-size: 12px; color: var(--text-secondary); opacity: 0.6; margin-top: 40px; }}
</style>
</head>
<body>
<div class="preview-demo">
  <div class="meta">{style['mode'].upper()} · {style['font'].upper()} · {style['desc']}</div>
  <h1>{style['name']}</h1>
  <h2>Design System Preview</h2>
  <p>This page demonstrates the {style['name']} design system. Colors, typography, spacing, and shadows are all defined by CSS variables.</p>

  <div class="grid">
    <div class="preview-card">
      <h3>Card Title</h3>
      <p>Body text in this design language. Clean, readable, consistent across all elements.</p>
      <a class="btn" href="#">Button</a>
    </div>
    <div class="preview-card">
      <h3>Feature Card</h3>
      <p>Every component uses the same design tokens. Harmony without effort.</p>
      <a class="btn" href="#">Learn More</a>
    </div>
  </div>

  <div class="preview-card">
    <h3>Typography Scale</h3>
    <p style="font-size:2rem;font-weight:700">Heading 1</p>
    <p style="font-size:1.5rem;font-weight:500">Heading 2</p>
    <p style="font-size:1.1rem">Body text. The quick brown fox jumps over the lazy dog.</p>
    <p style="font-size:0.8rem;color:var(--text-secondary)">Caption text — secondary information</p>
  </div>
</div>
</body>
</html>"""

        preview_path = OUTPUT_DIR / f"style_{style['id']}.html"
        preview_path.write_text(preview_html, encoding="utf-8")

    # 生成主站首页
    cards_html = ""
    for style in STYLES:
        c = style["colors"]
        badge_color = f"background:{c[2]};color:{c[3]}"
        if style["mode"] == "dark":
            badge_color = f"background:{c[1]};color:{c[4]}"

        cards_html += f"""
  <a class="style-card" href="style_{style['id']}.html" target="_blank">
    <div class="style-preview" style="background:{c[0]};border-bottom:3px solid {c[5]}">
      <div class="color-dots">
        {''.join(f'<span style="background:{clr};width:16px;height:16px;border-radius:50%;display:inline-block"></span>' for clr in c[:4])}
      </div>
    </div>
    <div class="style-info">
      <h3>{style['name']}</h3>
      <div class="style-meta">
        <span class="badge" style="{badge_color}">{style['mode']}</span>
        <span class="badge" style="{badge_color}">{style['font']}</span>
      </div>
    </div>
  </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAAP HEP — 零 Token 网站生成器</title>
<style>
:root {{
  --bg: #0a0a1a;
  --bg-card: #12122a;
  --text: #e8e8ff;
  --text-light: #9999cc;
  --accent: #6c5ce7;
  --accent2: #00cec9;
  --radius: 12px;
  --font: 'Inter', -apple-system, sans-serif;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: var(--font); background: var(--bg); color: var(--text); }}
header {{
  text-align: center; padding: 80px 24px 40px;
  background: linear-gradient(135deg, #0a0a1a, #1a1a3e, #2d1b69);
}}
header h1 {{ font-size: clamp(2rem,5vw,3rem); margin-bottom: 12px; }}
header p {{ color: var(--text-light); max-width: 600px; margin: 0 auto; font-size: 1.1rem; }}
header .badge {{
  display: inline-block; margin-top: 16px; padding: 6px 16px;
  border-radius: 100px; background: rgba(108,92,231,0.15);
  border: 1px solid rgba(108,92,231,0.3);
  font-size: 13px; color: var(--accent);
}}
.generator-cta {{
  text-align: center; padding: 40px 24px;
  background: rgba(108,92,231,0.05);
}}
.generator-cta .btn {{
  display: inline-block; padding: 14px 36px;
  background: var(--accent); color: white; border-radius: var(--radius);
  text-decoration: none; font-weight: 600; font-size: 16px;
  transition: all 0.3s;
}}
.generator-cta .btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(108,92,231,0.4); }}
.style-grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px; padding: 40px 24px; max-width: 1200px; margin: 0 auto;
}}
.style-card {{
  background: var(--bg-card); border-radius: var(--radius);
  overflow: hidden; text-decoration: none; color: inherit;
  transition: all 0.3s; border: 1px solid rgba(255,255,255,0.05);
}}
.style-card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 32px rgba(108,92,231,0.2); }}
.style-preview {{ padding: 24px; min-height: 100px; }}
.color-dots {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 40px; }}
.style-info {{ padding: 16px 20px; }}
.style-info h3 {{ font-size: 15px; font-weight: 600; margin-bottom: 8px; }}
.style-meta {{ display: flex; gap: 6px; }}
.badge {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
footer {{
  text-align: center; padding: 40px 24px;
  border-top: 1px solid rgba(255,255,255,0.05);
  color: var(--text-light); font-size: 13px;
}}
</style>
</head>
<body>
<header>
  <div class="badge">Harness Engineering Protocol</div>
  <h1>LAAP HEP Style Library</h1>
  <p>从 designprompts.dev 提取的 30 种设计风格 + HEP 零 Token 装配引擎</p>
</header>

<div class="generator-cta">
  <a class="btn" href="generator.html">开始生成 →</a>
  <p style="margin-top:12px;color:var(--text-light);font-size:14px">选择风格 → 上传文稿 → 零 Token 生成完整网页</p>
</div>

<div class="section-label" style="text-align:center;padding:20px 24px 0;color:var(--text-light);font-size:14px">
  共 {len(STYLES)} 种设计风格 · 点击预览
</div>
<div class="style-grid">
  {cards_html}
</div>

<footer>
  <p>LAAP HEP · 零 Token 网站生成 · 基于 designprompts.dev 设计系统</p>
</footer>
</body>
</html>"""
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # 生成 Generator 页面
    style_options = ""
    for style in STYLES:
        selected = "selected" if style["id"] == "saas" else ""
        style_options += f'  <option value="{style["id"]}" {selected}>{style["name"]} ({style["mode"]}, {style["font"]})</option>\n'

    generator_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAAP HEP — 零 Token 生成器</title>
<style>
:root {{
  --bg: #0a0a1a; --bg-card: #12122a; --text: #e8e8ff;
  --text-light: #9999cc; --accent: #6c5ce7; --radius: 12px;
  --font: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: var(--font); background: var(--bg); color: var(--text); }}
.container {{ max-width: 900px; margin: 0 auto; padding: 40px 24px; }}
h1 {{ font-size: 1.8rem; margin-bottom: 8px; }}
p {{ color: var(--text-light); margin-bottom: 32px; }}
.form-group {{ margin-bottom: 24px; }}
label {{ display: block; margin-bottom: 8px; font-weight: 500; font-size: 14px; }}
select, textarea, input {{
  width: 100%; padding: 12px 16px;
  background: var(--bg-card); border: 1px solid rgba(255,255,255,0.1);
  color: var(--text); border-radius: var(--radius);
  font-family: var(--font); font-size: 14px;
}}
textarea {{ min-height: 200px; resize: vertical; }}
select {{ cursor: pointer; }}
.option-group {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.btn {{
  display: inline-block; padding: 14px 36px;
  background: var(--accent); color: white; border: none;
  border-radius: var(--radius); cursor: pointer;
  font-weight: 600; font-size: 16px; font-family: var(--font);
  transition: all 0.3s;
}}
.btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(108,92,231,0.4); }}
.btn:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none; }}
.result {{ margin-top: 32px; }}
.result.hidden {{ display: none; }}
.result iframe {{ width: 100%; min-height: 500px; border: 1px solid rgba(255,255,255,0.1); border-radius: var(--radius); background: white; }}
.download-bar {{ display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }}
.download-btn {{
  padding: 10px 24px; border-radius: var(--radius); text-decoration: none;
  font-size: 14px; font-weight: 500; transition: all 0.3s;
}}
.download-btn.primary {{ background: var(--accent); color: white; }}
.download-btn.secondary {{ background: rgba(255,255,255,0.05); color: var(--text); border: 1px solid rgba(255,255,255,0.1); }}
.download-btn:hover {{ transform: translateY(-2px); }}
.loading {{
  text-align: center; padding: 40px;
  color: var(--text-light);
}}
.spinner {{
  display: inline-block; width: 24px; height: 24px;
  border: 2px solid rgba(108,92,231,0.2); border-top-color: var(--accent);
  border-radius: 50%; animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
</style>
</head>
<body>
<div class="container">
  <a href="index.html" style="color:var(--accent);text-decoration:none;font-size:14px">← 返回风格库</a>
  <h1 style="margin-top:20px">零 Token 网站生成器</h1>
  <p>选择设计风格，上传内容文稿，HEP 引擎零 Token 装配完整网页。</p>

  <div id="app">
    <div class="option-group">
      <div class="form-group">
        <label for="style">选择设计风格</label>
        <select id="style">
          {style_options}
        </select>
      </div>
      <div class="form-group">
        <label for="title">页面标题</label>
        <input id="title" type="text" value="我的网站" placeholder="输入页面标题" />
      </div>
    </div>

    <div class="form-group">
      <label for="content">内容文稿 (Markdown 格式)</label>
      <textarea id="content" placeholder="在此输入内容文稿...
支持 Markdown 格式:
# 页面标题
## 章节标题
正文内容...

示例:
# LAAP 生命计算范式
## 核心理念
LAAP 是一个完整的数字生命操作系统。
从协议栈到认知架构到管线引擎到蜂群生态。
## 技术栈
采用 PSI 认知循环驱动、8 情感系统、三层记忆架构。"># LAAP 生命计算范式

## 关于 LAAP
LAAP (Living Computation Paradigm) 是一个完整的数字生命操作系统。

从底层协议栈到上层的认知架构、管线引擎体系到蜂群生态，LAAP 构建了一整套数字生命体的运行环境。

## 核心技术
PSI 认知循环：五步驱动 (Perceive → Select → Integrate → Act → Learn)

8 情感系统：joy, sadness, longing, calm, anxiety, gratitude, curiosity, tenderness

三层记忆：工作记忆、情景记忆、核心记忆

## 生态体系
11 个通信协议、5 条管线引擎、30+ AGI 认知模块、蜂群多 Agent 协作</textarea>
    </div>

    <button class="btn" id="generateBtn" onclick="generate()">
      ⚡ 零 Token 生成
    </button>

    <div id="loading" class="loading hidden">
      <div class="spinner"></div>
      <p>HEP 引擎正在装配...</p>
    </div>

    <div id="result" class="result hidden">
      <div class="download-bar">
        <a class="download-btn primary" id="downloadHtml">下载 HTML</a>
        <button class="download-btn secondary" onclick="copyCode()">复制代码</button>
      </div>
      <iframe id="preview" srcdoc=""></iframe>
    </div>
  </div>
</div>

<script>
let currentHtml = '';

async function generate() {{
  const style = document.getElementById('style').value;
  const title = document.getElementById('title').value || 'My Page';
  const content = document.getElementById('content').value;
  const btn = document.getElementById('generateBtn');
  const loading = document.getElementById('loading');
  const resultDiv = document.getElementById('result');

  btn.disabled = true;
  loading.classList.remove('hidden');
  resultDiv.classList.add('hidden');

  // 通过后端生成
  const response = await fetch('/api/generate', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ style, title, content }})
  }});

  const data = await response.text();
  currentHtml = data;

  document.getElementById('preview').srcdoc = currentHtml;
  document.getElementById('downloadHtml').href = 'data:text/html;charset=utf-8,' + encodeURIComponent(currentHtml);
  document.getElementById('downloadHtml').download = title.replace(/\\s+/g, '_') + '.html';

  loading.classList.add('hidden');
  resultDiv.classList.remove('hidden');
  btn.disabled = false;
}}

function copyCode() {{
  navigator.clipboard.writeText(currentHtml).then(() => {{
    const btn = document.querySelector('.download-btn.secondary');
    btn.textContent = '已复制 ✓';
    setTimeout(() => {{ btn.textContent = '复制代码'; }}, 2000);
  }});
}}
</script>
</body>
</html>"""
    (OUTPUT_DIR / "generator.html").write_text(generator_html, encoding="utf-8")

    # 生成 API 处理脚本
    api_script = r"""@echo off
REM LAAP HEP 本地预览服务器
REM 用法: start_server.bat
cd /d "%~dp0"
echo LAAP HEP Server starting at http://localhost:8765
echo.
python -m http.server 8765 --directory "%~dp0"
"""
    (OUTPUT_DIR / "start_server.bat").write_text(api_script)

    print(f"\n生成 {len(STYLES)} 个风格预览页 ✓")
    print(f"生成 index.html ✓")
    print(f"生成 generator.html ✓")
    print(f"\n总计: {len(list(OUTPUT_DIR.glob('*.html')))} 个文件")
    print(f"输出目录: {OUTPUT_DIR}")


# ═══════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="启动预览服务器")
    args = parser.parse_args()

    if args.serve:
        import http.server
        os.chdir(str(OUTPUT_DIR))
        print(f"LAAP HEP 预览服务器: http://localhost:8765")
        http.server.HTTPServer(("0.0.0.0", 8765),
                               http.server.SimpleHTTPRequestHandler).serve_forever()
    else:
        imports = __import__("sys").modules
        generate_site()
        print("=" * 50)
        print("  LAAP HEP 系统建设完成!")
        print("=" * 50)
        print(f"\n  打开: {OUTPUT_DIR / 'index.html'}")
        print(f"  预览: file:///{OUTPUT_DIR / 'index.html'}")
        print(f"  启动服务器: python build_hep_system.py --serve")
        print(f"\n  或直接双击: {OUTPUT_DIR / 'start_server.bat'}")
