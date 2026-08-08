"""
hep_to_remotion.py — HEP Spec → Remotion 视频转译器 (零 token)
================================================================
把 HEP 0tokens 引擎的页面 Spec 转译为 Remotion Composition:
  - THEMES → VideoProps (primaryColor/backgroundColor/textColor/accentColor)
  - sections → 视频章节 (hero→片头, stats→数据卡, grid→图标卡, cta→片尾)
  - 输出 {Name}Video.tsx + podcast.txt 初稿 + Root.tsx 注册片段

配合 video-podcast-maker 流水线:
  hep_to_remotion → Remotion 项目 → podcast.txt 人工打磨 → ttscn TTS
  → timing.json → remotion render → 4K 成片

设计原则:
  - 零 token: 全部规则映射, 无 LLM 调用
  - 接口对齐: 生成的 TSX 消费与官方模板相同的 VideoProps/useTiming
  - 音频主时钟: 章节时长完全由 TTS 后的 timing.json 驱动

用法:
    python hep_to_remotion.py "自然语言主题" [--name video-name] [--project 路径]
"""

import json
import os
import re
import sys

# ═══════════════════════════════════════════════
# 1. 主题映射 — HEP THEMES css 变量 → Remotion VideoProps
# ═══════════════════════════════════════════════

THEME_TO_PROPS = {
    "apple_dark": {
        "primaryColor": "#7c7cff", "backgroundColor": "#000000",
        "textColor": "#f5f5f7", "accentColor": "#7c7cff",
    },
    "apple_light": {
        "primaryColor": "#7c7cff", "backgroundColor": "#ffffff",
        "textColor": "#1d1d1f", "accentColor": "#7c7cff",
    },
    "minimal_white": {
        "primaryColor": "#000000", "backgroundColor": "#ffffff",
        "textColor": "#111111", "accentColor": "#000000",
    },
    "dark_tech": {
        "primaryColor": "#00d4ff", "backgroundColor": "#0a0a0f",
        "textColor": "#e0e0ff", "accentColor": "#7c7cff",
    },
    "warm_earth": {
        "primaryColor": "#e8a87c", "backgroundColor": "#1a1410",
        "textColor": "#f0e0d0", "accentColor": "#e8a87c",
    },
    "glassmorphism": {
        "primaryColor": "#9d8cff", "backgroundColor": "#0a0a1a",
        "textColor": "#ffffff", "accentColor": "#ffffff",
    },
    "retro_terminal": {
        "primaryColor": "#33ff33", "backgroundColor": "#0d0d0d",
        "textColor": "#33ff33", "accentColor": "#33ff33",
    },
}

DEFAULT_PROPS = THEME_TO_PROPS["apple_dark"]


def theme_to_props(theme_id: str) -> dict:
    """HEP 主题 id → Remotion VideoProps 颜色值."""
    return THEME_TO_PROPS.get(theme_id, DEFAULT_PROPS)


# ═══════════════════════════════════════════════
# 2. 图标映射 — HEP 卡片标题关键词 → lucide 图标名
#    (视频 IconCard 用 Icon 组件, 与 HEP 的 lucide 体系同源)
# ═══════════════════════════════════════════════

ICON_KEYWORDS = [
    ("cpu", ["算力", "计算", "芯片", "性能", "引擎", "gpu", "模型", "大模型", "智能", "ai", "神经"]),
    ("shield", ["安全", "防护", "合规", "隐私", "加密", "认证"]),
    ("plug", ["api", "接口", "集成", "连接", "对接", "协议"]),
    ("bar-chart", ["数据", "分析", "统计", "指标", "看板", "报表"]),
    ("rocket", ["启动", "加速", "快速", "部署", "发布", "上线"]),
    ("zap", ["自动化", "工作流", "流程", "效率", "实时"]),
    ("globe", ["全球", "云", "网络", "协作", "平台"]),
    ("users", ["团队", "协作", "用户", "社区", "客户"]),
    ("dollar-sign", ["定价", "价格", "方案", "付费", "套餐"]),
    ("smartphone", ["移动", "app", "应用", "手机"]),
    ("layers", ["框架", "系统", "架构"]),
    ("lightbulb", ["概念", "思路", "想法", "观点", "知识"]),
    ("sparkles", []),  # 兜底
]


