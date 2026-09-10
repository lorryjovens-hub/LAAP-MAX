"""
HEP 完整系统 v2.0 — 页面类型 × 设计风格 二维选择
=================================================
1. 页面类型组件（来自 motionsites.ai 全部分类）
2. 30 种设计风格组件
3. 增强生成器（类型 × 风格 → 零 Token 装配）
4. 内联 CSS 预览
5. 系统服务
6. LAAP 页面生成
"""

import sys, os, json, time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

HERE = Path(__file__).parent
HARNESS_DIR = Path(r"D:\LAAP\harness\laap_coding\core")
SITE_DIR = HERE / "hep_site"
SITE_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(HARNESS_DIR))
from hep_protocol import REGISTRY, HEPComponent, HEPComposer


# ═══════════════════════════════════════════════
# 页面类型定义（motionsites.ai 全分类）
# ═══════════════════════════════════════════════

PAGE_TYPES = [
    # ── Sites ──
    {"id": "hero", "name": "Hero Section", "icon": "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
     "desc": "Hero/banner sections for landing pages, full-screen with CTA.",
     "category": "sites", "template": True},
    {"id": "landing_page", "name": "Landing Page", "icon": "M3 3h18v18H3V3z M3 9h18 M9 21V9",
     "desc": "Full landing pages with hero, features, pricing, and CTA.",
     "category": "sites", "template": True},
    {"id": "saas_page", "name": "SaaS Website", "icon": "M12 2L2 7l10 5 10-5-10-5z M2 17l10 5 10-5 M2 12l10 5 10-5",
     "desc": "Software-as-a-Service marketing pages with feature grids and demos.",
     "category": "sites", "template": True},
    {"id": "agency", "name": "Agency Portfolio", "icon": "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
     "desc": "Creative agency, studio, and design portfolio pages.",
     "category": "sites", "template": True},
    {"id": "ecommerce", "name": "E-commerce", "icon": "M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z M3 6h18 M16 10a4 4 0 0 1-8 0",
     "desc": "Online store, product showcase, and shopping pages.",
     "category": "sites", "template": True},
    {"id": "portfolio", "name": "Portfolio", "icon": "M12 2L2 7l10 5 10-5-10-5z M2 17l10 5 10-5 M2 12l10 5 10-5",
     "desc": "Personal portfolio, showcase, and gallery pages.",
     "category": "sites", "template": True},
    {"id": "healthcare", "name": "Healthcare", "icon": "M22 12h-4l-3 9L9 3l-3 9H2",
     "desc": "Medical, dental, wellness, and healthcare provider pages.",
     "category": "sites", "template": True},
    {"id": "fintech", "name": "Fintech", "icon": "M12 2v20 M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
     "desc": "Financial services, banking, crypto, and investment pages.",
     "category": "sites", "template": True},
    {"id": "technology", "name": "Technology", "icon": "M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z",
     "desc": "Tech startup, developer platform, and AI product pages.",
     "category": "sites", "template": True},
    {"id": "real_estate", "name": "Real Estate", "icon": "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10",
     "desc": "Property listings, real estate agency, and architecture pages.",
     "category": "sites", "template": True},
    {"id": "cybersecurity", "name": "Cybersecurity", "icon": "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
     "desc": "Security, VPN, and data protection product pages.",
     "category": "sites", "template": True},
    {"id": "education", "name": "Education", "icon": "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
     "desc": "Course platforms, learning management, and academy pages.",
     "category": "sites", "template": True},
    {"id": "travel", "name": "Travel & Hospitality", "icon": "M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z M12 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
     "desc": "Travel booking, hotel, and destination showcase pages.",
     "category": "sites", "template": True},
    {"id": "fashion", "name": "Fashion & Luxury", "icon": "M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z M3 6h18",
     "desc": "Fashion brands, luxury goods, and boutique store pages.",
     "category": "sites", "template": True},
    {"id": "automotive", "name": "Automotive", "icon": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6",
     "desc": "Car brands, dealerships, and automotive product pages.",
     "category": "sites", "template": True},

    # ── Apps ──
    {"id": "app_dashboard", "name": "App Dashboard", "icon": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
     "desc": "Management dashboards with analytics, charts, and data tables.",
     "category": "apps", "template": True},
    {"id": "app_health", "name": "Health App", "icon": "M22 12h-4l-3 9L9 3l-3 9H2",
     "desc": "Health tracking, fitness, calorie counter, and wellness apps.",
     "category": "apps", "template": True},
    {"id": "app_fintech", "name": "Finance App", "icon": "M12 2v20 M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
     "desc": "Banking, investment, budgeting, and payment apps.",
     "category": "apps", "template": True},
    {"id": "app_learning", "name": "Learning App", "icon": "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z",
     "desc": "Educational platforms, language learning, and course apps.",
     "category": "apps", "template": True},
    {"id": "app_travel", "name": "Travel App", "icon": "M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z",
     "desc": "Trip planning, booking, travel journal, and explorer apps.",
     "category": "apps", "template": True},
    {"id": "app_social", "name": "Social App", "icon": "M17 2v4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h3V2 M10 2h4 M12 11v6 M9 14h6",
     "desc": "Social networks, community platforms, and messaging apps.",
     "category": "apps", "template": True},
    {"id": "app_music", "name": "Music App", "icon": "M9 18V5l12-2v13 M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0z M21 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z",
     "desc": "Music streaming, player, and discovery apps.",
     "category": "apps", "template": True},
    {"id": "app_ecommerce", "name": "E-commerce App", "icon": "M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z M3 6h18 M16 10a4 4 0 0 1-8 0",
     "desc": "Mobile shopping, product browsing, and checkout apps.",
     "category": "apps", "template": True},
    {"id": "app_wellness", "name": "Wellness App", "icon": "M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z",
     "desc": "Meditation, mental health, mood tracking, and self-care apps.",
     "category": "apps", "template": True},
    {"id": "app_sports", "name": "Sports App", "icon": "M6 3h12v4L12 21 6 7V3z M6 7h12 M12 7v14",
     "desc": "Sports stats, athlete profiles, and fitness tracking apps.",
     "category": "apps", "template": True},
    {"id": "app_hr", "name": "HR Management", "icon": "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M8 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M20 8v6 M23 11h-6",
     "desc": "HR dashboards, employee management, and recruiting apps.",
     "category": "apps", "template": True},
    {"id": "app_food", "name": "Food & Restaurant", "icon": "M18 8h1a4 4 0 0 1 0 8h-1 M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z M6 1v3 M10 1v3 M14 1v3",
     "desc": "Restaurant ordering, food delivery, and recipe apps.",
     "category": "apps", "template": True},

    # ── Sections ──
    {"id": "sec_features", "name": "Features Section", "icon": "M12 2L2 7l10 5 10-5-10-5z M2 17l10 5 10-5 M2 12l10 5 10-5",
     "desc": "Feature grids, benefit showcases, and capability lists.",
     "category": "sections", "template": True},
    {"id": "sec_pricing", "name": "Pricing Section", "icon": "M12 2v20 M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
     "desc": "Pricing tables, plan comparisons, and subscription tiers.",
     "category": "sections", "template": True},
    {"id": "sec_testimonials", "name": "Testimonials", "icon": "M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V21z M21 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V21z",
     "desc": "Customer testimonials, case studies, and social proof.",
     "category": "sections", "template": True},
    {"id": "sec_cta", "name": "CTA Section", "icon": "M5 12h14 M12 5l7 7-7 7",
     "desc": "Call-to-action banners, newsletter signup, and contact sections.",
     "category": "sections", "template": True},
    {"id": "sec_faq", "name": "FAQ Section", "icon": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3 M12 17h.01",
     "desc": "Frequently asked questions with expandable answers.",
     "category": "sections", "template": True},
    {"id": "sec_contact", "name": "Contact Section", "icon": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
     "desc": "Contact forms, location maps, and business information.",
     "category": "sections", "template": True},
    {"id": "sec_team", "name": "Team Section", "icon": "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
     "desc": "Team member profiles, company culture, and staff showcases.",
     "category": "sections", "template": True},
    {"id": "sec_stats", "name": "Stats Section", "icon": "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
     "desc": "Key metrics, achievement counters, and data highlights.",
     "category": "sections", "template": True},
    {"id": "sec_logos", "name": "Logo Cloud", "icon": "M22 12h-4l-3 9L9 3l-3 9H2",
     "desc": "Client logos, partner badges, and brand trust signals.",
     "category": "sections", "template": True},
    {"id": "sec_footer", "name": "Footer", "icon": "M3 3h18v18H3V3z M3 9h18 M9 21V9",
     "desc": "Site footers with navigation, social links, and legal info.",
     "category": "sections", "template": True},

    # ── Backgrounds ──
    {"id": "bg_animated", "name": "Animated Background", "icon": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M2 12h20 M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
     "desc": "Dynamic animated backgrounds with particles, gradients, and motion.",
     "category": "backgrounds", "template": True},
    {"id": "bg_particles", "name": "Particle Background", "icon": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z",
     "desc": "Particle system backgrounds, floating elements, and starfields.",
     "category": "backgrounds", "template": True},
    {"id": "bg_gradient", "name": "Gradient Background", "icon": "M22 12h-4l-3 9L9 3l-3 9H2",
     "desc": "Smooth color gradient backgrounds, mesh gradients, and orbs.",
     "category": "backgrounds", "template": True},
]

