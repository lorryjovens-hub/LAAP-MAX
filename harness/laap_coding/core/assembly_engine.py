"""
AssemblyEngine - 商业级多页面组装引擎

核心功能：
1. 多页面批量组装
2. 自动导航生成（面包屑、侧边栏、Footer）
3. 零 Token 字符串拼接
4. 支持多种布局模板
5. CSS/JS 自动注入

使用示例：
    from assembly_engine import AssemblyEngine
    from content_parser import ContentParser
    
    parser = ContentParser()
    spec = parser.parse_markdown(markdown_content)
    
    engine = AssemblyEngine(style="apple_cn")
    files = engine.assemble_site(spec)
    
    for f in files:
        print(f"[OK] {f.filename} ({len(f.content)} bytes)")
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

# 尝试从 content_parser 导入，失败则定义本地版本
try:
    from content_parser import Page, Section, Card, CTA, Stat, UnifiedContentSpec
except ImportError:
    # 本地定义（用于独立测试）
    @dataclass
    class CTA:
        label: str
        url: str
        style: str = "primary"
    
    @dataclass
    class Card:
        title: str
        desc: str
        icon: Optional[str] = None
        cta: Optional[CTA] = None
    
    @dataclass
    class Stat:
        number: str
        label: str
    
    @dataclass
    class Section:
        type: str
        title: Optional[str] = None
        subtitle: Optional[str] = None
        label: Optional[str] = None
        cta: Optional[CTA] = None
        three_d: bool = False
        cards: List[Card] = field(default_factory=list)
        stats: List[Stat] = field(default_factory=list)
        content: Optional[str] = None
        cols: int = 3
    
    @dataclass
    class Page:
        filename: str
        title: str
        type: str = "landing"
        sections: List[Section] = field(default_factory=list)
    
    @dataclass
    class UnifiedContentSpec:
        brand: str
        pages: List[Page] = field(default_factory=list)
        style: str = "apple_dark"

# 导入 StyleEngine
try:
    from harness_style_engine import STYLE_PRESETS, StyleEngine
except ImportError:
    STYLE_PRESETS = {
        "apple_dark": {
            "name": "Apple 深色",
            "css_vars": {
                "--bg": "#000", "--bg-alt": "#0a0a0f", "--surface": "rgba(255,255,255,0.03)",
                "--text": "#f5f5f7", "--text-secondary": "rgba(255,255,255,0.5)",
                "--accent": "#7c7cff", "--radius": "16px",
                "--font": "'Inter', -apple-system, sans-serif",
            },
            "three_d": True,
        },
        "apple_cn": {
            "name": "Apple 中国",
            "css_vars": {
                "--bg": "#000000", "--bg-alt": "#1d1d1f", "--surface": "rgba(29,29,31,0.72)",
                "--text": "#f5f5f7", "--text-secondary": "#86868b",
                "--accent": "#0071e3", "--radius": "18px",
                "--font": "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
            },
            "three_d": True,
        },
    }


@dataclass
class HTMLFile:
    """生成的 HTML 文件"""
    filename: str
    content: str


class AssemblyEngine:
    """
    商业级多页面组装引擎
    
    特性：
    - 零 Token 生成（纯字符串拼接）
    - 多页面批量组装
    - 自动导航生成
    - 统一样式注入
    """

    def __init__(self, style: str = "apple_dark"):
        self.style = style
        self.style_data = STYLE_PRESETS.get(style, STYLE_PRESETS["apple_dark"])
        self.css_vars = self.style_data.get("css_vars", {})

    def assemble_site(self, spec) -> List[HTMLFile]:
        """
        组装整个网站
        
        输入: UnifiedContentSpec
        输出: List[HTMLFile]
        """
        files = []
        
        # 1. 生成全局导航
        global_nav = self._build_global_nav(spec)
        global_footer = self._build_global_footer(spec)
        
        # 2. 批量生成页面
        for page in spec.pages:
            html = self.assemble_page(
                page=page,
                brand=spec.brand,
                global_nav=global_nav,
                global_footer=global_footer,
                all_pages=spec.pages
            )
            files.append(HTMLFile(filename=page.filename, content=html))
        
        return files

    def assemble_page(self, page, brand: str, global_nav: str = "",
                      global_footer: str = "", all_pages: List = None) -> str:
        """组装单个页面"""
        
        # 1. 生成 CSS
        css = self._build_css()
        
        # 2. 生成导航
        nav = global_nav or self._build_nav(brand, all_pages or [])
        
        # 3. 生成 Sections
        sections_html = []
        for i, section in enumerate(page.sections):
            section_html = self._build_section(section, i)
            sections_html.append(section_html)
        
        # 4. 生成 Footer
        footer = global_footer or self._build_footer(brand)
        
        # 5. 生成脚本
        scripts = self._build_scripts(page)
        
        # 6. 组装完整页面
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{self._extract_description(page)}">
<meta name="keywords" content="{brand}, {page.title}">
<meta name="author" content="{brand}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{page.filename}">
<title>{page.title} · {brand}</title>
<style>
{css}
</style>
</head>
<body>
{nav}
<main>
{"".join(sections_html)}
</main>
{footer}
{scripts}
</body>
</html>'''
        
        return html

    def _build_css(self) -> str:
        """生成 CSS 变量和基础样式"""
        vars_str = "\n".join(f"  {k}: {v};" for k, v in self.css_vars.items())
        
        return f''':root {{
{vars_str}
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: {self.css_vars.get("--font", "sans-serif")};
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  line-height: 1.6;
}}
a {{ color: inherit; text-decoration: none; }}
img {{ max-width: 100%; height: auto; }}

/* 导航 */
.nav {{
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: 48px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border, rgba(255,255,255,0.1));
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}}
.nav-brand {{ font-size: 18px; font-weight: 600; color: var(--accent); }}
.nav-links {{ display: flex; gap: 24px; }}
.nav-link {{ font-size: 13px; color: var(--text-secondary); transition: color 0.2s; }}
.nav-link:hover {{ color: var(--text); }}
.nav-link.active {{ color: var(--accent); }}

/* Hero */
.hero {{
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 80px 24px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, var(--bg) 0%, var(--bg-alt) 100%);
}}
.hero-title {{
  font-size: clamp(40px, 8vw, 80px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin-bottom: 16px;
}}
.hero-subtitle {{
  font-size: clamp(16px, 2vw, 22px);
  color: var(--text-secondary);
  max-width: 640px;
  margin: 0 auto 32px;
  line-height: 1.6;
}}
.hero-cta {{
  display: inline-flex;
  padding: 14px 32px;
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  border-radius: 100px;
  transition: transform 0.2s, opacity 0.2s;
}}
.hero-cta:hover {{ transform: scale(1.02); opacity: 0.95; }}

/* Section */
.section {{
  padding: 100px 24px;
  max-width: 1200px;
  margin: 0 auto;
}}
.section-label {{
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--accent);
  margin-bottom: 8px;
}}
.section-title {{
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 16px;
}}
.section-subtitle {{
  font-size: 18px;
  color: var(--text-secondary);
  max-width: 600px;
  margin-bottom: 48px;
  line-height: 1.6;
}}

/* Grid */
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}}

/* Card */
.card {{
  padding: 28px;
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid rgba(255,255,255,0.06);
  transition: transform 0.3s, box-shadow 0.3s;
}}
.card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.3);
}}
.card-title {{
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 8px;
}}
.card-desc {{
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}}

/* Stats */
.stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  padding: 60px 24px;
  background: var(--bg-alt);
  border-top: 1px solid rgba(255,255,255,0.06);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}}
.stat {{
  text-align: center;
  padding: 32px 16px;
}}
.stat-number {{
  font-size: 48px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--accent);
}}
.stat-label {{
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
}}

/* CTA */
.cta-section {{
  text-align: center;
  padding: 100px 24px;
  background: linear-gradient(180deg, var(--bg-alt) 0%, var(--bg) 100%);
}}

/* Footer */
.footer {{
  padding: 48px 24px;
  border-top: 1px solid rgba(255,255,255,0.06);
  text-align: center;
}}
.footer-text {{
  font-size: 13px;
  color: var(--text-secondary);
}}

/* 响应式 */
@media (max-width: 768px) {{
  .nav-links {{ display: none; }}
  .section {{ padding: 60px 16px; }}
  .hero {{ padding: 60px 16px; }}
  .grid {{ grid-template-columns: 1fr; }}
}}
'''

    def _build_section(self, section, index: int) -> str:
        """生成 Section HTML"""
        section_type = section.type
        
        if section_type == "hero":
            return self._build_hero_section(section)
        elif section_type == "grid":
            return self._build_grid_section(section)
        elif section_type == "stats":
            return self._build_stats_section(section)
        elif section_type == "cta":
            return self._build_cta_section(section)
        elif section_type == "timeline":
            return self._build_timeline_section(section)
        elif section_type == "faq":
            return self._build_faq_section(section)
        else:
            return self._build_content_section(section)

    def _build_hero_section(self, section) -> str:
        """生成 Hero Section"""
        badge = f'<span class="section-label">{section.label}</span>' if section.label else ''
        cta = f'<a href="{section.cta.url}" class="hero-cta">{section.cta.label}</a>' if section.cta else ''
        
        return f'''<section class="hero" data-animate="fade-in">
  {badge}
  <h1 class="hero-title">{section.title or ""}</h1>
  <p class="hero-subtitle">{section.subtitle or ""}</p>
  {f'<div style="margin-top:24px">{cta}</div>' if cta else ''}
</section>'''

    def _build_grid_section(self, section) -> str:
        """生成 Grid Section"""
        label = f'<div class="section-label">{section.label}</div>' if section.label else ''
        title = f'<h2 class="section-title">{section.title}</h2>' if section.title else ''
        subtitle = f'<p class="section-subtitle">{section.subtitle}</p>' if section.subtitle else ''
        
        cards_html = ""
        for card in section.cards:
            icon = f'<div style="width:24px;height:24px;color:var(--accent);margin-bottom:12px">{card.icon}</div>' if card.icon else ''
            cards_html += f'''<div class="card" data-animate="slide-up">
  {icon}
  <h3 class="card-title">{card.title}</h3>
  <p class="card-desc">{card.desc}</p>
</div>'''
        
        return f'''<section class="section">
  {label}
  {title}
  {subtitle}
  <div class="grid" style="grid-template-columns: repeat({section.cols}, 1fr)">
    {cards_html}
  </div>
</section>'''

    def _build_stats_section(self, section) -> str:
        """生成 Stats Section"""
        stats_html = ""
        for stat in section.stats:
            stats_html += f'''<div class="stat">
  <div class="stat-number">{stat.number}</div>
  <div class="stat-label">{stat.label}</div>
</div>'''
        
        return f'''<section class="stats">
  {stats_html}
</section>'''

    def _build_cta_section(self, section) -> str:
        """生成 CTA Section"""
        title = f'<h2 class="section-title" style="margin-bottom:16px">{section.title}</h2>' if section.title else ''
        subtitle = f'<p class="section-subtitle" style="margin-bottom:32px">{section.subtitle}</p>' if section.subtitle else ''
        cta = f'<a href="{section.cta.url}" class="hero-cta">{section.cta.label}</a>' if section.cta else ''
        
        return f'''<section class="cta-section">
  {title}
  {subtitle}
  {cta}
</section>'''

    def _build_timeline_section(self, section) -> str:
        """生成 Timeline Section"""
        timeline_html = ""
        for i, item in enumerate(section.timeline, 1):
            timeline_html += f'''<div style="display:flex;gap:16px;margin-bottom:24px">
  <div style="min-width:80px;font-size:13px;color:var(--accent);font-weight:600">{item.date}</div>
  <div>
    <h4 style="font-size:17px;font-weight:600;margin-bottom:4px">{item.title}</h4>
    <p style="font-size:14px;color:var(--text-secondary)">{item.desc}</p>
  </div>
</div>'''
        
        return f'''<section class="section">
  <div class="section-label">{section.label or '路线图'}</div>
  <h2 class="section-title">{section.title or '里程碑'}</h2>
  <div style="margin-top:48px">{timeline_html}</div>
</section>'''

    def _build_faq_section(self, section) -> str:
        """生成 FAQ Section"""
        faq_html = ""
        for item in section.faq:
            faq_html += f'''<div style="padding:16px 0;border-bottom:1px solid rgba(255,255,255,0.06)">
  <h4 style="font-size:15px;font-weight:600;margin-bottom:8px">{item.question}</h4>
  <p style="font-size:14px;color:var(--text-secondary);line-height:1.7">{item.answer}</p>
</div>'''
        
        return f'''<section class="section">
  <h2 class="section-title">{section.title or '常见问题'}</h2>
  <div style="max-width:720px;margin:48px auto 0">{faq_html}</div>
</section>'''

    def _build_content_section(self, section) -> str:
        """生成通用内容 Section"""
        title = f'<h2 class="section-title">{section.title}</h2>' if section.title else ''
        subtitle = f'<p class="section-subtitle">{section.subtitle}</p>' if section.subtitle else ''
        content = f'<div style="font-size:16px;line-height:1.8;color:var(--text-secondary)">{section.content}</div>' if section.content else ''
        
        return f'''<section class="section">
  {title}
  {subtitle}
  {content}
</section>'''

    def _build_global_nav(self, spec) -> str:
        """生成全局导航"""
        return self._build_nav(spec.brand, spec.pages)

    def _build_nav(self, brand: str, pages: List) -> str:
        """生成导航栏"""
        # 只显示前 5 个页面
        nav_pages = pages[:5]
        
        links_html = ""
        for page in nav_pages:
            links_html += f'<a href="{page.filename}" class="nav-link">{page.title}</a>'
        
        # 如果超过 5 个页面，添加"更多"下拉
        if len(pages) > 5:
            links_html += '<a href="#" class="nav-link" onclick="toggleMoreNav(event)">更多 ▾</a>'
        
        return f'''<nav class="nav">
  <a href="index.html" class="nav-brand">{brand}</a>
  <div class="nav-links">
    {links_html}
  </div>
</nav>'''

    def _build_global_footer(self, spec) -> str:
        """生成全局 Footer"""
        return self._build_footer(spec.brand)

    def _build_footer(self, brand: str) -> str:
        """生成 Footer"""
        year = datetime.now().year
        return f'''<footer class="footer">
  <p class="footer-text">© {year} {brand} · 零 Token 生成 · HEP Pipeline</p>
</footer>'''

    def _build_scripts(self, page) -> str:
        """生成页面脚本"""
        return '''<script>
// 平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(a.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  });
});

// 动画触发
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('[data-animate]').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  observer.observe(el);
});
</script>'''

    def _extract_description(self, page) -> str:
        """提取页面描述（用于 SEO）"""
        for section in page.sections:
            if section.subtitle:
                return section.subtitle[:160]
            if section.content:
                return section.content[:160]
        return f"{page.title} - 详细介绍"


# ══════════════════════════════════════════════════════
# 测试
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    # 创建测试 Page 和 Section（不依赖 content_parser）
    test_page = Page(
        filename="index.html",
        title="测试页面",
        type="landing",
        sections=[
            Section(type="hero", title="测试标题", subtitle="测试副标题", 
                   cta=CTA(label="开始", url="#")),
            Section(type="grid", title="功能", cols=3, 
                   cards=[Card(title="功能一", desc="描述一"), Card(title="功能二", desc="描述二")]),
            Section(type="stats", stats=[Stat(number="95%", label="成功率"), Stat(number="0", label="Token")]),
        ]
    )
    
    # 组装网站
    engine = AssemblyEngine(style="apple_cn")
    html = engine.assemble_page(test_page, brand="测试品牌")
    
    print(f"[OK] 组装完成: {len(html):,} bytes")
    print(f"\n[PREVIEW] 前 500 字符:")
    print(html[:500] + "...")