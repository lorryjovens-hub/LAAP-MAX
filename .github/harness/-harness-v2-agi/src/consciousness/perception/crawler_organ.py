"""爬虫感知器官 - Crawler Organ

感知器官系统的核心模块，遵循"工程结构拆解一切，LLM 只负责语义缝合"原则。
所有特征提取（tech_stack / content / design_tokens / layout）使用 0-token 确定性算法，
仅在 semantic_annotate 阶段调用 LLM 做语义总结（≤500 token）。

感知流水线：
    preprocess(url) → extract_features() → structured_output() → semantic_annotate()
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from src.api.models import (
    CrawlerSnapshot,
    DesignToken,
    PerceptionModality,
    PerceptionSignal,
)
from src.config import get_settings
from src.consciousness.perception.base_organ import PerceptionOrgan
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# 可选依赖：requests / playwright 可能未安装，运行时降级
# ---------------------------------------------------------------------------
try:
    import requests as _requests_lib

    _REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _requests_lib = None
    _REQUESTS_AVAILABLE = False

try:
    from playwright.async_api import async_playwright as _async_playwright

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _async_playwright = None
    _PLAYWRIGHT_AVAILABLE = False


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------
class CrawlError(Exception):
    """爬虫抓取或解析错误"""


# ---------------------------------------------------------------------------
# 爬虫引擎
# ---------------------------------------------------------------------------
class RequestsBS4Engine:
    """静态爬虫引擎 - requests + BeautifulSoup

    适用于 SSR 站点或无需 JavaScript 渲染的页面。
    fetch() 同步执行，返回 (html, css_text, final_url)。
    """

    def __init__(self) -> None:
        self.timeout: int = settings.crawler_timeout
        self.user_agent: str = settings.crawler_user_agent
        self.available: bool = _REQUESTS_AVAILABLE
        self.name: str = "requests"

    def fetch(self, url: str) -> Tuple[str, str, str]:
        """抓取 URL，返回 (html, css_text, final_url)。

        Raises:
            CrawlError: 当 requests 未安装或网络请求失败时。
        """
        if not self.available:
            raise CrawlError("requests 库未安装，无法使用 RequestsBS4Engine")

        headers = {"User-Agent": self.user_agent}
        try:
            response = _requests_lib.get(  # type: ignore[union-attr]
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
        except Exception as exc:
            raise CrawlError(f"requests 抓取失败 {url}: {exc}") from exc

        html: str = response.text
        final_url: str = str(response.url)
        css_text = self._extract_css(html, final_url)
        logger.debug(f"[RequestsBS4Engine] 抓取完成: {final_url}, html={len(html)}B, css={len(css_text)}B")
        return html, css_text, final_url

    def _extract_css(self, html: str, base_url: str) -> str:
        """提取并合并所有 CSS：`<style>` 标签 + `<link rel=stylesheet>` 外链。"""
        soup = BeautifulSoup(html, "html.parser")
        css_parts: List[str] = []

        # 1. 内联 <style> 标签
        for style_tag in soup.find_all("style"):
            if style_tag.string:
                css_parts.append(style_tag.string)

        # 2. 外链 stylesheet
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if not href:
                continue
            css_url = urljoin(base_url, href)
            try:
                resp = _requests_lib.get(  # type: ignore[union-attr]
                    css_url,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                css_parts.append(resp.text)
            except Exception as exc:
                logger.warning(f"CSS 外链抓取失败 {css_url}: {exc}")

        return "\n".join(css_parts)


class PlaywrightEngine:
    """动态爬虫引擎 - Playwright (chromium)

    适用于需要 JavaScript 渲染的 SPA 站点。
    fetch() 异步执行，等待 networkidle 后提取完整 HTML 和 CSS。
    若 playwright 未安装则 available=False。
    """

    def __init__(self) -> None:
        self.timeout: int = settings.crawler_timeout
        self.available: bool = _PLAYWRIGHT_AVAILABLE
        self.name: str = "playwright"

    async def fetch(self, url: str) -> Tuple[str, str, str]:
        """异步抓取 URL，返回 (html, css_text, final_url)。

        Raises:
            CrawlError: 当 playwright 未安装或渲染失败时。
        """
        if not self.available:
            raise CrawlError("playwright 未安装，无法使用 PlaywrightEngine")

        try:
            async with _async_playwright() as p:  # type: ignore[misc]
                browser = await p.chromium.launch(headless=True)
                try:
                    page = await browser.new_page(
                        user_agent=settings.crawler_user_agent
                    )
                    await page.goto(
                        url,
                        wait_until="networkidle",
                        timeout=self.timeout * 1000,
                    )
                    html = await page.content()
                    final_url = page.url

                    # 从 document.styleSheets 提取所有 CSS（含动态注入的）
                    css_text = await page.evaluate(
                        """() => {
                            let css = '';
                            try {
                                for (const sheet of document.styleSheets) {
                                    try {
                                        for (const rule of sheet.cssRules) {
                                            css += rule.cssText + '\\n';
                                        }
                                    } catch(e) {
                                        // 跨域样式表无法访问 cssRules
                                    }
                                }
                            } catch(e) {}
                            return css;
                        }"""
                    )
                    logger.debug(
                        f"[PlaywrightEngine] 抓取完成: {final_url}, "
                        f"html={len(html)}B, css={len(css_text)}B"
                    )
                    return html, css_text, final_url
                finally:
                    await browser.close()
        except CrawlError:
            raise
        except Exception as exc:
            raise CrawlError(f"playwright 渲染失败 {url}: {exc}") from exc


# ---------------------------------------------------------------------------
# CrawlerOrgan 主类
# ---------------------------------------------------------------------------
class CrawlerOrgan(
    PerceptionOrgan[str, str, Dict[str, Any], CrawlerSnapshot, Dict[str, Any]]
):
    """爬虫感知器官

    通过爬虫引擎抓取目标 URL 的 HTML 和 CSS，使用 0-token 确定性算法提取：
    - 技术栈 (React/Vue/Next/Tailwind/...)
    - 内容分类 (blog/ecommerce/saas/portfolio/docs)
    - 设计令牌 (颜色/字体/圆角/阴影)
    - 布局结构 (DOM 深度/grid/flex/语义标签)

    最终组装为 CrawlerSnapshot，并可选调用 LLM 做语义总结。

    用法::

        organ = CrawlerOrgan()
        snapshot, signal = await organ.perceive("https://example.com")
    """

    # -- 技术栈检测模式（0-token，纯正则） --
    TECH_PATTERNS: Dict[str, List[str]] = {
        "next": [r"__NEXT_DATA__", r"_buildManifest\.js", r"_ssgManifest\.js"],
        "nuxt": [r"__NUXT__", r"_nuxt/", r"window\.__NUXT__"],
        "react": [r"react\.production", r"react-dom", r"data-reactroot"],
        "vue": [r"__INITIAL_STATE__", r"data-v-[a-f0-9]+", r"vue\.runtime"],
        "angular": [r"ng-version", r"ng-app", r"angular\."],
        "svelte": [r"svelte-[a-z0-9]+", r"__svelte_meta"],
        "wordpress": [r"wp-content/", r"wp-includes/", r"wp-json"],
        "tailwind": [r"tailwind\.css", r"tw-[a-z0-9]+", r"!flex\s*!flex"],
        "bootstrap": [r"bootstrap\.min\.css", r"container-fluid"],
        "radix-ui": [r"radix", r"data-radix"],
        "chakra-ui": [r"chakra", r"css-[a-z0-9]+"],
        "framer-motion": [r"framer-motion", r"data-framer"],
    }

    # -- 内容分类关键词（0-token，纯正则） --
    CONTENT_CATEGORIES: Dict[str, List[str]] = {
        "blog": ["article", "post", "author", "blog", "category", "tag", "archive", "comment"],
        "ecommerce": ["product", "cart", "price", "shop", "buy", "checkout", "wishlist", "add to cart"],
        "saas": ["pricing", "features", "dashboard", "signup", "login", "trial", "demo", "subscribe"],
        "portfolio": ["portfolio", "project", "work", "case study", "client", "agency"],
        "docs": ["documentation", "guide", "tutorial", "reference", "api", "examples"],
    }

    def __init__(self) -> None:
        super().__init__(name="crawler")

    # ======================================================================
    # 感知流水线 - 4 个阶段
    # ======================================================================

    def preprocess(self, raw: str) -> str:
        """预处理：规范化 URL。

        - 去除首尾空白
        - 若无 scheme 则补 https://
        - 存入 self._url
        """
        url = raw.strip()
        if not url:
            raise CrawlError("URL 不能为空")

        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)

        if not parsed.netloc:
            raise CrawlError(f"无效 URL: {raw}")

        self._url = url
        self.logger.info(f"预处理 URL: {url}")
        return url

    async def extract_features(self) -> Dict[str, Any]:
        """特征提取：调用爬虫引擎抓取，再调用各 0-token 特征检测器。

        中间结果存入实例属性：
            self._html, self._css_text, self._final_url
            self._tech_stack, self._content_structure,
            self._design_tokens, self._layout_analysis
        """
        url = self._url

        # 1. 选择并执行爬虫引擎
        engine, engine_name = self.select_engine(url)
        html = ""
        css_text = ""
        final_url = url

        try:
            if hasattr(engine, "fetch"):
                # 区分同步/异步引擎
                import inspect

                if inspect.iscoroutinefunction(engine.fetch):
                    html, css_text, final_url = await engine.fetch(url)
                else:
                    html, css_text, final_url = engine.fetch(url)
        except CrawlError as exc:
            self.logger.warning(f"引擎 {engine_name} 抓取失败: {exc}")
            html = ""
            css_text = ""

        # 2. auto 模式：检测 SSR + 内容缺失 → 回退 Playwright
        if engine_name == "auto" and html:
            needs_fallback = self._needs_dynamic_render(html)
            if needs_fallback and _PLAYWRIGHT_AVAILABLE:
                self.logger.info("检测到 SSR 框架但静态 HTML 内容缺失，回退 Playwright")
                pw_engine = PlaywrightEngine()
                try:
                    html, css_text, final_url = await pw_engine.fetch(url)
                    engine_name = "playwright"
                except CrawlError as exc:
                    self.logger.warning(f"Playwright 回退失败，使用静态结果: {exc}")
            elif needs_fallback and not _PLAYWRIGHT_AVAILABLE:
                self.logger.warning("检测到需要动态渲染但 playwright 未安装，使用静态结果")

        # 3. 0-token 特征提取（CPU 密集，同步）
        try:
            tech_stack = self.detect_tech_stack(html)
        except Exception as exc:
            self.logger.warning(f"技术栈检测失败: {exc}")
            tech_stack = []

        try:
            content_structure = self.classify_content(html)
        except Exception as exc:
            self.logger.warning(f"内容分类失败: {exc}")
            content_structure = {"type": "unknown", "confidence": 0.0, "scores": {}}

        try:
            design_tokens = self.extract_design_tokens(css_text, html)
        except Exception as exc:
            self.logger.warning(f"设计令牌提取失败: {exc}")
            design_tokens = []

        try:
            layout_analysis = self.analyze_layout_structure(html)
        except Exception as exc:
            self.logger.warning(f"布局分析失败: {exc}")
            layout_analysis = {
                "depth": 0,
                "grid_count": 0,
                "flex_count": 0,
                "element_density": 0.0,
                "top_level_sections": 0,
                "semantic_tags": {},
            }

        self._html = html
        self._css_text = css_text
        self._final_url = final_url
        self._engine_used = "playwright" if engine_name == "playwright" else "requests"
        self._features = {
            "tech_stack": tech_stack,
            "content_structure": content_structure,
            "design_tokens": design_tokens,
            "layout_analysis": layout_analysis,
        }

        self.logger.info(
            f"特征提取完成: tech={len(tech_stack)}, "
            f"type={content_structure.get('type', 'unknown')}, "
            f"tokens={len(design_tokens)}"
        )
        return self._features

    def structured_output(self) -> CrawlerSnapshot:
        """结构化输出：组装为 CrawlerSnapshot 对象。零 LLM token。"""
        features = getattr(self, "_features", {})
        snapshot = CrawlerSnapshot(
            url=getattr(self, "_final_url", self._url),
            tech_stack=features.get("tech_stack", []),
            design_tokens=features.get("design_tokens", []),
            content_structure=features.get("content_structure", {}),
            layout_analysis=features.get("layout_analysis", {}),
            fingerprint="",
            engine_used=getattr(self, "_engine_used", "requests"),
        )
        # 计算指纹
        snapshot.fingerprint = self.compute_fingerprint(snapshot)
        self._snapshot = snapshot
        return snapshot

    async def semantic_annotate(
        self, snapshot: Optional[CrawlerSnapshot] = None
    ) -> Dict[str, Any]:
        """语义标注：调用 LLM 做一句话总结（≤500 token）。

        失败时返回原始 snapshot 信息，不阻塞流水线。

        Returns:
            {"summary": str, "original_snapshot": CrawlerSnapshot, "confidence": float}
        """
        snap = snapshot or getattr(self, "_snapshot", None)
        if snap is None:
            return {"summary": "", "original_snapshot": None, "confidence": 0.0}

        try:
            from src.llm.client import get_llm_client

            client = await get_llm_client()

            tech_names = ", ".join(t.get("name", "") for t in snap.tech_stack)
            content_type = snap.content_structure.get("type", "unknown")
            layout = snap.layout_analysis
            layout_desc = (
                f"depth={layout.get('depth', 0)}, "
                f"grid={layout.get('grid_count', 0)}, "
                f"flex={layout.get('flex_count', 0)}"
            )

            prompt = (
                f"请用一句话（不超过 50 字）总结这个网站：\n"
                f"技术栈: {tech_names}\n"
                f"内容类型: {content_type}\n"
                f"布局特征: {layout_desc}\n"
                f"URL: {snap.url}\n"
                f"格式要求：这是一个用 X+Y 做的 Z 类型站点。"
            )

            summary = await client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是网站分析专家，用简洁的一句话总结网站特征。",
                    },
                    {"role": "user", "content": prompt},
                ],
                stage="perception",
                temperature=0.2,
                max_tokens=500,
            )

            return {
                "summary": summary.strip(),
                "original_snapshot": snap,
                "confidence": 0.9,
            }
        except Exception as exc:
            self.logger.warning(f"LLM 语义标注失败，返回原始 snapshot: {exc}")
            return {
                "summary": "",
                "original_snapshot": snap,
                "confidence": 0.5,
            }

    # ======================================================================
    # 主入口 perceive（async，覆盖基类同步版本）
    # ======================================================================

    async def perceive(self, url: str) -> Tuple[CrawlerSnapshot, PerceptionSignal]:
        """爬虫感知主入口。

        Args:
            url: 目标网站 URL

        Returns:
            (CrawlerSnapshot, PerceptionSignal) 元组
        """
        self.logger.info(f"[{self.name}] 感知流水线启动: {url}")

        # 1. 预处理
        self.preprocess(url)
        self.logger.debug(f"[{self.name}] 预处理完成")

        # 2. 特征提取（含网络 IO）
        await self.extract_features()
        self.logger.debug(f"[{self.name}] 特征提取完成")

        # 3. 结构化输出
        snapshot = self.structured_output()
        self.logger.debug(f"[{self.name}] 结构化输出完成")

        # 4. 语义标注（可选 LLM）
        annotation = await self.semantic_annotate(snapshot)

        # 5. 构建 PerceptionSignal
        signal = PerceptionSignal(
            modality=PerceptionModality.CRAWLER,
            payload={
                "tech_stack": snapshot.tech_stack,
                "content_type": snapshot.content_structure.get("type", "unknown"),
                "engine": snapshot.engine_used,
                "fingerprint": snapshot.fingerprint,
                "semantic_summary": annotation.get("summary", ""),
            },
            confidence=annotation.get("confidence", 0.8),
            source="crawler_organ",
        )

        self.logger.info(
            f"[{self.name}] 感知流水线完成: "
            f"tech={len(snapshot.tech_stack)}, "
            f"type={snapshot.content_structure.get('type', 'unknown')}"
        )
        return snapshot, signal

    # ======================================================================
    # 引擎选择器
    # ======================================================================

    def select_engine(
        self, target_url: str
    ) -> Tuple[Union[RequestsBS4Engine, PlaywrightEngine], str]:
        """根据配置选择爬虫引擎。

        Args:
            target_url: 目标 URL（当前仅用于日志，未来可基于域名路由）

        Returns:
            (engine_instance, engine_name) 元组。
            engine_name 为 "requests" / "playwright" / "auto"。
            "auto" 表示当前使用静态引擎，extract_features 中可能回退。
        """
        engine_setting = settings.crawler_engine

        if engine_setting == "requests":
            return RequestsBS4Engine(), "requests"

        if engine_setting == "playwright":
            if not _PLAYWRIGHT_AVAILABLE:
                self.logger.warning(
                    "配置指定 playwright 但未安装，回退到 requests 引擎"
                )
                return RequestsBS4Engine(), "requests"
            return PlaywrightEngine(), "playwright"

        # auto 模式：先用静态引擎，extract_features 中按需回退
        static_engine = RequestsBS4Engine()
        if not static_engine.available and _PLAYWRIGHT_AVAILABLE:
            self.logger.info("requests 不可用，auto 模式直接使用 playwright")
            return PlaywrightEngine(), "playwright"

        return static_engine, "auto"

    def _needs_dynamic_render(self, html: str) -> bool:
        """检测是否需要动态渲染：SSR 框架 + 核心内容缺失。"""
        # 检测 SSR 框架标记
        ssr_markers = ["__NEXT_DATA__", "__NUXT__", "window.__NUXT__"]
        is_ssr = any(marker in html for marker in ssr_markers)
        if not is_ssr:
            return False

        # 检测 #app / #__next 容器是否为空
        soup = BeautifulSoup(html, "html.parser")
        for container_id in ["__next", "app", "root"]:
            container = soup.find(id=container_id)
            if container is not None:
                # 容器存在但子内容极少 → 需要 JS 渲染
                child_text = container.get_text(strip=True)
                child_tags = container.find_all(recursive=True)
                if len(child_text) < 50 and len(child_tags) < 5:
                    return True
        return False

    # ======================================================================
    # 0-token 特征检测器
    # ======================================================================

    @staticmethod
    def detect_tech_stack(html: str) -> List[Dict[str, Any]]:
        """技术栈检测（0-token，纯正则）。

        检测 Next.js / Nuxt / React / Vue / Angular / Svelte / WordPress /
        Tailwind / Bootstrap / Radix UI / Chakra UI / Framer Motion。

        Returns:
            [{"name": str, "version": Optional[str], "confidence": float}, ...]
            confidence = matched_patterns / total_patterns，最低 0.3。
        """
        if not html:
            return []

        results: List[Dict[str, Any]] = []

        # 尝试从 HTML 注释或 meta 提取版本信息
        version_map: Dict[str, Optional[str]] = {}
        for name, patterns in CrawlerOrgan.TECH_PATTERNS.items():
            version_map[name] = CrawlerOrgan._extract_version(html, name)

        for name, patterns in CrawlerOrgan.TECH_PATTERNS.items():
            total = len(patterns)
            matched = 0
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    matched += 1

            if matched > 0:
                confidence = max(0.3, matched / total) if total > 0 else 0.3
                results.append(
                    {
                        "name": name,
                        "version": version_map.get(name),
                        "confidence": round(confidence, 3),
                    }
                )

        # 按 confidence 降序排列
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    @staticmethod
    def _extract_version(html: str, framework: str) -> Optional[str]:
        """从 HTML 注释或 meta 标签提取框架版本（尽力而为）。"""
        # 从 meta 标签提取
        meta_patterns = {
            "next": [r'<meta\s+name=["\']generator["\']\s+content=["\']Next\.js\s*([\d.]+)'],
            "nuxt": [r'<meta\s+name=["\']generator["\']\s+content=["\']Nuxt\s*([\d.]+)'],
            "react": [r'React(?:DOM)?[^\d]*([\d]+\.[\d]+\.[\d]+)'],
            "vue": [r'Vue\.js[^\d]*([\d]+\.[\d]+\.[\d]+)'],
            "angular": [r'ng-version=["\']([\d.]+)'],
            "svelte": [r'svelte[^\d]*([\d]+\.[\d]+\.[\d]+)'],
            "wordpress": [r'<meta\s+name=["\']generator["\']\s+content=["\']WordPress\s*([\d.]+)'],
            "bootstrap": [r'bootstrap[^\d]*([\d]+\.[\d]+\.[\d]+)'],
            "tailwind": [r'tailwindcss?[^\d]*([\d]+\.[\d]+\.[\d]+)'],
        }
        patterns = meta_patterns.get(framework, [])
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def classify_content(html: str) -> Dict[str, Any]:
        """内容分类器（0-token，纯正则）。

        对每个类别的关键词在 HTML 中计数，计算得分。
        得分 = 关键词总匹配数 / HTML 字符数 * 1000。
        Top-1 confidence = top_score / sum(all_scores)。

        Returns:
            {"type": str, "confidence": float, "scores": Dict[str, float]}
        """
        if not html:
            return {"type": "unknown", "confidence": 0.0, "scores": {}}

        char_count = len(html)
        if char_count == 0:
            return {"type": "unknown", "confidence": 0.0, "scores": {}}

        # 提取 HTML 纯文本用于关键词匹配
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ")

        scores: Dict[str, float] = {}
        for category, keywords in CrawlerOrgan.CONTENT_CATEGORIES.items():
            total_matches = 0
            for keyword in keywords:
                matches = re.findall(
                    re.escape(keyword), text, re.IGNORECASE
                )
                total_matches += len(matches)
            scores[category] = total_matches / char_count * 1000

        # 所有得分都为 0
        total_score = sum(scores.values())
        if total_score == 0:
            return {"type": "unknown", "confidence": 0.0, "scores": scores}

        # Top-1 类别
        top_category = max(scores, key=scores.get)
        top_score = scores[top_category]
        confidence = top_score / total_score

        return {
            "type": top_category,
            "confidence": round(confidence, 3),
            "scores": {k: round(v, 4) for k, v in scores.items()},
        }

    @staticmethod
    def extract_design_tokens(css_text: str, html: str) -> List[DesignToken]:
        """设计令牌提取（0-token，纯正则）。

        解析 CSS 文本，提取颜色、字体、圆角、阴影。
        颜色统一转换为 HEX 格式。confidence: 0.9（CSS 变量）/ 0.7（内联样式）。

        Returns:
            List[DesignToken]
        """
        tokens: List[DesignToken] = []
        if not css_text:
            return tokens

        # 1. 提取 CSS 变量（:root / body 块内的 --var: value）
        css_vars: Dict[str, str] = {}
        for block_selector in [r":root\s*\{([^}]+)\}", r"body\s*\{([^}]+)\}"]:
            for block_match in re.finditer(block_selector, css_text, re.DOTALL):
                block_content = block_match.group(1)
                for var_match in re.finditer(
                    r"(--[\w-]+)\s*:\s*([^;]+)", block_content
                ):
                    var_name = var_match.group(1).strip()
                    var_value = var_match.group(2).strip()
                    css_vars[var_name] = var_value

        # 2. 颜色令牌
        # 2a. CSS 变量中的颜色
        seen_colors: set = set()
        for var_name, var_value in css_vars.items():
            color_hex = CrawlerOrgan._to_hex(var_value)
            if color_hex and color_hex not in seen_colors:
                seen_colors.add(color_hex)
                tokens.append(
                    DesignToken(
                        name=var_name,
                        value=color_hex,
                        type="color",
                        semantics=f"CSS 变量定义的颜色 {var_name}",
                        usage=[":root", "body"],
                        confidence=0.9,
                    )
                )

        # 2b. 直接颜色属性（color / background-color / border-color）
        color_properties = [
            ("color", r"(?<!-)color\s*:\s*([^;{}]+)"),
            ("background-color", r"background-color\s*:\s*([^;{}]+)"),
            ("border-color", r"border-color\s*:\s*([^;{}]+)"),
        ]
        for prop_name, pattern in color_properties:
            for match in re.finditer(pattern, css_text, re.IGNORECASE):
                value = match.group(1).strip()
                # 解析 var() 引用
                resolved = CrawlerOrgan._resolve_var(value, css_vars)
                color_hex = CrawlerOrgan._to_hex(resolved)
                if color_hex and color_hex not in seen_colors:
                    seen_colors.add(color_hex)
                    tokens.append(
                        DesignToken(
                            name=f"{prop_name}-{color_hex}",
                            value=color_hex,
                            type="color",
                            semantics=f"从 {prop_name} 属性提取的颜色",
                            usage=[prop_name],
                            confidence=0.7,
                        )
                    )

        # 3. 字体令牌（去重，保留前 3 个）
        seen_fonts: set = set()
        font_count = 0
        for match in re.finditer(r"font-family\s*:\s*([^;{}]+)", css_text, re.IGNORECASE):
            value = match.group(1).strip().rstrip(",")
            # 提取首个字体族
            first_font = value.split(",")[0].strip().strip("'\"")
            if first_font and first_font.lower() not in seen_fonts and font_count < 3:
                seen_fonts.add(first_font.lower())
                font_count += 1
                tokens.append(
                    DesignToken(
                        name=f"font-family-{font_count}",
                        value=first_font,
                        type="font",
                        semantics=f"页面字体族: {first_font}",
                        usage=["font-family"],
                        confidence=0.7,
                    )
                )

        # 4. 圆角令牌（去重）
        seen_radius: set = set()
        for match in re.finditer(r"border-radius\s*:\s*([^;{}]+)", css_text, re.IGNORECASE):
            value = match.group(1).strip()
            if value and value not in seen_radius and value not in ("0", "0px", "none"):
                seen_radius.add(value)
                tokens.append(
                    DesignToken(
                        name=f"border-radius-{value}",
                        value=value,
                        type="radius",
                        semantics=f"圆角: {value}",
                        usage=["border-radius"],
                        confidence=0.7,
                    )
                )

        # 5. 阴影令牌（去重）
        seen_shadow: set = set()
        for match in re.finditer(r"box-shadow\s*:\s*([^;{}]+)", css_text, re.IGNORECASE):
            value = match.group(1).strip()
            if value and value not in seen_shadow and value != "none":
                seen_shadow.add(value)
                tokens.append(
                    DesignToken(
                        name=f"box-shadow-{len(seen_shadow)}",
                        value=value,
                        type="shadow",
                        semantics=f"盒阴影: {value[:50]}",
                        usage=["box-shadow"],
                        confidence=0.7,
                    )
                )

        return tokens

    @staticmethod
    def analyze_layout_structure(html: str) -> Dict[str, Any]:
        """布局结构分析（0-token，纯 BeautifulSoup + 正则）。

        Returns:
            {
                "depth": int,           # DOM 树最大深度
                "grid_count": int,       # display: grid 出现次数
                "flex_count": int,       # display: flex 出现次数
                "element_density": float, # 总元素数 / 1000
                "top_level_sections": int, # body 直接子元素数量
                "semantic_tags": Dict[str, int],  # 语义标签统计
            }
        """
        if not html:
            return {
                "depth": 0,
                "grid_count": 0,
                "flex_count": 0,
                "element_density": 0.0,
                "top_level_sections": 0,
                "semantic_tags": {},
            }

        soup = BeautifulSoup(html, "html.parser")

        # DOM 树最大深度
        def _compute_depth(tag: Tag) -> int:
            children = [c for c in tag.children if isinstance(c, Tag)]
            if not children:
                return 1
            return 1 + max(_compute_depth(c) for c in children)

        body = soup.find("body")
        if body:
            depth = _compute_depth(body)
            top_level_sections = len(
                [c for c in body.children if isinstance(c, Tag)]
            )
        else:
            depth = _compute_depth(soup) if soup else 0
            top_level_sections = 0

        # display: grid / flex 出现次数（在 HTML 字符串中搜索，含内联和 style 标签）
        grid_count = len(re.findall(r"display\s*:\s*grid", html, re.IGNORECASE))
        flex_count = len(re.findall(r"display\s*:\s*flex", html, re.IGNORECASE))

        # 总元素数
        all_tags = soup.find_all()
        total_elements = len(all_tags)
        element_density = total_elements / 1000.0

        # 语义标签统计
        semantic_tags: Dict[str, int] = {}
        for tag_name in ["header", "nav", "main", "section", "footer", "aside"]:
            semantic_tags[tag_name] = len(soup.find_all(tag_name))

        return {
            "depth": depth,
            "grid_count": grid_count,
            "flex_count": flex_count,
            "element_density": round(element_density, 3),
            "top_level_sections": top_level_sections,
            "semantic_tags": semantic_tags,
        }

    # ======================================================================
    # 内容指纹
    # ======================================================================

    @staticmethod
    def compute_fingerprint(snapshot: CrawlerSnapshot) -> str:
        """计算内容指纹（SHA256）。

        取 tech_stack（按 name 排序）+ content_structure.type + layout_analysis 关键字段，
        JSON 序列化后计算 SHA256 哈希。

        Returns:
            64 字符的十六进制字符串
        """
        tech_sorted = sorted(
            snapshot.tech_stack, key=lambda x: x.get("name", "")
        )
        fingerprint_data = {
            "tech_stack": [t.get("name") for t in tech_sorted],
            "content_type": snapshot.content_structure.get("type", ""),
            "layout": {
                "depth": snapshot.layout_analysis.get("depth", 0),
                "grid_count": snapshot.layout_analysis.get("grid_count", 0),
                "flex_count": snapshot.layout_analysis.get("flex_count", 0),
                "top_level_sections": snapshot.layout_analysis.get(
                    "top_level_sections", 0
                ),
            },
        }
        serialized = json.dumps(fingerprint_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # ======================================================================
    # 辅助方法
    # ======================================================================

    @staticmethod
    def _to_hex(color_value: str) -> Optional[str]:
        """将颜色值统一转换为 HEX 格式 (#aabbcc)。

        支持: #abc, #aabbcc, #rrggbbaa, rgb(r,g,b), rgba(r,g,b,a)
        无法识别的值返回 None。
        """
        value = color_value.strip().lower()

        # #aabbcc / #abc / #rrggbbaa
        hex_match = re.match(r"^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$", value)
        if hex_match:
            hex_digits = hex_match.group(1)
            if len(hex_digits) == 3:
                # #abc → #aabbcc
                return "#" + "".join(c * 2 for c in hex_digits)
            elif len(hex_digits) == 8:
                # #rrggbbaa → #rrggbb (丢弃 alpha)
                return "#" + hex_digits[:6]
            else:
                return "#" + hex_digits

        # rgb(r, g, b) / rgba(r, g, b, a)
        rgb_match = re.match(
            r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", value
        )
        if rgb_match:
            r, g, b = (int(rgb_match.group(i)) for i in (1, 2, 3))
            return f"#{r:02x}{g:02x}{b:02x}"

        return None

    @staticmethod
    def _resolve_var(value: str, css_vars: Dict[str, str]) -> str:
        """解析 CSS var() 引用。若变量未定义则返回原值。"""
        var_match = re.match(r"^var\(\s*(--[\w-]+)\s*\)", value.strip())
        if var_match:
            var_name = var_match.group(1)
            return css_vars.get(var_name, value)
        return value
