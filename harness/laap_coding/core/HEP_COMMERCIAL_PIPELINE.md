# HEP 商业级 0-Token 网站生成管线设计

## 一、核心理念

**用户输入**：文案稿件 + 内容信息（结构化或非结构化）
**HEP 输出**：生产级完整网站

**关键创新**：
1. **内容解析器**：把用户文案自动转为结构化 Spec
2. **智能布局引擎**：根据内容类型自动选择页面模板
3. **组件装配器**：零 Token 拼接生成 HTML
4. **质量门禁**：自动检测并修复问题

---

## 二、管线架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户输入层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ 文案稿件     │  │ 结构化 JSON │  │ 设计稿/图片  │                 │
│  │ (Word/MD)   │  │ (Spec)      │  │ (Figma/PNG) │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        内容解析层                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ 文案结构化   │  │ 内容分类    │  │ 视觉风格提取 │                 │
│  │ 解析器      │  │ 识别器      │  │ (可选LLM)   │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                     │
│  输出: UnifiedContentSpec {                                         │
│    brand, pages[], sections[], components[], style_preset           │
│  }                                                                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      智能布局层                       │
│                                                                     │
│  输入: UnifiedContentSpec                                           │
│  输出: LayoutPlan { pages: [{template, sections[], components[]}] } │
│                                                                     │
│  规则:                                                              │
│  - 首页 → Landing Page 模板                                         │
│  - 产品介绍 → Product Page 模板                                     │
│  - 技术文档 → Feature Page 模板                                     │
│  - API 参考 → Doc Page 模板                                         │
│  - 关于我们 → About Page 模板                                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     组件装配层                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ HEP Registry                                                │   │
│  │ ├── Layouts: landing, product, feature, doc, about          │   │
│  │ ├── Sections: hero, grid, stats, cta, timeline, tabs...     │   │
│  │ ├── Molecules: card, stat-card, nav-item, breadcrumb...     │   │
│  │ └── Atoms: button, input, badge, icon, link...              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  AssemblyEngine:                                                    │
│  1. 加载 Layout 模板                                                │
│  2. 填充 Section 组件                                                │
│  3. 注入用户内容（文案、图片、链接）                                   │
│  4. 应用 Style preset                                               │
│  5. 生成完整 HTML                                                    │
│                                                                     │
│  关键: 全程零 LLM 调用，纯字符串拼接                                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       质量门禁层                      │
│                                                                     │
│  ├── 语法检查: HTML 验证、CSS 验证                                    │
│  ├── 响应式检查: 移动端/平板/桌面断点                                 │
│  ├── 可访问性检查: alt 标签、aria 属性、键盘导航                       │
│  ├── 性能检查: 图片压缩、CSS 精简、JS 延迟加载                         │
│  ├── SEO 检查: title、meta、h1-h6 层级                               │
│  └── 商业规范: 无 emoji、品牌一致性、法律声明                          │
│                                                                     │
│  不通过 → 自动修复或拒绝生成                                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         输出层                                       │
│                                                                     │
│  ├── 静态 HTML 文件（可直接部署）                                      │
│  ├── CSS 文件（提取为独立文件）                                        │
│  ├── JS 文件（交互脚本）                                              │
│  ├── 资源清单（图片、字体清单）                                        │
│  └── 部署脚本（一键部署到 CDN）                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、核心模块设计

### 3.1 内容解析器（ContentParser）

**功能**：把用户文案转为结构化 UnifiedContentSpec

**输入格式**：
1. **Markdown 文档**：
   ```markdown
   # 智擎科技
   
   ## 关于我们
   智擎科技是一家专注于编译式 AI 的科技公司...
   
   ## 产品
   ### 编译式 AI 平台
   零 Token 生成网页...
   ```

2. **结构化 JSON**：
   ```json
   {
     "brand": "智擎科技",
     "pages": [
       {
         "title": "首页",
         "sections": [
           {"type": "hero", "title": "...", "subtitle": "..."},
           {"type": "grid", "cards": [...]}
         ]
       }
     ]
   }
   ```

