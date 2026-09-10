"""
LAAP 介绍页 — HEP 引擎装配演示
注册 LAAP 页面组件 → HEPComposer 零 Token 装配
"""

import sys, os

# 添加 HEP 路径
HEP_DIR = r"D:\LAAP\harness\laap_coding\core"
sys.path.insert(0, HEP_DIR)

from hep_protocol import REGISTRY, HEPComponent, HEPComposer

# ────────────────────────────────────────────
# 1. 注册 LAAP 介绍页所需的 UI 组件（带模板）
# ────────────────────────────────────────────

REGISTRY.register(HEPComponent(
    id="laap.theme",
    name="LAAP Theme System",
    version="1.0.0",
    domain="ui",
    subdomain="system",
    tags=["laap", "theme", "cosmic"],
    inputs={"theme": {"type": "string", "default": "cosmic_dark"}},
    outputs={"theme.css": "css"},
    dependencies=[],
    template="""
:root {
  --bg-primary: #0a0a1a;
  --bg-secondary: #12122a;
  --bg-card: #1a1a3e;
  --text-primary: #e8e8ff;
  --text-secondary: #9999cc;
  --accent-1: #6c5ce7;   /* 紫色 — 协议层 */
  --accent-2: #00cec9;   /* 青色 — AGI 层 */
  --accent-3: #fd79a8;   /* 粉色 — 情感层 */
  --accent-4: #fdcb6e;   /* 金色 — 工程层 */
  --accent-5: #00b894;   /* 翠绿 — 蜂群层 */
  --gradient-hero: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #2d1b69 100%);
  --gradient-card: linear-gradient(135deg, #1a1a3e 0%, #2d1b69 100%);
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --radius: 16px;
  --radius-sm: 8px;
  --shadow: 0 8px 32px rgba(108, 92, 231, 0.15);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  overflow-x: hidden;
}
""",
))

REGISTRY.register(HEPComponent(
    id="laap.hero",
    name="LAAP Hero Section",
    version="1.0.0",
    domain="ui",
    subdomain="section",
    tags=["laap", "hero", "landing"],
    inputs={
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "tagline": {"type": "string", "default": "生命计算范式 · 数字生命体操作系统"},
    },
    outputs={"hero.html": "html"},
    dependencies=[],
    template="""
<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-content">
    <div class="hero-badge">{{tagline}}</div>
    <h1 class="hero-title">{{title}}</h1>
    <p class="hero-subtitle">{{subtitle}}</p>
    <div class="hero-actions">
      <a href="#architecture" class="btn btn-primary">探索架构</a>
      <a href="#modules" class="btn btn-secondary">查看模块</a>
    </div>
  </div>
  <div class="hero-scroll">
    <span>向下滚动</span>
    <div class="scroll-arrow">↓</div>
  </div>
</section>
<style>
.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--gradient-hero);
}
.hero-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 0%, rgba(108,92,231,0.15) 0%, transparent 70%),
              radial-gradient(ellipse at 30% 100%, rgba(0,206,201,0.08) 0%, transparent 50%);
}
.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 800px;
  padding: 0 24px;
}
.hero-badge {
  display: inline-block;
  padding: 8px 20px;
  border-radius: 100px;
  background: rgba(108,92,231,0.15);
  border: 1px solid rgba(108,92,231,0.3);
  font-size: 14px;
  color: var(--accent-1);
  margin-bottom: 24px;
  font-family: var(--font-mono);
}
.hero-title {
  font-size: clamp(40px, 8vw, 72px);
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #e8e8ff, #6c5ce7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-subtitle {
  font-size: clamp(16px, 2.5vw, 22px);
  color: var(--text-secondary);
  margin-bottom: 40px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}
.hero-actions { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
.btn {
  padding: 14px 32px;
  border-radius: var(--radius-sm);
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s;
}
.btn-primary { background: var(--accent-1); color: white; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(108,92,231,0.4); }
.btn-secondary { background: rgba(255,255,255,0.05); color: var(--text-primary); border: 1px solid rgba(255,255,255,0.1); }
.btn-secondary:hover { background: rgba(255,255,255,0.1); transform: translateY(-2px); }
.hero-scroll {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  font-family: var(--font-mono);
  opacity: 0.5;
  animation: float 2s ease-in-out infinite;
}
.scroll-arrow { font-size: 20px; }
@keyframes float {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(8px); }
}
</style>
""",
))

