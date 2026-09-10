"""
HEP 电商组件库 — 从 tailstore4 模板提取 + 注册
==============================================
1. 读取 tailstore4 的 7 个页面
2. 提取每页的核心 UI 模块为 HEPComponent
3. 注册到 HEP 注册表
4. 接入网站编译器
"""

import sys, os, re, json
from pathlib import Path

HERE = Path(__file__).parent
TAILSTORE = HERE / "tailstore4" / "tailstore4-main"
HARNESS_DIR = Path(r"D:\LAAP\harness\laap_coding\core")
sys.path.insert(0, str(HARNESS_DIR))
from hep_protocol import REGISTRY, HEPComponent, HEPComposer

# ── 读取页面的工具函数 ──

def read_page(name):
    path = TAILSTORE / name
    if not path.exists():
        print(f"  ⚠️  {name} not found")
        return ""
    return path.read_text(encoding="utf-8")

def extract_between(html, start_tag, end_tag=None, start_marker=None):
    """提取两个标签之间的 HTML"""
    if start_marker:
        s = html.find(start_marker)
    else:
        s = html.find(start_tag)
    if s == -1:
        return ""
    if end_tag:
        # 找匹配的 end_tag
        depth = 1
        pos = s + len(start_tag)
        while pos < len(html) and depth > 0:
            next_open = html.find(start_tag, pos)
            next_close = html.find(end_tag, pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + len(start_tag)
            else:
                depth -= 1
                pos = next_close + len(end_tag)
        return html[s:pos]
    return html[s:]


# ═══════════════════════════════════════════════
# 从各页面提取 HEP 组件
# ═══════════════════════════════════════════════

def register_components():
    """提取并注册所有电商组件"""
    count_before = len(REGISTRY._components)

    # ── 1. Header / Navigation ──
    index_html = read_page("index.html")
    # Extract header
    header_match = re.search(r'<header.*?</header>', index_html, re.DOTALL)
    header_html = header_match.group(0) if header_match else ""

    REGISTRY.register(HEPComponent(
        id="ecom.header", name="E-commerce Header",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "header", "nav"],
        inputs={"logo_url": {"type": "string", "default": "assets/images/template-logo.png"},
                "logo_text": {"type": "string", "default": "Store"},
                "categories": {"type": "array", "default": ["Home", "Shop", "About", "Contact"]}},
        outputs={"header.html": "html"}, dependencies=[],
        template=re.sub(r'src="assets/images/[^"]*"', 'src="{{logo_url}}"', header_html) if header_html else "<header>Header</header>",
    ))

    # ── 2. Hero Banner ──
    hero_match = re.search(r'<section[^>]*banner[^>]*>.*?</section>', index_html, re.DOTALL)
    if not hero_match:
        hero_match = re.search(r'<section[^>]*class="[^"]*relative[^"]*overflow-hidden[^"]*"[^>]*>.*?<div class="container[^>]*>.*?</div>\s*</section>', index_html, re.DOTALL)
    if not hero_match:
        # Fallback: find large section with slider
        hero_match = re.search(r'<section[^>]*class="[^"]*slider[^"]*"[^>]*>.*?</section>', index_html, re.DOTALL)
    hero_html = hero_match.group(0) if hero_match else "<section>Hero Banner</section>"

    REGISTRY.register(HEPComponent(
        id="ecom.hero_banner", name="Hero Banner",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "hero", "banner"],
        inputs={"title": {"type": "string", "default": "Summer Collection"},
                "subtitle": {"type": "string", "default": "Up to 50% off"},
                "cta_text": {"type": "string", "default": "Shop Now"},
                "cta_url": {"type": "string", "default": "/shop"},
                "bg_image": {"type": "string", "default": "assets/images/banner1.jpg"}},
        outputs={"hero.html": "html"}, dependencies=[],
        template=hero_html,
    ))

    # ── 3. Footer ──
    footer_match = re.search(r'<footer.*?</footer>', index_html, re.DOTALL)
    footer_html = footer_match.group(0) if footer_match else "<footer>Footer</footer>"

    REGISTRY.register(HEPComponent(
        id="ecom.footer", name="E-commerce Footer",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "footer"],
        inputs={"brand_name": {"type": "string", "default": "Store"},
                "email": {"type": "string", "default": "info@store.com"},
                "social_links": {"type": "array"}},
        outputs={"footer.html": "html"}, dependencies=[],
        template=footer_html,
    ))

    # ── 4. Product Grid (from shop.html) ──
    shop_html = read_page("shop.html")
    product_cards = re.findall(r'<div[^>]*class="[^"]*product[^"]*card[^"]*"[^>]*>.*?</div>\s*</div>\s*</div>', shop_html, re.DOTALL)

    REGISTRY.register(HEPComponent(
        id="ecom.product_card", name="Product Card",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "product", "card"],
        inputs={"image": {"type": "string", "default": "assets/images/products/1.jpg"},
                "name": {"type": "string", "default": "Product Name"},
                "price": {"type": "string", "default": "$49.99"},
                "rating": {"type": "number", "default": 4.5}},
        outputs={"card.html": "html"}, dependencies=[],
        template=product_cards[0] if product_cards else "<div>Product Card</div>",
    ))

    # ── 5. Product Grid Container ──
    grid_match = re.search(r'<div[^>]*class="[^"]*grid[^"]*products[^"]*"[^>]*>', shop_html, re.DOTALL)
    if not grid_match:
        grid_match = re.search(r'<div[^>]*class="[^"]*grid[^"]*gap[^"]*"[^>]*>', shop_html, re.DOTALL)

    REGISTRY.register(HEPComponent(
        id="ecom.product_grid", name="Product Grid",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "products", "grid"],
        inputs={"columns": {"type": "number", "default": 4},
                "products": {"type": "array"}},
        outputs={"grid.html": "html"}, dependencies=["ecom.product_card"],
        template='<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-{{columns}} gap-6">{{products}}</div>',
    ))

    # ── 6. Cart Table (from cart.html) ──
    cart_html = read_page("cart.html")
    cart_table = re.search(r'<table.*?</table>', cart_html, re.DOTALL)
    cart_summary = re.search(r'<div[^>]*order[^>]*summary[^>]*>.*?</div>\s*</div>\s*</div>', cart_html, re.DOTALL)

    REGISTRY.register(HEPComponent(
        id="ecom.cart_table", name="Cart Table",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "cart"],
        inputs={"items": {"type": "array"}},
        outputs={"cart.html": "html"}, dependencies=[],
        template=cart_table.group(0) if cart_table else "<table>Cart</table>",
    ))

    REGISTRY.register(HEPComponent(
        id="ecom.cart_summary", name="Cart Summary",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "cart", "summary"],
        inputs={"subtotal": {"type": "string", "default": "$0.00"},
                "shipping": {"type": "string", "default": "Free"},
                "total": {"type": "string", "default": "$0.00"}},
        outputs={"summary.html": "html"}, dependencies=[],
        template=cart_summary.group(0) if cart_summary else "<div>Summary</div>",
    ))

    # ── 7. Checkout Form (from checkout.html) ──
    checkout_html = read_page("checkout.html")
    form_match = re.search(r'<form.*?</form>', checkout_html, re.DOTALL)
    order_review = re.search(r'<div[^>]*order[^>]*review[^>]*>.*?</div>\s*</div>\s*</div>', checkout_html, re.DOTALL)

    REGISTRY.register(HEPComponent(
        id="ecom.checkout_form", name="Checkout Form",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "checkout"],
        inputs={},
        outputs={"checkout.html": "html"}, dependencies=[],
        template=form_match.group(0) if form_match else "<form>Checkout</form>",
    ))

    REGISTRY.register(HEPComponent(
        id="ecom.order_summary", name="Order Summary",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "order"],
        inputs={"items": {"type": "array"},
                "total": {"type": "string"}},
        outputs={"summary.html": "html"}, dependencies=[],
        template=order_review.group(0) if order_review else "<div>Order</div>",
    ))

    # ── 8. Register/Login (from register.html) ──
    reg_html = read_page("register.html")
    form_match2 = re.search(r'<form.*?</form>', reg_html, re.DOTALL)

    REGISTRY.register(HEPComponent(
        id="ecom.auth_form", name="Auth Form",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "auth", "login", "register"],
        inputs={"mode": {"type": "string", "default": "login"},
                "redirect_url": {"type": "string", "default": "/"}},
        outputs={"auth.html": "html"}, dependencies=[],
        template=form_match2.group(0) if form_match2 else "<form>Auth</form>",
    ))

    # ── 9. Single Product Detail ──
    detail_html = read_page("single-product-page.html")
    gallery = re.search(r'<div[^>]*gallery[^>]*>.*?</div>\s*</div>\s*</div>', detail_html, re.DOTALL)
    reviews = re.search(r'<div[^>]*review[^>]*>.*?</div>\s*</div>\s*</div>', detail_html, re.DOTALL)
    related = re.search(r'<section[^>]*related[^>]*>.*?</section>', detail_html, re.DOTALL)

    REGISTRY.register(HEPComponent(
        id="ecom.product_gallery", name="Product Gallery",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "product", "gallery"],
        inputs={"images": {"type": "array"}},
        outputs={"gallery.html": "html"}, dependencies=[],
        template=gallery.group(0) if gallery else "<div>Gallery</div>",
    ))

    REGISTRY.register(HEPComponent(
        id="ecom.product_info", name="Product Info",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "product", "info"],
        inputs={"name": {"type": "string"}, "price": {"type": "string"},
                "description": {"type": "string"}, "sizes": {"type": "array"}},
        outputs={"info.html": "html"}, dependencies=[],
        template="""<div class="product-info">
  <h1 class="text-3xl font-bold">{{name}}</h1>
  <p class="text-2xl text-red-600 font-semibold mt-2">{{price}}</p>
  <p class="text-gray-600 mt-4">{{description}}</p>
  <button class="bg-black text-white px-8 py-3 mt-6 rounded hover:bg-gray-800">Add to Cart</button>
</div>""",
    ))

    REGISTRY.register(HEPComponent(
        id="ecom.reviews", name="Reviews Section",
        version="1.0.0", domain="ui", subdomain="ecommerce",
        tags=["ecommerce", "reviews"],
        inputs={"reviews": {"type": "array"}},
        outputs={"reviews.html": "html"}, dependencies=[],
        template=reviews.group(0) if reviews else "<div>Reviews</div>",
    ))

    count_after = len(REGISTRY._components)
    added = count_after - count_before
    print(f"注册电商组件: +{added} (总计 {count_after})")


