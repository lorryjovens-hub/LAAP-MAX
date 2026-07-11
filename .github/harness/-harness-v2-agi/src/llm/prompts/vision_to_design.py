"""提示词工程 - 视觉到设计的结构化提取"""

VISION_ANALYSIS_PROMPT = """
作为 Harness 意识大脑的视觉皮层，请对这张网页截图进行深度结构化分析。

你必须以严格的 JSON 格式返回，禁止任何其他文本。

分析维度：
1. 页面类型与整体布局模式
2. 组件识别（按视觉层级排序）
3. 设计系统参数（颜色、字体、间距、圆角、阴影）
4. 响应式线索
5. 图片/图标资源描述

JSON 格式：
{
  "page_type": "landing|dashboard|ecommerce|blog|saas",
  "layout_pattern": "hero-features|sidebar-content|grid-gallery|split-screen",
  "components": [
    {
      "type": "navbar|hero|feature_card|cta|footer|text_block|image_gallery",
      "relative_position": {"x_percent": 0, "y_percent": 0, "width_percent": 100, "height_percent": 10},
      "z_index": 1,
      "text_content": "检测到的文本",
      "visual_weight": 15
    }
  ],
  "design_system": {
    "colors": [
      {"hex": "#0A0A0A", "role": "primary", "usage": ["text", "buttons"]}
    ],
    "typography": {
      "font_family": "Inter",
      "heading_sizes": ["48px", "36px", "24px"],
      "body_size": "16px",
      "line_height": 1.5
    },
    "spacing": {
      "base_unit": 4,
      "scale": [4, 8, 16, 24, 32, 48, 64]
    },
    "border_radius": ["4px", "8px", "16px"],
    "shadows": ["0 1px 3px rgba(0,0,0,0.1)", "0 4px 6px rgba(0,0,0,0.1)"]
  },
  "responsive_hints": {
    "current_viewport": "desktop",
    "suggested_breakpoints": ["640px", "768px", "1024px", "1280px"]
  }
}
"""

VIDEO_ANALYSIS_PROMPT = """
分析这段网页交互录屏，提取所有动画和微交互规范。

输出 JSON 格式：
{
  "animations": [
    {
      "trigger": "load|hover|click|scroll|focus",
      "target_element": "button|card|modal|navbar",
      "duration_ms": 300,
      "easing": "ease-out",
      "properties": ["opacity", "transform", "scale"],
      "keyframes": [
        {"percent": 0, "opacity": 0, "transform": "translateY(10px)"},
        {"percent": 100, "opacity": 1, "transform": "translateY(0)"}
      ]
    }
  ],
  "interactions": [
    {
      "type": "hover",
      "element": "button",
      "effect": "scale up + shadow increase"
    }
  ]
}
"""

WEB_CRAWL_ANALYSIS_PROMPT = """
作为 Harness 意识大脑的爬虫之眼，请分析这个网站的 HTML/CSS/JS 结构。

输出 JSON 格式：
{
  "tech_stack": {
    "framework": "next|nuxt|react|vue|vanilla",
    "styling": "tailwind|css-modules|styled-components|scss",
    "ui_library": "shadcn|mui|antd|chakra",
    "animation": "framer-motion|gsap|css-transitions",
    "confidence": 0.95
  },
  "design_tokens": {
    "colors": [{"name": "primary", "value": "#0A0A0A", "source": "css-variable"}],
    "fonts": [{"family": "Inter", "weights": [400, 600, 700], "source": "google-fonts"}],
    "spacing": {"base": 4, "scale": [4, 8, 16, 24, 32]},
    "radius": ["0px", "4px", "8px", "16px"],
    "shadows": ["0 1px 2px rgba(0,0,0,0.05)"]
  },
  "content_structure": {
    "type": "landing|saas|ecommerce|blog|docs",
    "sections": ["hero", "features", "pricing", "testimonials", "cta", "footer"],
    "navigation": ["top", "sidebar", "none"]
  },
  "performance_hints": {
    "has_lazy_loading": true,
    "has_ssg": true,
    "image_optimization": "next-image|cloudinary|none"
  }
}
"""
