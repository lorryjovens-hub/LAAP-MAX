# -*- coding: utf-8 -*-
"""测试视频管线模板系统"""
import json, sys
sys.path.insert(0, r'D:\LAAP\harness\laap_coding\core')
from video_pipeline.pipeline import list_templates, load_template, generate_tsx, template_to_default_props

# 1. 列出模板
print("=== 可用模板 ===")
for t in list_templates():
    print(f"  {t['id']:20s} {t['name']:16s} {t['description']}")

# 2. 加载模板
tpl = load_template("dark-tech")
print(f"\n=== 暗色科技风模板 ===")
print(f"  主题: {tpl['theme']}")
print(f"  动画: {tpl['animations']}")
print(f"  背景: {tpl['background']}")

# 3. 生成默认 props
props = template_to_default_props(tpl)
print(f"\n  defaultProps: {json.dumps(props, indent=2)[:200]}...")

# 4. 创建 spec 并生成 TSX
spec = {
    "title": "管线测试视频",
    "theme": "dark_tech",
    "sections": [
        {"type": "hero", "title": "测试标题", "subtitle": "测试副标题", "badge": "v2.0", "cta": "开始"},
        {"type": "stats", "title": "核心数据", "items": [
            {"number": "99%", "label": "成功率"},
            {"number": "57x", "label": "速度提升"},
        ]},
        {"type": "grid", "title": "功能列表", "cards": [
            {"title": "功能A", "desc": "描述A"},
            {"title": "功能B", "desc": "描述B"},
        ]},
        {"type": "hero", "title": "感谢观看", "badge": "", "cta": "再见", "height": "60vh"},
    ],
}

tsx = generate_tsx(spec, "dark-tech", "test-video")
print(f"\n=== TSX 生成 ===")
print(f"  长度: {len(tsx)} 字符")
print(f"  包含 SplitText: {'SplitText' in tsx}")
print(f"  包含 StaggerContainer: {'StaggerContainer' in tsx}")
print(f"  包含 ParticleBackground: {'ParticleBackground' in tsx}")
print(f"  包含 useEntrance: {'useEntrance' in tsx}")
print(f"  包含 entranceStyle: {'entranceStyle' in tsx}")
print(f"  模板 props 正确: {'TEMPLATE_PROPS' in tsx}")

# 5. 验证所有模板
for t in list_templates():
    tpl2 = load_template(t['id'])
    tsx2 = generate_tsx(spec, t['id'], f"test-{t['id']}")
    assert tpl2['id'] == t['id']
    assert len(tsx2) > 1000
    print(f"  [{t['id']}] TSX: {len(tsx2)} char")

print("\nALL TESTS PASSED")