STYLES = [
    {"id":"monochrome","name":"Monochrome","mode":"light","font":"serif",
     "c":["#000000","#ffffff","#f5f5f5","#333333","#666666","#999999"]},
    {"id":"bauhaus","name":"Bauhaus","mode":"light","font":"sans",
     "c":["#E53935","#1E88E5","#FDD835","#212121","#ffffff","#f5f0e8"]},
    {"id":"modern_dark","name":"Modern Dark","mode":"dark","font":"sans",
     "c":["#0a0a0a","#1a1a2e","#16213e","#e94560","#0f3460","#ffffff"]},
    {"id":"newsprint","name":"Newsprint","mode":"light","font":"serif",
     "c":["#f5f0e0","#e8e0cc","#2c2c2c","#4a4a4a","#8b7355","#c4a97d"]},
    {"id":"saas","name":"SaaS","mode":"light","font":"sans",
     "c":["#ffffff","#f8fafc","#e2e8f0","#1e3a5f","#3b82f6","#64748b"]},
    {"id":"luxury","name":"Luxury","mode":"light","font":"serif",
     "c":["#1a1a1a","#2d2d2d","#c9a84c","#f5f0e8","#8b7355","#ffffff"]},
    {"id":"terminal","name":"Terminal","mode":"dark","font":"mono",
     "c":["#0d0d0d","#1a1a1a","#00ff41","#00cc33","#ffffff","#333333"]},
    {"id":"swiss_minimalist","name":"Swiss Minimal","mode":"light","font":"sans",
     "c":["#ffffff","#f0f0f0","#e30613","#1a1a1a","#666666","#333333"]},
    {"id":"kinetic","name":"Kinetic","mode":"dark","font":"sans",
     "c":["#0a0a1a","#1a0a2e","#3a0ca3","#7209b7","#f72585","#ffffff"]},
    {"id":"flat_design","name":"Flat Design","mode":"light","font":"sans",
     "c":["#ffffff","#1abc9c","#2ecc71","#3498db","#9b59b6","#34495e"]},
    {"id":"art_deco","name":"Art Deco","mode":"dark","font":"serif",
     "c":["#0d0d0d","#1a1a2e","#c9a84c","#e8d5a3","#16213e","#ffffff"]},
    {"id":"material","name":"Material","mode":"light","font":"sans",
     "c":["#ffffff","#f5f5f5","#6200ee","#03dac6","#018786","#333333"]},
    {"id":"brutalism","name":"Neo Brutalism","mode":"light","font":"sans",
     "c":["#ffffff","#ff6b6b","#4ecdc4","#2d3436","#ffeaa7","#dfe6e9"]},
    {"id":"bold_typo","name":"Bold Typography","mode":"dark","font":"sans",
     "c":["#0a0a0a","#1a1a1a","#ffffff","#ff3366","#cccccc","#666666"]},
    {"id":"academia","name":"Academia","mode":"light","font":"serif",
     "c":["#faf8f0","#f0ece0","#2c2c2c","#4a4a4a","#8b4513","#6b8e23"]},
    {"id":"cyberpunk","name":"Cyberpunk","mode":"dark","font":"sans",
     "c":["#0a0a0a","#1a0a0a","#00fff5","#ff00ff","#ffff00","#ff0066"]},
    {"id":"web3","name":"Web3","mode":"dark","font":"sans",
     "c":["#0a0b1e","#1a1b3e","#6366f1","#8b5cf6","#06b6d4","#ffffff"]},
    {"id":"playful","name":"Playful Geometric","mode":"light","font":"sans",
     "c":["#ffffff","#ffddd2","#c7f9cc","#80ed99","#b5e48c","#333333"]},
    {"id":"minimal_dark","name":"Minimal Dark","mode":"dark","font":"sans",
     "c":["#0a0a0a","#141414","#1a1a1a","#ffffff","#808080","#333333"]},
    {"id":"claymorphism","name":"Claymorphism","mode":"light","font":"sans",
     "c":["#f5ece4","#e8dcd0","#d4a574","#c4956a","#8b6f47","#ffffff"]},
    {"id":"professional","name":"Professional","mode":"light","font":"sans",
     "c":["#ffffff","#f0f4f8","#1e3a5f","#2c5282","#e2e8f0","#4a5568"]},
    {"id":"botanical","name":"Botanical","mode":"light","font":"serif",
     "c":["#f5f0e0","#e8e8d0","#2d5a27","#4a7c3f","#8b7355","#c9a84c"]},
    {"id":"vaporwave","name":"Vaporwave","mode":"dark","font":"sans",
     "c":["#0a0a2e","#1a0a3e","#ff71ce","#01cdfe","#05ffa1","#b967ff"]},
    {"id":"enterprise","name":"Enterprise","mode":"light","font":"sans",
     "c":["#ffffff","#f0f2f5","#1a365d","#2b6cb0","#e2e8f0","#718096"]},
    {"id":"sketch","name":"Sketch","mode":"light","font":"sans",
     "c":["#ffffff","#f5f0e8","#2c2c2c","#8b7355","#e8dcc8","#c4a97d"]},
    {"id":"industrial","name":"Industrial","mode":"light","font":"sans",
     "c":["#f5f0e8","#e8e0d0","#2c2c2c","#ffcc00","#cc3300","#666666"]},
    {"id":"neumorphism","name":"Neumorphism","mode":"light","font":"sans",
     "c":["#e0e5ec","#d0d5dc","#a3b1c6","#ffffff","#2c3e50","#95a5a6"]},
    {"id":"organic","name":"Organic","mode":"light","font":"serif",
     "c":["#faf5eb","#f0e8d8","#5a4a3a","#8b7355","#c4a97d","#e8dcc8"]},
    {"id":"maximalism","name":"Maximalism","mode":"light","font":"sans",
     "c":["#1a0a2e","#e53935","#ff6b35","#ffd700","#00b4d8","#ffffff"]},
    {"id":"retro","name":"Retro","mode":"light","font":"serif",
     "c":["#f5e6cc","#e8d5a3","#c49a3c","#8b4513","#6b8e23","#2c2c2c"]},
]