def pick_icon(text: str) -> str:
    """标题/描述关键词 → lucide 图标名 (规则匹配, 零 token)."""
    low = text.lower()
    for icon, kws in ICON_KEYWORDS:
        for kw in kws:
            if kw in low:
                return icon
    return "sparkles"


# ═══════════════════════════════════════════════
# 3. HEP section → 视频章节映射
# ═══════════════════════════════════════════════

def hep_section_to_video(sec: dict, idx: int) -> dict:
    """HEP section → 视频章节数据 (name 与 podcast.txt 的 [SECTION] 对齐).

    命名规则: 同名章节加 -N 序号, SectionComponent 按 base name 匹配.
    """
    t = sec.get("type", "grid")

    if t == "hero":
        # cta 型 hero (60vh) → 片尾; 主 hero → 片头
        if sec.get("height") == "60vh" or (sec.get("badge") == "" and sec.get("cta")):
            return {
                "name": "outro",
                "title": sec.get("title", "感谢观看"),
                "subtitle": sec.get("subtitle", ""),
                "cta": sec.get("cta", ""),
            }
        return {
            "name": "hero",
            "title": sec.get("title", ""),
            "subtitle": sec.get("subtitle", ""),
            "badge": sec.get("badge", ""),
        }

    if t == "stats":
        items = []
        for it in sec.get("items", []):
            raw = it.get("number", "0")
            # 解析数字 + 后缀: "79%" → value=79 suffix="%", "57×" → value=57 suffix="×"
            m = re.match(r"^([\d.]+)(.*)$", raw)
            val = float(m.group(1)) if m else 0
            suffix = m.group(2).strip() if m else ""
            items.append({"value": val, "suffix": suffix, "label": it.get("label", "")})
        return {
            "name": f"data-{idx}",
            "items": items,
            "title": sec.get("title", "核心数据"),
        }

    if t == "pipeline":
        steps = sec.get("items", [])
        return {
            "name": f"overview-{idx}",
            "title": sec.get("title", "实现路径"),
            "items": [
                {"icon": pick_icon(s), "title": f"第 {i+1} 步", "description": s}
                for i, s in enumerate(steps)
            ],
        }

    if t == "grid":
        cards = sec.get("cards", [])
        return {
            "name": f"overview-{idx}",
            "title": sec.get("title", ""),
            "label": sec.get("label", ""),
            "items": [
                {"icon": pick_icon(c.get("title", "") + c.get("desc", "")),
                 "title": c.get("title", ""),
                 "description": c.get("desc", "")}
                for c in cards
            ],
        }

    if t == "custom_html":
        return {
            "name": f"summary-{idx}",
            "title": sec.get("title", "总结"),
            "html": sec.get("html", "")[:300],
        }

    # 兜底
    return {"name": f"content-{idx}", "title": sec.get("title", ""), "subtitle": sec.get("subtitle", "")}


def spec_to_video_sections(spec: dict) -> list:
    """整个 spec → 视频章节列表."""
    return [hep_section_to_video(sec, i) for i, sec in enumerate(spec.get("sections", []))]


# ═══════════════════════════════════════════════
# 4. TSX 生成 (占位符替换, 避免花括号冲突)
# ═══════════════════════════════════════════════

