"""HEP 网站编译器 — 生产级零 Token 系统
=========================================
网站类型分类器 + 组件树映射 + 意图编译管线

架构:
  User Intent → WebsiteClassifier → ComponentTree → HEPComposer → HTML
                  ↓
            WebsiteType enum (40+ 种)
                  ↓
            ComponentMap (每种类型分解为原子组件)
"""

import json, re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ═══════════════════════════════════════════════
# 网站类型枚举
# ═══════════════════════════════════════════════

class WebsiteCategory(Enum):
    SITES = "sites"
    APPS = "apps"
    SECTIONS = "sections"
    BACKGROUNDS = "backgrounds"

class WebsiteType(Enum):
    # ── Sites ──
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    LANDING_PAGE = "landing_page"
    PORTFOLIO = "portfolio"
    AGENCY = "agency"
    BLOG = "blog"
    HEALTHCARE = "healthcare"
    FINTECH = "fintech"
    TECHNOLOGY = "technology"
    REAL_ESTATE = "real_estate"
    EDUCATION = "education"
    TRAVEL = "travel"
    RESTAURANT = "restaurant"
    FITNESS = "fitness"
    PODCAST = "podcast"
    PERSONAL = "personal"
    DOCUMENTATION = "documentation"
    NEWSLETTER = "newsletter"

    # ── Apps ──
    APP_DASHBOARD = "app_dashboard"
    APP_SOCIAL = "app_social"
    APP_MUSIC = "app_music"
    APP_HEALTH = "app_health"
    APP_FINTECH = "app_fintech"
    APP_LEARNING = "app_learning"

    @classmethod
    def from_keywords(cls, text: str) -> "WebsiteType":
        """从用户输入的关键词匹配网站类型"""
        text = text.lower()
        patterns = {
            cls.ECOMMERCE: ["shop", "store", "ecommerce", "e-commerce", "商品", "电商", "商城"],
            cls.SAAS: ["saas", "software", "platform", "cloud", "服务"],
            cls.LANDING_PAGE: ["landing", "hero", "promotion", "landing page", "落地页"],
            cls.PORTFOLIO: ["portfolio", "作品", "个人"],
            cls.AGENCY: ["agency", "studio", "创意", "agency"],
            cls.BLOG: ["blog", "文章", "blog"],
            cls.HEALTHCARE: ["health", "medical", "clinic", "dental", "医疗", "健康"],
            cls.FINTECH: ["fintech", "finance", "bank", "金融", "支付"],
            cls.TECHNOLOGY: ["tech", "technology", "startup", "科技"],
            cls.REAL_ESTATE: ["real estate", "property", "realestate", "房产", "地产"],
            cls.EDUCATION: ["education", "course", "learning", "教育", "课程"],
            cls.TRAVEL: ["travel", "hotel", "tourism", "旅游"],
            cls.RESTAURANT: ["restaurant", "cafe", "food", "coffee", "餐厅", "咖啡"],
            cls.FITNESS: ["fitness", "gym", "workout", "健身"],
            cls.PODCAST: ["podcast", "audio", "播客"],
            cls.PERSONAL: ["personal", "resume", "cv", "简历"],
            cls.DOCUMENTATION: ["docs", "documentation", "api", "文档"],
            cls.NEWSLETTER: ["newsletter", "email", "订阅"],
            cls.APP_DASHBOARD: ["dashboard", "analytics", "管理"],
            cls.APP_SOCIAL: ["social", "community", "社交"],
            cls.APP_MUSIC: ["music", "audio", "播放器"],
            cls.APP_HEALTH: ["health app", "fitness app", "健康应用"],
            cls.APP_FINTECH: ["finance app", "payment", "金融应用"],
            cls.APP_LEARNING: ["learning app", "course app", "学习应用"],
        }
        scores = {}
        for wtype, keywords in patterns.items():
            score = sum(2 if kw in text else 0 for kw in keywords)
            if score > 0:
                scores[wtype] = score
        if scores:
            return max(scores, key=scores.get)
        return cls.LANDING_PAGE


# ═══════════════════════════════════════════════
# 组件树定义
# ═══════════════════════════════════════════════

@dataclass
class ComponentNode:
    """一个 UI 组件节点"""
    id: str
    name: str
    description: str = ""
    children: List["ComponentNode"] = field(default_factory=list)
    hep_component_id: str = ""          # 映射到 HEP 注册表的组件 ID
    required: bool = True               # 是否必须
    multiple: bool = False              # 是否可以多个实例
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "children": [c.to_dict() for c in self.children],
            "required": self.required,
            "multiple": self.multiple,
        }