3. **Word/PDF 文档**（需提取文本）

**解析逻辑**（纯 Python，零 LLM）：
```python
class ContentParser:
    def parse_markdown(self, content: str) -> UnifiedContentSpec:
        """解析 Markdown 文档"""
        # 1. 识别标题层级 → 页面/Section 结构
        # 2. 识别列表 → 卡片/导航项
        # 3. 识别图片 → 图片链接
        # 4. 识别链接 → CTA/导航链接
        # 5. 识别代码块 → 代码示例
        
    def parse_json(self, content: dict) -> UnifiedContentSpec:
        """解析 JSON Spec"""
        # 直接转换为 UnifiedContentSpec
        
    def detect_content_type(self, content: str) -> str:
        """识别内容类型"""
        # 关键词匹配：产品介绍 / 技术文档 / API 参考 / 关于我们
```

### 3.2 智能布局引擎（LayoutEngine）

**功能**：根据内容类型自动选择页面模板

**布局规则**：
```python
LAYOUT_RULES = {
    "homepage": {
        "template": "landing",
        "required_sections": ["hero", "stats", "features", "cta"],
        "optional_sections": ["testimonials", "pricing", "faq"]
    },
    "product": {
        "template": "product",
        "required_sections": ["hero", "features", "specs", "pricing"],
        "optional_sections": ["faq", "testimonials", "cta"]
    },
    "feature": {
        "template": "feature",
        "required_sections": ["hero", "overview", "architecture", "code_examples"],
        "optional_sections": ["related_features", "docs_link"]
    },
    "doc": {
        "template": "doc",
        "required_sections": ["sidebar", "content", "toc"],
        "optional_sections": ["feedback", "edit_link"]
    },
    "about": {
        "template": "about",
        "required_sections": ["hero", "story", "team", "values"],
        "optional_sections": ["careers", "contact"]
    }
}
```

**自动布局逻辑**：
```python
class LayoutEngine:
    def plan_layout(self, spec: UnifiedContentSpec) -> LayoutPlan:
        """生成布局方案"""
        pages = []
        for page_spec in spec.pages:
            # 1. 识别页面类型
            page_type = self.detect_page_type(page_spec)
            
            # 2. 加载对应的布局模板
            layout = LAYOUT_RULES[page_type]
            
            # 3. 分配 Section 到模板位置
            sections = self.assign_sections(page_spec.sections, layout)
            
            # 4. 选择需要的组件
            components = self.select_components(sections)
            
            pages.append({
                "filename": page_spec.filename,
                "template": layout["template"],
                "sections": sections,
                "components": components
            })
        
        return LayoutPlan(pages=pages, style=spec.style_preset)
```

### 3.3 组件装配器（AssemblyEngine）

**功能**：零 Token 拼接生成完整 HTML

**装配流程**：
```python
class AssemblyEngine:
    def assemble(self, plan: LayoutPlan) -> List[HTMLFile]:
        """装配生成 HTML"""
        files = []
        
        for page in plan.pages:
            # 1. 加载布局模板
            layout_template = self.registry.get_layout(page.template)
            
            # 2. 装配各个 Section
            sections_html = []
            for section in page.sections:
                section_template = self.registry.get_section(section.type)
                section_html = self.fill_section(section_template, section.data)
                sections_html.append(section_html)
            
            # 3. 注入导航
            nav_html = self.build_navigation(page.navigation)
            
            # 4. 注入样式
            css_html = self.build_styles(plan.style)
            
            # 5. 注入脚本
            js_html = self.build_scripts(page.scripts)
            
            # 6. 组装完整页面
            html = layout_template.format(
                title=page.title,
                nav=nav_html,
                sections="\n".join(sections_html),
                css=css_html,
                js=js_html,
                footer=self.build_footer(page.footer)
            )
            
            files.append(HTMLFile(filename=page.filename, content=html))
        
        return files
    
    def fill_section(self, template: str, data: dict) -> str:
        """填充 Section 模板"""
        # 纯字符串替换，零 LLM
        html = template
        for key, value in data.items():
            html = html.replace(f"{{{{ {key} }}}}", str(value))
        return html
```

