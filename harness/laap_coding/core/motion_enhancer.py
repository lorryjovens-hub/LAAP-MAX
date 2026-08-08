"""
motion_enhancer.py — HEP 动效增强引擎 (零 token)
=================================================
GSAP 动效 + Three.js 3D 场景的规则化生成器，与 HarnessComposer 无缝集成。

核心能力:
  1. MOTION_PRESETS — 可组合的 GSAP 动效预设库 (10+ 种)
  2. detect_motion() — 自然语言关键词 → spec["motion"] 配置
  3. render_motion_script() — spec → GSAP 注入脚本 (CDN + 初始化)
  4. render_three_scene() — spec → Three.js 3D 场景脚本 (3 种场景)

设计原则:
  - 零 token: 全部纯 Python 规则合成, ~0.5ms
  - 向后兼容: spec 无 motion 字段时回退到 animations 布尔字段行为
  - 零侵入: 动效通过 class/data 属性约定选择元素, 不要求改动 Atoms

用法:
    from motion_enhancer import detect_motion, render_motion_script, render_three_scene
    spec["motion"] = detect_motion(text)
    html = composer.from_spec(spec)   # composer 内部自动调用 render_*
"""

# ═══════════════════════════════════════════════
# 1. GSAP 动效预设库
#    每个模板含 __SCROLL__ 占位符: 替换为 ScrollTrigger 配置或空串
# ═══════════════════════════════════════════════

