"""
ContentParser - Markdown/JSON → UnifiedContentSpec 解析器

核心功能：
1. 解析 Markdown 文档，识别页面结构、Section 类型、内容元素
2. 支持 JSON Spec 直接转换
3. 自动识别内容类型（首页/产品/技术/文档）
4. 零 LLM 调用，纯规则引擎

使用示例：
    parser = ContentParser()
    spec = parser.parse_markdown(markdown_content)
    spec = parser.parse_json(json_content)
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class PageType(Enum):
    """页面类型"""
    HOMEPAGE = "homepage"
    PRODUCT = "product"
    FEATURE = "feature"
    DOC = "doc"
    ABOUT = "about"
    PRICING = "pricing"
    CONTACT = "contact"


class SectionType(Enum):
    """Section 类型"""
    HERO = "hero"
    GRID = "grid"
    STATS = "stats"
    CTA = "cta"
    TIMELINE = "timeline"
    TABS = "tabs"
    FAQ = "faq"
    TESTIMONIALS = "testimonials"
    PRICING = "pricing"
    CONTENT = "content"
    CODE = "code"
    FORM = "form"
    FOOTER = "footer"


@dataclass
class CTA:
    """CTA 按钮"""
    label: str
    url: str
    style: str = "primary"  # primary / secondary / outline


@dataclass
class Card:
    """卡片组件"""
    title: str
    desc: str
    icon: Optional[str] = None
    cta: Optional[CTA] = None


@dataclass
class Stat:
    """数据指标"""
    number: str
    label: str


@dataclass
class TimelineItem:
    """时间线项"""
    date: str
    title: str
    desc: str


@dataclass
class FAQItem:
    """FAQ 项"""
    question: str
    answer: str


@dataclass
class Section:
    """页面 Section"""
    type: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    label: Optional[str] = None
    cta: Optional[CTA] = None
    three_d: bool = False
    cards: List[Card] = field(default_factory=list)
    stats: List[Stat] = field(default_factory=list)
    timeline: List[TimelineItem] = field(default_factory=list)
    faq: List[FAQItem] = field(default_factory=list)
    content: Optional[str] = None
    cols: int = 3
    custom_html: Optional[str] = None


@dataclass
class Page:
    """页面"""
    filename: str
    title: str
    type: str = "landing"
    sections: List[Section] = field(default_factory=list)
    nav: Optional[Dict] = None
    footer: Optional[Dict] = None


@dataclass
class UnifiedContentSpec:
    """统一内容规格"""
    brand: str
    pages: List[Page] = field(default_factory=list)
    style: str = "apple_dark"
    nav: Optional[Dict] = None
    footer: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "brand": self.brand,
            "style": self.style,
            "nav": self.nav,
            "footer": self.footer,
            "pages": [
                {
                    "filename": p.filename,
                    "title": p.title,
                    "type": p.type,
                    "nav": p.nav,
                    "footer": p.footer,
                    "sections": [
                        {
                            "type": s.type,
                            "title": s.title,
                            "subtitle": s.subtitle,
                            "label": s.label,
                            "cta": {"label": s.cta.label, "url": s.cta.url} if s.cta else None,
                            "three_d": s.three_d,
                            "cols": s.cols,
                            "cards": [{"title": c.title, "desc": c.desc, "icon": c.icon} for c in s.cards],
                            "stats": [{"number": st.number, "label": st.label} for st in s.stats],
                            "timeline": [{"date": t.date, "title": t.title, "desc": t.desc} for t in s.timeline],
                            "faq": [{"question": f.question, "answer": f.answer} for f in s.faq],
                            "content": s.content,
                            "custom_html": s.custom_html,
                        }
                        for s in p.sections
                    ],
                }
                for p in self.pages
            ],
        }


class ContentParser:
    """
    内容解析器 - Markdown/JSON → UnifiedContentSpec

    零 LLM 调用，纯规则引擎
    """

    # 页面类型关键词
    PAGE_TYPE_KEYWORDS = {
        PageType.HOMEPAGE: ["首页", "主页", "home", "landing", "欢迎"],
        PageType.PRODUCT: ["产品", "功能", "product", "feature", "平台"],
        PageType.FEATURE: ["技术", "架构", "原理", "tech", "architecture", "引擎"],
        PageType.DOC: ["文档", "api", "教程", "doc", "tutorial", "reference"],
        PageType.ABOUT: ["关于", "我们", "团队", "about", "team", "公司"],
        PageType.PRICING: ["定价", "价格", "套餐", "pricing", "price"],
        PageType.CONTACT: ["联系", "contact", "客服", "支持"],
    }

    # Section 类型关键词
    SECTION_TYPE_KEYWORDS = {
        SectionType.HERO: ["hero", "首屏", "头部", "主视觉"],
        SectionType.GRID: ["功能", "特性", "能力", "feature", "grid", "卡片"],
        SectionType.STATS: ["数据", "指标", "统计", "stat", "number", "数字"],
        SectionType.CTA: ["cta", "行动", "按钮", "立即", "开始"],
        SectionType.TIMELINE: ["路线图", "时间线", "里程碑", "timeline", "roadmap"],
        SectionType.FAQ: ["faq", "问答", "常见问题"],
        SectionType.TESTIMONIALS: ["客户", "案例", "评价", "testimonial", "case"],
        SectionType.PRICING: ["定价", "套餐", "pricing", "价格"],
    }

    def __init__(self):
        self.current_page: Optional[Page] = None
        self.current_section: Optional[Section] = None

    def parse_markdown(self, content: str, brand: str = "品牌", style: str = "apple_dark") -> UnifiedContentSpec:
        """
        解析 Markdown 文档

        识别规则：
        - # 标题 → 品牌名称或页面标题
        - ## 二级标题 → 新页面
        - ### 三级标题 → 新 Section
        - - 列表项 → 卡片/导航项/数据项
        - **粗体** → 标题或强调
        - [链接](url) → CTA 或导航链接
        - 图片 ![alt](url) → 图片元素
        - 代码块 → 代码示例 Section
        """
        lines = content.strip().split('\n')
        pages: List[Page] = []
        current_page: Optional[Page] = None
        current_section: Optional[Section] = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 跳过空行
            if not line:
                i += 1
                continue

            # 一级标题 → 品牌名称（首页标题）
            if line.startswith('# ') and not line.startswith('## '):
                title = line[2:].strip()
                if not pages:  # 第一个一级标题作为首页
                    current_page = Page(
                        filename="index.html",
                        title=title,
                        type="landing",
                        sections=[]
                    )
                    pages.append(current_page)
                # 后续一级标题作为新页面
                else:
                    # 保存当前页面
                    if current_section and current_page:
                        current_page.sections.append(current_section)
                        current_section = None
                    # 创建新页面
                    filename = self._title_to_filename(title)
                    current_page = Page(
                        filename=filename,
                        title=title,
                        type=self._detect_page_type(title).value,
                        sections=[]
                    )
                    pages.append(current_page)

            # 二级标题 → 新页面
            elif line.startswith('## '):
                # 保存当前 Section
                if current_section and current_page:
                    current_page.sections.append(current_section)
                current_section = None

                title = line[3:].strip()
                # 如果没有页面，创建首页
                if not pages:
                    pages.append(Page(
                        filename="index.html",
                        title=brand,
                        type="landing",
                        sections=[]
                    ))
                    current_page = pages[0]

                # 创建新页面
                filename = self._title_to_filename(title)
                current_page = Page(
                    filename=filename,
                    title=title,
                    type=self._detect_page_type(title).value,
                    sections=[]
                )
                pages.append(current_page)

            # 三级标题 → 新 Section
            elif line.startswith('### '):
                # 保存当前 Section
                if current_section and current_page:
                    current_page.sections.append(current_section)

                title = line[4:].strip()
                section_type = self._detect_section_type(title)
                current_section = Section(
                    type=section_type.value,
                    title=title
                )

            # 四级标题 → Section 属性或卡片标题
            elif line.startswith('#### '):
                text = line[5:].strip()
                if current_section:
                    # 检查是否为属性格式 "键: 值"
                    if ':' in text:
                        key, value = text.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        self._set_section_attr(current_section, key, value)
                    else:
                        # 作为卡片标题
                        card = Card(title=text, desc="")
                        current_section.cards.append(card)

            # 列表项
            elif line.startswith('- ') or line.startswith('* '):
                text = line[2:].strip()
                self._parse_list_item(text, current_section)

            # 数字列表
            elif re.match(r'^\d+\.\s', line):
                text = re.sub(r'^\d+\.\s*', '', line).strip()
                self._parse_list_item(text, current_section)

            # 属性行（键: 值）
            elif ':' in line and not line.startswith('http'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    if current_section:
                        self._set_section_attr(current_section, key, value)
                    elif current_page:
                        self._set_page_attr(current_page, key, value)

            # 普通文本 → Section 内容或副标题
            else:
                if current_section:
                    if not current_section.subtitle:
                        current_section.subtitle = line
                    else:
                        if current_section.content:
                            current_section.content += '\n' + line
                        else:
                            current_section.content = line

            i += 1

        # 保存最后的 Section 和页面
        if current_section and current_page:
            current_page.sections.append(current_section)

        # 如果没有页面，创建默认首页
        if not pages:
            pages.append(Page(
                filename="index.html",
                title=brand,
                type="landing",
                sections=[Section(type="hero", title=brand)]
            ))

        return UnifiedContentSpec(
            brand=brand,
            pages=pages,
            style=style
        )

    def parse_json(self, content: str | dict) -> UnifiedContentSpec:
        """解析 JSON Spec"""
        if isinstance(content, str):
            data = json.loads(content)
        else:
            data = content

        pages = []
        for page_data in data.get('pages', []):
            sections = []
            for sec_data in page_data.get('sections', []):
                section = Section(
                    type=sec_data.get('type', 'content'),
                    title=sec_data.get('title'),
                    subtitle=sec_data.get('subtitle'),
                    label=sec_data.get('label'),
                    three_d=sec_data.get('three_d', False),
                    cols=sec_data.get('cols', 3),
                    content=sec_data.get('content'),
                    custom_html=sec_data.get('custom_html'),
                )

                # CTA
                if sec_data.get('cta'):
                    cta_data = sec_data['cta']
                    section.cta = CTA(
                        label=cta_data.get('label', ''),
                        url=cta_data.get('url', '#')
                    )

                # Cards
                for card_data in sec_data.get('cards', []):
                    card = Card(
                        title=card_data.get('title', ''),
                        desc=card_data.get('desc', ''),
                        icon=card_data.get('icon'),
                    )
                    if card_data.get('cta'):
                        card.cta = CTA(
                            label=card_data['cta'].get('label', ''),
                            url=card_data['cta'].get('url', '#')
                        )
                    section.cards.append(card)

                # Stats
                for stat_data in sec_data.get('stats', []):
                    section.stats.append(Stat(
                        number=stat_data.get('number', ''),
                        label=stat_data.get('label', '')
                    ))

                # Timeline
                for tl_data in sec_data.get('timeline', []):
                    section.timeline.append(TimelineItem(
                        date=tl_data.get('date', ''),
                        title=tl_data.get('title', ''),
                        desc=tl_data.get('desc', '')
                    ))

                # FAQ
                for faq_data in sec_data.get('faq', []):
                    section.faq.append(FAQItem(
                        question=faq_data.get('question', ''),
                        answer=faq_data.get('answer', '')
                    ))

                sections.append(section)

            page = Page(
                filename=page_data.get('filename', 'index.html'),
                title=page_data.get('title', ''),
                type=page_data.get('type', 'landing'),
                sections=sections,
                nav=page_data.get('nav'),
                footer=page_data.get('footer')
            )
            pages.append(page)

        return UnifiedContentSpec(
            brand=data.get('brand', 'Brand'),
            pages=pages,
            style=data.get('style', 'apple_dark'),
            nav=data.get('nav'),
            footer=data.get('footer')
        )

    def _detect_page_type(self, title: str) -> PageType:
        """检测页面类型"""
        title_lower = title.lower()
        for page_type, keywords in self.PAGE_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in title_lower:
                    return page_type
        return PageType.HOMEPAGE

    def _detect_section_type(self, title: str) -> SectionType:
        """检测 Section 类型"""
        title_lower = title.lower()
        for section_type, keywords in self.SECTION_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in title_lower:
                    return section_type
        return SectionType.CONTENT

    def _parse_list_item(self, text: str, section: Optional[Section]):
        """解析列表项"""
        if not section:
            return

        # 格式: "标题: 描述"
        if ':' in text:
            parts = text.split(':', 1)
            title = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            section.cards.append(Card(title=title, desc=desc))
        # 格式: "数字 + 单位 标签" (如 "95% 覆盖率")
        elif re.match(r'^[\d]+\s*[%\w]+\s+\w+', text):
            match = re.match(r'^([\d]+\s*[%\w]+)\s+(.+)', text)
            if match:
                number = match.group(1)
                label = match.group(2)
                section.stats.append(Stat(number=number, label=label))
        # 格式: "标题 - 描述"
        elif ' - ' in text:
            parts = text.split(' - ', 1)
            title = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            section.cards.append(Card(title=title, desc=desc))
        # 普通列表项作为卡片
        else:
            section.cards.append(Card(title=text, desc=""))

    def _set_section_attr(self, section: Section, key: str, value: str):
        """设置 Section 属性"""
        key_map = {
            'title': 'title',
            'subtitle': 'subtitle',
            '副标题': 'subtitle',
            '标题': 'title',
            'label': 'label',
            '标签': 'label',
            'cta': 'cta',
            '按钮': 'cta',
            'cols': 'cols',
            '列数': 'cols',
            'three_d': 'three_d',
            '3d': 'three_d',
        }

        attr_name = key_map.get(key)
        if not attr_name:
            return

        if attr_name == 'cta':
            # 解析 CTA 格式: "按钮文字 @ 链接"
            if '@' in value:
                label, url = value.split('@', 1)
                section.cta = CTA(label=label.strip(), url=url.strip())
            else:
                section.cta = CTA(label=value, url='#')
        elif attr_name == 'cols':
            section.cols = int(value) if value.isdigit() else 3
        elif attr_name == 'three_d':
            section.three_d = value.lower() in ('true', 'yes', '是', '1')
        else:
            setattr(section, attr_name, value)

    def _set_page_attr(self, page: Page, key: str, value: str):
        """设置页面属性"""
        key_map = {
            'filename': 'filename',
            '文件名': 'filename',
            'type': 'type',
            '类型': 'type',
        }
        attr_name = key_map.get(key)
        if attr_name:
            setattr(page, attr_name, value)

    def _title_to_filename(self, title: str) -> str:
        """标题转文件名"""
        # 移除特殊字符，转为小写，空格替换为下划线
        filename = re.sub(r'[^\w\s-]', '', title.lower())
        filename = re.sub(r'[\s]+', '_', filename)
        return f"{filename}.html" if filename else "page.html"


# ══════════════════════════════════════════════════════
# 测试
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = ContentParser()

    # 测试 Markdown 解析
    markdown = """