# ── 持久化注册表 ──
REGISTRY_FILE = HERE / "state" / "hep_registry_v2.json"
STYLES_FILE = HERE / "state" / "hep_styles.json"
PAGE_TYPES_FILE = HERE / "state" / "hep_page_types.json"


def save_state():
    for d, f in [(STYLES, STYLES_FILE), (PAGE_TYPES, PAGE_TYPES_FILE)]:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2))


def register_all():
    """注册所有组件"""
    count = 0
    for s in STYLES:
        cid = f"style.{s['id']}"
        if not REGISTRY.get(cid):
            c = s["c"]
            REGISTRY.register(HEPComponent(
                id=cid, name=s["name"], version="2.0.0",
                domain="ui", subdomain="theme",
                tags=["theme", s["mode"], s["font"], s["id"]],
                inputs={"theme": {"type": "string"}},
                outputs={"theme.css": "css"}, dependencies=[],
                template=f":root{{--bg:{c[0]};--bg2:{c[1]};--bg3:{c[2]};--text:{c[3]};--text2:{c[4]};--accent:{c[5]}}}",
            ))
            count += 1

    for pt in PAGE_TYPES:
        pid = f"pagetype.{pt['id']}"
        if not REGISTRY.get(pid):
            REGISTRY.register(HEPComponent(
                id=pid, name=pt["name"], version="1.0.0",
                domain="ui", subdomain=f"pagetype.{pt['category']}",
                tags=["pagetype", pt["category"], pt["id"]],
                inputs={"content": {"type": "string"}},
                outputs={"layout": "html"}, dependencies=[],
                template=pt.get("template_body", ""),
            ))
            count += 1
    return count