# ═══════════════════════════════════════════════
# 网站类型 → 组件树映射
# ═══════════════════════════════════════════════

WEBSITE_COMPONENT_MAPS = {

    WebsiteType.ECOMMERCE: ComponentNode(
        id="ecommerce", name="E-commerce Platform",
        description="Complete online store with product catalog, cart, and checkout",
        children=[
            ComponentNode(id="ecom_global", name="Global Elements", children=[
                ComponentNode(id="header", name="Header", hep_component_id="ecom.header",
                              children=[
                                  ComponentNode(id="logo", name="Logo", required=True),
                                  ComponentNode(id="search_bar", name="Search Bar"),
                                  ComponentNode(id="cart_icon", name="Cart Icon", required=True),
                                  ComponentNode(id="nav_menu", name="Navigation Menu", required=True),
                              ]),
                ComponentNode(id="footer", name="Footer", required=True),
                ComponentNode(id="announcement", name="Announcement Bar", required=False),
            ]),
            ComponentNode(id="ecom_home", name="Homepage", children=[
                ComponentNode(id="hero_banner", name="Hero Banner", required=True),
                ComponentNode(id="category_grid", name="Category Grid", required=True),
                ComponentNode(id="featured_products", name="Featured Products", required=True),
                ComponentNode(id="trust_signals", name="Trust Signals"),
                ComponentNode(id="newsletter", name="Newsletter Signup"),
            ]),
            ComponentNode(id="ecom_listing", name="Product Listing", children=[
                ComponentNode(id="filters", name="Filter Sidebar", required=True),
                ComponentNode(id="product_grid", name="Product Grid", required=True),
                ComponentNode(id="pagination", name="Pagination", required=True),
                ComponentNode(id="sort_bar", name="Sort Bar", required=True),
            ]),
            ComponentNode(id="ecom_detail", name="Product Detail", children=[
                ComponentNode(id="image_gallery", name="Image Gallery", required=True),
                ComponentNode(id="product_info", name="Product Info", required=True),
                ComponentNode(id="add_to_cart", name="Add to Cart", required=True),
                ComponentNode(id="reviews", name="Reviews Section"),
                ComponentNode(id="related_products", name="Related Products"),
            ]),
            ComponentNode(id="ecom_cart", name="Shopping Cart", children=[
                ComponentNode(id="cart_items", name="Cart Items", required=True),
                ComponentNode(id="cart_summary", name="Price Summary", required=True),
                ComponentNode(id="checkout_btn", name="Checkout Button", required=True),
            ]),
            ComponentNode(id="ecom_checkout", name="Checkout", children=[
                ComponentNode(id="shipping_form", name="Shipping Form", required=True),
                ComponentNode(id="payment_form", name="Payment Form", required=True),
                ComponentNode(id="order_summary", name="Order Summary", required=True),
            ]),
            ComponentNode(id="ecom_account", name="User Account", children=[
                ComponentNode(id="login", name="Login"),
                ComponentNode(id="register", name="Register"),
                ComponentNode(id="order_history", name="Order History"),
            ]),
        ]
    ),

    WebsiteType.SAAS: ComponentNode(
        id="saas", name="SaaS Website",
        description="Software-as-a-Service marketing site",
        children=[
            ComponentNode(id="saas_global", name="Global", children=[
                ComponentNode(id="header", name="Header", required=True),
                ComponentNode(id="footer", name="Footer", required=True),
            ]),
            ComponentNode(id="saas_home", name="Homepage", children=[
                ComponentNode(id="hero", name="Hero Section", required=True),
                ComponentNode(id="features", name="Feature Grid", required=True),
                ComponentNode(id="pricing", name="Pricing Table", required=True),
                ComponentNode(id="testimonials", name="Testimonials"),
                ComponentNode(id="cta", name="CTA Section", required=True),
                ComponentNode(id="faq", name="FAQ"),
                ComponentNode(id="integrations", name="Integrations"),
            ]),
            ComponentNode(id="saas_demo", name="Demo Page"),
            ComponentNode(id="saas_docs", name="Documentation"),
            ComponentNode(id="saas_blog", name="Blog"),
            ComponentNode(id="saas_contact", name="Contact"),
        ]
    ),

    WebsiteType.BLOG: ComponentNode(
        id="blog", name="Blog/News",
        description="Content-driven blog with articles, categories, and reading experience",
        children=[
            ComponentNode(id="blog_global", name="Global", children=[
                ComponentNode(id="header", name="Header", required=True),
                ComponentNode(id="sidebar", name="Sidebar"),
                ComponentNode(id="footer", name="Footer", required=True),
            ]),
            ComponentNode(id="blog_home", name="Homepage", children=[
                ComponentNode(id="featured_post", name="Featured Post", required=True),
                ComponentNode(id="post_grid", name="Post Grid", required=True),
                ComponentNode(id="categories", name="Categories"),
                ComponentNode(id="tags", name="Tags Cloud"),
            ]),
            ComponentNode(id="blog_post", name="Article Page", children=[
                ComponentNode(id="article", name="Article Content", required=True),
                ComponentNode(id="author", name="Author Bio"),
                ComponentNode(id="comments", name="Comments"),
                ComponentNode(id="related_posts", name="Related Posts"),
            ]),
            ComponentNode(id="blog_archive", name="Archive"),
            ComponentNode(id="blog_about", name="About"),
            ComponentNode(id="blog_contact", name="Contact"),
        ]
    ),

    WebsiteType.PORTFOLIO: ComponentNode(
        id="portfolio", name="Portfolio",
        description="Personal or agency portfolio showcasing work and skills",
        children=[
            ComponentNode(id="pf_hero", name="Hero", required=True),
            ComponentNode(id="pf_about", name="About Me", required=True),
            ComponentNode(id="pf_works", name="Work/Projects Grid", required=True),
            ComponentNode(id="pf_skills", name="Skills"),
            ComponentNode(id="pf_experience", name="Experience Timeline"),
            ComponentNode(id="pf_testimonials", name="Testimonials"),
            ComponentNode(id="pf_contact", name="Contact", required=True),
            ComponentNode(id="pf_footer", name="Footer", required=True),
        ]
    ),

    WebsiteType.LANDING_PAGE: ComponentNode(
        id="landing", name="Landing Page",
        description="Single-page landing with hero, features, CTA",
        children=[
            ComponentNode(id="lp_hero", name="Hero Section", required=True),
            ComponentNode(id="lp_features", name="Features", required=True),
            ComponentNode(id="lp_stats", name="Stats"),
            ComponentNode(id="lp_testimonials", name="Testimonials"),
            ComponentNode(id="lp_cta", name="CTA Section", required=True),
            ComponentNode(id="lp_faq", name="FAQ"),
            ComponentNode(id="lp_footer", name="Footer", required=True),
        ]
    ),

    WebsiteType.RESTAURANT: ComponentNode(
        id="restaurant", name="Restaurant",
        description="Restaurant/cafe website with menu, reservations, and location",
        children=[
            ComponentNode(id="rest_hero", name="Hero Banner", required=True),
            ComponentNode(id="rest_about", name="About Us"),
            ComponentNode(id="rest_menu", name="Menu/Products", required=True),
            ComponentNode(id="rest_gallery", name="Gallery"),
            ComponentNode(id="rest_reservation", name="Reservation/Booking", required=True),
            ComponentNode(id="rest_reviews", name="Reviews"),
            ComponentNode(id="rest_location", name="Location & Hours", required=True),
            ComponentNode(id="rest_contact", name="Contact"),
            ComponentNode(id="rest_footer", name="Footer", required=True),
        ]
    ),
}