MOTION_PRESETS = {
    # 每个预设: {"js": 模板(含 __SCROLL__), "scroll": 该模板作用域下的 ScrollTrigger 配置}
    # 上浮入场 — 经典 power3 曲线, 用于卡片/区块
    "fade_up": {
        "js": '''
gsap.utils.toArray(".card,.stat-card,[data-motion='fade_up']").forEach(el=>{
  gsap.from(el,{__SCROLL__y:40,opacity:0,duration:.8,ease:"power3.out"});
});''',
        "scroll": 'scrollTrigger:{trigger:el,start:"top 85%"},',
    },

    # 淡入 — 柔和显隐, 用于装饰与背景层
    "fade_in": {
        "js": '''
gsap.utils.toArray("[data-motion='fade_in'],.section-label,h2").forEach(el=>{
  gsap.from(el,{__SCROLL__opacity:0,duration:1,ease:"power2.out"});
});''',
        "scroll": 'scrollTrigger:{trigger:el,start:"top 85%"},',
    },

    # 左侧滑入 — 方向感强, 用于流程/时间线
    "slide_left": {
        "js": '''
gsap.utils.toArray(".pipeline-step,[data-motion='slide_left']").forEach(el=>{
  gsap.from(el,{__SCROLL__x:-60,opacity:0,duration:.7,ease:"power3.out"});
});''',
        "scroll": 'scrollTrigger:{trigger:el,start:"top 85%"},',
    },

    # 缩放入场 — 聚焦感, 用于 CTA/主按钮
    "scale_in": {
        "js": '''
gsap.utils.toArray("[data-motion='scale_in'],.hero a[href='#']").forEach(el=>{
  gsap.from(el,{__SCROLL__scale:.85,opacity:0,duration:.9,ease:"back.out(1.7)"});
});''',
        "scroll": 'scrollTrigger:{trigger:el,start:"top 85%"},',
    },

    # 翻转入场 — 3D 旋转感, 用于卡片
    "flip_in": {
        "js": '''
gsap.utils.toArray("[data-motion='flip_in'],.card").forEach(el=>{
  gsap.from(el,{__SCROLL__rotationX:-40,transformOrigin:"center top",opacity:0,duration:.9,ease:"power2.out"});
});''',
        "scroll": 'scrollTrigger:{trigger:el,start:"top 85%"},',
    },

    # 级联网格 — 卡片依次入场 (stagger), 用于 grid 区
    "stagger_grid": {
        "js": '''
gsap.utils.toArray("[data-stagger]").forEach(group=>{
  gsap.from(group.children,{__SCROLL__y:36,opacity:0,duration:.7,stagger:.08,ease:"power3.out"});
});''',
        "scroll": 'scrollTrigger:{trigger:group,start:"top 85%"},',
    },

    # 数字滚动 — 从 stat-card 数字元素解析数值并滚动计数
    "counter": {
        "js": '''
gsap.utils.toArray(".stat-card").forEach(el=>{
  const numEl=el.querySelector("div");if(!numEl)return;
  const raw=numEl.textContent.trim();
  const num=parseFloat(raw.replace(/[^0-9.\\-]/g,""));
  if(isNaN(num))return;
  const suffix=raw.replace(/[0-9.\\-]/g,"")||"";
  const decimals=(raw.split(".")[1]||"").replace(/[^0-9]/g,"").length;
  const obj={v:0};
  gsap.to(obj,{v:num,duration:1.8,ease:"power2.out",__SCROLL__onUpdate:()=>{numEl.textContent=obj.v.toFixed(decimals)+suffix;}});
});''',
        "scroll": 'scrollTrigger:{trigger:el,start:"top 85%"},',
    },

    # 标题拆字 — 逐字上升入场 (无需 SplitText 插件, 纯 DOM 实现)
    "split_text": {
        "js": '''
gsap.utils.toArray(".hero h1,[data-motion='split_text']").forEach(el=>{
  const txt=el.textContent;if(!txt)return;
  el.textContent="";el.style.display="inline-block";el.style.overflow="hidden";
  [...txt].forEach(ch=>{
    const s=document.createElement("span");
    s.textContent=ch===" "?"\\u00A0":ch;
    s.style.display="inline-block";s.style.transform="translateY(110%)";
    s.style.transition="transform .7s cubic-bezier(.16,1,.3,1)";
    el.appendChild(s);
  });
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    [...el.children].forEach((s,i)=>setTimeout(()=>s.style.transform="translateY(0)",i*30));
  }));
});''',
        "scroll": "",
    },

    # 滚动视差 — 元素随滚动缓速移动 (scrub 驱动)
    "parallax": {
        "js": '''
gsap.utils.toArray("[data-parallax]").forEach(el=>{
  const depth=parseFloat(el.dataset.parallax||"0.3");
  gsap.to(el,{yPercent:-25*depth,ease:"none",scrollTrigger:{trigger:el,start:"top bottom",end:"bottom top",scrub:true}});
});''',
        "scroll": "",
    },

    # 光晕脉冲 — 强调元素呼吸发光 (无限循环)
    "pulse_glow": {
        "js": '''
gsap.utils.toArray("[data-glow]").forEach(el=>{
  gsap.to(el,{scale:1.05,duration:1.4,yoyo:true,repeat:-1,ease:"sine.inOut"});
});''',
        "scroll": "",
    },

    # 进度条 — 顶部加载进度 (仿 Lenis/Apple 风格)
    "progress_bar": {
        "js": '''
const bar=document.createElement("div");
bar.style.cssText="position:fixed;top:0;left:0;height:2px;width:0;background:var(--accent);z-index:9999;transition:width .2s";
document.body.appendChild(bar);
addEventListener("scroll",()=>{
  const h=document.documentElement;
  bar.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+"%";
},{passive:true});''',
        "scroll": "",
    },
}

# ═══════════════════════════════════════════════
# 2. 章节类型 → 默认动效组合
# ═══════════════════════════════════════════════

SECTION_MOTION_DEFAULT = {
    "hero": ["split_text", "fade_up", "scale_in"],
    "stats": ["counter", "stagger_grid"],
    "grid": ["stagger_grid", "fade_up"],
    "pipeline": ["slide_left", "stagger_grid"],
    "custom_html": [],
}

# 无 motion 字段时的回退组合 (等价旧 GSAP_SCRIPT 的升级版)
FALLBACK_PRESETS = ["fade_up", "stagger_grid"]