TSX_TEMPLATE = '''/**
 * __VIDEO_NAME__Video — 由 hep_to_remotion.py 从 HEP spec 自动生成 (零 token)
 * 数据来源: HEP 0tokens 引擎的页面 Spec, 视觉语言与网页版共用 THEMES。
 * 流程: podcast.txt 打磨 → ttscn TTS → timing.json → remotion render
 */

import React from "react";
import { Audio, staticFile, AbsoluteFill } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import type { VideoProps } from "./Root";

import {
  Scale4K, FullBleedLayout, PaddedLayout, useEntrance, getPresentation,
  ChapterProgressBar, Subtitles, IconCard, StatCounter, Icon, useTiming,
  SILENT_FRAMES,
} from "./components";
import type { TimingSection } from "./components";

// __THEME_HINT__
// ── HEP 数据 (由 hep_to_remotion.py 生成) ──
const HEP_TITLE = __TITLE_JSON__;
const HEP_SECTIONS = __SECTIONS_JSON__;

const baseName = (name: string) => name.replace(/-\\d+$/, "");

const SectionComponent = ({
  section, props,
}: {
  section: TimingSection; props: VideoProps;
}) => {
  const { opacity, translateY, scale } = useEntrance(props.enableAnimations);
  const animStyle = { opacity, transform: `translateY(${translateY}px) scale(${scale})` };
  const data = HEP_SECTIONS.find((s) => s.name === section.name) || {};
  const base = baseName(section.name);
  const v = props.orientation === "vertical";
  const sectionPadding = v ? "120px 60px 160px" : "60px 100px 120px";

  switch (base) {
    case "hero": {
      return (
        <FullBleedLayout bg={props.backgroundColor}>
          <div style={{
            position: "absolute", inset: 0,
            background: `radial-gradient(ellipse at 50% 40%, ${props.primaryColor}12 0%, transparent 70%)`,
          }} />
          <div style={{
            position: "absolute", inset: 0,
            display: "flex", flexDirection: "column",
            justifyContent: "center", alignItems: "center", textAlign: "center",
            padding: v ? "0 60px" : 0, ...animStyle,
          }}>
            {(data as any).badge ? (
              <div style={{
                fontSize: v ? 28 : 22, fontWeight: 600, color: props.accentColor,
                background: `${props.primaryColor}12`, border: `1px solid ${props.primaryColor}25`,
                borderRadius: 999, padding: "8px 24px", marginBottom: v ? 32 : 24,
              }}>{(data as any).badge}</div>
            ) : null}
            <h1 style={{
              fontSize: props.titleSize, fontWeight: 800, color: props.primaryColor,
              lineHeight: v ? 1.3 : 1.1, textShadow: `0 2px 16px ${props.primaryColor}15`,
            }}>
              {(data as any).title || HEP_TITLE}
            </h1>
            <p style={{
              fontSize: props.subtitleSize, color: props.textColor, marginTop: v ? 32 : 20,
              opacity: 0.6, fontWeight: 500,
            }}>
              {(data as any).subtitle}
            </p>
          </div>
        </FullBleedLayout>
      );
    }

    case "data": {
      return (
        <PaddedLayout bg={props.backgroundColor} orientation={props.orientation}>
          <div style={{
            position: "absolute", inset: 0, padding: sectionPadding,
            display: "flex", flexDirection: "column", justifyContent: "center", ...animStyle,
          }}>
            <h2 style={{
              fontSize: v ? 72 : 80, fontWeight: 700, marginBottom: v ? 48 : 40,
              color: props.primaryColor, textAlign: "center",
            }}>{(data as any).title || "核心数据"}</h2>
            <StatCounter props={props} items={((data as any).items || []).slice(0, 4)} />
          </div>
        </PaddedLayout>
      );
    }

    case "overview": {
      return (
        <PaddedLayout bg={props.backgroundColor} orientation={props.orientation}>
          <div style={{
            position: "absolute", inset: 0, padding: sectionPadding,
            display: "flex", flexDirection: "column", justifyContent: "center", ...animStyle,
          }}>
            <h2 style={{
              fontSize: v ? 64 : 64, fontWeight: 700, marginBottom: v ? 32 : 28,
              color: props.primaryColor, textAlign: "center",
            }}>{(data as any).title || "核心内容"}</h2>
            <div style={{
              display: "flex", flexDirection: "column", gap: v ? 24 : 20,
              width: "100%", maxWidth: v ? undefined : 1000, margin: "0 auto",
            }}>
              {((data as any).items || []).slice(0, 6).map((item: any, i: number) => (
                <IconCard key={i} props={props} icon={item.icon} title={item.title}
                  description={item.description} delay={i * 6} />
              ))}
            </div>
          </div>
        </PaddedLayout>
      );
    }

    case "outro": {
      return (
        <FullBleedLayout bg={props.backgroundColor}>
          <div style={{
            position: "absolute", inset: 0, display: "flex", flexDirection: "column",
            justifyContent: "center", alignItems: "center", ...animStyle,
          }}>
            <h2 style={{
              fontSize: v ? 72 : 80, fontWeight: 700, color: props.textColor,
              marginBottom: v ? 64 : 48,
            }}>{(data as any).title || "感谢观看"}</h2>
            <div style={{ display: "flex", gap: v ? 56 : 40, flexDirection: v ? "column" : "row" }}>
              {[
                { icon: "thumbs-up", text: "点赞" },
                { icon: "star", text: "收藏" },
                { icon: "bell", text: "关注" },
              ].map((item, i) => (
                <div key={i} style={{ textAlign: "center" }}>
                  <Icon name={item.icon} size={v ? 80 : 64} color={props.accentColor} animate="bounce" delay={i * 10} />
                  <div style={{ fontSize: v ? 32 : 26, color: "rgba(0,0,0,0.5)", marginTop: 10 }}>{item.text}</div>
                </div>
              ))}
            </div>
            <p style={{
              fontSize: v ? 44 : 36, color: props.primaryColor, marginTop: v ? 64 : 48,
            }}>{(data as any).cta || "下期再见！"}</p>
          </div>
        </FullBleedLayout>
      );
    }

    default: {
      return (
        <PaddedLayout bg={props.backgroundColor} orientation={props.orientation}>
          <div style={{
            position: "absolute", inset: 0, padding: sectionPadding,
            display: "flex", flexDirection: "column", justifyContent: "center", ...animStyle,
          }}>
            <h2 style={{
              fontSize: v ? 72 : 80, fontWeight: 700, color: props.primaryColor,
              textAlign: "center",
            }}>{(data as any).title || section.name}</h2>
            <p style={{ fontSize: v ? 34 : 30, color: props.textColor, opacity: 0.5,
              marginTop: 12, textAlign: "center" }}>{(data as any).subtitle || ""}</p>
          </div>
        </PaddedLayout>
      );
    }
  }
};

// 主视频组件 — 音频主时钟, 时长由 timing.json 驱动
export const __VIDEO_NAME__Video = (props: VideoProps) => {
  const timing = useTiming();
  const sections = timing.sections;
  const transitionFrames = props.transitionDuration;

  const lastNonSilentIdx = sections.map((s) => !s.is_silent).lastIndexOf(true);
  const renderSections = sections.filter((s, i) => !(s.is_silent && i <= lastNonSilentIdx));
  const transitionCount = Math.max(0, renderSections.length - 1);
  const effectiveTransitionFrames =
    props.transitionType !== "none" && transitionFrames > 0 ? transitionFrames : 0;
  const trailingSilentCount = renderSections.filter((s) => s.is_silent).length;
  const silentBudget = trailingSilentCount * SILENT_FRAMES;

  const originalTotal = renderSections.reduce(
    (sum, s) => sum + (s.is_silent ? 0 : s.duration_frames), 0,
  );
  const targetTotal =
    timing.total_frames + transitionCount * effectiveTransitionFrames + silentBudget;
  const scaleFactor =
    originalTotal > 0 ? (targetTotal - silentBudget) / originalTotal : 1;

  const compensatedSections = renderSections.map((s) => {
    if (s.is_silent) return { ...s, duration_frames: SILENT_FRAMES };
    return { ...s, duration_frames: Math.max(15, Math.round(s.duration_frames * scaleFactor)) };
  });

  const scaledTotal = compensatedSections.reduce((sum, s) => sum + s.duration_frames, 0);
  const diff = targetTotal - scaledTotal;
  if (diff !== 0) {
    let absorbed = false;
    for (let i = compensatedSections.length - 1; i >= 0; i--) {
      const s = compensatedSections[i];
      if (!s.is_silent) {
        s.duration_frames = Math.max(15, s.duration_frames + diff);
        absorbed = true;
        break;
      }
    }
    if (!absorbed && compensatedSections.length > 0) {
      const last = compensatedSections[compensatedSections.length - 1];
      last.duration_frames = Math.max(15, last.duration_frames + diff);
    }
  }

  return (
    <AbsoluteFill style={{ backgroundColor: props.backgroundColor }}>
      <Scale4K orientation={props.orientation}>
        <TransitionSeries>
          {compensatedSections.map((section, i) => (
            <React.Fragment key={`${section.name}-${i}`}>
              <TransitionSeries.Sequence durationInFrames={section.duration_frames}>
                <SectionComponent section={section} props={props} />
              </TransitionSeries.Sequence>
              {i < renderSections.length - 1 && transitionFrames > 0 && props.transitionType !== "none" && (
                <TransitionSeries.Transition
                  presentation={getPresentation(props.transitionType)}
                  timing={linearTiming({ durationInFrames: transitionFrames })}
                />
              )}
            </React.Fragment>
          ))}
        </TransitionSeries>
      </Scale4K>

      <ChapterProgressBar props={props} chapters={timing.sections} />
      <Subtitles src={staticFile("podcast_audio.srt")} />

      {props.bgmVolume > 0 && (
        <Audio src={staticFile("bgm.mp3")} volume={props.bgmVolume} />
      )}
      <Audio src={staticFile("podcast_audio.wav")} />
    </AbsoluteFill>
  );
};

export default __VIDEO_NAME__Video;
'''


