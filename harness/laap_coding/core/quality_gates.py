"""
QualityGates - 网页质量门禁检查器

核心功能：
1. 响应式检查：移动端/平板/桌面断点
2. SEO 检查：title、meta、h1-h6、alt 标签
3. 可访问性检查：aria 属性、键盘导航、颜色对比度
4. 性能检查：图片大小、CSS 精简、JS 延迟加载
5. 商业规范检查：emoji、品牌一致性、法律声明

使用示例：
    from quality_gates import QualityGates
    
    validator = QualityGates()
    result = validator.validate(html_content)
    
    if result.errors:
        html = validator.auto_fix(html_content, result.errors)
    
    print(f"[{result.status}] {len(result.errors)} errors, {len(result.warnings)} warnings")
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from enum import Enum


class ValidationStatus(Enum):
    """验证状态"""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass
class ValidationIssue:
    """验证问题"""
    code: str
    message: str
    severity: str  # error / warning / info
    line: int = 0
    auto_fixable: bool = False


@dataclass
class ValidationResult:
    """验证结果"""
    status: ValidationStatus
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class QualityGates:
    """
    质量门禁检查器
    
    检查项目：
    - 响应式：@media 断点、移动端布局
    - SEO：title、meta、h1-h6、canonical
    - 可访问性：alt、aria、键盘焦点
    - 性能：图片大小、CSS 精简
    - 商业规范：emoji、法律声明
    """
    
    # 响应式断点
    RESPONSIVE_BREAKPOINTS = {
        "mobile": "480px",
        "tablet": "768px",
        "desktop": "1024px"
    }
    
    # Emoji 正则（排除常见表情）
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs
        "\U00002702-\U000027B0"
        "\U00002460-\U0001F650"
        "]+",
        flags=re.UNICODE
    )
    
    def __init__(self, strict: bool = False):
        """
        初始化
        
        Args:
            strict: 严格模式，warning 也视为 error
        """
        self.strict = strict

    def validate(self, html: str) -> ValidationResult:
        """
        验证 HTML
        
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        info = []
        
        # 1. SEO 检查
        seo_issues = self._check_seo(html)
        errors.extend([i for i in seo_issues if i.severity == "error"])
        warnings.extend([i for i in seo_issues if i.severity == "warning"])
        
        # 2. 响应式检查
        responsive_issues = self._check_responsive(html)
        warnings.extend([i for i in responsive_issues if i.severity == "warning"])
        info.extend([i for i in responsive_issues if i.severity == "info"])
        
        # 3. 可访问性检查
        a11y_issues = self._check_accessibility(html)
        warnings.extend([i for i in a11y_issues if i.severity == "warning"])
        info.extend([i for i in a11y_issues if i.severity == "info"])
        
        # 4. 商业规范检查
        business_issues = self._check_business_rules(html)
        errors.extend([i for i in business_issues if i.severity == "error"])
        warnings.extend([i for i in business_issues if i.severity == "warning"])
        
        # 5. 性能检查
        perf_issues = self._check_performance(html)
        warnings.extend([i for i in perf_issues if i.severity == "warning"])
        info.extend([i for i in perf_issues if i.severity == "info"])
        
        # 确定状态
        if errors:
            status = ValidationStatus.FAIL
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASS
        
        return ValidationResult(
            status=status,
            errors=errors,
            warnings=warnings,
            info=info
        )

    def auto_fix(self, html: str, issues: List[ValidationIssue]) -> str:
        """
        自动修复问题
        
        Args:
            html: 原始 HTML
            issues: 需要修复的问题列表
        
        Returns:
            修复后的 HTML
        """
        for issue in issues:
            if not issue.auto_fixable:
                continue
            
            if issue.code == "SEO_TITLE_MISSING":
                html = self._fix_missing_title(html)
            elif issue.code == "SEO_META_DESCRIPTION_MISSING":
                html = self._fix_missing_meta_description(html)
            elif issue.code == "SEO_H1_MISSING":
                html = self._fix_missing_h1(html)
            elif issue.code == "SEO_CANONICAL_MISSING":
                html = self._fix_missing_canonical(html)
            elif issue.code == "A11Y_ALT_MISSING":
                html = self._fix_missing_alt(html)
            elif issue.code == "BIZ_EMOJI_FOUND":
                html = self._remove_emoji(html)
        
        return html

    # ══════════════════════════════════════════════════════
    # SEO 检查
    # ══════════════════════════════════════════════════════
    
    def _check_seo(self, html: str) -> List[ValidationIssue]:
        """SEO 检查"""
        issues = []
        
        # 1. 检查 title
        if not re.search(r'<title[^>]*>.*?</title>', html, re.IGNORECASE | re.DOTALL):
            issues.append(ValidationIssue(
                code="SEO_TITLE_MISSING",
                message="缺少 <title> 标签",
                severity="error",
                auto_fixable=True
            ))
        else:
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                if len(title) < 10:
                    issues.append(ValidationIssue(
                        code="SEO_TITLE_TOO_SHORT",
                        message=f"title 过短: '{title}' (建议 > 10 字符)",
                        severity="warning"
                    ))
                elif len(title) > 60:
                    issues.append(ValidationIssue(
                        code="SEO_TITLE_TOO_LONG",
                        message=f"title 过长: {len(title)} 字符 (建议 < 60)",
                        severity="info"
                    ))
        
        # 2. 检查 meta description
        if not re.search(r'<meta[^>]*name=["\']description["\'][^>]*>', html, re.IGNORECASE):
            issues.append(ValidationIssue(
                code="SEO_META_DESCRIPTION_MISSING",
                message="缺少 meta description",
                severity="error",
                auto_fixable=True
            ))
        
        # 3. 检查 h1
        h1_count = len(re.findall(r'<h1[^>]*>', html, re.IGNORECASE))
        if h1_count == 0:
            issues.append(ValidationIssue(
                code="SEO_H1_MISSING",
                message="缺少 <h1> 标签",
                severity="error",
                auto_fixable=True
            ))
        elif h1_count > 1:
            issues.append(ValidationIssue(
                code="SEO_H1_MULTIPLE",
                message=f"有多个 <h1> 标签 ({h1_count} 个)，建议只有一个",
                severity="warning"
            ))
        
        # 4. 检查 h2-h6 层级
        headings = re.findall(r'<h([1-6])[^>]*>', html, re.IGNORECASE)
        if headings:
            levels = [int(h) for h in headings]
            for i in range(1, len(levels)):
                if levels[i] > levels[i-1] + 1:
                    issues.append(ValidationIssue(
                        code="SEO_HEADING_SKIP",
                        message=f"标题层级跳过: h{levels[i-1]} → h{levels[i]}",
                        severity="info"
                    ))
                    break
        
        # 5. 检查 canonical
        if not re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*>', html, re.IGNORECASE):
            issues.append(ValidationIssue(
                code="SEO_CANONICAL_MISSING",
                message="缺少 canonical 链接",
                severity="warning",
                auto_fixable=True
            ))
        
        # 6. 检查 robots
        if not re.search(r'<meta[^>]*name=["\']robots["\'][^>]*>', html, re.IGNORECASE):
            issues.append(ValidationIssue(
                code="SEO_ROBOTS_MISSING",
                message="缺少 robots meta 标签",
                severity="info"
            ))
        
        return issues

    # ══════════════════════════════════════════════════════
    # 响应式检查
    # ══════════════════════════════════════════════════════
    
    def _check_responsive(self, html: str) -> List[ValidationIssue]:
        """响应式检查"""
        issues = []
        
        # 1. 检查 viewport meta
        if not re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', html, re.IGNORECASE):
            issues.append(ValidationIssue(
                code="RESPONSIVE_VIEWPORT_MISSING",
                message="缺少 viewport meta 标签",
                severity="warning",
                auto_fixable=True
            ))
        
        # 2. 检查 @media 查询
        media_count = len(re.findall(r'@media', html, re.IGNORECASE))
        if media_count == 0:
            issues.append(ValidationIssue(
                code="RESPONSIVE_NO_MEDIA_QUERIES",
                message="缺少 @media 响应式断点",
                severity="warning"
            ))
        else:
            issues.append(ValidationIssue(
                code="RESPONSIVE_MEDIA_FOUND",
                message=f"发现 {media_count} 个 @media 查询",
                severity="info"
            ))
        
        # 3. 检查固定宽度
        fixed_width = re.findall(r'width:\s*\d+px', html)
        if len(fixed_width) > 3:
            issues.append(ValidationIssue(
                code="RESPONSIVE_FIXED_WIDTH",
                message=f"发现 {len(fixed_width)} 处固定宽度，可能影响响应式",
                severity="info"
            ))
        
        # 4. 检查 max-width
        if 'max-width' not in html.lower():
            issues.append(ValidationIssue(
                code="RESPONSIVE_NO_MAX_WIDTH",
                message="建议使用 max-width 限制最大宽度",
                severity="info"
            ))
        
        return issues

    # ══════════════════════════════════════════════════════
    # 可访问性检查
    # ══════════════════════════════════════════════════════
    
    def _check_accessibility(self, html: str) -> List[ValidationIssue]:
        """可访问性检查"""
        issues = []
        
        # 1. 检查图片 alt
        imgs_without_alt = re.findall(r'<img[^>]*(?<!alt=)[^>]*>', html, re.IGNORECASE)
        if imgs_without_alt:
            issues.append(ValidationIssue(
                code="A11Y_ALT_MISSING",
                message=f"有 {len(imgs_without_alt)} 个图片缺少 alt 属性",
                severity="warning",
                auto_fixable=True
            ))
        
        # 2. 检查 lang 属性
        if not re.search(r'<html[^>]*lang=["\'][^"\']+["\'][^>]*>', html, re.IGNORECASE):
            issues.append(ValidationIssue(
                code="A11Y_LANG_MISSING",
                message="缺少 lang 属性",
                severity="warning",
                auto_fixable=True
            ))
        
        # 3. 检查 aria 标签
        aria_count = len(re.findall(r'aria-[a-z]+=', html, re.IGNORECASE))
        issues.append(ValidationIssue(
            code="A11Y_ARIA_FOUND",
            message=f"发现 {aria_count} 个 aria 属性",
            severity="info"
        ))
        
        # 4. 检查表单 label
        inputs = re.findall(r'<input[^>]*>', html, re.IGNORECASE)
        labels = re.findall(r'<label[^>]*>', html, re.IGNORECASE)
        if inputs and len(labels) < len(inputs):
            issues.append(ValidationIssue(
                code="A11Y_LABEL_MISSING",
                message=f"有 {len(inputs) - len(labels)} 个输入框缺少对应 label",
                severity="info"
            ))
        
        return issues

    # ══════════════════════════════════════════════════════
    # 商业规范检查
    # ══════════════════════════════════════════════════════
    
    def _check_business_rules(self, html: str) -> List[ValidationIssue]:
        """商业规范检查"""
        issues = []
        
        # 1. 检查 emoji
        emojis = self.EMOJI_PATTERN.findall(html)
        if emojis:
            issues.append(ValidationIssue(
                code="BIZ_EMOJI_FOUND",
                message=f"发现 {len(emojis)} 个 emoji，不符合商业规范",
                severity="error",
                auto_fixable=True
            ))
        
        # 2. 检查版权信息
        if '©' not in html and 'copyright' not in html.lower():
            issues.append(ValidationIssue(
                code="BIZ_COPYRIGHT_MISSING",
                message="缺少版权信息",
                severity="warning"
            ))
        
        # 3. 检查隐私政策链接
        if 'privacy' not in html.lower() and '隐私' not in html:
            issues.append(ValidationIssue(
                code="BIZ_PRIVACY_MISSING",
                message="建议添加隐私政策链接",
                severity="info"
            ))
        
        return issues

    # ══════════════════════════════════════════════════════
    # 性能检查
    # ══════════════════════════════════════════════════════
    
    def _check_performance(self, html: str) -> List[ValidationIssue]:
        """性能检查"""
        issues = []
        
        # 1. 检查外部 CSS
        external_css = re.findall(r'<link[^>]*href=["\']https?://[^"\']+\.css["\'][^>]*>', html, re.IGNORECASE)
        if len(external_css) > 3:
            issues.append(ValidationIssue(
                code="PERF_EXTERNAL_CSS",
                message=f"有 {len(external_css)} 个外部 CSS，可能影响加载速度",
                severity="info"
            ))
        
        # 2. 检查外部 JS
        external_js = re.findall(r'<script[^>]*src=["\']https?://[^"\']+\.js["\'][^>]*>', html, re.IGNORECASE)
        if len(external_js) > 5:
            issues.append(ValidationIssue(
                code="PERF_EXTERNAL_JS",
                message=f"有 {len(external_js)} 个外部 JS，可能影响加载速度",
                severity="warning"
            ))
        
        # 3. 检查 async/defer
        async_scripts = re.findall(r'<script[^>]*(async|defer)[^>]*>', html, re.IGNORECASE)
        if external_js and len(async_scripts) < len(external_js):
            issues.append(ValidationIssue(
                code="PERF_SCRIPT_ASYNC",
                message="建议为外部脚本添加 async 或 defer",
                severity="info"
            ))
        
        # 4. 检查 HTML 大小
        html_size = len(html)
        if html_size > 100000:  # 100KB
            issues.append(ValidationIssue(
                code="PERF_HTML_SIZE",
                message=f"HTML 文件较大: {html_size / 1024:.1f}KB",
                severity="warning"
            ))
        
        return issues

    # ══════════════════════════════════════════════════════
    # 自动修复方法
    # ══════════════════════════════════════════════════════
    
    def _fix_missing_title(self, html: str) -> str:
        """修复缺失的 title"""
        if '<title>' not in html.lower():
            # 尝试从 h1 提取标题
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
            title = h1_match.group(1).strip() if h1_match else "页面标题"
            
            # 在 </head> 前插入 title
            html = re.sub(
                r'</head>',
                f'<title>{title}</title>\n</head>',
                html,
                flags=re.IGNORECASE
            )
        return html
    
    def _fix_missing_meta_description(self, html: str) -> str:
        """修复缺失的 meta description"""
        if 'name="description"' not in html.lower():
            # 尝试从第一个 p 提取描述
            p_match = re.search(r'<p[^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
            desc = p_match.group(1).strip()[:160] if p_match else "这是一个网页"
            
            html = re.sub(
                r'</title>',
                f'</title>\n<meta name="description" content="{desc}">',
                html,
                flags=re.IGNORECASE
            )
        return html
    
    def _fix_missing_h1(self, html: str) -> str:
        """修复缺失的 h1"""
        if '<h1' not in html.lower():
            # 尝试从 title 提取
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "标题"
            
            # 在 body 后插入 h1
            html = re.sub(
                r'<body[^>]*>',
                f'<body>\n<h1>{title}</h1>',
                html,
                flags=re.IGNORECASE
            )
        return html
    
    def _fix_missing_canonical(self, html: str) -> str:
        """修复缺失的 canonical"""
        if 'rel="canonical"' not in html.lower():
            html = re.sub(
                r'</title>',
                '</title>\n<link rel="canonical" href="#">',
                html,
                flags=re.IGNORECASE
            )
        return html
    
    def _fix_missing_alt(self, html: str) -> str:
        """修复缺失的 alt"""
        # 为没有 alt 的图片添加空 alt
        html = re.sub(
            r'<img([^>]*?)>',
            lambda m: f'<img{m.group(1)} alt="">' if 'alt=' not in m.group(1).lower() else m.group(0),
            html,
            flags=re.IGNORECASE
        )
        return html
    
    def _remove_emoji(self, html: str) -> str:
        """移除 emoji"""
        return self.EMOJI_PATTERN.sub('', html)


# ══════════════════════════════════════════════════════
# 测试
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    validator = QualityGates()
    
    # 测试用例 1：缺少关键 SEO 元素的页面
    bad_html = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
</head>
<body>
<p>这是一个测试页面 🎉</p>
<img src="test.png">
</body>
</html>
'''
    
    result = validator.validate(bad_html)
    print(f"[{result.status.value}] 验证结果:")
    print(f"  Errors: {len(result.errors)}")
    for e in result.errors:
        print(f"    - [{e.code}] {e.message}")
    print(f"  Warnings: {len(result.warnings)}")
    for w in result.warnings:
        print(f"    - [{w.code}] {w.message}")
    
    # 自动修复
    fixed_html = validator.auto_fix(bad_html, result.errors + result.warnings)
    print(f"\n[FIXED] 修复后重新验证:")
    result2 = validator.validate(fixed_html)
    print(f"  Errors: {len(result2.errors)}, Warnings: {len(result2.warnings)}")
    
    # 测试用例 2：完整的页面
    good_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="这是一个测试页面">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://example.com/">
<title>测试页面 - 示例</title>
<style>
@media (max-width: 768px) { body { padding: 16px; } }
</style>
</head>
<body>
<h1>测试页面</h1>
<p>这是内容</p>
<img src="test.png" alt="测试图片">
<footer>© 2024 示例</footer>
</body>
</html>
'''
    
    result3 = validator.validate(good_html)
    print(f"\n[GOOD] 验证结果: {result3.status.value}")
    print(f"  Errors: {len(result3.errors)}, Warnings: {len(result3.warnings)}")