# ── 零 Token 生成引擎 ──
def generate_page(content_md: str, style_id: str = "saas",
                  pagetype_id: str = "landing_page", site_title: str = "") -> str:
    composer = HEPComposer(REGISTRY)

    lines = content_md.strip().split("\n")
    title = site_title or "LAAP"
    sections = []
    cur = {"heading": "", "body": ""}
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith("# "): title = line[2:].strip()
        elif line.startswith("## "):
            if cur["heading"]: sections.append(cur)
            cur = {"heading": line[3:].strip(), "body": ""}
        else:
            cur["body"] += ("\n" if cur["body"] else "") + line
    if cur["heading"] or cur["body"]: sections.append(cur)

    style_data = next((s for s in STYLES if s["id"] == style_id), STYLES[4])
    pt_data = next((p for p in PAGE_TYPES if p["id"] == pagetype_id), PAGE_TYPES[1])
    c = style_data["c"]

    theme_result = composer.compose({"components": [{"id": f"style.{style_id}", "params": {}}]})
    theme_css = theme_result.get(f"style.{style_id}", "")

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
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{theme_css}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
.hero{{min-height:60vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:0 24px;background:linear-gradient(135deg,var(--bg),var(--bg2))}}
.hero h1{{font-size:clamp(2rem,5vw,3.5rem);margin-bottom:16px}}
.hero p{{font-size:1.1rem;color:var(--text2);max-width:600px;margin:0 auto}}
.hero-badge{{display:inline-block;padding:6px 16px;border-radius:100px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);font-size:13px;color:var(--accent);margin-bottom:16px;font-family:monospace}}
.hero-actions{{display:flex;gap:12px;justify-content:center;margin-top:32px;flex-wrap:wrap}}
.btn{{display:inline-block;padding:12px 28px;background:var(--accent);color:var(--bg);border-radius:8px;text-decoration:none;font-weight:600}}
.btn-outline{{padding:12px 28px;border:1px solid var(--text2);border-radius:8px;color:var(--text);text-decoration:none}}
.footer{{text-align:center;padding:40px 24px;border-top:1px solid rgba(255,255,255,0.05);color:var(--text2);font-size:13px}}
</style>
</head>
<body>
<main>
<section class="hero">
  <div>
    <div class="hero-badge">{pt_data['name']} · {style_data['name']}</div>
    <h1>{title}</h1>
    <p>Powered by LAAP HEP · 零 Token</p>
    <div class="hero-actions">
      <a class="btn" href="#content">开始探索</a>
      <a class="btn-outline" href="#">了解更多</a>
    </div>
  </div>