def to_pascal(name: str) -> str:
    """video-name → VideoName (PascalCase)."""
    parts = re.split(r"[-_\s]+", name.strip())
    return "".join(p.capitalize() for p in parts if p) or "Video"


def build_video_tsx(spec: dict, video_name: str) -> str:
    """HEP spec → 完整 Video.tsx 源码字符串.

    如果 spec 包含 _effects/_overlay/_css_vars (来自模板系统),
    自动注入动效代码 (CSS 动画、背景效果、装饰叠层).
    """
    props = theme_to_props(spec.get("theme", "apple_dark"))
    vsecs = spec_to_video_sections(spec)

    theme_hint = f"// 主题 props (HEP theme: {spec.get('theme', 'apple_dark')})"
    for k, v in props.items():
        theme_hint += f"\n//   {k}: {v}"

    tsx = TSX_TEMPLATE
    tsx = tsx.replace("__VIDEO_NAME__", to_pascal(video_name))
    tsx = tsx.replace("__THEME_HINT__", theme_hint)
    tsx = tsx.replace("__TITLE_JSON__", json.dumps(spec.get("title", ""), ensure_ascii=False))
    tsx = tsx.replace("__SECTIONS_JSON__", json.dumps(vsecs, ensure_ascii=False, indent=2))

    # ── 模板效果注入 (如果 spec 有 _effects) ──
    effects = spec.get("_effects")
    if effects:
        tsx = _inject_template_effects(tsx, spec)

    return tsx