# 智擎科技

## 首页

### Hero
标题: 让 AI 为你工作
副标题: 零 Token、零成本、零等待，让网页自动生成
按钮: 立即体验 @ /start

### 功能
- 智能解析: 自动识别内容结构
- 零 Token 生成: 纯字符串拼接
- 一键部署: 自动上传 CDN

### 数据指标
- 95% 成功率
- 0 Token 消耗
- <10ms 生成延迟

### CTA
标题: 开始使用
按钮: 免费试用 @ /trial

## 产品

### 编译式 AI 平台
描述: 从意图到实现，零 Token 生成

"""

    spec = parser.parse_markdown(markdown, brand="智擎科技", style="apple_cn")
    print(f"[OK] 解析完成: {len(spec.pages)} 页, {sum(len(p.sections) for p in spec.pages)} sections")
    for page in spec.pages:
        print(f"  - {page.filename}: {len(page.sections)} sections")
        for sec in page.sections:
            print(f"    - {sec.type}: {sec.title or ''} ({len(sec.cards)} cards, {len(sec.stats)} stats)")

    # 测试 JSON 解析
    json_spec = {
        "brand": "测试品牌",
        "style": "apple_dark",
        "pages": [
            {
                "filename": "index.html",
                "title": "首页",
                "sections": [
                    {
                        "type": "hero",
                        "title": "测试标题",
                        "subtitle": "测试副标题",
                        "cta": {"label": "开始", "url": "#"}
                    }
                ]
            }
        ]
    }

    spec2 = parser.parse_json(json_spec)
    print(f"\n[OK] JSON 解析完成: {spec2.brand}, {len(spec2.pages)} 页")

    # 输出 Spec
    print(f"\n[OUTPUT] UnifiedContentSpec:")
    print(json.dumps(spec.to_dict(), indent=2, ensure_ascii=False)[:500] + "...")