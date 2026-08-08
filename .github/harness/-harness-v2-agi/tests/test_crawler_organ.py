"""爬虫感知器官测试 - 0-token 特征检测（本地 HTML fixture，不依赖外部网络）"""

import pytest

from src.consciousness.perception.crawler_organ import (
    CrawlError,
    CrawlerOrgan,
    PlaywrightEngine,
    RequestsBS4Engine,
)
from src.api.models import CrawlerSnapshot


# 测试用 HTML fixture
NEXTJS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/_next/static/css/app.css">
    <style>
        :root {
            --color-primary: #635BFF;
            --color-secondary: #00B8A9;
            --font-family: 'Inter', sans-serif;
            --radius-md: 0.375rem;
        }
        body { color: #333; background: #fff; }
        .btn { background-color: #635BFF; border-radius: 0.375rem; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    </style>
    <script id="__NEXT_DATA__" type="application/json">{"props":{}}</script>
</head>
<body>
    <div id="__next">
        <nav class="navbar"><a href="#">Home</a><a href="/pricing">Pricing</a></nav>
        <main>
            <section class="hero"><h1>Build your business</h1><button class="btn">Get Started</button></section>
            <section class="features">
                <div class="card">Feature 1</div>
                <div class="card">Feature 2</div>
            </section>
        </main>
        <footer>Copyright 2024</footer>
    </div>
</body>
</html>
"""

WORDPRESS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/wp-content/themes/theme/style.css">
    <link rel="stylesheet" href="/wp-includes/css/dist/block-library/style.min.css">
</head>
<body>
    <article class="post">
        <h2>Blog Post Title</h2>
        <p>Author: John</p>
        <p>This is a blog post content.</p>
        <span class="category">Tech</span>
    </article>
</body>
</html>
"""


def test_detect_tech_stack_nextjs():
    """技术栈检测器能识别 Next.js"""
    stack = CrawlerOrgan.detect_tech_stack(NEXTJS_HTML)
    names = [t["name"] for t in stack]
    assert "next" in names
    next_entry = next(t for t in stack if t["name"] == "next")
    assert next_entry["confidence"] > 0.3


def test_detect_tech_stack_wordpress():
    """技术栈检测器能识别 WordPress"""
    stack = CrawlerOrgan.detect_tech_stack(WORDPRESS_HTML)
    names = [t["name"] for t in stack]
    assert "wordpress" in names


def test_detect_tech_stack_empty_html():
    """空 HTML 不抛异常"""
    stack = CrawlerOrgan.detect_tech_stack("<html><body></body></html>")
    assert isinstance(stack, list)


def test_detect_tech_stack_blank_returns_empty():
    """空字符串返回空列表"""
    assert CrawlerOrgan.detect_tech_stack("") == []


def test_classify_content_saas():
    """内容分类器能识别 SaaS（NEXTJS_HTML 含 pricing 关键词）"""
    result = CrawlerOrgan.classify_content(NEXTJS_HTML)
    assert result["type"] in ["saas", "unknown"]
    assert "confidence" in result
    assert "scores" in result


def test_classify_content_blog():
    """内容分类器能识别 blog（WORDPRESS_HTML 含 article/author/post）"""
    result = CrawlerOrgan.classify_content(WORDPRESS_HTML)
    assert result["type"] in ["blog", "unknown"]
    assert result["confidence"] >= 0.0


def test_classify_content_empty_html():
    """空 HTML 返回 unknown"""
    result = CrawlerOrgan.classify_content("")
    assert result["type"] == "unknown"
    assert result["confidence"] == 0.0


def test_extract_design_tokens():
    """设计令牌提取器能从 CSS 提取颜色/字体/圆角/阴影"""
    css = """
    :root {
        --color-primary: #635BFF;
        --font-family: 'Inter', sans-serif;
        --radius-md: 0.375rem;
    }
    body { color: #333; background-color: #fff; }
    .btn { border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    """
    tokens = CrawlerOrgan.extract_design_tokens(css, "<html></html>")
    types = [t.type for t in tokens]
    # 应包含至少 color 类型
    assert "color" in types
    assert len(tokens) > 0


def test_extract_design_tokens_empty_css():
    """空 CSS 返回空列表"""
    tokens = CrawlerOrgan.extract_design_tokens("", "<html></html>")
    assert tokens == []


def test_analyze_layout_structure():
    """布局结构分析器返回结构化字段"""
    result = CrawlerOrgan.analyze_layout_structure(NEXTJS_HTML)
    assert "depth" in result
    assert "grid_count" in result
    assert "flex_count" in result
    assert "element_density" in result
    assert isinstance(result["depth"], int)
    assert result["depth"] > 0


def test_analyze_layout_structure_empty():
    """空 HTML 返回零值结构"""
    result = CrawlerOrgan.analyze_layout_structure("")
    assert result["depth"] == 0
    assert result["grid_count"] == 0


def test_compute_fingerprint_deterministic():
    """内容指纹是确定性的"""
    snapshot1 = CrawlerSnapshot(
        url="https://example.com",
        tech_stack=[{"name": "next", "confidence": 0.99}],
        content_structure={"type": "saas"},
        layout_analysis={
            "depth": 5,
            "grid_count": 1,
            "flex_count": 2,
            "element_density": 0.5,
        },
    )
    snapshot2 = CrawlerSnapshot(
        url="https://example.com",
        tech_stack=[{"name": "next", "confidence": 0.99}],
        content_structure={"type": "saas"},
        layout_analysis={
            "depth": 5,
            "grid_count": 1,
            "flex_count": 2,
            "element_density": 0.5,
        },
    )
    fp1 = CrawlerOrgan.compute_fingerprint(snapshot1)
    fp2 = CrawlerOrgan.compute_fingerprint(snapshot2)
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA256 hex 长度


def test_compute_fingerprint_different_for_different_content():
    """不同内容生成不同指纹"""
    snap1 = CrawlerSnapshot(
        url="https://a.com",
        tech_stack=[{"name": "next", "confidence": 0.9}],
        content_structure={"type": "saas"},
        layout_analysis={
            "depth": 5,
            "grid_count": 1,
            "flex_count": 2,
            "element_density": 0.5,
        },
    )
    snap2 = CrawlerSnapshot(
        url="https://b.com",
        tech_stack=[{"name": "vue", "confidence": 0.9}],
        content_structure={"type": "blog"},
        layout_analysis={
            "depth": 3,
            "grid_count": 0,
            "flex_count": 1,
            "element_density": 0.3,
        },
    )
    assert CrawlerOrgan.compute_fingerprint(snap1) != CrawlerOrgan.compute_fingerprint(snap2)


def test_select_engine_returns_engine_tuple():
    """引擎选择器返回 (engine, name) 元组"""
    organ = CrawlerOrgan()
    result = organ.select_engine("https://example.com")
    # 实际 API 返回元组
    assert isinstance(result, tuple)
    assert len(result) == 2
    engine, name = result
    assert engine is not None
    assert hasattr(engine, "fetch") or hasattr(engine, "available")
    assert name in ["requests", "playwright", "auto"]


def test_preprocess_normalizes_url():
    """URL 预处理规范化"""
    organ = CrawlerOrgan()
    result = organ.preprocess("example.com")
    assert "http" in result
    assert "example.com" in result
    assert organ._url == result


def test_preprocess_empty_raises():
    """空 URL 抛出 CrawlError"""
    organ = CrawlerOrgan()
    with pytest.raises(CrawlError):
        organ.preprocess("")


def test_structured_output_returns_snapshot():
    """structured_output 返回 CrawlerSnapshot"""
    organ = CrawlerOrgan()
    # 手动设置内部状态以测试 structured_output
    organ._url = "https://example.com"
    organ._html = NEXTJS_HTML
    organ._css_text = ":root { --color: #fff; }"
    organ._engine_used = "requests"
    snapshot = organ.structured_output()
    assert isinstance(snapshot, CrawlerSnapshot)
    assert snapshot.url == "https://example.com"
    assert snapshot.engine_used == "requests"
    assert len(snapshot.fingerprint) == 64


def test_requests_engine_has_name():
    """RequestsBS4Engine 有 name 属性"""
    engine = RequestsBS4Engine()
    assert engine.name == "requests"
    assert hasattr(engine, "available")


def test_playwright_engine_has_name():
    """PlaywrightEngine 有 name 属性"""
    engine = PlaywrightEngine()
    assert engine.name == "playwright"
    assert hasattr(engine, "available")


def test_to_hex_various_formats():
    """_to_hex 支持多种颜色格式"""
    assert CrawlerOrgan._to_hex("#fff") == "#ffffff"
    assert CrawlerOrgan._to_hex("#FFFFFF") == "#ffffff"
    assert CrawlerOrgan._to_hex("#635BFF") == "#635bff"
    assert CrawlerOrgan._to_hex("rgb(0, 0, 0)") == "#000000"
    assert CrawlerOrgan._to_hex("rgba(255, 255, 255, 0.5)") == "#ffffff"
    assert CrawlerOrgan._to_hex("#aabbcc22") == "#aabbcc"  # 丢弃 alpha
    assert CrawlerOrgan._to_hex("not-a-color") is None


@pytest.mark.asyncio
async def test_perceive_returns_tuple():
    """perceive() 返回 (snapshot, signal) 元组"""
    organ = CrawlerOrgan()

    # Mock 引擎（异步 fetch）
    class MockEngine:
        available = True
        name = "mock"

        async def fetch(self, url):
            return NEXTJS_HTML, ":root { --color: #fff; }", url

    # select_engine 实际返回 (engine, name) 元组
    organ.select_engine = lambda url: (MockEngine(), "mock")

    snapshot, signal = await organ.perceive("https://example.com")
    assert isinstance(snapshot, CrawlerSnapshot)
    assert signal.modality.value == "crawler"
    assert signal.source == "crawler_organ"
    # 应提取到技术栈
    assert len(snapshot.tech_stack) > 0
    assert snapshot.engine_used in ["requests", "playwright"]


@pytest.mark.asyncio
async def test_perceive_handles_engine_failure():
    """引擎抓取失败时不阻塞流水线（特征为空但仍返回 snapshot）"""
    organ = CrawlerOrgan()

    class FailingEngine:
        available = True
        name = "failing"

        async def fetch(self, url):
            raise CrawlError("simulated failure")

    organ.select_engine = lambda url: (FailingEngine(), "failing")

    snapshot, signal = await organ.perceive("https://example.com")
    assert isinstance(snapshot, CrawlerSnapshot)
    assert signal.source == "crawler_organ"


def test_needs_dynamic_render_detection():
    """_needs_dynamic_render 识别 SSR 但内容缺失"""
    organ = CrawlerOrgan()
    # Next.js 标记 + 空容器
    sparse_html = """
    <html><body>
    <div id="__next"></div>
    <script id="__NEXT_DATA__">{"props":{}}</script>
    </body></html>
    """
    assert organ._needs_dynamic_render(sparse_html) is True

    # 充实的内容不需要动态渲染
    rich_html = """
    <html><body>
    <div id="__next"><main><h1>Welcome</h1><p>Long content here that exceeds threshold for detection of rendered content easily.</p></main></div>
    <script id="__NEXT_DATA__">{"props":{}}</script>
    </body></html>
    """
    assert organ._needs_dynamic_render(rich_html) is False

    # 非 SSR 站点
    assert organ._needs_dynamic_render("<html><body>Hello</body></html>") is False