# ═══════════════════════════════════════════════
# 3. 关键词 → 动效/3D 风格识别
# ═══════════════════════════════════════════════

MOTION_KEYWORDS = {
    "fade_up": ["上浮", "升起", "fade up", "fade-up"],
    "fade_in": ["淡入", "渐显", "fade in", "fade-in"],
    "slide_left": ["左滑", "滑入", "slide in", "slide-left"],
    "scale_in": ["弹出", "缩放", "scale in", "scale-in", "zoom"],
    "flip_in": ["翻转", "flip", "翻转进入"],
    "stagger_grid": ["级联", "依次", "逐个", "stagger", "瀑布", "错落"],
    "counter": ["数字滚动", "计数", "滚动数字", "counter", "数字跳动"],
    "split_text": ["拆字", "逐字", "文字动画", "标题动画", "split text", "打字机", "逐字动画"],
    "parallax": ["视差", "parallax", "滚动视差", "深度"],
    "pulse_glow": ["光晕", "脉冲", "呼吸", "发光", "glow", "pulse"],
    "progress_bar": ["进度条", "顶部进度", "progress bar", "加载进度"],
}

THREE_STYLE_KEYWORDS = {
    "neural": ["粒子", "神经网络", "星点", "neural", "粒子网络", "星尘"],
    "orb": ["球体", "光球", "星球", "orb", "球", "环"],
    "cubes": ["立方体", "几何体", "方块", "cubes", "box", "晶体"],
}

# 风格默认 3D (与 intent_mapper._THREE_D_STYLES 对齐)
THREE_DEFAULT_STYLES = {"apple_dark", "dark_tech", "glassmorphism", "sunset", "ocean"}


def detect_motion(text: str) -> dict:
    """自然语言 → motion 配置 dict.

    Returns:
        {"enabled": bool, "presets": [...], "scroll": bool}
    """
    if not text:
        return {"enabled": True, "presets": [], "scroll": True}

    low = text.lower()

    # 显式禁用
    if any(kw in low for kw in ["无动效", "不要动画", "静态", "禁用动效", "no animation", "no motion", "静态页面"]):
        return {"enabled": False, "presets": [], "scroll": False}

    presets = []
    for preset, kws in MOTION_KEYWORDS.items():
        if any(kw in low for kw in kws):
            presets.append(preset)

    # 平滑滚动
    scroll = any(kw in low for kw in ["平滑", "smooth", "滚动", "scroll"])

    # 去重保序
    seen, uniq = set(), []
    for p in presets:
        if p not in seen:
            seen.add(p)
            uniq.append(p)

    return {"enabled": True, "presets": uniq, "scroll": scroll}


def detect_three_style(text: str) -> str:
    """自然语言 → 3D 场景风格 id (neural/orb/cubes)."""
    if not text:
        return "neural"
    low = text.lower()
    for style, kws in THREE_STYLE_KEYWORDS.items():
        if any(kw in low for kw in kws):
            return style
    return "neural"


def _default_presets(spec: dict) -> list:
    """按 section 类型推导默认动效组合 (无显式 motion.presets 时)."""
    presets = []
    for sec in spec.get("sections", []):
        sec_type = sec.get("type", "")
        for p in SECTION_MOTION_DEFAULT.get(sec_type, []):
            if p not in presets:
                presets.append(p)
    return presets or list(FALLBACK_PRESETS)


# ═══════════════════════════════════════════════
# 4. GSAP 脚本生成
# ═══════════════════════════════════════════════

GSAP_CDN_CORE = '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>'
SCROLLTRIGGER_CDN = '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>'


def resolve_presets(spec: dict) -> list:
    """返回最终生效的动效预设列表 (与 render_motion_script 完全一致).

    composer 用它决定给布局注入哪些 data-* 钩子, 保证标记与脚本同步.
    """
    motion = spec.get("motion")
    if motion is None:
        if not spec.get("animations", True):
            return []
        return _default_presets(spec)
    if not motion.get("enabled", True):
        return []
    return motion.get("presets") or _default_presets(spec)