# ═══════════════════════════════════════════════
# 电商网站生成管线
# ═══════════════════════════════════════════════

def generate_ecommerce_site(content_md: str, style_id: str = "saas",
                             site_title: str = "My Store") -> str:
    """生成完整电商网站"""
    composer = HEPComposer(REGISTRY)

    # 解析内容
    lines = content_md.strip().split("\n")
    title = site_title
    store_name = site_title
    sections = []
    cur = {"heading": "", "body": ""}
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith("# "): title = line[2:].strip(); store_name = title
        elif line.startswith("## "):
            if cur["heading"]: sections.append(cur)
            cur = {"heading": line[3:].strip(), "body": ""}
        else:
            cur["body"] += ("\n" if cur["body"] else "") + line
    if cur["heading"] or cur["body"]: sections.append(cur)

    # 获取风格
    style_data = {s["id"]: s for s in STYLES}
    s = style_data.get(style_id, style_data.get("saas", {"c":["#fff","#f5f5f5","#e2e8f0","#000","#666","#3b82f6"]}))
    c = s["c"]

    style_result = composer.compose({"components": [{"id": f"style.{style_id}", "params": {}}]})
    theme_css = style_result.get(f"style.{style_id}", "")

    # 构建页面
    header_result = composer.compose({"components": [{"id": "ecom.header", "params": {
        "logo_url": "", "logo_text": store_name}}]})
    footer_result = composer.compose({"components": [{"id": "ecom.footer", "params": {}}]})
    header_html = header_result.get("ecom.header", "<header>Store</header>")
    footer_html = footer_result.get("ecom.footer", "<footer>Footer</footer>")

    # 商品展示
    products_html = ""
    product_card_result = composer.compose({"components": [{"id": "ecom.product_card", "params": {
        "image": "", "name": "Product 1", "price": "$29.99", "rating": 4.5}}]})
    card = product_card_result.get("ecom.product_card", "<div>Product</div>")
    for i in range(4):
        products_html += card.replace("Product 1", f"Product {i+1}").replace("$29.99", f"${19.99 + i*10:.2f}")

    content_sections = ""
    for sec in sections:
        if sec["heading"]:
            paragraphs = "\n".join(f"<p>{p}</p>" for p in sec["body"].split("\n") if p.strip())
            content_sections += f"""
<section style="padding:60px 24px;background:var(--bg)">
  <div style="max-width:1200px;margin:0 auto">
    <h2 style="font-size:1.8rem;margin-bottom:24px;text-align:center">{sec['heading']}</h2>
    <div style="max-width:800px;margin:0 auto;line-height:1.8;color:var(--text2)">{paragraphs}</div>
  </div>
</section>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>
{theme_css}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
.hero{{padding:80px 24px;text-align:center;background:linear-gradient(135deg,var(--bg),var(--bg2),var(--bg3))}}
.hero h1{{font-size:clamp(2rem,4vw,3rem);margin-bottom:12px}}
.hero p{{color:var(--text2);max-width:600px;margin:0 auto 24px}}
.prod-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;max-width:1200px;margin:0 auto;padding:40px 24px}}
.prod-card{{background:var(--bg3);border-radius:16px;overflow:hidden;transition:all .3s}}
.prod-card:hover{{transform:translateY(-4px);box-shadow:0 12px 32px rgba(0,0,0,.3)}}
.prod-card-img{{height:200px;background:var(--bg2);display:flex;align-items:center;justify-content:center;font-size:48px;color:var(--text3)}}
.prod-card-body{{padding:16px}}
.prod-card-body h3{{font-size:16px;margin-bottom:4px}}
.prod-card-body .price{{font-size:18px;font-weight:700;color:var(--accent)}}
.prod-card-body .rating{{font-size:12px;color:var(--text2)}}
.footer{{text-align:center;padding:40px 24px;border-top:1px solid rgba(255,255,255,.05);color:var(--text2);font-size:13px}}
</style>
</head>
<body>
{header_html}
<section class="hero">
  <div class="hero-badge" style="display:inline-block;padding:4px 14px;border-radius:100px;background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.3);font-size:11px;color:var(--accent);margin-bottom:16px">Zero-Token E-commerce</div>
  <h1>{title}</h1>
  <p>Powered by LAAP HEP · Assembled in milliseconds</p>
  <a href="#" style="display:inline-block;padding:12px 28px;background:var(--accent);color:var(--bg);border-radius:8px;text-decoration:none;font-weight:600">Shop Now</a>
</section>
{content_sections}
<div class="prod-grid">{products_html}</div>
{footer_html}
<p style="text-align:center;padding:16px;font-size:11px;color:var(--text3)">LAAP HEP · Zero-Token Generation</p>
</body>
</html>"""
    return html


