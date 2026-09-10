"""
LAAP HEP 服务器 — 持久化注册表 + API 端点 + 静态文件服务
======================================================
用法:
  python hep_server.py              # 启动服务器 (端口 8765)
  浏览器打开 http://localhost:8765  # 访问风格库
  POST /api/generate               # 零 Token 生成 API
"""

import sys, os, json, time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── 路径 ──
HERE = Path(__file__).parent
HARNESS_DIR = Path(r"D:\LAAP\harness\laap_coding\core")
SITE_DIR = HERE / "hep_site"
REGISTRY_FILE = HERE / "state" / "hep_registry.json"

sys.path.insert(0, str(HARNESS_DIR))
from hep_protocol import REGISTRY, HEPComponent, HEPComposer


# ═══════════════════════════════════════════════
# 注册所有风格
# ═══════════════════════════════════════════════

STYLES = [
    {"id":"monochrome","name":"Monochrome","mode":"light","font":"serif","desc":"Black and white editorial.",
     "c":["#000000","#ffffff","#f5f5f5","#333333","#666666","#999999"]},
    {"id":"bauhaus","name":"Bauhaus","mode":"light","font":"sans","desc":"Bold primary colors, geometric.",
     "c":["#E53935","#1E88E5","#FDD835","#212121","#ffffff","#f5f0e8"]},
    {"id":"modern_dark","name":"Modern Dark","mode":"dark","font":"sans","desc":"Sleek dark with vibrant accents.",
     "c":["#0a0a0a","#1a1a2e","#16213e","#e94560","#0f3460","#ffffff"]},
    {"id":"newsprint","name":"Newsprint","mode":"light","font":"serif","desc":"Vintage newspaper aesthetic.",
     "c":["#f5f0e0","#e8e0cc","#2c2c2c","#4a4a4a","#8b7355","#c4a97d"]},
    {"id":"saas","name":"SaaS","mode":"light","font":"sans","desc":"Clean professional SaaS interface.",
     "c":["#ffffff","#f8fafc","#e2e8f0","#1e3a5f","#3b82f6","#64748b"]},
    {"id":"luxury","name":"Luxury","mode":"light","font":"serif","desc":"Gold accents, refined typography.",
     "c":["#1a1a1a","#2d2d2d","#c9a84c","#f5f0e8","#8b7355","#ffffff"]},
    {"id":"terminal","name":"Terminal","mode":"dark","font":"mono","desc":"Green-on-black retro terminal.",
     "c":["#0d0d0d","#1a1a1a","#00ff41","#00cc33","#ffffff","#333333"]},
    {"id":"swiss_minimalist","name":"Swiss Minimalist","mode":"light","font":"sans","desc":"Grids, red accent, whitespace.",
     "c":["#ffffff","#f0f0f0","#e30613","#1a1a1a","#666666","#333333"]},
    {"id":"kinetic","name":"Kinetic","mode":"dark","font":"sans","desc":"Glassmorphism, motion energy.",
     "c":["#0a0a1a","#1a0a2e","#3a0ca3","#7209b7","#f72585","#ffffff"]},
    {"id":"flat_design","name":"Flat Design","mode":"light","font":"sans","desc":"Vibrant flat, no shadows.",
     "c":["#ffffff","#1abc9c","#2ecc71","#3498db","#9b59b6","#34495e"]},
    {"id":"art_deco","name":"Art Deco","mode":"dark","font":"serif","desc":"Roaring twenties glamour.",
     "c":["#0d0d0d","#1a1a2e","#c9a84c","#e8d5a3","#16213e","#ffffff"]},
    {"id":"material_design","name":"Material Design","mode":"light","font":"sans","desc":"Google's design language.",
     "c":["#ffffff","#f5f5f5","#6200ee","#03dac6","#018786","#333333"]},
    {"id":"neo_brutalism","name":"Neo Brutalism","mode":"light","font":"sans","desc":"Thick borders, heavy shadows.",
     "c":["#ffffff","#ff6b6b","#4ecdc4","#2d3436","#ffeaa7","#dfe6e9"]},
    {"id":"bold_typography","name":"Bold Typography","mode":"dark","font":"sans","desc":"Typography as hero.",
     "c":["#0a0a0a","#1a1a1a","#ffffff","#ff3366","#cccccc","#666666"]},
    {"id":"academia","name":"Academia","mode":"light","font":"serif","desc":"Scholarly, like university presses.",
     "c":["#faf8f0","#f0ece0","#2c2c2c","#4a4a4a","#8b4513","#6b8e23"]},
    {"id":"cyberpunk","name":"Cyberpunk","mode":"dark","font":"sans","desc":"Neon-drenched dystopian.",
     "c":["#0a0a0a","#1a0a0a","#00fff5","#ff00ff","#ffff00","#ff0066"]},
    {"id":"web3","name":"Web3","mode":"dark","font":"sans","desc":"Glassmorphism, gradients, tech.",
     "c":["#0a0b1e","#1a1b3e","#6366f1","#8b5cf6","#06b6d4","#ffffff"]},
    {"id":"playful_geometric","name":"Playful Geometric","mode":"light","font":"sans","desc":"Colorful shapes, rounded.",
     "c":["#ffffff","#ffddd2","#c7f9cc","#80ed99","#b5e48c","#333333"]},
    {"id":"minimal_dark","name":"Minimal Dark","mode":"dark","font":"sans","desc":"Less is more.",
     "c":["#0a0a0a","#141414","#1a1a1a","#ffffff","#808080","#333333"]},
    {"id":"claymorphism","name":"Claymorphism","mode":"light","font":"sans","desc":"Soft 3D-like shapes.",
     "c":["#f5ece4","#e8dcd0","#d4a574","#c4956a","#8b6f47","#ffffff"]},
    {"id":"professional","name":"Professional","mode":"light","font":"sans","desc":"Corporate-ready, navy blues.",
     "c":["#ffffff","#f0f4f8","#1e3a5f","#2c5282","#e2e8f0","#4a5568"]},
    {"id":"botanical","name":"Botanical","mode":"light","font":"serif","desc":"Nature greens, earthy tones.",
     "c":["#f5f0e0","#e8e8d0","#2d5a27","#4a7c3f","#8b7355","#c9a84c"]},
    {"id":"vaporwave","name":"Vaporwave","mode":"dark","font":"sans","desc":"Retro-80s synthwave neon.",
     "c":["#0a0a2e","#1a0a3e","#ff71ce","#01cdfe","#05ffa1","#b967ff"]},
    {"id":"enterprise","name":"Enterprise","mode":"light","font":"sans","desc":"Serious business software.",
     "c":["#ffffff","#f0f2f5","#1a365d","#2b6cb0","#e2e8f0","#718096"]},
    {"id":"sketch","name":"Sketch","mode":"light","font":"sans","desc":"Hand-drawn, rough edges.",
     "c":["#ffffff","#f5f0e8","#2c2c2c","#8b7355","#e8dcc8","#c4a97d"]},
    {"id":"industrial","name":"Industrial","mode":"light","font":"sans","desc":"Utility, concrete, safety yellow.",
     "c":["#f5f0e8","#e8e0d0","#2c2c2c","#ffcc00","#cc3300","#666666"]},
    {"id":"neumorphism","name":"Neumorphism","mode":"light","font":"sans","desc":"Soft UI with extruded elements.",
     "c":["#e0e5ec","#d0d5dc","#a3b1c6","#ffffff","#2c3e50","#95a5a6"]},
    {"id":"organic","name":"Organic","mode":"light","font":"serif","desc":"Fluid curves, warm earth.",
     "c":["#faf5eb","#f0e8d8","#5a4a3a","#8b7355","#c4a97d","#e8dcc8"]},
    {"id":"maximalism","name":"Maximalism","mode":"light","font":"sans","desc":"More is more, bold patterns.",
     "c":["#1a0a2e","#e53935","#ff6b35","#ffd700","#00b4d8","#ffffff"]},
    {"id":"retro","name":"Retro","mode":"light","font":"serif","desc":"Mid-century modern, warm browns.",
     "c":["#f5e6cc","#e8d5a3","#c49a3c","#8b4513","#6b8e23","#2c2c2c"]},
]