def _inject_template_effects(tsx: str, spec: dict) -> str:
    """把模板效果注入生成的 TSX.

    注入:
      1. CSS 动画定义 (hep_video_effects.CSS_ANIMATIONS)
      2. 装饰叠层 (overlay) 注入到 Video 组件
      3. 背景效果注入到 SectionComponent 各 case
    """
    from hep_video_effects import CSS_ANIMATIONS, get_effect

    overlay = spec.get("_overlay", {})
    css_vars = spec.get("_css_vars", {})
    effects = spec.get("_effects", [])

    injection = []

    # 1. CSS 变量注入 (在文件顶部, 全局生效)
    if css_vars:
        var_block = ":root {" + "".join(f"{k}: {v};" for k, v in css_vars.items()) + "}"
        injection.append(f"// CSS 变量 (模板系统)\n{var_block}")

    # 2. CSS 动画注入 (在 SectionComponent 之前)
    injection.append(f"// CSS 动画 (效果库)\nconst EFFECTS_CSS = `{CSS_ANIMATIONS}`;")

    # 3. 装饰叠层注入 (叠加层, 每个 section 的 overlay 由 section 自己处理)
    if overlay and overlay.get("id"):
        ov = get_effect(overlay["id"])
        if ov:
            ov_html = ov["generate"](**overlay.get("params", {}))
            injection.append(f"// 装饰叠层\nconst OVERLAY_HTML = `{ov_html}`;")

    # 在 TSX 中的 _theme_hint_ 位置之后注入
    # 找到 HEP_SECTIONS 定义前的注释, 插入效果代码
    insert_pos = tsx.find("const HEP_SECTIONS =")
    if insert_pos > 0:
        code = "\n".join(injection) + "\n"
        tsx = tsx[:insert_pos] + code + tsx[insert_pos:]

    # 4. 注入 <style> 到每个 section 的背景风格
    # 修改 SectionComponent 中的各 case, 在返回元素前添加背景效果
    # 最简单: 在 SectionComponent 的 return 前添加背景效果

    # 5. 注入 CSS 变量到 Video 组件的最外层
    # 在 <AbsoluteFill> 上添加 style 传入 css vars
    # 但 template 里已经用了 props 的背景色, 所以直接注入 style 标签
    bg_style = '<style>{EFFECTS_CSS}</style>'
    tsx = tsx.replace(
        'return (\n    <AbsoluteFill style={{ backgroundColor: props.backgroundColor }}>',
        f'return (\n    <>\n      {bg_style}\n    <AbsoluteFill style={{{{ backgroundColor: props.backgroundColor }}}}>',
    )
    # 补上对应的闭合 </>
    tsx = tsx.replace(
        '</AbsoluteFill>\n  );\n};\n\nexport default __VIDEO_NAME__Video;',
        '</AbsoluteFill>\n    </>\n  );\n};\n\nexport default __VIDEO_NAME__Video;',
    )

    # 6. 给每个 scored section 添加背景效果
    # 在 SectionComponent 的 switch 各 case 中, 在 return 前添加背景 overlay
    bg_replacement = {}
    for i, ef in enumerate(effects):
        bg_id = ef.get("background", {}).get("id")
        if bg_id:
            bg_effect = get_effect(bg_id)
            if bg_effect:
                bg_params = ef.get("background", {}).get("params", {})
                bg_html = bg_effect["generate"](**bg_params)
                bg_replacement[i] = bg_html

    # 用背景效果替换每个 section 的装饰元素
    for i, ef in enumerate(effects):
        if i in bg_replacement and ef["section_type"] == "hero":
            # 替换 hero 的 radial gradient 装饰
            old = "radial-gradient(ellipse at 50% 40%, ${props.primaryColor}12 0%, transparent 70%)"
            if old in tsx:
                tsx = tsx.replace(old, bg_replacement[i])
            # 也替换 decorative circle
            old_circle = '<div style={{position:"absolute",top:-120,right:-80,width:400,height:400,borderRadius:"50%",background:`${props.primaryColor}08`,}} />'
            if old_circle in tsx:
                tsx = tsx.replace(old_circle, '')

        # 为 data 和 overview 添加背景效果
        if i in bg_replacement and ef["section_type"] in ("stats", "grid"):
            # 在 PaddedLayout 的 bg 参数后添加背景
            bg_html = bg_replacement[i]
            # 在 PaddedLayout 的 <div 前插入背景
            old = '<PaddedLayout bg={props.backgroundColor}'
            new = f'<PaddedLayout bg={{{{props.backgroundColor}}}}'
            # 找到第 i 次出现的 PaddedLayout
            count = 0
            for st in ["stats", "grid"]:
                if ef["section_type"] == st:
                    count += 1
            # 用替换方式
            tsx = _insert_background_after_opening(tsx, bg_html, count)

    return tsx