# 更多类型可以按同样方式扩展


# ═══════════════════════════════════════════════
# 网站分类器
# ═══════════════════════════════════════════════

class WebsiteClassifier:
    """
    网站分类器 — 从用户意图解析出网站类型 + 组件树 + 参数

    使用::
        classifier = WebsiteClassifier()
        result = classifier.analyze("I need an online store for handmade jewelry")

        result.type  → WebsiteType.ECOMMERCE
        result.tree  → ComponentTree for e-commerce
        result.params → {"products": "handmade jewelry", "categories": 5}
    """

    def analyze(self, user_intent: str) -> dict:
        """分析用户意图，返回网站蓝图"""
        text = user_intent.lower()

        # 1. 识别网站类型
        wtype = WebsiteType.from_keywords(text)

        # 2. 获取组件树
        tree = WEBSITE_COMPONENT_MAPS.get(wtype,
                  WEBSITE_COMPONENT_MAPS[WebsiteType.LANDING_PAGE])

        # 3. 提取参数
        params = self._extract_params(text)

        # 4. 检测样式偏好
        style_hints = self._detect_style(text)

        return {
            "type": wtype.value,
            "type_name": wtype.name,
            "tree": tree.to_dict(),
            "params": params,
            "style_hints": style_hints,
            "display_name": self._get_display_name(wtype),
        }

    def _extract_params(self, text: str) -> Dict:
        """从文本提取结构化参数"""
        params = {}
        # 产品/服务
        product_match = re.search(r'(?:sell|selling|for|about)\s+([a-zA-Z\s]{3,30})', text)
        if product_match:
            params["topic"] = product_match.group(1).strip()
        # 数字
        nums = re.findall(r'(\d+)\s*(?:page|section|product|category|item)', text)
        if nums:
            params["count"] = int(nums[0])
        # 颜色偏好
        colors = re.findall(r'(dark|light|minimal|bold|colorful|elegant)', text)
        if colors:
            params["mood"] = colors[0]
        return params

    def _detect_style(self, text: str) -> Dict:
        """检测风格偏好"""
        hints = {}
        if any(w in text for w in ["dark", "night", "cyber", "neon"]):
            hints["mode"] = "dark"
        if any(w in text for w in ["light", "clean", "minimal", "white"]):
            hints["mode"] = "light"
        if any(w in text for w in ["elegant", "luxury", "premium", "gold"]):
            hints["style"] = "luxury"
        if any(w in text for w in ["modern", "sleek", "tech"]):
            hints["style"] = "modern_dark"
        if any(w in text for w in ["fun", "playful", "colorful", "creative"]):
            hints["style"] = "playful"
        return hints

    def _get_display_name(self, wtype: WebsiteType) -> str:
        names = {
            WebsiteType.ECOMMERCE: "E-commerce Platform",
            WebsiteType.SAAS: "SaaS Website",
            WebsiteType.LANDING_PAGE: "Landing Page",
            WebsiteType.PORTFOLIO: "Portfolio",
            WebsiteType.AGENCY: "Agency Website",
            WebsiteType.BLOG: "Blog",
            WebsiteType.HEALTHCARE: "Healthcare Website",
            WebsiteType.FINTECH: "Fintech Website",
            WebsiteType.RESTAURANT: "Restaurant Website",
            WebsiteType.FITNESS: "Fitness Website",
            WebsiteType.PODCAST: "Podcast Website",
            WebsiteType.TRAVEL: "Travel Website",
            WebsiteType.REAL_ESTATE: "Real Estate Website",
            WebsiteType.EDUCATION: "Education Website",
        }
        return names.get(wtype, wtype.name.replace("_", " ").title())