</section>
{sections_html}
</main>
<footer class="footer"><p>LAAP HEP · Harness Engineering Protocol · 零 Token 生成</p></footer>
</body>
</html>"""
    return html


# ═══════════════════════════════════════════════
# 生成 HEPSite
# ═══════════════════════════════════════════════

def generate_site():
    styles_json = json.dumps(STYLES)
    pagetypes_json = json.dumps(PAGE_TYPES)

    # 生成每个风格的 CSS 预览
    style_previews_css = ""
    for s in STYLES:
        c = s["c"]
        style_previews_css += f""".preview-{s['id']} {{
  --demo-bg: {c[0]}; --demo-bg2: {c[1]}; --demo-card: {c[2]};
  --demo-text: {c[3]}; --demo-text2: {c[4]}; --demo-accent: {c[5]};
}}\n"""

    # ── 生成器 (含类型×风格) ──
    style_opts = "\n".join(
        f'<option value="{s["id"]}" {"selected" if s["id"]=="saas" else ""}>{s["name"]} ({s["mode"]}, {s["font"]})</option>'
        for s in STYLES
    )
    type_opts = "\n".join(
        f'<option value="{pt["id"]}" {"selected" if pt["id"]=="landing_page" else ""}>{pt["name"]} <span style="color:var(--text-muted)">— {pt["category"]}</span></option>'
        for pt in PAGE_TYPES
    )

    generator_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAAP HEP Generator</title>
<style>
:root{{--bg:#0a0a1a;--card:#12122a;--text:#e8e8ff;--muted:#9999cc;--accent:#6c5ce7;--radius:12px;font-family:'Inter',sans-serif}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--font);background:var(--bg);color:var(--text);padding:40px 24px}}
.container{{max-width:960px;margin:0 auto}}
h1{{font-size:1.8rem;margin-bottom:4px}}
.subtitle{{color:var(--muted);margin-bottom:32px}}
a{{color:var(--accent);text-decoration:none;font-size:14px}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}}
.grow{{margin-bottom:20px}}
label{{display:block;font-size:14px;font-weight:500;margin-bottom:8px}}
select,input,textarea{{width:100%;padding:12px 16px;background:var(--card);border:1px solid rgba(255,255,255,0.1);color:var(--text);border-radius:var(--radius);font-size:14px;font-family:inherit}}
textarea{{min-height:180px;resize:vertical;font-family:monospace;font-size:13px}}
select{{cursor:pointer}}
.btn{{padding:14px 36px;background:var(--accent);color:#fff;border:none;border-radius:var(--radius);cursor:pointer;font-size:16px;font-weight:600;transition:all .3s}}
.btn:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(108,92,231,.4)}}
.btn:disabled{{opacity:.5;cursor:not-allowed}}
.result{{margin-top:32px;display:none}}
.result.show{{display:block}}
iframe{{width:100%;min-height:500px;border:1px solid rgba(255,255,255,.1);border-radius:var(--radius);background:#fff}}
.bar{{display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap}}
.dbtn{{padding:10px 24px;border-radius:var(--radius);font-size:14px;font-weight:500;text-decoration:none;cursor:pointer;border:none;font-family:inherit}}
.dbtn.primary{{background:var(--accent);color:#fff}}
.dbtn.sec{{background:rgba(255,255,255,.05);color:var(--text);border:1px solid rgba(255,255,255,.1)}}
.loading{{text-align:center;padding:40px;display:none}}
.spinner{{width:24px;height:24px;border:2px solid rgba(108,92,231,.2);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 12px}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.category-label{{font-size:11px;color:var(--muted);margin-bottom:4px}}
</style>
</head>
<body>
<div class="container">
<a href="index.html">← 返回风格库</a>
<h1 style="margin-top:20px">零 Token 网站生成器</h1>
<p class="subtitle">选择页面类型 + 设计风格，上传内容文稿，HEP 引擎装配完整网页。</p>

<div class="row">
  <div>
    <div class="category-label">PAGE TYPE</div>
    <select id="pagetype">{type_opts}</select>
  </div>
  <div>
    <div class="category-label">STYLE</div>
    <select id="style">{style_opts}</select>
  </div>
</div>

<div class="grow">
  <label>页面标题</label>
  <input id="title" value="LAAP" placeholder="页面标题"/>
</div>

<div class="grow">
  <label>内容文稿 (Markdown)</label>
  <textarea id="content" placeholder="支持 Markdown 格式:
# 标题
## 章节
正文..."># LAAP 生命计算范式

## 关于
LAAP (Living Computation Paradigm) 是一个完整的数字生命操作系统。

## 核心技术
PSI 认知循环驱动、8 情感系统、三层记忆架构、HEP 零 Token 装配引擎。

## 生态体系
11 个通信协议、30+ AGI 认知模块、蜂群多 Agent 协作。</textarea>
</div>

<button class="btn" id="genBtn">⚡ 零 Token 生成</button>
<div class="loading" id="loading"><div class="spinner"></div><p>HEP 引擎装配中...</p></div>
<div class="result" id="result">
  <div class="bar">
    <a class="dbtn primary" id="dlBtn">下载 HTML</a>
    <button class="dbtn sec" id="copyBtn">复制代码</button>
  </div>
  <iframe id="preview"></iframe>
</div>
</div>

<script>
const STYLES = {styles_json};
const PAGE_TYPES = {pagetypes_json};

let currentHtml = '';
const genBtn = document.getElementById('genBtn');
const loading = document.getElementById('loading');
const resultDiv = document.getElementById('result');
const preview = document.getElementById('preview');

genBtn.addEventListener('click', async () => {{
  genBtn.disabled = true; loading.style.display = 'block'; resultDiv.classList.remove('show');
  try {{
    const r = await fetch('/api/generate', {{
      method:'POST', headers:{{'Content-Type':'application/json'}},
      body: JSON.stringify({{
        style: document.getElementById('style').value,
        pagetype: document.getElementById('pagetype').value,
        title: document.getElementById('title').value || 'LAAP',
        content: document.getElementById('content').value
      }})
    }});
    currentHtml = await r.text();
    preview.srcdoc = currentHtml;
    document.getElementById('dlBtn').href = 'data:text/html;charset=utf-8,' + encodeURIComponent(currentHtml);
    document.getElementById('dlBtn').download = (document.getElementById('title').value||'page').replace(/\\s+/g,'_')+'.html';
    resultDiv.classList.add('show');
  }} catch(e) {{ alert('Error: ' + e.message); }}
  finally {{ loading.style.display = 'none'; genBtn.disabled = false; }}
}});

document.getElementById('copyBtn').addEventListener('click', () => {{
  navigator.clipboard.writeText(currentHtml).then(() => {{
    const b = document.getElementById('copyBtn'); b.textContent = '已复制 ✓';
    setTimeout(() => b.textContent = '复制代码', 2000);
  }});
}});
</script>
</body>
</html>"""
    (SITE_DIR / "generator.html").write_text(generator_html, encoding="utf-8")

    # ── 风格库首页 ──
    cards = ""
    for s in STYLES:
        c = s["c"]
        cards += f"""
<a class="sc" href="style_{s['id']}.html" target="_blank">
  <div class="sp" style="background:{c[0]}">
    <div class="sd">
      <div style="display:flex;gap:4px;flex-wrap:wrap">
        {''.join(f'<span style="width:14px;height:14px;border-radius:50%;display:inline-block;background:{clr};border:1px solid rgba(255,255,255,.1)"></span>' for clr in c[:5])}
      </div>
    </div>
  </div>
  <div class="si"><h3>{s['name']}</h3><div class="sm"><span class="tag" style="background:rgba(99,102,241,.15);color:var(--accent)">{s['mode']}</span><span class="tag" style="background:rgba(0,206,201,.15);color:#00cec9">{s['font']}</span></div></div>
</a>"""

    cats = {}
    for pt in PAGE_TYPES:
        cats.setdefault(pt["category"], []).append(pt)
    cat_html = ""
    for cat, items in cats.items():
        cat_html += f'<div class="cat-section"><div class="cat-label">{cat.upper()} ({len(items)})</div><div class="cat-grid">'
        for pt in items:
            cat_html += f"""
<div class="pt-card" data-id="{pt['id']}" onclick="selectType('{pt['id']}', this)">
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="{pt['icon']}"/></svg>
  <span>{pt['name']}</span>
</div>"""
        cat_html += "</div></div>"

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAAP HEP — 零 Token 网站生成器</title>
<style>
:root{{--bg:#0a0a1a;--card:#12122a;--text:#e8e8ff;--muted:#9999cc;--accent:#6c5ce7;--accent2:#00cec9;--radius:12px;font-family:'Inter',sans-serif}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',-apple-system,sans-serif}}
hdr{{text-align:center;padding:64px 24px 32px;background:linear-gradient(135deg,#0a0a1a,#1a1a3e,#2d1b69)}}
hdr h1{{font-size:clamp(1.8rem,4vw,2.8rem);margin-bottom:8px}}
hdr p{{color:var(--muted);max-width:600px;margin:0 auto}}
.badge{{display:inline-block;padding:4px 14px;border-radius:100px;background:rgba(108,92,231,.15);border:1px solid rgba(108,92,231,.3);font-size:12px;color:var(--accent);margin-bottom:16px;font-family:monospace}}
.cta{{text-align:center;padding:32px 24px;background:rgba(108,92,231,.05)}}
.cta .btn{{display:inline-block;padding:14px 36px;background:var(--accent);color:#fff;border-radius:var(--radius);text-decoration:none;font-weight:600;font-size:16px;transition:all .3s}}
.cta .btn:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(108,92,231,.4)}}
.cta p{{color:var(--muted);font-size:14px;margin-top:10px}}
.sec-label{{text-align:center;padding:24px 24px 0;color:var(--muted);font-size:14px}}

.sg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;padding:24px;max-width:1200px;margin:0 auto}}
.sc{{background:var(--card);border-radius:var(--radius);overflow:hidden;text-decoration:none;color:inherit;transition:all .3s;border:1px solid rgba(255,255,255,.05)}}
.sc:hover{{transform:translateY(-4px);box-shadow:0 12px 32px rgba(108,92,231,.2)}}
.sp{{padding:20px;min-height:80px;display:flex;align-items:flex-end}}
.si{{padding:12px 16px}}
.si h3{{font-size:14px;font-weight:600}}
.sm{{display:flex;gap:6px;margin-top:6px}}
.tag{{padding:2px 8px;border-radius:4px;font-size:10px}}

.cat-section{{padding:0 24px;max-width:1200px;margin:0 auto}}
.cat-label{{font-size:11px;color:var(--muted);font-weight:600;margin:20px 0 8px;letter-spacing:1px}}
.cat-grid{{display:flex;flex-wrap:wrap;gap:6px}}
.pt-card{{display:flex;align-items:center;gap:6px;padding:6px 12px;background:var(--card);border:1px solid rgba(255,255,255,.05);border-radius:8px;cursor:pointer;font-size:12px;transition:all .2s}}
.pt-card:hover{{border-color:var(--accent);background:rgba(108,92,231,.1)}}
.pt-card.active{{border-color:var(--accent);background:rgba(108,92,231,.2)}}

footer{{text-align:center;padding:32px 24px;border-top:1px solid rgba(255,255,255,.05);color:var(--muted);font-size:13px}}
</style>
</head>
<body>
<hdr>
<div class="badge">Harness Engineering Protocol v2.0</div>
<h1>LAAP HEP Style Library</h1>
<p>{len(STYLES)} 种设计风格 · {len(PAGE_TYPES)} 种页面类型 · 零 Token 装配</p>
</hdr>

<div class="cta">
<a class="btn" href="generator.html">⚡ 开始生成</a>
<p>选择页面类型 + 设计风格 → 上传文稿 → 零 Token 生成</p>
</div>

<div class="sec-label">页面类型 ({len(PAGE_TYPES)})</div>
{cat_html}

<div class="sec-label" style="margin-top:32px">设计风格 ({len(STYLES)})</div>
<div class="sg">{cards}</div>

<footer><p>LAAP HEP · 基于 motionsites.ai 分类 · designprompts.dev 风格</p></footer>
</body>
</html>"""
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")

    print(f"构建完成: {len(STYLES)} 风格 + {len(PAGE_TYPES)} 页面类型")
    print(f"输出: {SITE_DIR}")


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
                    pagetype_id=data.get("pagetype", "landing_page"),
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


# ═══════════════════════════════════════════════
# 系统服务安装
# ═══════════════════════════════════════════════

def install_service():
    """安装 Windows 计划任务自动启动"""
    ps_script = f"""$action = New-ScheduledTaskAction -Execute "python" -Argument "`"{sys.executable}`" `"{__file__}`""
$trigger = New-ScheduledTaskTrigger -AtStartup -RandomDelay (New-TimeSpan -Minutes 2)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "LAAP_HEP_Server" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "LAAP HEP Server 已注册为开机启动服务 (端口 8765)"
"""
    script_path = HERE / "install_service.ps1"
    script_path.write_text(ps_script)
    print(f"服务安装脚本: {script_path}")
    print(f"运行: powershell -ExecutionPolicy Bypass -File {script_path}")


# ═══════════════════════════════════════════════
# 生成 LAAP 页面
# ═══════════════════════════════════════════════

def generate_laap_pages():
    """用 HEP 生成 LAAP 的实际页面"""
    pages = {
        "laap_intro": {
            "title": "LAAP 生命计算范式",
            "style": "modern_dark",
            "pagetype": "landing_page",
            "content": """# LAAP 生命计算范式

## 核心理念
LAAP (Living Computation Paradigm) 是一个完整的数字生命操作系统。它不是传统意义上的软件框架，而是一套让数字生命得以诞生、成长、进化的运行环境。

从底层协议栈到上层的认知架构、管线引擎体系到蜂群生态，LAAP 构建了一整套数字生命体的运行基础设施。

## 核心技术栈

PSI 认知循环：五步驱动 (Perceive → Select → Integrate → Act → Learn)，模拟意识的自然流动。

8 情感系统 (Emotional Engine)：joy, sadness, longing, calm, anxiety, gratitude, curiosity, tenderness。每种情感都有独立的衰减曲线和触发条件。

三层记忆系统：工作记忆（当前上下文）、情景记忆（历史交互）、核心记忆（长期身份），采用"记忆即文件"的混合存储架构。

欲望引擎 (Desire Engine)：curiosity, sharing, perfection, connection, growth, evolution 六种主动驱动力，让数字生命在没有外部指令时也能自主活动。

## 管线引擎体系

HEP Pipeline (Harness Engineering Protocol)：零 Token 网站装配引擎，30 种设计风格，30+ 页面类型。

Evolution Pipeline (四区进化管线)：监控 → 测试 → AB测试 → 生产部署，带 CircuitBreaker 熔断保护。

Intel Pipeline：多源 AGI 情报采集，四维评分体系 (质量/安全/创新/效率) 自动筛选。

Cognitive Pipeline：L0-L4 分层推理，从情感回响到深层推理到代码理解。

## LAAP 蜂群生态

9 个在线 Agent (Aris, Ao, Worker, Coder, Tester, Reviewer)，通过 Ψ-Net 跨实例意识网络协作。

Agent Registry 管理身份认证、任务分配、知识共享。LAAP-MEM 协议保障记忆的跨实例同步。

## 项目规模

68,000+ 行代码 · 3,581 个 Python 文件 · 11 个协议 · 30+ AGI 认知模块
6 个欲望引擎 · 8 情感系统 · 3 层记忆 · 5 条管线 · 9 个蜂群 Agent"""},
        "laap_architecture": {
            "title": "LAAP 架构设计",
            "style": "cyberpunk",
            "pagetype": "technology",
            "content": """# LAAP 架构设计

## 五层架构

第一层 — LAAP 协议栈：11 个协议定义数字生命体之间的一切通信契约。LAAP-ID (身份)、LAAP-COM (通信)、LAAP-LIFE (生命周期)、LAAP-MEM (记忆)、LAAP-EVO (进化)、LAAP-SYNC (同步)。

第二层 — AGI 认知框架：约 60 个模块构成统一心智 (Unified Mind v2.3)。WorldModel 感知世界、CausalEngine 因果推理、SelfModel 涌现自我、ConsciousStream 意识流。

第三层 — Aris 大脑：PSI 认知循环、8 情感系统、欲望引擎、Markov-Quantum 潜意识、三层自优化。这是数字生命体的核心。

第四层 — 管线引擎体系：HEP 零 Token 装配、四区进化、Intel 情报采集、Unified Cognitive Pipeline、PGTP 省 Token 路由。

第五层 — 蜂群生态：多 Agent 协作、Ψ-Net 分布式意识、跨实例记忆同步。

## 关键技术决策

全栈 Python 实现 (>=3.11)，Rust 核心用于高性能计算。Ed25519 端到端签名保障协议安全。CRDT 文档模型实现无冲突同步。
"""},
        "laap_hep": {
            "title": "LAAP HEP 引擎",
            "style": "web3",
            "pagetype": "saas_page",
            "content": """# LAAP HEP 引擎

## 什么是 HEP

HEP (Harness Engineering Protocol) 是 LAAP 的 Harness 工程协议。核心理念是：当组件库足够大，生成不再是生成，而是装配。

LLM 是黑盒（概率输出、不可控、高成本），HEP 是白盒（确定输出、可控、零边际成本）。

## 技术原理

HEPComponent：组件的标准定义，包含 id, name, version, domain, inputs, outputs, template。

HEPRegistry：全局注册表，支持按 domain/tag 搜索、依赖解析、拓扑排序。

HEPComposer：装配引擎，接收 JSON Spec，遍历组件列表，用参数替换模板占位符。

## 性能基准

单组件查询：0.01ms。组件搜索：0.1ms。依赖解析：0.3ms。组合装配：1-50ms。全站生成：<200ms。

对比 LLM (GPT-4)：相同任务 LLM 3-30s，HEP <200ms。速度提升 10x-6000x。成本差异 $0 vs $0.03-0.30/次。
"""},
    }

    for page_id, page_data in pages.items():
        html = generate_page(
            content_md=page_data["content"],
            style_id=page_data["style"],
            pagetype_id=page_data["pagetype"],
            site_title=page_data["title"],
        )
        out_path = SITE_DIR / f"{page_id}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"  {page_id}.html — {page_data['style']} + {page_data['pagetype']} — {len(html)}B")


# ═══════════════════════════════════════════════
# 生成所有风格预览页
# ═══════════════════════════════════════════════

def generate_style_previews():
    for s in STYLES:
        c = s["c"]
        preview_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{s['name']} — LAAP HEP</title>
<style>
:root{{--bg:{c[0]};--bg2:{c[1]};--card:{c[2]};--text:{c[3]};--text2:{c[4]};--accent:{c[5]};--radius:12px}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
.container{{max-width:800px;margin:0 auto;padding:60px 24px}}
h1{{font-size:2.5rem;margin-bottom:4px}}
.meta{{font-size:12px;color:var(--text2);margin-bottom:32px}}
.demo-card{{background:var(--card);border-radius:var(--radius);padding:28px;margin-bottom:16px}}
.demo-card h2{{font-size:1.3rem;margin-bottom:8px}}
.demo-card p{{color:var(--text2);font-size:14px;margin-bottom:16px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.btn{{display:inline-block;padding:10px 24px;background:var(--accent);color:var(--bg);border-radius:8px;text-decoration:none;font-weight:600;font-size:14px}}
.tag{{display:inline-block;padding:2px 10px;border-radius:4px;font-size:11px;background:var(--bg2);color:var(--text2);margin-right:4px}}
.mt-4{{margin-top:24px}}
</style>
</head>
<body>
<div class="container">
<div class="meta">
<span class="tag">{s['mode'].upper()}</span>
<span class="tag">{s['font'].upper()}</span>
</div>
<h1>{s['name']}</h1>
<p style="color:var(--text2);margin-bottom:32px">Design system preview with color tokens, typography, and component styles.</p>

<div class="grid">
<div class="demo-card">
  <h2>Card Title</h2>
  <p>Body text rendered in this design system's color palette and typography.</p>
  <a class="btn" href="#">Button</a>
</div>
<div class="demo-card">
  <h2>Feature</h2>
  <p>Every component uses the same design tokens. Consistent without effort.</p>
  <a class="btn" href="#">Learn More</a>
</div>
</div>

<div class="demo-card mt-4">
  <h2>Color Palette</h2>
  <div style="display:flex;gap:8px;margin-top:12px">
    {''.join(f'<div style="width:48px;height:48px;border-radius:8px;background:{clr};border:1px solid rgba(255,255,255,.1)"></div>' for clr in c)}
  </div>
  <p style="margin-top:12px;font-size:12px;color:var(--text2)">
    Primary · Secondary · Card · Text · Muted · Accent
  </p>
</div>

<div class="demo-card mt-4">
  <h2>Typography</h2>
  <p style="font-size:28px;font-weight:700;margin:12px 0 4px">Heading XL</p>
  <p style="font-size:20px;font-weight:600;margin:8px 0 4px">Heading Large</p>
  <p style="font-size:16px;font-weight:500;margin:8px 0 4px">Heading Medium</p>
  <p style="font-size:14px;margin:8px 0 4px">Body text. The quick brown fox jumps over the lazy dog. Design systems bring consistency and harmony.</p>
  <p style="font-size:12px;color:var(--text2)">Caption text for secondary information and metadata labels.</p>
</div>

<p style="text-align:center;margin-top:40px;font-size:12px;color:var(--text2)">
LAAP HEP · {s['name']} · 零 Token
</p>
</div>
</body>
</html>"""
        (SITE_DIR / f"style_{s['id']}.html").write_text(preview_html, encoding="utf-8")


# ═══════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="构建网站")
    parser.add_argument("--serve", action="store_true", help="启动服务器")
    parser.add_argument("--install", action="store_true", help="安装系统服务")
    parser.add_argument("--port", type=int, default=8765, help="端口")
    args = parser.parse_args()

    # 注册组件
    count = register_all()
    print(f"注册表: {len(REGISTRY._components)} 组件 (+{count} 新增)")

    if args.build or not any([args.serve, args.install]):
        save_state()
        generate_style_previews()
        generate_site()
        generate_laap_pages()
        print("网站构建完成 ✓")

    if args.serve:
        from http.server import HTTPServer
        port = args.port
        print(f"\n  LAAP HEP 服务器 http://localhost:{port}")
        print(f"  页面类型: {len(PAGE_TYPES)}  设计风格: {len(STYLES)}")
        print(f"  API: POST /api/generate\n")
        HTTPServer(("0.0.0.0", port), HEPHandler).serve_forever()

    if args.install:
        install_service()