def render_motion_script(spec: dict) -> str:
    """spec → GSAP 注入脚本 (含 CDN + registerPlugin + 预设初始化).

    兼容规则:
      - spec["motion"]["enabled"]=False 或 spec["animations"]=False → 空串
      - spec 无 motion 字段 → 回退 FALLBACK_PRESETS (保持旧行为)
    """
    presets = resolve_presets(spec)
    if not presets:
        return ""

    motion = spec.get("motion")
    scroll = motion.get("scroll", True) if motion else True

    # 需要 ScrollTrigger 的预设 (滚动驱动)
    needs_trigger = scroll and any(p in presets for p in
                                   ("fade_up", "fade_in", "slide_left", "scale_in",
                                    "flip_in", "stagger_grid", "counter"))

    body = []
    for p in presets:
        if p in MOTION_PRESETS:
            tmpl = MOTION_PRESETS[p]
            code = tmpl["js"].replace("__SCROLL__", tmpl["scroll"] if needs_trigger else "")
            body.append(code)

    if not body:
        return ""

    register = 'gsap.registerPlugin(ScrollTrigger);' if needs_trigger else ''
    js = "\n".join(body)

    cdn = GSAP_CDN_CORE + ('\n' + SCROLLTRIGGER_CDN if needs_trigger else '')

    # 包一层 load 事件 + 防御检查, 避免 CDN 时序抖动导致脚本挂掉
    return f'''{cdn}
<script>
window.addEventListener("load",function(){{
if(typeof gsap==="undefined")return;
{register}
{js}
}});
</script>'''


# ═══════════════════════════════════════════════
# 5. Three.js 3D 场景生成
#    场景挂载点: <div id="three-hero"> (Layouts.hero 的 three_d=True 时生成)
# ═══════════════════════════════════════════════

THREE_IMPORTMAP = '''<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}</script>'''


def _neural_scene_js() -> str:
    """粒子网络场景 — 2500 星点 + 近邻连线 + Bloom."""
    return '''
export function createNeuralScene(c){
  const s=new THREE.Scene(),ca=new THREE.PerspectiveCamera(75,c.clientWidth/c.clientHeight,0.1,1e3),r=new THREE.WebGLRenderer({alpha:true,antialias:true});
  r.setSize(c.clientWidth,c.clientHeight);r.setPixelRatio(Math.min(devicePixelRatio,2));c.appendChild(r.domElement);
  const n=2500,p=new Float32Array(n*3);for(let i=0;i<n*3;i++)p[i]=(Math.random()-.5)*25;
  const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.BufferAttribute(p,3));
  const m=new THREE.PointsMaterial({size:.04,color:0x7c7cff,transparent:true,opacity:.5,blending:THREE.AdditiveBlending}),pt=new THREE.Points(g,m);s.add(pt);
  const lp=[];for(let i=0;i<400;i++){const i1=Math.floor(Math.random()*n),i2=Math.floor(Math.random()*n),a=p.slice(i1*3,i1*3+3),b=p.slice(i2*3,i2*3+3);if(Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2])<4)lp.push(...a,...b);}
  const lg=new THREE.BufferGeometry();lg.setAttribute("position",new THREE.Float32BufferAttribute(lp,3));
  const ls=new THREE.LineSegments(lg,new THREE.LineBasicMaterial({color:0x7c7cff,transparent:true,opacity:.06}));s.add(ls);
  const co=new EffectComposer(r);co.addPass(new RenderPass(s,ca));co.addPass(new UnrealBloomPass(new THREE.Vector2(c.clientWidth,c.clientHeight),.2,.5,.1));
  ca.position.z=10;let rot=0;function anim(){requestAnimationFrame(anim);rot+=.0008;pt.rotation.y=rot;ls.rotation.y=rot;co.render();}anim();
  addEventListener("resize",()=>{ca.aspect=c.clientWidth/c.clientHeight;ca.updateProjectionMatrix();r.setSize(c.clientWidth,c.clientHeight);co.setSize(c.clientWidth,c.clientHeight);});
}'''