# ═══════════════════════════════════════════════
# 组件生成器
# ═══════════════════════════════════════════════

class ComponentGenerator:
    """根据组件树生成 HEP 可装配的 Spec"""

    def __init__(self):
        self.classifier = WebsiteClassifier()

    def generate_spec(self, user_intent: str, style_id: str = "saas",
                      content: str = "") -> Dict:
        """从用户意图生成完整的 HEP compose spec"""
        blueprint = self.classifier.analyze(user_intent)

        # 构建 assemble plan
        components = []
        tree = blueprint["tree"]

        def walk(node, prefix=""):
            """递归遍历组件树生成装配计划"""
            if node.get("children"):
                for child in node["children"]:
                    walk(child, f"{prefix}{node['id']}_")
            else:
                comp_id = node.get("hep_component_id") or f"sec_{node['id']}"
                components.append({
                    "id": comp_id,
                    "params": node.get("params", {}).copy(),
                    "required": node.get("required", True),
                })

        walk(tree)

        return {
            "website_type": blueprint["type"],
            "display_name": blueprint["display_name"],
            "style": style_id,
            "params": blueprint["params"],
            "style_hints": blueprint["style_hints"],
            "components": components,
        }


# ═══════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 50)
    print("  HEP 网站编译器 — 演示")
    print("=" * 50)

    classifier = WebsiteClassifier()

    test_cases = [
        "I need an online store for handmade jewelry with 5 categories",
        "Build me a dark theme SaaS landing page for my AI startup",
        "Create a personal portfolio to showcase my design work",
        "I want a restaurant website with online reservation and menu",
        "Build a blog with articles about technology and programming",
        "Create a fintech dashboard for tracking cryptocurrency",
    ]

    for case in test_cases:
        result = classifier.analyze(case)
        print(f"\n  Input: {case}")
        print(f"  → Type: {result['type_name']} ({result['display_name']})")
        if result["params"]:
            print(f"  → Params: {result['params']}")
        if result["style_hints"]:
            print(f"  → Style: {result['style_hints']}")
        print(f"  → Components: {len(result['tree'].get('children', []))} groups")

    print("\n\n  Generator 演示:")
    gen = ComponentGenerator()
    spec = gen.generate_spec("Create a modern e-commerce store for handmade crafts", "luxury")
    print(f"  Website: {spec['display_name']}")
    print(f"  Style: {spec['style']}")
    print(f"  Components in plan: {len(spec['components'])}")
    print(f"  Params: {spec['params']}")
