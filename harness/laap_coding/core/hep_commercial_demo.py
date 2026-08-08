#!/usr/bin/env python3
"""
HEP 商业级 0-Token 网站生成管线 - 端到端演示

工作流程：
1. 用户输入 Markdown 文案
2. ContentParser 解析为 UnifiedContentSpec
3. AssemblyEngine 组装为完整网站
4. QualityGates 检查并自动修复
5. 输出生产级 HTML 文件

使用方法：
    python hep_commercial_demo.py
"""

import os
import sys

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_parser import ContentParser
from assembly_engine import AssemblyEngine
from quality_gates import QualityGates

# ══════════════════════════════════════════════════════
# 用户输入：Markdown 文案
# ══════════════════════════════════════════════════════

USER_MARKDOWN = """
# 智擎科技

让 AI 为企业工作，零 Token 成本，零等待时间。

## 首页

### Hero
标题: 编译式 AI 平台
副标题: 从意图到实现，让网页自动生成，让代码持续进化
按钮: 免费试用 @ /trial

### 核心能力
- 零 Token 生成: 纯字符串拼接，运行时零 LLM 调用
- 智能解析: Markdown 自动转结构化内容
- 一键部署: 生成的网站可直接部署到 CDN
- 风格迁移: 从参考网站提取风格，批量应用

### 数据指标
- 95% 测试通过率
- 0 Token 运行时消耗
- <10ms 页面生成延迟
- 12+ 预设风格

### CTA
标题: 开始构建你的网站
按钮: 立即开始 @ /start

## 产品

### 编译式 AI 平台
标题: HEP 管线
副标题: 从文案到网站的零 Token 生成管线

### 功能列表
- ContentParser: Markdown → UnifiedContentSpec
- AssemblyEngine: 多页面组装 + 自动导航
- QualityGates: SEO + 响应式 + 可访问性检查

## 技术

### 架构
标题: 三层架构
副标题: 解析层 → 布局层 → 组装层

### 核心模块
- 意识架构: PSI 循环 + 记忆系统
- Harness 引擎: HEP 协议 + 零 Token 生成
- 代码平台: True RSI + Species Library

## 路线图

### 里程碑
- Q1: ContentParser 上线
- Q2: AssemblyEngine 商业化
- Q3: QualityGates 完善
- Q4: Web IDE 发布
"""

# ══════════════════════════════════════════════════════
# 管线执行
# ══════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("HEP 商业级 0-Token 网站生成管线")
    print("=" * 60)
    
    # 1. 解析 Markdown
    print("\n[1/4] ContentParser 解析 Markdown...")
    parser = ContentParser()
    spec = parser.parse_markdown(USER_MARKDOWN, brand="智擎科技", style="apple_cn")
    
    print(f"  [OK] 品牌: {spec.brand}")
    print(f"  [OK] 风格: {spec.style}")
    print(f"  [OK] 页面: {len(spec.pages)} 个")
    for page in spec.pages:
        print(f"       - {page.filename}: {len(page.sections)} sections")
    
    # 2. 组装网站
    print("\n[2/4] AssemblyEngine 组装网站...")
    engine = AssemblyEngine(style="apple_cn")
    files = engine.assemble_site(spec)
    
    print(f"  [OK] 生成: {len(files)} 个 HTML 文件")
    total_bytes = 0
    for f in files:
        size = len(f.content)
        total_bytes += size
        print(f"       - {f.filename}: {size:,} bytes")
    print(f"  [OK] 总大小: {total_bytes:,} bytes ({total_bytes/1024:.1f} KB)")
    
    # 3. 质量检查
    print("\n[3/4] QualityGates 质量检查...")
    validator = QualityGates()
    total_errors = 0
    total_warnings = 0
    fixed_files = []
    
    for f in files:
        result = validator.validate(f.content)
        total_errors += len(result.errors)
        total_warnings += len(result.warnings)
        
        if result.has_errors():
            # 自动修复
            f.content = validator.auto_fix(f.content, result.errors)
            fixed_files.append(f.filename)
    
    print(f"  [OK] 检查: {len(files)} 个文件")
    print(f"  [OK] 错误: {total_errors} 个 (已自动修复: {len(fixed_files)} 个)")
    print(f"  [OK] 警告: {total_warnings} 个")
    
    # 4. 输出文件
    print("\n[4/4] 输出生产级 HTML...")
    output_dir = os.path.join(os.path.dirname(__file__), "output_site")
    os.makedirs(output_dir, exist_ok=True)
    
    for f in files:
        path = os.path.join(output_dir, f.filename)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(f.content)
    
    print(f"  [OK] 输出目录: {output_dir}")
    print(f"  [OK] 文件数量: {len(files)} 个")
    
    # 5. 统计
    print("\n" + "=" * 60)
    print("管线执行完成")
    print("=" * 60)
    print(f"  输入: Markdown 文案 ({len(USER_MARKDOWN):,} 字符)")
    print(f"  输出: {len(files)} 个 HTML 文件 ({total_bytes:,} bytes)")
    print(f"  Token 消耗: 0 (零 LLM 调用)")
    print(f"  质量门禁: {total_errors} 错误已修复, {total_warnings} 警告")
    print("=" * 60)
    
    # 6. 预览第一个文件
    if files:
        print(f"\n[预览] {files[0].filename}:")
        print("-" * 60)
        print(files[0].content[:800])
        print("...")
        print("-" * 60)

if __name__ == "__main__":
    main()