"""
video_pipeline/pipeline.py — LAAP 视频生产管线 (面板工作区)
============================================================
一键工作流: 上传脚本 → 选模板 → 装配动效 → TTS → 渲染 → 成片

用法:
    python -m laap_coding.core.video_pipeline.pipeline \\
        --script videos/my-video/podcast.txt \\
        --template dark-tech \\
        --name my-video \\
        [--render] [--bgm]

管线架构:
    Script → HEP Spec → Video Sections → Template Assembly → TSX
         → TTS (edge) → timing.json → Remotion Render → BGM Mix → Final
"""

import json, os, re, sys, subprocess, textwrap
from pathlib import Path

# ── 路径 ──
HERE = Path(__file__).parent
TEMPLATES_DIR = HERE / "templates"
ANIMATIONS_DIR = HERE / "animations"
PROJECT_DIR = Path(r"C:\Users\user\Desktop\OH-WorkSpace\remotion-project")
SKILL_DIR = Path(r"C:\Users\user\Desktop\OH-WorkSpace\video-podcast-maker\skills\video-podcast-maker")
TTSCN_HOME = Path(r"C:\Users\user\Desktop\OH-WorkSpace\ttsCN\skills\ttscn")


# ═══════════════════════════════════════════════
# 1. 模板系统
# ═══════════════════════════════════════════════

def list_templates() -> list:
    templates = []
    for f in sorted(TEMPLATES_DIR.glob("*.json")):
        tpl = json.loads(f.read_text("utf-8"))
        templates.append({"id": tpl["id"], "name": tpl["name"], "description": tpl["description"], "theme": tpl["theme"]})
    return templates


def load_template(template_id: str) -> dict:
    path = TEMPLATES_DIR / f"{template_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"TEMPLATE '{template_id}' NOT FOUND: {[t['id'] for t in list_templates()]}")
    return json.loads(path.read_text("utf-8"))


def template_to_default_props(tpl: dict) -> dict:
    c, a, d = tpl["colors"], tpl["animations"], tpl["decorations"]
    return {
        "primaryColor": c["primaryColor"], "backgroundColor": c["backgroundColor"],
        "textColor": c["textColor"], "accentColor": c["accentColor"],
        "titleSize": tpl["typography"]["titleSize"], "subtitleSize": tpl["typography"]["subtitleSize"],
        "bodySize": tpl["typography"]["bodySize"],
        "transitionType": a["transition"], "transitionDuration": a["transitionDuration"],
        "showProgressBar": d["showProgressBar"], "progressBarHeight": d["progressBarHeight"],
        "progressActiveColor": d["progressActiveColor"],
        "enableAnimations": True, "entranceStyle": a["entrance"], "staggerDelay": a["staggerDelay"], "bgmVolume": 0,
    }


# ═══════════════════════════════════════════════
# 2. HEP 集成
# ═══════════════════════════════════════════════

def spec_to_video_sections(spec: dict) -> list:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hep_to_remotion import hep_section_to_video
    return [hep_section_to_video(sec, i) for i, sec in enumerate(spec.get("sections", []))]