### 3.4 质量门禁（QualityGates）

**检查项**：
```python
class QualityGates:
    def validate(self, html: str) -> ValidationResult:
        """验证生成的 HTML"""
        errors = []
        warnings = []
        
        # 1. 语法检查
        if not self.validate_html_syntax(html):
            errors.append("HTML 语法错误")
        
        # 2. 响应式检查
        if not self.check_responsive_breakpoints(html):
            warnings.append("缺少响应式断点")
        
        # 3. 可访问性检查
        if not self.check_accessibility(html):
            warnings.append("缺少 alt 标签或 aria 属性")
        
        # 4. SEO 检查
        if not self.check_seo(html):
            warnings.append("缺少 title 或 meta 标签")
        
        # 5. 商业规范
        if self.contains_emoji(html):
            errors.append("包含 emoji，不符合商业规范")
        
        return ValidationResult(errors=errors, warnings=warnings)
    
    def auto_fix(self, html: str, issues: List[str]) -> str:
        """自动修复问题"""
        for issue in issues:
            if "缺少 alt 标签" in issue:
                html = self.add_missing_alt_tags(html)
            if "缺少 title" in issue:
                html = self.add_default_title(html)
        return html
```

---

## 四、用户输入格式规范

### 4.1 最简输入（仅文案）

```markdown
# 我的品牌

## 首页

### Hero
标题: 让 AI 为你工作
副标题: 零 Token、零成本、零等待，让网页自动生成
按钮: 立即体验

### 功能
- 功能一：智能解析
- 功能二：零 Token 生成
- 功能三：一键部署

### 联系我们
邮箱: contact@mybrand.com
电话: 400-123-4567
```

### 4.2 结构化输入（JSON Spec）

```json
{
  "brand": "我的品牌",
  "style": "apple_cn",
  "pages": [
    {
      "filename": "index.html",
      "title": "首页",
      "sections": [
        {
          "type": "hero",
          "title": "让 AI 为你工作",
          "subtitle": "零 Token、零成本、零等待",
          "cta": {"label": "立即体验", "url": "#"}
        },
        {
          "type": "grid",
          "title": "核心功能",
          "cards": [
            {"title": "智能解析", "desc": "自动识别内容结构"},
            {"title": "零 Token 生成", "desc": "纯字符串拼接"},
            {"title": "一键部署", "desc": "自动上传 CDN"}
          ]
        }
      ]
    }
  ]
}
```

### 4.3 设计稿输入（Figma/图片）

（需要 LLM 一次提取，之后零 Token 复用）

```python
# 一次提取流程
design_extractor = DesignExtractor()
style_preset = design_extractor.extract_from_figma(figma_url)
# 或
style_preset = design_extractor.extract_from_image(image_path)

# 注册为新的 Style preset
registry.register_style("my_brand", style_preset)

# 之后零 Token 使用
composer = HarnessComposer("my_brand")
html = composer.from_spec(spec)
```

---

## 五、商业级特性

### 5.1 多页面站点生成

```python
# 输入：用户文案文档
parser = ContentParser()
spec = parser.parse_markdown(user_document)

# 布局规划
engine = LayoutEngine()
plan = engine.plan_layout(spec)

# 批量生成
assembler = AssemblyEngine()
files = assembler.assemble(plan)

# 质量检查
validator = QualityGates()
for f in files:
    result = validator.validate(f.content)
    if result.errors:
        f.content = validator.auto_fix(f.content, result.errors)

# 输出
for f in files:
    f.save(f"dist/{f.filename}")
```

### 5.2 风格迁移

