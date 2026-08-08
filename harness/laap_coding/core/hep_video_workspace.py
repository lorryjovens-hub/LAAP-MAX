"""
hep_video_workspace.py — HEP 视频工作区 (零 token 流水线)
========================================================
一条命令: 文案 → 高级感 4K 视频

工作流:
  1. 读文案 (文件或 stdin)
  2. HEP intent_mapper → spec (零 token)
  3. 模板装配 → spec + 效果配置
  4. hep_to_remotion → TSX + podcast.txt 初稿
  5. 提示用户打磨脚本
  6. ttscn TTS → podcast_audio.wav + timing.json
  7. Remotion 渲染 → 4K 视频 + BGM 混音

用法:
    python hep_video_workspace.py "AI Agent 入门指南" --style dark_tech_premium
    python hep_video_workspace.py path/to/script.md --style apple_glass --render
    python hep_video_workspace.py --list-templates
"""

import json
import os
import re
import subprocess
import sys
import time

# ── 项目路径 ──
HARNESS_CORE = r"D:\LAAP\harness\laap_coding\core"
REMOTION_PROJECT = r"C:\Users\user\Desktop\OH-WorkSpace\remotion-project"
SKILL_DIR = r"C:\Users\user\Desktop\OH-WorkSpace\video-podcast-maker\skills\video-podcast-maker"
TTSCN_HOME = r"C:\Users\user\Desktop\OH-WorkSpace\ttsCN\skills\ttscn"

sys.path.insert(0, HARNESS_CORE)

# 懒加载模块 (import 在函数内, 避免启动时循环依赖)


def to_pascal(name: str) -> str:
    parts = re.split(r"[-_\s]+", name.strip())
    return "".join(p.capitalize() for p in parts if p) or "Video"