# ═══════════════════════════════════════════════
# 保存注册表
# ═══════════════════════════════════════════════

STYLES = [
    {"id":"saas","name":"SaaS","mode":"light","font":"sans",
     "c":["#ffffff","#f8fafc","#e2e8f0","#1e3a5f","#3b82f6","#64748b"]},
    {"id":"modern_dark","name":"Modern Dark","mode":"dark","font":"sans",
     "c":["#0a0a0a","#1a1a2e","#16213e","#e94560","#0f3460","#ffffff"]},
    {"id":"luxury","name":"Luxury","mode":"light","font":"serif",
     "c":["#1a1a1a","#2d2d2d","#c9a84c","#f5f0e8","#8b7355","#ffffff"]},
    {"id":"cyberpunk","name":"Cyberpunk","mode":"dark","font":"sans",
     "c":["#0a0a0a","#1a0a0a","#00fff5","#ff00ff","#ffff00","#ff0066"]},
]

def save_registry():
    reg_dir = HERE / "state"
    reg_dir.mkdir(parents=True, exist_ok=True)
    data = {}
    for cid, comp in REGISTRY._components.items():
        data[cid] = {
            "id": comp.id, "name": comp.name, "version": comp.version,
            "domain": comp.domain, "tags": comp.tags,
        }
    (reg_dir / "hep_components.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"注册表已保存: {len(data)} 组件")


if __name__ == "__main__":
    # 确保风格组件已注册
    for s in STYLES:
        cid = f"style.{s['id']}"
        if not REGISTRY.get(cid):
            c = s["c"]
            REGISTRY.register(HEPComponent(
                id=cid, name=s["name"], version="1.0.0",
                domain="ui", subdomain="theme",
                tags=["theme", s["mode"], s["font"]],
                inputs={"theme": {"type": "string"}},
                outputs={"theme.css": "css"}, dependencies=[],
                template=f":root{{--bg:{c[0]};--bg2:{c[1]};--bg3:{c[2]};--text:{c[3]};--accent:{c[4]};--text2:{c[5]}}}",
            ))

    register_components()
    save_registry()
    print(f"\n总计: {len(REGISTRY._components)} 个 HEP 组件")

    # 测试生成
    test_html = generate_ecommerce_site(
        content_md="# My Store\n\n## About Us\nWe sell amazing products.\n\n## Featured\nCheck out our latest collection.",
        style_id="modern_dark",
        site_title="My E-commerce Store"
    )
    out_path = HERE / "hep_site" / "ecommerce_demo.html"
    out_path.write_text(test_html, encoding="utf-8")
    print(f"电商演示页: {out_path} ({len(test_html)}B)")