def _to_pascal(name: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[-_\s]+", name.strip()) if p) or "Video"


# ═══════════════════════════════════════════════
# 3. TSX 生成 (占位符替换, 零 f-string 冲突)
# ═══════════════════════════════════════════════

def generate_tsx(spec: dict, template_id: str, video_name: str) -> str:
    tpl = load_template(template_id)
    props = template_to_default_props(tpl)
    entrance_tsx = (ANIMATIONS_DIR / "entrance.tsx").read_text("utf-8")
    comp_name = _to_pascal(video_name)

    tsx = TSX_FRAME
    for k, v in {
        "__COMP_NAME__": comp_name,
        "__TEMPLATE_NAME__": tpl["name"],
        "__TEMPLATE_ID__": tpl["id"],
        "__ENTRANCE_STYLE__": tpl["animations"]["entrance"],
        "__TEXT_STYLE__": tpl["animations"]["text"],
        "__DATA_STYLE__": tpl["animations"]["data"],
        "__TRANSITION_TYPE__": tpl["animations"]["transition"],
        "__TITLE_JSON__": json.dumps(spec.get("title", ""), ensure_ascii=False),
        "__SECTIONS_JSON__": json.dumps(spec_to_video_sections(spec), ensure_ascii=False, indent=2),
        "__PROPS_JSON__": json.dumps(props, ensure_ascii=False, indent=2),
        "__ENTRANCE_TSX__": entrance_tsx,
    }.items():
        tsx = tsx.replace(k, v)
    return tsx


TSX_FRAME = r"""
/**
 * __COMP_NAME__Video.tsx — LAAP Video Pipeline v2
 * Template: __TEMPLATE_NAME__ (__TEMPLATE_ID__)
 * Animations: __ENTRANCE_STYLE__ / __TEXT_STYLE__ / __DATA_STYLE__
 * Transition: __TRANSITION_TYPE__
 */

import React from "react";
import { Audio, staticFile, AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import type { VideoProps } from "./Root";

import {
  Scale4K, FullBleedLayout, PaddedLayout, getPresentation,
  ChapterProgressBar, Subtitles, IconCard, StatCounter, Icon, useTiming,
  SILENT_FRAMES,
} from "./components";
import type { TimingSection } from "./components";

// ── Animation components (from video_pipeline/animations) ──
__ENTRANCE_TSX__

// ── Template defaults ──
const TEMPLATE_PROPS: Record<string, any> = __PROPS_JSON__;

// ── HEP section data ──
const HEP_TITLE = __TITLE_JSON__;
const HEP_SECTIONS = __SECTIONS_JSON__;

const baseName = (name: string) => name.replace(/-\d+$/, "");

const SectionComponent = ({
  section, props,
}: {
  section: TimingSection; props: VideoProps;
}) => {
  const data = HEP_SECTIONS.find((s) => s.name === section.name) || {};
  const base = baseName(section.name);
  const v = props.orientation === "vertical";
  const sectionPadding = v ? "120px 60px 160px" : "60px 100px 120px";

  switch (base) {
    case "hero": {
      const { opacity, translateY, scale } = useEntrance(
        (props as any).entranceStyle || "__ENTRANCE_STYLE__", props, 0
      );
      const animStyle = { opacity, transform: `translateY(${translateY}px) scale(${scale})` };
      return (
        <FullBleedLayout bg={props.backgroundColor}>
          <ParticleBackground color={props.primaryColor} />
          <div style={{
            position: "absolute", inset: 0,
            background: `radial-gradient(ellipse at 50% 40%, ${props.primaryColor}12 0%, transparent 70%)`,
          }} />
          <div style={{
            position: "absolute", inset: 0, display: "flex", flexDirection: "column",
            justifyContent: "center", alignItems: "center", textAlign: "center",
            padding: v ? "0 60px" : 0, ...animStyle,
          }}>
            {(data as any).badge ? (
              <div style={{
                fontSize: v ? 28 : 22, fontWeight: 600, color: props.accentColor,
                background: `${props.primaryColor}15`, border: `1px solid ${props.primaryColor}25`,
                borderRadius: 999, padding: "8px 24px", marginBottom: v ? 32 : 24,
                backdropFilter: "blur(8px)",
              }}>{(data as any).badge}</div>
            ) : null}
            <h1 style={{
              fontSize: props.titleSize, fontWeight: 800, color: props.primaryColor,
              lineHeight: v ? 1.3 : 1.1, textShadow: `0 2px 24px ${props.primaryColor}20`,
            }}>
              <SplitText text={(data as any).title || HEP_TITLE} />
            </h1>
            <p style={{
              fontSize: props.subtitleSize, color: props.textColor, marginTop: v ? 32 : 20,
              opacity: 0.6, fontWeight: 500,
            }}>{(data as any).subtitle}</p>
          </div>
        </FullBleedLayout>
      );
    }

    case "data": {
      const { opacity, translateY } = useEntrance("fade-slide-up", props, 0);
      const items = ((data as any).items || []).slice(0, 4);
      return (
        <PaddedLayout bg={props.backgroundColor} orientation={props.orientation}>
          <div style={{
            position: "absolute", inset: 0, padding: sectionPadding,
            display: "flex", flexDirection: "column", justifyContent: "center",
            opacity, transform: `translateY(${translateY}px)`,
          }}>
            <h2 style={{
              fontSize: v ? 72 : 80, fontWeight: 700, marginBottom: v ? 48 : 40,
              color: props.primaryColor, textAlign: "center",
            }}>{(data as any).title || "Core Data"}</h2>
            <StatCounter props={props} items={items} />
          </div>
        </PaddedLayout>
      );
    }

    case "overview": {
      const { opacity, translateY } = useEntrance("fade-slide-up", props, 0);
      const items = ((data as any).items || []).slice(0, 6);
      const staggerDelay = (props as any).staggerDelay || 6;
      return (
        <PaddedLayout bg={props.backgroundColor} orientation={props.orientation}>
          <div style={{
            position: "absolute", inset: 0, padding: sectionPadding,
            display: "flex", flexDirection: "column", justifyContent: "center",
            opacity, transform: `translateY(${translateY}px)`,
          }}>
            <h2 style={{
              fontSize: v ? 64 : 64, fontWeight: 700, marginBottom: v ? 32 : 28,
              color: props.primaryColor, textAlign: "center",
            }}>{(data as any).title || "Content"}</h2>
            <div style={{
              display: "flex", flexDirection: "column", gap: v ? 24 : 20,
              width: "100%", maxWidth: v ? undefined : 1000, margin: "0 auto",
            }}>
              {items.map((item: any, i: number) => (
                <IconCard key={i} props={props} icon={item.icon} title={item.title}
                  description={item.description} delay={i * staggerDelay} />
              ))}
            </div>
          </div>
        </PaddedLayout>
      );
    }

    case "outro": {
      const { opacity, scale } = useEntrance("__ENTRANCE_STYLE__", props, 0);
      return (
        <FullBleedLayout bg={props.backgroundColor}>
          <ParticleBackground color={props.accentColor} opacity={0.08} />
          <div style={{
            position: "absolute", inset: 0, display: "flex", flexDirection: "column",
            justifyContent: "center", alignItems: "center",
            opacity, transform: `scale(${scale})`,
          }}>
            <h2 style={{
              fontSize: v ? 72 : 80, fontWeight: 700, color: props.textColor, marginBottom: v ? 64 : 48,
            }}>{(data as any).title || "Thank You"}</h2>
            <div style={{ display: "flex", gap: v ? 56 : 40, flexDirection: v ? "column" : "row" }}>
              {[
                { icon: "thumbs-up", text: "Like" },
                { icon: "star", text: "Save" },
                { icon: "bell", text: "Follow" },
              ].map((item, i) => (
                <div key={i} style={{ textAlign: "center" }}>
                  <Icon name={item.icon} size={v ? 80 : 64} color={props.accentColor} animate="bounce" delay={i * 10} />
                  <div style={{ fontSize: v ? 32 : 26, color: "rgba(0,0,0,0.5)", marginTop: 10 }}>{item.text}</div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: v ? 44 : 36, color: props.primaryColor, marginTop: v ? 64 : 48 }}>
              {(data as any).cta || "See you next time!"}
            </p>
          </div>
        </FullBleedLayout>
      );
    }

    default: {
      const { opacity, translateY } = useEntrance("fade-slide-up", props, 0);
      return (
        <PaddedLayout bg={props.backgroundColor} orientation={props.orientation}>
          <div style={{
            position: "absolute", inset: 0, padding: sectionPadding,
            display: "flex", flexDirection: "column", justifyContent: "center",
            opacity, transform: `translateY(${translateY}px)`,
          }}>
            <h2 style={{
              fontSize: v ? 72 : 80, fontWeight: 700, color: props.primaryColor, textAlign: "center",
            }}>{(data as any).title || section.name}</h2>
          </div>
        </PaddedLayout>
      );
    }
  }
};

// Main video component
export const __COMP_NAME__Video = (props: VideoProps) => {
  const timing = useTiming();
  const sections = timing.sections;
  const transitionFrames = props.transitionDuration;

  const lastNonSilentIdx = sections.map((s) => !s.is_silent).lastIndexOf(true);
  const renderSections = sections.filter((s, i) => !(s.is_silent && i <= lastNonSilentIdx));
  const transitionCount = Math.max(0, renderSections.length - 1);
  const eff = props.transitionType !== "none" && transitionFrames > 0 ? transitionFrames : 0;
  const trailingSilentCount = renderSections.filter((s) => s.is_silent).length;
  const silentBudget = trailingSilentCount * SILENT_FRAMES;

  const origTotal = renderSections.reduce((s, s2) => s + (s2.is_silent ? 0 : s2.duration_frames), 0);
  const targetTotal = timing.total_frames + transitionCount * eff + silentBudget;
  const scaleFactor = origTotal > 0 ? (targetTotal - silentBudget) / origTotal : 1;

  const comp = renderSections.map((s) => {
    if (s.is_silent) return { ...s, duration_frames: SILENT_FRAMES };
    return { ...s, duration_frames: Math.max(15, Math.round(s.duration_frames * scaleFactor)) };
  });

  const scaledTotal = comp.reduce((s, s2) => s + s2.duration_frames, 0);
  const diff = targetTotal - scaledTotal;
  if (diff !== 0) {
    let absorbed = false;
    for (let i = comp.length - 1; i >= 0; i--) {
      if (!comp[i].is_silent) { comp[i].duration_frames = Math.max(15, comp[i].duration_frames + diff); absorbed = true; break; }
    }
    if (!absorbed && comp.length > 0) comp[comp.length - 1].duration_frames = Math.max(15, comp[comp.length - 1].duration_frames + diff);
  }

  return (
    <AbsoluteFill style={{ backgroundColor: props.backgroundColor }}>
      <Scale4K orientation={props.orientation}>
        <TransitionSeries>
          {comp.map((section, i) => (
            <React.Fragment key={`${section.name}-${i}`}>
              <TransitionSeries.Sequence durationInFrames={section.duration_frames}>
                <SectionComponent section={section} props={props} />
              </TransitionSeries.Sequence>
              {i < renderSections.length - 1 && transitionFrames > 0 && props.transitionType !== "none" && (
                <TransitionSeries.Transition presentation={getPresentation(props.transitionType)} timing={linearTiming({ durationInFrames: transitionFrames })} />
              )}
            </React.Fragment>
          ))}
        </TransitionSeries>
      </Scale4K>
      <ChapterProgressBar props={props} chapters={timing.sections} />
      <Subtitles src={staticFile("podcast_audio.srt")} />
      {props.bgmVolume > 0 && <Audio src={staticFile("bgm.mp3")} volume={props.bgmVolume} />}
      <Audio src={staticFile("podcast_audio.wav")} />
    </AbsoluteFill>
  );
};

export default __COMP_NAME__Video;
"""


# ═══════════════════════════════════════════════
# 4. 外部命令执行
# ═══════════════════════════════════════════════

def _run(cmd: list, cwd: str = None, timeout: int = 3600) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["Path"] += ";C:\\Users\\user\\Desktop\\OH-WorkSpace\\tools\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin;C:\\Users\\user\\Desktop\\OH-WorkSpace\\tools\\shims"
    env["TTSCN_HOME"] = str(TTSCN_HOME)
    env["TTS_BACKEND"] = "edge"
    env["TTS_VOICE"] = "zh-CN-XiaoxiaoNeural"
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env, timeout=timeout)