```python
# 用户上传参考网站
style = StyleExtractor().extract_from_url("https://reference-site.com")
registry.register_style("client_brand", style)

# 使用新风格生成
composer = HarnessComposer("client_brand")
html = composer.from_spec(spec)
```

### 5.3 组件扩展

```python
# 用户自定义组件
custom_card = HEPComponent(
    id="custom_card_v1",
    type="molecule",
    inputs=["title", "desc", "icon"],
    template="""
    <div class="custom-card">
      <div class="icon">{{ icon }}</div>
      <h3>{{ title }}</h3>
      <p>{{ desc }}</p>
    </div>
    """
)
registry.register(custom_card)

# 之后零 Token 使用
```

### 5.4 实时预览

```python
# 启动预览服务器
preview = PreviewServer(output_dir="dist")
preview.start(port=3000)

# 用户修改文案后自动重新生成
watcher = FileWatcher(input_file="content.md")
watcher.on_change(lambda: regenerate_and_refresh())
```

---

## 六、部署方案

### 6.1 CLI 工具

```bash
# 安装
pip install hep-cli

# 从文案生成
hep generate --input content.md --output dist/ --style apple_cn

# 从 JSON Spec 生成
hep generate --input spec.json --output dist/

# 提取风格
hep extract-style --url https://apple.com --name apple_cn

# 预览
hep preview --output dist/ --port 3000

# 部署
hep deploy --output dist/ --target cdn --domain mysite.com
```

### 6.2 API 服务

```python
# 启动 API 服务
hep-server --port 8000

# 客户端调用
import requests

response = requests.post("http://localhost:8000/generate", json={
    "brand": "我的品牌",
    "style": "apple_cn",
    "content": "..."
})

# 返回生成的 HTML
files = response.json()["files"]
```

### 6.3 Web IDE

```
用户界面：
┌─────────────────────────────────────────────────────────┐
│  左侧：文案编辑器                                          │
│  右侧：实时预览                                            │
│  顶部：风格选择、布局选择、组件库                            │
│  底部：导出按钮、部署按钮                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 七、性能指标

| 指标 | 目标值 | 说明 |
|---|---|---|
| 单页生成延迟 | < 10ms | 纯字符串拼接 |
| 多页站点生成 | < 100ms | 并行装配 |
| 运行时 Token | 0 | 不调用 LLM |
| 编译时 Token | 一次性 | 仅提取新风格或新组件时 |
| 输出文件大小 | < 100KB/页 | 优化后的 HTML+CSS+JS |

---

## 八、商业化路径

### 8.1 免费版

- 5 种预设风格
- 4 种页面模板
- 最多 5 页网站
- 水印保留

### 8.2 专业版

- 无限风格（支持自定义）
- 无限页面
- 组件库扩展
- 去水印
- API 访问

### 8.3 企业版

- 私有化部署
- 自定义组件库
- 团队协作
- 品牌资产管理
- 技术支持

---

## 九、与现有 HEP 管线的关系

| 现有能力 | 商业化升级 |
|---|---|
| HarnessComposer | 升级为 AssemblyEngine，支持多页面 |
| StyleEngine | 升级为 StyleRegistry，支持动态注册 |
| IntentMapper | 升级为 ContentParser，支持 Markdown/JSON/Word |
| ProductionComposer | 重构为 LayoutEngine + AssemblyEngine |
| - | 新增 QualityGates |
| - | 新增 PreviewServer |
| - | 新增 DeploymentAdapter |

---

**总结**：

HEP 商业级管线的核心创新是**把"内容解析"从 LLM 黑盒中剥离**，用规则引擎替代：

1. **文案结构化**：Markdown 标题层级 → 页面/Section 结构
2. **内容分类**：关键词匹配 → 页面类型识别
3. **布局选择**：规则表 → 模板匹配
4. **组件装配**：字符串替换 → 零 Token 生成

用户只需要提供文案，HEP 就能零 Token 生成完整网站。风格和组件库可以预先积累，越用越强大。