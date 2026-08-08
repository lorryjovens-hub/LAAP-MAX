"""
hep_video_templates.py — HEP 视频风格模板系统 (零 token)
=========================================================
每个模板是一次"风格注入"的完整配置：
  - 主题 (HEP theme id)
  - 背景效果 (background effect)
  - 文字动效 (text effect)
  - 数据动效 (data effect)
  - 装饰叠层 (overlay)
  - 视觉强度 (subtle / moderate / dramatic)

工作时:
  hep_to_remotion 读 spec → 按模板注入效果代码 → 生成 TSX
  模板越用越多, 未来可通过"风格选择"切换, 不同视频不同观感

用法:
    from hep_video_templates import TEMPLATES, apply_template
    enriched_spec = apply_template(spec, "dark_tech_premium")
"""

# ═══════════════════════════════════════════════
# 模板定义
# ═══════════════════════════════════════════════

TEMPLATES = {
    "dark_tech_premium": {
        "name": "暗色科技 Premium",
        "description": "深色背景 + 渐变动画 + 粒子场 + 拆字文字",
        "theme": "dark_tech",
        "background": {
            "hero": "gradient_mesh",
            "data": "particle_field",
            "overview": "particle_field",
            "summary": "gradient_mesh",
            "outro": "gradient_mesh",
        },
        "background_params": {
            "gradient_mesh": {"color1": "#00d4ff", "color2": "#0a0a0f", "color3": "#7c7cff", "speed": 1.0},
            "particle_field": {"color": "#00d4ff", "count": 30, "speed": 1.0},
        },
        "text": {
            "hero": "split_reveal",
            "overview": "gradient_text",
            "summary": "glow_text",
            "outro": "gradient_text",
        },
        "data": "bar_chart",
        "overlay": "grid_lines",
        "overlay_params": {"color": "#00d4ff", "spacing": 60, "opacity": 0.04},
        "intensity": "moderate",
        "css_vars": {
            "--glow": "#00d4ff",
        },
    },

    "apple_glass": {
        "name": "苹果玻璃",
        "description": "浅色背景 + 光晕球 + 渐变文字 + 进度环",
        "theme": "glassmorphism",
        "background": {
            "hero": "glow_orb",
            "data": "gradient_mesh",
            "overview": "glow_orb",
            "summary": "gradient_mesh",
            "outro": "glow_orb",
        },
        "background_params": {
            "glow_orb": {"color": "#9d8cff", "count": 3, "intensity": 1.0},
            "gradient_mesh": {"color1": "#9d8cff", "color2": "#0a0a1a", "color3": "#ffffff", "speed": 0.5},
        },
        "text": {
            "hero": "gradient_text",
            "overview": "split_reveal",
            "summary": "typewriter",
            "outro": "gradient_text",
        },
        "data": "progress_ring",
        "overlay": "scan_line",
        "overlay_params": {"color": "#ffffff", "opacity": 0.02},
        "intensity": "subtle",
        "css_vars": {
            "--glow": "#9d8cff",
        },
    },

    "minimal_editorial": {
        "name": "极简杂志",
        "description": "纯白背景 + 几何网格 + 打字机 + 柱状图",
        "theme": "minimal_white",
        "background": {
            "hero": "geometric_pattern",
            "data": "wave_field",
            "overview": "geometric_pattern",
            "summary": "wave_field",
            "outro": "geometric_pattern",
        },
        "background_params": {
            "geometric_pattern": {"color": "#000000", "size": 40, "opacity": 0.04},
            "wave_field": {"color": "#000000", "height": 40, "speed": 0.8},
        },
        "text": {
            "hero": "typewriter",
            "overview": "split_reveal",
            "summary": "typewriter",
            "outro": "typewriter",
        },
        "data": "bar_chart",
        "overlay": None,
        "overlay_params": {},
        "intensity": "subtle",
        "css_vars": {},
    },

    "retro_wave": {
        "name": "复古赛博",
        "description": "终端绿 + 扫描线 + 发光文字 + 柱状图",
        "theme": "retro_terminal",
        "background": {
            "hero": "particle_field",
            "data": "gradient_mesh",
            "overview": "particle_field",
            "summary": "gradient_mesh",
            "outro": "particle_field",
        },
        "background_params": {
            "particle_field": {"color": "#33ff33", "count": 20, "speed": 0.5},
            "gradient_mesh": {"color1": "#33ff33", "color2": "#0d0d0d", "color3": "#33ff33", "speed": 0.5},
        },
        "text": {
            "hero": "glow_text",
            "overview": "typewriter",
            "summary": "glow_text",
            "outro": "glow_text",
        },
        "data": "bar_chart",
        "overlay": "scan_line",
        "overlay_params": {"color": "#33ff33", "opacity": 0.05},
        "intensity": "dramatic",
        "css_vars": {
            "--glow": "#33ff33",
        },
    },
}


def list_templates() -> list:
    """列出所有可用模板."""
    return [{"id": tid, **tpl} for tid, tpl in TEMPLATES.items()]


def get_template(template_id: str) -> dict:
    """按 id 获取模板, 不存在则返回默认."""
    return TEMPLATES.get(template_id, TEMPLATES["dark_tech_premium"])


def apply_template(spec: dict, template_id: str = "dark_tech_premium") -> dict:
    """把模板配置注入 spec.

    返回 enriched spec, 包含:
      spec["_template"]: 模板 id
      spec["_effects"]: 各章节的效果配置
      spec["_css_vars"]: 自定义 CSS 变量
    """
    tpl = get_template(template_id)
    enriched = dict(spec)
    enriched["_template"] = template_id
    enriched["theme"] = tpl["theme"]

    # 按章节配置效果
    section_effects = []
    for sec in spec.get("sections", []):
        st = sec["type"]
        # 背景
        bg_map = tpl.get("background", {})
        bg_id = bg_map.get(st, bg_map.get("hero", "gradient_mesh"))
        bg_params = tpl.get("background_params", {}).get(bg_id, {})
        # 文字
        txt_map = tpl.get("text", {})
        txt_id = txt_map.get(st, txt_map.get("hero", "split_reveal"))
        section_effects.append({
            "section_type": st,
            "background": {"id": bg_id, "params": bg_params},
            "text": {"id": txt_id},
            "data": {"id": tpl.get("data", "bar_chart")},
        })

    enriched["_effects"] = section_effects
    enriched["_overlay"] = {
        "id": tpl.get("overlay"),
        "params": tpl.get("overlay_params", {}),
    }
    enriched["_css_vars"] = tpl.get("css_vars", {})
    enriched["_intensity"] = tpl.get("intensity", "moderate")
    return enriched


# ═══════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    templates = list_templates()
    print(f"Templates: {len(templates)}")
    for t in templates:
        print(f"  [{t['id']}] {t['name']} — {t['description']}")
        print(f"    theme={t['theme']} intensity={t['intensity']}")

    # 测试 apply
    sample_spec = {
        "sections": [
            {"type": "hero", "title": "Test"},
            {"type": "stats", "items": []},
        ]
    }
    for tid in ["dark_tech_premium", "apple_glass", "minimal_editorial", "retro_wave"]:
        enriched = apply_template(sample_spec, tid)
        assert enriched["_template"] == tid
        assert len(enriched["_effects"]) == 2
        assert enriched["_effects"][0]["section_type"] == "hero"
        assert enriched["_effects"][0]["background"]["id"] is not None
        print(f"  apply [{tid}] OK: {len(enriched['_effects'])} effects")

    print("ALL TEMPLATE TESTS PASSED")