# ═══════════════════════════════════════════════
# 5. 流水线
# ═══════════════════════════════════════════════

class VideoPipeline:
    def __init__(self, script_path: str, template_id: str = "dark-tech", video_name: str = None):
        self.script_path = Path(script_path)
        self.template_id = template_id
        self.tpl = load_template(template_id)
        self.video_name = video_name or self.script_path.parent.name
        self.video_dir = PROJECT_DIR / "videos" / self.video_name
        self.video_dir.mkdir(parents=True, exist_ok=True)

    def run_tts(self) -> bool:
        print(f"[TTS] Generating voiceover... ({self.tpl['name']})")
        r = _run(["python3", str(SKILL_DIR / "scripts" / "generate_tts.py"), "--input", str(self.script_path), "--output-dir", str(self.video_dir)])
        if r.returncode != 0: print(f"[TTS] FAILED: {r.stderr[-200:]}"); return False
        print(f"[TTS] OK ({r.stdout[-100:]})")
        return True

    def generate_tsx(self, spec: dict = None) -> str:
        print(f"[TSX] Generating... ({self.template_id})")
        if spec is None:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from intent_mapper import IntentMapper
            spec = IntentMapper().parse(self.script_path.read_text("utf-8"))
        tsx = generate_tsx(spec, self.template_id, self.video_name)
        p = PROJECT_DIR / "src" / "remotion" / f"{_to_pascal(self.video_name)}Video.tsx"
        p.write_text(tsx, encoding="utf-8")
        print(f"[TSX] OK: {p}")
        return str(p)

    def register_root(self) -> str:
        props = template_to_default_props(self.tpl)
        cn = _to_pascal(self.video_name)
        pl = ",\n".join(f'          {k}: {json.dumps(v)}' for k, v in props.items())
        hint = f"// LAAP Video Pipeline v2 — {self.tpl['name']}\n//   import {{ Video as {cn}Video }} from \"./{cn}Video\";\n//   <Composition id=\"{cn}\" component={{{cn}Video}} durationInFrames={{300}} calculateMetadata={{calculateVideoMetadata}} fps={{30}} width={{3840}} height={{2160}} schema={{videoSchema}} defaultProps={{\n//       ...defaultVideoProps,\n{pl}\n//     }} />\n"
        p = self.video_dir / "root_registration.txt"
        p.write_text(hint, encoding="utf-8")
        print(f"[ROOT] {p}")
        return str(p)

    def render(self) -> bool:
        cn = _to_pascal(self.video_name)
        out = self.video_dir / "output.mp4"
        print(f"[RENDER] 4K video... ({cn})")
        r = _run(["npx", "remotion", "render", "src/remotion/index.ts", cn, str(out), "--public-dir", f"videos/{self.video_name}"], cwd=str(PROJECT_DIR), timeout=7200)
        if r.returncode != 0: print(f"[RENDER] FAILED: {r.stderr[-300:]}"); return False
        print(f"[RENDER] OK: {out}")
        return True

    def mix_bgm(self, bgm_path: str = None) -> bool:
        if bgm_path is None: bgm_path = str(SKILL_DIR / "assets" / "perfect-beauty-191271.mp3")
        out = self.video_dir / "video_with_bgm.mp4"
        print(f"[BGM] Mixing...")
        r = _run(["ffmpeg", "-i", str(self.video_dir / "output.mp4"), "-i", bgm_path, "-filter_complex", "[1:a]volume=0.08[a1];[0:a][a1]amix=inputs=2:duration=first", "-c:v", "copy", str(out), "-y"])
        if r.returncode != 0: print(f"[BGM] FAILED: {r.stderr[-200:]}"); return False
        print(f"[BGM] OK: {out}")
        return True

    def run_all(self, spec: dict = None, bgm: bool = True) -> bool:
        steps = [self.run_tts()]
        self.generate_tsx(spec)
        self.register_root()
        steps.append(True)
        steps.append(self.render())
        if bgm: steps.append(self.mix_bgm())
        ok = all(s == True for s in steps)
        print(f"\n{'='*50}\nLAAP Video Pipeline v2 — Complete\n{'='*50}\n  Template: {self.tpl['name']}\n  Script: {self.script_path}\n  Output: {self.video_dir / ('video_with_bgm.mp4' if bgm else 'output.mp4')}\n  Status: {'OK' if ok else 'PARTIAL'}")
        return ok


# ═══════════════════════════════════════════════
# 6. CLI
# ═══════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="LAAP Video Pipeline v2")
    parser.add_argument("--script", required=True, help="podcast.txt path")
    parser.add_argument("--template", default="dark-tech", help="template id")
    parser.add_argument("--name", default=None, help="video name")
    parser.add_argument("--render", action="store_true", help="render video")
    parser.add_argument("--bgm", action="store_true", help="mix BGM")
    parser.add_argument("--list-templates", action="store_true", help="list templates")
    parser.add_argument("--spec", default=None, help="HEP spec JSON path")
    args = parser.parse_args()

    if args.list_templates:
        print("Available templates:\n")
        for t in list_templates():
            print(f"  {t['id']:20s} {t['name']:16s} {t['description']}")
        return

    spec = json.loads(Path(args.spec).read_text("utf-8")) if args.spec else None
    pipe = VideoPipeline(args.script, args.template, args.name)
    if args.render:
        pipe.run_all(spec, bgm=args.bgm)
    else:
        pipe.generate_tsx(spec)
        pipe.register_root()
        print("\nTip: add --render to run full pipeline")


if __name__ == "__main__":
    main()