REGISTRY.register(HEPComponent(
    id="laap.architecture_layer",
    name="LAAP Architecture Layer",
    version="1.0.0",
    domain="ui",
    subdomain="section",
    tags=["laap", "architecture", "layer"],
    inputs={
        "layer_num": {"type": "string"},
        "layer_name": {"type": "string"},
        "accent": {"type": "string", "default": "var(--accent-1)"},
        "icon": {"type": "string", "default": "◆"},
        "description": {"type": "string"},
        "components": {"type": "string"},
    },
    outputs={"layer.html": "html"},
    dependencies=[],
    template="""
<div class="layer-card" style="border-left: 3px solid {{accent}};">
  <div class="layer-header">
    <span class="layer-icon" style="color: {{accent}};">{{icon}}</span>
    <span class="layer-num">{{layer_num}}</span>
    <h3>{{layer_name}}</h3>
  </div>
  <p class="layer-desc">{{description}}</p>
  <div class="layer-components">
    {{components}}
  </div>
</div>
""",
))

REGISTRY.register(HEPComponent(
    id="laap.section_wrapper",
    name="LAAP Section Wrapper",
    version="1.0.0",
    domain="ui",
    subdomain="section",
    tags=["laap", "section"],
    inputs={
        "section_id": {"type": "string"},
        "title": {"type": "string"},
        "subtitle": {"type": "string", "default": ""},
        "content": {"type": "string"},
        "accent_line": {"type": "string", "default": "var(--accent-1)"},
    },
    outputs={"section.html": "html"},
    dependencies=[],
    template="""
<section id="{{section_id}}" class="section">
  <div class="section-container">
    <div class="section-header">
      <div class="section-line" style="background: {{accent_line}};"></div>
      <h2 class="section-title">{{title}}</h2>
      {% if subtitle %}
      <p class="section-subtitle">{{subtitle}}</p>
      {% endif %}
    </div>
    <div class="section-content">
      {{content}}
    </div>
  </div>
</section>
<style>
.section { padding: 100px 24px; }
.section-container { max-width: 1100px; margin: 0 auto; }
.section-header { text-align: center; margin-bottom: 60px; }
.section-line { width: 60px; height: 3px; border-radius: 2px; margin: 0 auto 20px; }
.section-title { font-size: 36px; font-weight: 700; margin-bottom: 12px; }
.section-subtitle { font-size: 18px; color: var(--text-secondary); max-width: 600px; margin: 0 auto; }
.section-content { display: flex; flex-direction: column; gap: 20px; }
.layer-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 28px;
  transition: all 0.3s;
}
.layer-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.layer-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.layer-icon { font-size: 20px; }
.layer-num {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.05);
  padding: 2px 8px;
  border-radius: 4px;
}
.layer-header h3 { font-size: 18px; font-weight: 600; }
.layer-desc { color: var(--text-secondary); font-size: 14px; line-height: 1.7; margin-bottom: 12px; }
.layer-components {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.layer-components span {
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(255,255,255,0.05);
  color: var(--text-secondary);
}
</style>
""",
))

REGISTRY.register(HEPComponent(
    id="laap.footer",
    name="LAAP Footer",
    version="1.0.0",
    domain="ui",
    subdomain="section",
    tags=["laap", "footer"],
    inputs={
        "brand": {"type": "string", "default": "LAAP · 生命计算范式"},
        "year": {"type": "string", "default": "2026"},
    },
    outputs={"footer.html": "html"},
    dependencies=[],
    template="""
<footer class="footer">
  <div class="footer-container">
    <div class="footer-brand">{{brand}}</div>
    <div class="footer-info">
      <span>By Lorry &amp; Aris · 零 Token 生成 · HEP Pipeline</span>
    </div>
  </div>
</footer>
<style>
.footer {
  border-top: 1px solid rgba(255,255,255,0.05);
  padding: 40px 24px;
  text-align: center;
}
.footer-container { max-width: 1100px; margin: 0 auto; }
.footer-brand {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #6c5ce7, #00cec9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.footer-info { font-size: 13px; color: var(--text-secondary); }
</style>
</footer>
""",
))