def _orb_scene_js() -> str:
    """光球场景 — 双层线框二十面体 + 光环 + Bloom."""
    return '''
export function createOrbScene(c){
  const s=new THREE.Scene(),ca=new THREE.PerspectiveCamera(60,c.clientWidth/c.clientHeight,0.1,1e3),r=new THREE.WebGLRenderer({alpha:true,antialias:true});
  r.setSize(c.clientWidth,c.clientHeight);r.setPixelRatio(Math.min(devicePixelRatio,2));c.appendChild(r.domElement);
  const core=new THREE.Mesh(
    new THREE.IcosahedronGeometry(2.2,1),
    new THREE.MeshStandardMaterial({color:0x7c7cff,wireframe:true,transparent:true,opacity:.6,emissive:0x7c7cff,emissiveIntensity:.4}));
  const shell=new THREE.Mesh(
    new THREE.IcosahedronGeometry(3.2,1),
    new THREE.MeshBasicMaterial({color:0x9d8cff,wireframe:true,transparent:true,opacity:.15}));
  s.add(core,shell);
  s.add(new THREE.AmbientLight(0xffffff,.6));
  const ring=new THREE.Mesh(
    new THREE.TorusGeometry(4.4,.04,8,96),
    new THREE.MeshBasicMaterial({color:0x7c7cff,transparent:true,opacity:.35}));
  ring.rotation.x=Math.PI/2.4;s.add(ring);
  const co=new EffectComposer(r);co.addPass(new RenderPass(s,ca));co.addPass(new UnrealBloomPass(new THREE.Vector2(c.clientWidth,c.clientHeight),.6,.6,.2));
  ca.position.z=9;function anim(){requestAnimationFrame(anim);core.rotation.y+=.004;core.rotation.x+=.0015;shell.rotation.y-=.002;ring.rotation.z+=.003;co.render();}anim();
  addEventListener("resize",()=>{ca.aspect=c.clientWidth/c.clientHeight;ca.updateProjectionMatrix();r.setSize(c.clientWidth,c.clientHeight);co.setSize(c.clientWidth,c.clientHeight);});
}'''


def _cubes_scene_js() -> str:
    """晶体场景 — 随机浮动立方体 + 旋转 + Bloom."""
    return '''
export function createCubesScene(c){
  const s=new THREE.Scene(),ca=new THREE.PerspectiveCamera(70,c.clientWidth/c.clientHeight,0.1,1e3),r=new THREE.WebGLRenderer({alpha:true,antialias:true});
  r.setSize(c.clientWidth,c.clientHeight);r.setPixelRatio(Math.min(devicePixelRatio,2));c.appendChild(r.domElement);
  const group=new THREE.Group();const mats=[0x7c7cff,0x00d4ff,0x9d8cff,0x4f6ef7];
  for(let i=0;i<14;i++){
    const size=.3+Math.random()*1.1;
    const cube=new THREE.Mesh(
      new THREE.BoxGeometry(size,size,size),
      new THREE.MeshStandardMaterial({color:mats[i%4],wireframe:i%3===0,transparent:true,opacity:.85,emissive:mats[i%4],emissiveIntensity:.25}));
    cube.position.set((Math.random()-.5)*16,(Math.random()-.5)*9,(Math.random()-.5)*6-2);
    cube.rotation.set(Math.random()*3,Math.random()*3,0);
    cube.userData.speed=.003+Math.random()*.006;
    group.add(cube);
  }
  s.add(group);s.add(new THREE.AmbientLight(0xffffff,.7));
  const co=new EffectComposer(r);co.addPass(new RenderPass(s,ca));co.addPass(new UnrealBloomPass(new THREE.Vector2(c.clientWidth,c.clientHeight),.3,.6,.15));
  ca.position.z=12;function anim(){requestAnimationFrame(anim);group.children.forEach(cb=>{cb.rotation.x+=cb.userData.speed;cb.rotation.y+=cb.userData.speed*.7;});group.rotation.y+=.0012;co.render();}anim();
  addEventListener("resize",()=>{ca.aspect=c.clientWidth/c.clientHeight;ca.updateProjectionMatrix();r.setSize(c.clientWidth,c.clientHeight);co.setSize(c.clientWidth,c.clientHeight);});
}'''