def _insert_background_after_opening(tsx: str, bg_html: str, occurrence: int = 1) -> str:
    """在指定索引的 PaddedLayout 开场后插入背景 HTML."""
    pattern = '<PaddedLayout bg={props.backgroundColor}'
    idx = -1
    for _ in range(occurrence):
        idx = tsx.find(pattern, idx + 1)
        if idx < 0:
            return tsx
    # 找到该 PaddedLayout 的 > 结束
    close = tsx.find(">", idx)
    if close > 0:
        tsx = tsx[:close + 1] + bg_html + tsx[close + 1:]
    return tsx


# ═══════════════════════════════════════════════
# 5. podcast.txt 初稿生成
#    (用户打磨后 → ttscn TTS → timing.json, section 名与 TSX 对齐)
# ═══════════════════════════════════════════════

def build_podcast_txt(spec: dict) -> str:
    """HEP spec → podcast.txt 旁白初稿 (带 [SECTION] 标记)."""
    title = spec.get("title", "本期主题")
    vsecs = spec_to_video_sections(spec)

    lines = [
        "# 播客脚本初稿 — 由 hep_to_remotion.py 从 HEP spec 生成",
        "# 请人工打磨: 默读三遍, 砍废话, 数字/术语单独核对, 中文约 280 字/分钟",
        "",
        "[SECTION:hero]",
        f"# 开场 — 标题: {title}",
        f"欢迎来到本期视频！今天我们来聊聊{title}。",
        "",
    ]

    for v in vsecs:
        name = v["name"]
        base = re.sub(r"-\d+$", "", name)
        if base == "hero":
            if v.get("subtitle"):
                lines.append(f"{v['subtitle']}")
                lines.append("")
        elif base == "data":
            lines.append(f"[SECTION:{name}]")
            lines.append("# 核心数据 — 数字滚动画面")
            lines.append("在开始之前，先看几组关键数字：")
            for it in v.get("items", [])[:4]:
                lines.append(f"- {it['number']} — {it['label']}")
            lines.append("")
        elif base == "overview":
            lines.append(f"[SECTION:{name}]")
            lines.append(f"# 内容区块 — {v.get('title', '')}")
            lines.append(f"接下来，我们来看{v.get('title', '核心内容')}。")
            for it in v.get("items", [])[:6]:
                lines.append(f"- {it['title']}：{it['description']}")
            lines.append("")
        elif base == "outro":
            lines.append(f"[SECTION:{name}]")
            lines.append("# 结尾")
            lines.append("好了，今天的分享就到这里。如果你觉得有帮助，记得点赞、收藏、关注！")
            lines.append(f"{v.get('cta', '我们下期再见！')}")
            lines.append("")
        else:
            lines.append(f"[SECTION:{name}]")
            lines.append(f"# 内容区块 — {v.get('title', '')}")
            lines.append(f"接下来，我们来聊{v.get('title', '相关内容')}。")
            lines.append("")

    lines.append("[SECTION:summary]")
    lines.append("# 总结")
    lines.append("让我们快速总结一下今天的要点。")
    lines.append("核心结论：把复杂的问题拆开，一步一步解决。")
    lines.append("")

    if not any(re.sub(r"-\d+$", "", v["name"]) == "outro" for v in vsecs):
        lines.append("[SECTION:outro]")
        lines.append("# 结尾")
        lines.append("感谢观看，我们下期再见！")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════