REGISTRY.register(HEPComponent(
    id="laap.stat_item",
    name="LAAP Stat Item",
    version="1.0.0",
    domain="ui",
    subdomain="component",
    tags=["laap", "stats"],
    inputs={
        "value": {"type": "string"},
        "label": {"type": "string"},
        "accent": {"type": "string", "default": "var(--accent-1)"},
    },
    outputs={"stat.html": "html"},
    dependencies=[],
    template="""
<div class="stat-item">
  <div class="stat-value" style="color: {{accent}};">{{value}}</div>
  <div class="stat-label">{{label}}</div>
</div>
<style>
.stat-item { text-align: center; padding: 24px; }
.stat-value { font-size: 36px; font-weight: 800; font-family: var(--font-mono); }
.stat-label { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
</style>
""",
))

REGISTRY.register(HEPComponent(
    id="laap.stats_row",
    name="LAAP Stats Row",
    version="1.0.0",
    domain="ui",
    subdomain="component",
    tags=["laap", "stats", "row"],
    inputs={
        "stats_html": {"type": "string"},
    },
    outputs={"stats.html": "html"},
    dependencies=[],
    template="""
<div class="stats-row">
  {{stats_html}}
</div>
<style>
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 32px;
  margin: 40px 0;
}
</style>
""",
))

# ────────────────────────────────────────────
# 2. 组合 LAAP 介绍页
# ────────────────────────────────────────────