def _scene_style_map(style: str) -> str:
    """style id → JS 场景函数源码."""
    return {
        "neural": _neural_scene_js(),
        "orb": _orb_scene_js(),
        "cubes": _cubes_scene_js(),
    }.get(style, _neural_scene_js())


def render_three_scene(spec: dict) -> str:
    """spec → Three.js 场景注入脚本.

    检测 sections 中 hero.three_d=True 的节, 按 three_d_style 生成场景.
    返回空串表示无需注入.
    """
    styles = []
    for sec in spec.get("sections", []):
        if sec.get("three_d") and sec.get("type") == "hero":
            style = sec.get("three_d_style", "neural")
            if style not in styles:
                styles.append(style)

    if not styles:
        return ""

    scenes_js = "\n".join(_scene_style_map(st) for st in styles)

    # 创建调度: 同名挂载点取第一个场景, 其余场景在额外的挂载点创建
    mount_code = '''
addEventListener("DOMContentLoaded",()=>{
  const mounts=document.querySelectorAll("[data-three],#three-hero");
  const creators=STYLE_FN_MAP;
  mounts.forEach(m=>{const st=m.dataset.three||"neural";const fn=creators[st];if(fn)fn(m);});
});'''

    # 挂载点命名: 默认 #three-hero, 多场景时用 data-three 属性
    fn_map = "{" + ",".join(f'"{st}":create{st.capitalize()}Scene' for st in styles) + "}"

    imports = ('import*as THREE from"three";'
               'import{EffectComposer}from"three/addons/postprocessing/EffectComposer.js";'
               'import{RenderPass}from"three/addons/postprocessing/RenderPass.js";'
               'import{UnrealBloomPass}from"three/addons/postprocessing/UnrealBloomPass.js";')
    return THREE_IMPORTMAP + '\n<script type="module">\n' + imports + '\n' + scenes_js + mount_code.replace("STYLE_FN_MAP", fn_map) + '\n</script>'


# ═══════════════════════════════════════════════
# 6. 测试
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        "深色SaaS落地页带3D粒子背景",
        "科技公司首页 要数字滚动和视差效果",
        "产品落地页 带动效",
        "静态文档页 无动效",
        "玻璃拟态作品集 球体3D背景 文字动画",
        "简约博客 不要动画",
    ]
    for t in tests:
        m = detect_motion(t)
        t3 = detect_three_style(t)
        print(f"[{t}]")
        print(f"  motion={m}")
        print(f"  three_style={t3}")

    spec = {
        "title": "Test",
        "theme": "apple_dark",
        "sections": [
            {"type": "hero", "title": "Hello", "three_d": True, "three_d_style": "orb"},
            {"type": "stats", "items": [{"number": "99%", "label": "Save"}]},
            {"type": "grid", "cards": [{"title": "A", "desc": "B"}]},
        ],
    }
    js = render_motion_script(spec)
    print(f"\nmotion script: {len(js):,} chars, presets={_default_presets(spec)}")
    assert "ScrollTrigger" in js
    three = render_three_scene(spec)
    print(f"three script: {len(three):,} chars, orb={'createOrbScene' in three}")
    assert "createOrbScene" in three

    # 兼容性: 无 motion 字段
    old_spec = {"title": "Old", "sections": [{"type": "grid", "cards": []}]}
    old_js = render_motion_script(old_spec)
    print(f"fallback script: {len(old_js):,} chars (兼容旧 spec)")
    assert "fade_up" in old_js

    # 禁用
    off = render_motion_script({"title": "X", "motion": {"enabled": False}, "sections": []})
    assert off == ""
    print("\nALL TESTS PASSED")