def snake_case(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ═══════════════════════════════════════════════
# 核心流水线
# ═══════════════════════════════════════════════

class VideoWorkspace:
    """视频工作区 — 管理从文案到成片的完整流水线."""

    def __init__(self, project_dir: str = REMOTION_PROJECT):
        self.project = project_dir
        self.name = ""
        self.spec = None
        self.enriched = None
        self.template_id = "dark_tech_premium"
        self.video_dir = ""

    def list_templates(self) -> list:
        """列出可用模板."""
        from hep_video_templates import list_templates
        return list_templates()

    def ingest(self, text: str, name: str = "", template_id: str = "dark_tech_premium") -> dict:
        """Step 1-3: 文案 → spec → 模板装配."""
        self.template_id = template_id
        self.name = name or snake_case(text[:30])

        from intent_mapper import IntentMapper
        from hep_video_templates import apply_template

        spec = IntentMapper().parse(text)
        self.spec = spec
        self.enriched = apply_template(spec, template_id)
        return self.enriched

    def generate_tsx(self) -> str:
        """Step 4: 生成 TSX + podcast.txt 初稿."""
        from hep_to_remotion import build_video_tsx, spec_to_video_sections, build_podcast_txt

        tsx = build_video_tsx(self.spec, self.name)
        pname = to_pascal(self.name)

        tsx_path = os.path.join(self.project, "src", "remotion", f"{pname}Video.tsx")
        os.makedirs(os.path.dirname(tsx_path), exist_ok=True)
        with open(tsx_path, "w", encoding="utf-8") as f:
            f.write(tsx)

        self.video_dir = os.path.join(self.project, "videos", self.name)
        os.makedirs(self.video_dir, exist_ok=True)

        txt = build_podcast_txt(self.spec)
        txt_path = os.path.join(self.video_dir, "podcast.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt)

        # 注册提示
        comp_name = pname
        from hep_to_remotion import theme_to_props
        props = theme_to_props(self.spec.get("theme", "apple_dark"))
        props_lines = ",\n".join(f'          {k}: "{v}",' for k, v in props.items())
        reg_hint = (
            f"\n// 在 src/remotion/Root.tsx 中注册:\n"
            f'//   import {{ Video as {comp_name}Video }} from "./{comp_name}Video";\n'
            f'//   <Composition id="{comp_name}" component={{{comp_name}Video}}\n'
            f'//     durationInFrames={{300}} calculateMetadata={{calculateVideoMetadata}} fps={{30}}\n'
            f'//     width={{3840}} height={{2160}} schema={{videoSchema}}\n'
            f'//     defaultProps={{\n'
            f'//       ...defaultVideoProps,\n'
            f'{props_lines}\n'
            f'//     }} />\n'
        )
        with open(os.path.join(self.video_dir, "root_registration.txt"), "w", encoding="utf-8") as f:
            f.write(reg_hint)

        vsecs = spec_to_video_sections(self.spec)
        return tsx_path, txt_path, vsecs

    def run_tts(self) -> dict:
        """Step 6: ttscn TTS → audio + srt + timing."""
        tts_script = os.path.join(SKILL_DIR, "scripts", "generate_tts.py")
        input_txt = os.path.join(self.video_dir, "podcast.txt")

        env = os.environ.copy()
        env["TTSCN_HOME"] = TTSCN_HOME
        env["TTS_BACKEND"] = "edge"
        env["TTS_VOICE"] = "zh-CN-XiaoxiaoNeural"
        env["Path"] += ";C:\\Users\\user\\Desktop\\OH-WorkSpace\\tools\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin"
        env["Path"] += ";C:\\Users\\user\\Desktop\\OH-WorkSpace\\tools\\shims"

        result = subprocess.run(
            [sys.executable, tts_script, "--input", input_txt, "--output-dir", self.video_dir],
            capture_output=True, text=True, env=env, timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"TTS failed: {result.stderr[-500:]}")
        return json.loads(result.stdout)

    def render(self) -> str:
        """Step 7: Remotion 渲染 4K 视频."""
        comp_name = to_pascal(self.name)
        output = os.path.join(self.video_dir, "output.mp4")

        result = subprocess.run(
            ["npx", "remotion", "render", "src/remotion/index.ts", comp_name, output,
             "--public-dir", f"videos/{self.name}"],
            capture_output=True, text=True, env=os.environ, timeout=3600,
            cwd=self.project,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Render failed: {result.stderr[-500:]}")
        return output

    def mix_bgm(self) -> str:
        """混音 BGM."""
        bgm = os.path.join(SKILL_DIR, "assets", "perfect-beauty-191271.mp3")
        output = os.path.join(self.video_dir, "output.mp4")
        bgm_output = os.path.join(self.video_dir, "video_with_bgm.mp4")

        env = os.environ.copy()
        env["Path"] += ";C:\\Users\\user\\Desktop\\OH-WorkSpace\\tools\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin"

        subprocess.run(
            ["ffmpeg", "-i", output, "-i", bgm,
             "-filter_complex", "[1:a]volume=0.08[a1];[0:a][a1]amix=inputs=2:duration=first",
             "-c:v", "copy", bgm_output, "-y"],
            capture_output=True, text=True, env=env, timeout=300,
        )
        # 清理临时渲染文件
        for f in os.listdir(self.video_dir):
            if f.startswith("_review_") or f.startswith("part_") or f == "concat_list.txt":
                try:
                    os.remove(os.path.join(self.video_dir, f))
                except OSError:
                    pass
        return bgm_output


# ═══════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    if not args or "--list-templates" in args:
        ws = VideoWorkspace()
        print("HEP 视频工作区 v1.0")
        print("=" * 50)
        print("可用模板:")
        for t in ws.list_templates():
            print(f"  [{t['id']}] {t['name']}")
            print(f"         {t['description']}")
            print(f"         theme={t['theme']} intensity={t['intensity']}")
        print()
        print("用法:")
        print(f"  python {sys.argv[0]} \"视频主题\" [--style dark_tech_premium] [--name video-name] [--render]")
        print(f"  python {sys.argv[0]} path/to/script.md --style apple_glass --render")
        return

    ws = VideoWorkspace()
    text = args[0]
    style = "dark_tech_premium"
    name = ""
    do_render = False

    for i, a in enumerate(args):
        if a == "--style" and i + 1 < len(args):
            style = args[i + 1]
        if a == "--name" and i + 1 < len(args):
            name = args[i + 1]
        if a == "--render":
            do_render = True

    # 如果输入是文件路径, 读文件
    if os.path.isfile(text):
        with open(text, "r", encoding="utf-8") as f:
            text = f.read()

    print(f"HEP 视频工作区 — 模板: {style}")
    print("=" * 50)

    # 1-3: 文案 → spec → 模板
    print(f"[1/5] 解析文案 → HEP spec...")
    enriched = ws.ingest(text, name, style)
    section_types = [s["type"] for s in enriched.get("sections", [])]
    print(f"      主题: {enriched.get('theme')}, 章节: {section_types}")

    # 4: 生成 TSX
    print(f"[2/5] 生成视觉组件 + 脚本初稿...")
    tsx_path, txt_path, vsecs = ws.generate_tsx()
    print(f"      TSX: {tsx_path}")
    print(f"      脚本: {txt_path}")
    print(f"      视频章节: {[v['name'] for v in vsecs]}")

    print(f"[3/5] 提示: 请打磨 {txt_path} 中的脚本")
    print(f"      (默读三遍, 砍废话, 数字/术语核对)")
    if not do_render:
        print(f"[4/5] 跳过 TTS (加 --render 执行完整流水线)")
        print(f"[5/5] 跳过渲染 (加 --render 执行完整流水线)")
        print()
        print("准备就绪. 运行以下命令完成流水线:")
        print(f"  python {sys.argv[0]} \"{text[:30]}...\" --style {style} --name {name or ws.name} --render")
        return

    # 5: TTS
    print(f"[4/5] TTS 配音 (edge)...")
    try:
        tts_result = ws.run_tts()
        dur = tts_result.get("data", {}).get("total_duration_seconds", 0)
        sections = tts_result.get("data", {}).get("sections", [])
        print(f"      配音完成: {dur:.1f}s, {len(sections)} 章节")
        for s in sections:
            print(f"        {s['name']}: {s['start_time']:.1f}s - "
                  f"{s['start_time'] + s['duration']:.1f}s ({s['duration']:.1f}s)")
    except RuntimeError as e:
        print(f"      TTS 失败: {e}")
        return

    # 6: 渲染
    print(f"[5/5] Remotion 渲染 4K 视频...")
    try:
        output = ws.render()
        size_mb = os.path.getsize(output) / 1024 / 1024
        print(f"      渲染完成: {output} ({size_mb:.0f} MB)")

        print(f"      混音 BGM...")
        bgm_out = ws.mix_bgm()
        bgm_size = os.path.getsize(bgm_out) / 1024 / 1024
        print(f"      BGM 混音完成: {bgm_out} ({bgm_size:.0f} MB)")
        print()
        print("=" * 50)
        print(f"🎬 视频就绪: {bgm_out}")
        print(f"   时长: {dur:.0f}s | 分辨率: 4K (3840×2160)")
        print(f"   模板: {style} | 主题: {enriched.get('theme')}")
    except RuntimeError as e:
        print(f"      渲染失败: {e}")
        return


if __name__ == "__main__":
    main()