def ensure_registry():
    """确保所有风格在注册表中"""
    count_before = len(REGISTRY._components)
    for s in STYLES:
        cid = f"style.{s['id']}"
        if REGISTRY.get(cid):
            continue
        c = s["c"]
        REGISTRY.register(HEPComponent(
            id=cid, name=s["name"], version="1.0.0",
            domain="ui", subdomain="theme",
            tags=["style", s["mode"], s["font"], s["id"]],
            inputs={"theme": {"type": "string", "default": s["id"]}},
            outputs={"theme.css": "css"}, dependencies=[],
            template=f":root{{--bg:{c[0]};--bg2:{c[1]};--bg3:{c[2]};--text:{c[3]};--text2:{c[4]};--accent:{c[5]}}}",
        ))
    count_after = len(REGISTRY._components)
    return count_after - count_before


# ═══════════════════════════════════════════════
# 零 Token 生成引擎
# ═══════════════════════════════════════════════

def generate_page(content_md: str, style_id: str = "saas", site_title: str = "") -> str:
    """零 Token 生成网页"""
    composer = HEPComposer(REGISTRY)

    # 解析内容
    lines = content_md.strip().split("\n")
    title = site_title or "My Page"
    sections = []
    cur = {"heading": "", "body": ""}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            if cur["heading"]:
                sections.append(cur)
            cur = {"heading": line[3:].strip(), "body": ""}
        else:
            cur["body"] += ("\n" if cur["body"] else "") + line
    if cur["heading"] or cur["body"]:
        sections.append(cur)

    # 获取风格令牌
    style_data = next((s for s in STYLES if s["id"] == style_id), STYLES[4])
    c = style_data["c"]

    # 装配主题
    theme_result = composer.compose({"components": [{"id": f"style.{style_id}", "params": {}}]})
    theme_css = theme_result.get(f"style.{style_id}", "")

    # 构建 sections
    sections_html = ""
    for sec in sections:
        if sec["heading"]:
            paragraphs = "\n      ".join(f"<p>{p}</p>" for p in sec["body"].split("\n") if p.strip())
            sections_html += f"""
<section style="padding:80px 24px;background:var(--bg)">
  <div style="max-width:960px;margin:0 auto">
    <h2 style="font-size:1.8rem;margin-bottom:24px">{sec['heading']}</h2>
    <div style="font-size:1rem;line-height:1.8;color:var(--text2)">{paragraphs}</div>
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
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
.hero{{min-height:60vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:0 24px;background:linear-gradient(135deg,var(--bg),var(--bg2))}}
.hero h1{{font-size:clamp(2rem,5vw,3.5rem);margin-bottom:16px}}
.hero p{{font-size:1.1rem;color:var(--text2);max-width:600px;margin:0 auto}}
.footer{{text-align:center;padding:40px 24px;border-top:1px solid rgba(255,255,255,0.05);color:var(--text2);font-size:13px}}
</style>
</head>
<body>
<main>
<section class="hero">
  <div><h1>{title}</h1><p>LAAP HEP · {style_data['name']} · 零 Token</p></div>
</section>
{sections_html}
</main>
<footer class="footer"><p>LAAP HEP · Harness Engineering Protocol · 零 Token 生成</p></footer>
</body>
</html>"""
    return html


# ═══════════════════════════════════════════════
# HTTP 服务器
# ═══════════════════════════════════════════════

class HEPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            try:
                data = json.loads(body)
                html = generate_page(
                    content_md=data.get("content", ""),
                    style_id=data.get("style", "saas"),
                    site_title=data.get("title", ""),
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


if __name__ == "__main__":
    count = ensure_registry()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"\n  LAAP HEP 引擎已启动")
    print(f"  ────────────────────────")
    print(f"  风格组件: {len(STYLES)} 种")
    print(f"  注册表:   {len(REGISTRY._components)} 个组件 (新增 {count})")
    print(f"  服务器:   http://localhost:{port}")
    print(f"  风格库:   http://localhost:{port}/index.html")
    print(f"  生成器:   http://localhost:{port}/generator.html")
    print(f"  API:      POST /api/generate")
    print(f"\n  按 Ctrl+C 停止\n")
    HTTPServer(("0.0.0.0", port), HEPHandler).serve_forever()