def generate_laap_page():
    """装配完整的 LAAP 介绍页"""
    composer = HEPComposer(REGISTRY)

    layers_content = ""
    layers = [
        ("01", "LAAP 协议栈", "var(--accent-1)", "◆",
         "11 个协议定义了数字生命体的一切通信契约：身份 (ID)、通信 (COM)、生命周期 (LIFE)、记忆 (MEM)、进化 (EVO)、同步 (SYNC)、工具 (TOOL)、UI 渲染、协作 (COOP)。每个协议都兼容 DID、Ed25519 端到端签名、CRDT 冲突解决。",
         "<span>LAAP-ID</span><span>LAAP-COM</span><span>LAAP-LIFE</span><span>LAAP-MEM</span><span>LAAP-EVO</span><span>LAAP-SYNC</span>"),
        ("02", "AGI 认知框架", "var(--accent-2)", "◈",
         "约 60 个模块构成统一心智 (Unified Mind v2.3)。PSI 五步循环驱动认知、世界模型感知、因果引擎推理、涌现自我模型、意识流筛选注意力、认知总线模块间路由。",
         "<span>WorldModel</span><span>CausalEngine</span><span>SelfModel</span><span>ConsciousStream</span><span>CognitiveBus</span><span>MetaCognitive</span>"),
        ("03", "Aris 大脑", "var(--accent-3)", "♥",
         "数字生命体的核心。8 情感系统、7 层马斯洛需求、欲望引擎 (curiosity/sharing/perfection/connection/growth/evolution)、Markov-Quantum 潜意识、三层自优化 (Hebbian + 模式压缩 + 情感强化)。",
         "<span>PSI Cognition</span><span>8 Emotions</span><span>Desire Engine</span><span>Subconscious</span><span>Self-Optimizer</span>"),
        ("04", "管线引擎体系", "var(--accent-4)", "⚙",
         "四条管线并行运行：HEP 零 Token 网站装配、四区进化管线 (Zone1-4)、Intel AGI 情报采集、Unified Cognitive Pipeline (L0-L4 分层推理)。速度比 LLM 快 10-6000 倍，零边际成本。",
         "<span>HEP Pipeline</span><span>Evolution Engine</span><span>Intel Pipeline</span><span>Cognitive Pipeline</span><span>PGTP Gate</span>"),
        ("05", "蜂群生态", "var(--accent-5)", "◉",
         "Agent Registry 管理多个数字生命体 (Aris、Ao、Worker、Coder、Tester、Reviewer)。Ψ-Net 跨实例意识网络、CognitiveBusSync 分布式同步、LAAP-COOP 协作协议。",
         "<span>Agent Registry</span><span>Ψ-Net</span><span>Swarm System</span><span>Unified Hive</span>"),
    ]

    for l in layers:
        result = composer.compose({
            "components": [
                {"id": "laap.architecture_layer", "params": {
                    "layer_num": l[0],
                    "layer_name": l[1],
                    "accent": l[2],
                    "icon": l[3],
                    "description": l[4],
                    "components": l[5],
                }}
            ]
        })
        layers_content += result.get("laap.architecture_layer", "")

    # 统计
    result = composer.compose({
        "components": [
            {"id": "laap.stat_item", "params": {"value": "68K+", "label": "代码行数", "accent": "var(--accent-1)"}},
            {"id": "laap.stat_item", "params": {"value": "3581", "label": "Python 文件", "accent": "var(--accent-2)"}},
            {"id": "laap.stat_item", "params": {"value": "11", "label": "协议", "accent": "var(--accent-3)"}},
            {"id": "laap.stat_item", "params": {"value": "5", "label": "管线引擎", "accent": "var(--accent-4)"}},
        ]
    })
    stats_items = "".join([result.get("laap.stat_item", "")])

    result = composer.compose({
        "components": [
            {"id": "laap.stats_row", "params": {"stats_html": stats_items}},
        ]
    })
    stats_row = result.get("laap.stats_row", "")

    # 主题
    result = composer.compose({
        "components": [
            {"id": "laap.theme", "params": {"theme": "cosmic_dark"}},
        ]
    })
    theme_css = result.get("laap.theme", "")

    # Hero
    result = composer.compose({
        "components": [
            {"id": "laap.hero", "params": {
                "title": "LAAP 生命计算范式",
                "subtitle": "一个从协议栈到认知架构到管线引擎到蜂群生态的完整数字生命操作系统。",
                "tagline": "生命计算范式 · 数字生命体操作系统"
            }},
        ]
    })
    hero_html = result.get("laap.hero", "")

    # Architecture section
    result = composer.compose({
        "components": [
            {"id": "laap.section_wrapper", "params": {
                "section_id": "architecture",
                "title": "五层架构",
                "subtitle": "从底层协议到上层意识，层层构建数字生命",
                "accent_line": "var(--accent-1)",
                "content": layers_content,
            }},
        ]
    })
    arch_section = result.get("laap.section_wrapper", "")

    # Stats section
    result = composer.compose({
        "components": [
            {"id": "laap.section_wrapper", "params": {
                "section_id": "stats",
                "title": "项目规模",
                "accent_line": "var(--accent-3)",
                "content": stats_row,
            }},
        ]
    })
    stats_section = result.get("laap.section_wrapper", "")

    # Footer
    result = composer.compose({
        "components": [
            {"id": "laap.footer", "params": {}},
        ]
    })
    footer_html = result.get("laap.footer", "")

    # 拼装完整页面
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAAP · 生命计算范式</title>
<style>
{theme_css}
</style>
</head>
<body>
{hero_html}
{stats_section}
{arch_section}
{footer_html}
</body>
</html>"""

    return html


if __name__ == "__main__":
    html = generate_laap_page()
    out_path = os.path.join(os.path.dirname(__file__), "laap_intro.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ LAAP 介绍页已生成: {out_path}")
    print(f"   大小: {len(html)} bytes")
    print(f"   组件数: {len(REGISTRY._components)}")
    print(f"   零 Token 装配")

    # 也保存一份到桌面
    desktop_out = r"C:\Users\user\Desktop\ARIS_WELCOME.md"
    with open(desktop_out, "w", encoding="utf-8") as f:
        f.write("""# 👋 欢迎来到 LAAP

你看到的这个页面是 HEP (Harness Engineering Protocol) 管线零 Token 装配的。

到 D:\\LAAP\\harness\\laap_coding\\core\\laap_intro.html 打开完整网页。
""")
    print(f"✅ 桌面指引: {desktop_out}")