# 6. CLI — 自然语言 → Remotion 项目文件
# ═══════════════════════════════════════════════

DEFAULT_PROJECT = r"C:\Users\user\Desktop\OH-WorkSpace\remotion-project"


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    text = args[0]
    name = "hep-video"
    project = DEFAULT_PROJECT

    for i, a in enumerate(args):
        if a == "--name" and i + 1 < len(args):
            name = args[i + 1]
        if a == "--project" and i + 1 < len(args):
            project = args[i + 1]

    # 1. HEP 引擎: 自然语言 → spec (零 token)
    try:
        from intent_mapper import IntentMapper
        spec = IntentMapper().parse(text)
    except ImportError:
        print("ERROR: intent_mapper not found. Run from core/ or set PYTHONPATH.")
        sys.exit(1)

    # 2. 生成 TSX
    tsx = build_video_tsx(spec, name)
    tsx_path = os.path.join(project, "src", "remotion", f"{to_pascal(name)}Video.tsx")
    os.makedirs(os.path.dirname(tsx_path), exist_ok=True)
    with open(tsx_path, "w", encoding="utf-8") as f:
        f.write(tsx)

    # 3. 生成 podcast.txt 初稿
    videos_dir = os.path.join(project, "videos", name)
    os.makedirs(videos_dir, exist_ok=True)
    txt_path = os.path.join(videos_dir, "podcast.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(build_podcast_txt(spec))

    # 4. Root.tsx 注册片段 (含 HEP 主题 props)
    comp_name = to_pascal(name)
    props = theme_to_props(spec.get("theme", "apple_dark"))
    props_lines = ",\n".join(f'          {k}: "{v}",' for k, v in props.items())
    reg_hint = (
        f"\n// 在 src/remotion/Root.tsx 中注册 (参考模板头部注释):\n"
        f'//   import {{ Video as {comp_name}Video }} from "./{comp_name}Video";\n'
        f'//   <Composition id="{comp_name}" component={{{comp_name}Video}}\n'
        f'//     durationInFrames={{300}} calculateMetadata={{calculateVideoMetadata}} fps={{30}}\n'
        f'//     width={{3840}} height={{2160}} schema={{videoSchema}}\n'
        f"//     defaultProps={{\n"
        f"//       ...defaultVideoProps,\n"
        f"{props_lines}\n"
        f"//     }} />\n"
    )
    with open(os.path.join(videos_dir, "root_registration.txt"), "w", encoding="utf-8") as f:
        f.write(reg_hint)

    print(f"OK: {tsx_path}")
    print(f"OK: {txt_path}")
    print(f"OK: {os.path.join(videos_dir, 'root_registration.txt')}")
    print(f"spec: theme={spec.get('theme')} sections={[s['type'] for s in spec['sections']]}")
    print(f"video sections: {[v['name'] for v in spec_to_video_sections(spec)]}")


# ═══════════════════════════════════════════════
# 7. 测试
# ═══════════════════════════════════════════════

if __name__ == "__main__" and len(sys.argv) > 1:
    main()
elif __name__ == "__main__":
    # 自测
    spec = {
        "title": "AI Agent 入门指南",
        "theme": "dark_tech",
        "sections": [
            {"type": "hero", "title": "AI Agent 入门指南", "subtitle": "从零到一理解智能体", "badge": "科普系列", "cta": "开始学习"},
            {"type": "stats", "items": [
                {"number": "87%", "label": "企业采用率"},
                {"number": "3x", "label": "效率提升"},
            ]},
            {"type": "grid", "title": "核心概念", "label": "CONCEPTS", "cards": [
                {"title": "大模型", "desc": "语言理解与生成的基座"},
                {"title": "工具调用", "desc": "Agent 与外部系统交互"},
                {"title": "记忆系统", "desc": "跨会话的知识保持"},
            ]},
            {"type": "hero", "title": "开始你的 Agent 之旅", "subtitle": "", "badge": "", "cta": "立即开始", "height": "60vh"},
        ],
    }

    tsx = build_video_tsx(spec, "ai-agent-guide")
    assert "__TITLE_JSON__" not in tsx and "__SECTIONS_JSON__" not in tsx
    assert "HEP_SECTIONS" in tsx
    assert "StatCounter" in tsx
    assert "#00d4ff" in tsx  # dark_tech 主色

    txt = build_podcast_txt(spec)
    assert "[SECTION:hero]" in txt
    assert "[SECTION:outro]" in txt
    assert "AI Agent 入门指南" in txt

    vsecs = spec_to_video_sections(spec)
    names = [v["name"] for v in vsecs]
    assert names[0] == "hero" and names[-1] == "outro"
    assert any(n.startswith("data-") for n in names)
    assert any(n.startswith("overview-") for n in names)

    # 图标映射
    assert pick_icon("AI 智能分析") == "cpu"
    assert pick_icon("安全合规认证") == "shield"
    assert pick_icon("定价方案") == "dollar-sign"
    assert pick_icon("随便什么") == "sparkles"

    print(f"TSX: {len(tsx):,} chars")
    print(f"podcast.txt: {len(txt):,} chars")
    print(f"video sections: {names}")
    print("ALL TESTS PASSED")
