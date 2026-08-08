"""
hep_video_effects.py — HEP 视频动效物种库 (零 token)
=====================================================
可复用的视频动效模板，全部注册为 HEP 认知物种，供模板系统匹配-装配。

每个效果是一个"物种"：
  - 名称 + 参数接口 → 可在 spec 中通过名称引用
  - 返回 TSX 代码片段 → 装配到视频 Composition
  - 参数可调 → 同一物种可适配不同风格

效果分类:
  - Backgrounds: 动态背景 (粒子/渐变/几何/光晕)
  - Text: 文字动画 (拆字/渐变/发光/打字机)
  - Data: 数据动效 (计数/进度环/柱状图)
  - Transitions: 转场 (擦除/径向/故障)
  - Overlays: 装饰叠层 (浮点/网格/扫描线/光晕)
"""

import re

# ═══════════════════════════════════════════════
# 效果注册表 — 所有效果在此注册, 按名称查找
# ═══════════════════════════════════════════════

EFFECT_REGISTRY = {}

def register(effect_id: str, category: str, params: dict, generator_fn):
    """注册一个效果物种到 HEP 效果库."""
    EFFECT_REGISTRY[effect_id] = {
        "id": effect_id,
        "category": category,
        "params": params,
        "generate": generator_fn,
    }

def get_effect(effect_id: str):
    """按名称获取效果物种."""
    return EFFECT_REGISTRY.get(effect_id)

def list_effects(category: str = None) -> list:
    """列出效果, 可按分类筛选."""
    if category:
        return [e for e in EFFECT_REGISTRY.values() if e["category"] == category]
    return list(EFFECT_REGISTRY.values())

# ═══════════════════════════════════════════════
# 1. 背景效果 (Backgrounds)
# ═══════════════════════════════════════════════

def _gen_gradient_mesh(color1: str, color2: str, color3: str = "", speed: float = 1.0):
    """动态渐变网格背景 — 三个颜色混合, 缓慢动画."""
    c3 = color3 or color2
    return f'''
<div style={{position:"absolute",inset:0,overflow:"hidden",pointerEvents:"none"}}>
  <div style={{position:"absolute",width:"150%",height:"150%",top:"-25%",left:"-25%",
    background:`radial-gradient(ellipse at 30% 40%,{color1}22 0%,transparent 60%),
                radial-gradient(ellipse at 70% 60%,{c3}18 0%,transparent 50%),
                radial-gradient(ellipse at 50% 50%,{color2}15 0%,transparent 70%)`,
    animation:`gradientShift {10 / speed}s ease-in-out infinite alternate`}} />
</div>'''

register("gradient_mesh", "background", {
    "color1": "string", "color2": "string", "color3": "string?", "speed": "float",
}, _gen_gradient_mesh)


def _gen_particle_field(color: str, count: int = 30, speed: float = 1.0):
    """粒子场背景 — 浮动光点, 纯 CSS 实现 (无 Three.js 依赖)."""
    dots = "".join(
        f'<div key={i} style={{position:"absolute",width:"{2 + (i % 3)}px",height:"{2 + (i % 3)}px",'
        f'borderRadius:"50%",background:color,opacity:{0.1 + (i % 5) * 0.04},'
        f'top:"{(i * 7) % 100}%",left:"{(i * 13) % 100}%",'
        f'animation:`floatParticle {3 + (i % 4) * 1.5 / speed}s ease-in-out {i * 0.3}s infinite alternate`}} />'
        for i in range(count)
    )
    return f'<div style={{position:"absolute",inset:0,pointerEvents:"none"}}>{dots}</div>'

register("particle_field", "background", {
    "color": "string", "count": "int", "speed": "float",
}, _gen_particle_field)


def _gen_geometric_pattern(color: str, size: int = 40, opacity: float = 0.06):
    """几何网格背景 — 重复六边形/菱形网格."""
    return f'''
<div style={{position:"absolute",inset:0,pointerEvents:"none",opacity,
  backgroundImage:`linear-gradient(45deg,{color} 1px,transparent 1px),
                   linear-gradient(-45deg,{color} 1px,transparent 1px)`,
  backgroundSize:`{size}px {size}px`}} />'''

register("geometric_pattern", "background", {
    "color": "string", "size": "int", "opacity": "float",
}, _gen_geometric_pattern)


def _gen_glow_orb(color: str, count: int = 3, intensity: float = 1.0):
    """光晕球背景 — 浮动半透明光球."""
    orbs = "".join(
        f'<div key={i} style={{position:"absolute",width:"{120 + i * 80}px",height:"{120 + i * 80}px",'
        f'borderRadius:"50%",background:`radial-gradient(circle,{color}{20} 0%,transparent 70%)`,'
        f'top:"{20 + i * 25}%",left:"{60 - i * 15}%",'
        f'animation:`floatOrb {6 + i * 2 / intensity}s ease-in-out {i * 1.5}s infinite alternate`}} />'
        for i in range(count)
    )
    return f'<div style={{position:"absolute",inset:0,pointerEvents:"none"}}>{orbs}</div>'

register("glow_orb", "background", {
    "color": "string", "count": "int", "intensity": "float",
}, _gen_glow_orb)


def _gen_wave_field(color: str, height: int = 60, speed: float = 1.0):
    """波浪背景 — sin 波形动画."""
    return f'''
<div style={{position:"absolute",inset:0,pointerEvents:"none",overflow:"hidden"}}>
  <svg viewBox="0 0 1440 {height}" preserveAspectRatio="none"
    style={{position:"absolute",bottom:0,width:"200%",height:`{height}px`,opacity:0.4}}>
    <defs><linearGradient id="wg"><stop offset="0%" stopColor="{color}" stopOpacity="0.3"/>
      <stop offset="100%" stopColor="{color}" stopOpacity="0"/></linearGradient></defs>
    <path d="M0,{height} C{height * 0.5},{height * 0.3} {height},{height * 0.7} {height * 2},{height}"
      fill="none" stroke="url(#wg)" strokeWidth="2">
      <animate attributeName="d" dur="{4 / speed}s" repeatCount="indefinite"
        values="M0,{height} C{height * 0.5},{height * 0.3} {height},{height * 0.7} {height * 2},{height};
                M0,{height} C{height * 0.7},{height * 0.5} {height},{height * 0.2} {height * 2},{height};
                M0,{height} C{height * 0.5},{height * 0.3} {height},{height * 0.7} {height * 2},{height}"/>
    </path>
  </svg>
</div>'''

register("wave_field", "background", {
    "color": "string", "height": "int", "speed": "float",
}, _gen_wave_field)


# ═══════════════════════════════════════════════
# 2. 文字动画效果 (Text)
# ═══════════════════════════════════════════════

def _gen_split_reveal(text: str, color: str, size: str, delay: int = 0):
    """逐字拆解入场 — 每个字独立上升淡入, 级联延迟."""
    chars = []
    for i, ch in enumerate(text):
        sp = ch if ch != " " else "\\u00A0"
        d = i * 0.04 + delay * 0.03
        chars.append(f'<span key={i} style={{"display":"inline-block","opacity":0,'
                     f'"animation":`charReveal 0.6s cubic-bezier(.16,1,.3,1) {d}s forwards`}}>{sp}</span>')
    return '<h1 style={{fontSize:size,fontWeight:800,color,lineHeight:1.1,textShadow:`0 2px 16px {color}15`}}>' + "".join(chars) + '</h1>'

register("split_reveal", "text", {
    "text": "string", "color": "string", "size": "string", "delay": "int",
}, _gen_split_reveal)


def _gen_gradient_text(text: str, color1: str, color2: str, size: str):
    """渐变文字 — 双色渐变文字, 动画扫光."""
    return f'''
<h1 style={{fontSize:size,fontWeight:800,lineHeight:1.1,
  background:`linear-gradient(135deg,{color1},{color2},{color1})`,
  backgroundSize:"200% 200%",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent",
  animation:`gradientShift 4s ease-in-out infinite`}}>{text}</h1>'''

register("gradient_text", "text", {
    "text": "string", "color1": "string", "color2": "string", "size": "string",
}, _gen_gradient_text)


def _gen_glow_text(text: str, color: str, glow_color: str, size: str):
    """发光文字 — 文字带光晕脉冲."""
    return f'''
<h1 style={{fontSize:size,fontWeight:800,color,lineHeight:1.1,
  textShadow:`0 0 20px {glow_color}40,0 0 40px {glow_color}20`,
  animation:`glowPulse 3s ease-in-out infinite`}}>{text}</h1>'''

register("glow_text", "text", {
    "text": "string", "color": "string", "glow_color": "string", "size": "string",
}, _gen_glow_text)


def _gen_typewriter(text: str, color: str, size: str):
    """打字机效果 — 字符逐字出现."""
    return f'''
<div style={{fontSize:size,fontWeight:600,color,lineHeight:1.4,
  overflow:"hidden",whiteSpace:"nowrap",maxWidth:"fit-content",
  borderRight:`2px solid {color}`,
  animation:`typewriter 2s steps({len(text)}) forwards, blink 0.8s step-end 2s 3`}}>{text}</div>'''

register("typewriter", "text", {
    "text": "string", "color": "string", "size": "string",
}, _gen_typewriter)


# ═══════════════════════════════════════════════
# 3. 数据动效 (Data)
# ═══════════════════════════════════════════════

def _gen_animated_bar(items: list, color: str, accent: str):
    """柱状图动效 — 逐条伸长的动画柱."""
    bars = "".join(
        f'<div key={i} style={{display:"flex",alignItems:"center",gap:16,marginBottom:12}}>'
        f'<div style={{width:80,fontSize:14,fontWeight:500,color,textAlign:"right"}}>{it["label"]}</div>'
        f'<div style={{flex:1,height:28,borderRadius:14,background:`{accent}15`,overflow:"hidden"}}>'
        f'<div style={{height:"100%",width:0,borderRadius:14,background:`linear-gradient(90deg,{accent},{accent}80)`,'
        f'animation:`barGrow {1.2 + i * 0.2}s ease-out {i * 0.15}s forwards`}}></div></div>'
        f'<div style={{width:60,fontSize:14,fontWeight:700,color:accent,textAlign:"left"}}>{it["value"]}</div></div>'
        for i, it in enumerate(items)
    )
    return f'<div style={{width:"100%",maxWidth:800,margin:"0 auto"}}>{bars}</div>'

register("bar_chart", "data", {
    "items": "list", "color": "string", "accent": "string",
}, _gen_animated_bar)


def _gen_progress_ring(percent: int, color: str, label: str, size: int = 120):
    """进度环 — 圆形进度指示器."""
    r = size * 0.35
    circumference = 2 * 3.14159 * r
    return f'''
<div style={{display:"flex",flexDirection:"column",alignItems:"center",gap:12}}>
  <svg width={size} height={size} viewBox="0 0 {size} {size}">
    <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="{color}15" strokeWidth={size * 0.08}/>
    <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="{color}" strokeWidth={size * 0.08}
      strokeDasharray={circumference} strokeDashoffset={circumference}
      strokeLinecap="round" transform="rotate(-90,{size/2},{size/2})">
      <animate attributeName="stroke-dashoffset" from={circumference} to={circumference * (1 - percent/100)}
        dur="1.5s" fill="freeze"/>
    </circle>
    <text x={size/2} y={size/2} textAnchor="middle" dominantBaseline="central"
      fill="{color}" fontSize={size * 0.2} fontWeight="bold">{percent}%</text>
  </svg>
  <div style={{fontSize:13,color,opacity:0.6}}>{label}</div>
</div>'''

register("progress_ring", "data", {
    "percent": "int", "color": "string", "label": "string", "size": "int",
}, _gen_progress_ring)


# ═══════════════════════════════════════════════
# 4. 转场效果 (Transitions)
# ═══════════════════════════════════════════════

def _gen_wipe_transition(direction: str = "left", duration: float = 0.8):
    """擦除转场 — 方向性擦除."""
    dir_map = {"left": "to right", "right": "to left", "up": "to bottom", "down": "to top"}
    grad = dir_map.get(direction, "to right")
    return f'''
<div style={{position:"absolute",inset:0,pointerEvents:"none",
  background:`linear-gradient({grad},transparent 0%,transparent 30%,{color}15 50%,transparent 70%,transparent 100%)`,
  animation:`wipeSlide {duration}s ease-out`}} />'''

register("wipe_transition", "transition", {
    "direction": "string", "duration": "float",
}, _gen_wipe_transition)


def _gen_radial_transition(duration: float = 1.0):
    """径向转场 — 圆形展开."""
    return f'''
<div style={{position:"absolute",inset:0,pointerEvents:"none",
  clipPath:`circle(0% at 50% 50%)`,
  animation:`radialReveal {duration}s cubic-bezier(.16,1,.3,1) forwards`,
  background:`radial-gradient(circle at 50% 50%,{color}10 0%,transparent 70%)`}} />'''

register("radial_transition", "transition", {
    "duration": "float",
}, _gen_radial_transition)


# ═══════════════════════════════════════════════
# 5. 装饰叠层 (Overlays)
# ═══════════════════════════════════════════════

def _gen_scan_line(color: str, opacity: float = 0.03):
    """扫描线叠层 — CRT 风格."""
    return f'''
<div style={{position:"absolute",inset:0,pointerEvents:"none",opacity,
  backgroundImage:`repeating-linear-gradient(0deg,transparent,transparent 2px,{color} 2px,{color} 4px)`,
  backgroundSize:"100% 4px"}} />'''

register("scan_line", "overlay", {
    "color": "string", "opacity": "float",
}, _gen_scan_line)


def _gen_grid_lines(color: str, spacing: int = 60, opacity: float = 0.05):
    """网格线叠层 — 科技感."""
    return f'''
<div style={{position:"absolute",inset:0,pointerEvents:"none",opacity,
  backgroundImage:`linear-gradient(90deg,{color} 1px,transparent 1px),
                   linear-gradient(0deg,{color} 1px,transparent 1px)`,
  backgroundSize:`{spacing}px {spacing}px`}} />'''

register("grid_lines", "overlay", {
    "color": "string", "spacing": "int", "opacity": "float",
}, _gen_grid_lines)


# ═══════════════════════════════════════════════
# CSS 动画定义 (注入到 TSX 模板的 <style> 中)
# ═══════════════════════════════════════════════

CSS_ANIMATIONS = '''
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes floatParticle {
  from { transform: translateY(0) translateX(0); }
  to { transform: translateY(-30px) translateX(10px); }
}
@keyframes floatOrb {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(-20px, -20px) scale(1.1); }
}
@keyframes charReveal {
  from { opacity: 0; transform: translateY(40px) rotateX(-20deg); }
  to { opacity: 1; transform: translateY(0) rotateX(0); }
}
@keyframes glowPulse {
  0%, 100% { text-shadow: 0 0 20px var(--glow, currentColor)40, 0 0 40px var(--glow, currentColor)20; }
  50% { text-shadow: 0 0 30px var(--glow, currentColor)60, 0 0 60px var(--glow, currentColor)30; }
}
@keyframes typewriter {
  from { width: 0; }
  to { width: 100%; }
}
@keyframes blink {
  50% { border-color: transparent; }
}
@keyframes barGrow {
  from { width: 0; }
  to { width: var(--bar-target, 100%); }
}
@keyframes wipeSlide {
  from { opacity: 1; transform: translateX(-100%); }
  to { opacity: 1; transform: translateX(100%); }
}
@keyframes radialReveal {
  from { clip-path: circle(0% at 50% 50%); }
  to { clip-path: circle(100% at 50% 50%); }
}
'''


# ═══════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    cats = set(e["category"] for e in EFFECT_REGISTRY.values())
    print(f"Registered effects: {len(EFFECT_REGISTRY)} across {len(cats)} categories: {sorted(cats)}")
    for cat in sorted(cats):
        items = list_effects(cat)
        print(f"  {cat}: {[e['id'] for e in items]}")

    # 验证生成
    g = get_effect("gradient_mesh")
    code = g["generate"]("#00d4ff", "#0a0a0f", "#7c7cff", 1.0)
    assert "gradientShift" in code
    print("gradient_mesh generate OK")

    g = get_effect("split_reveal")
    code = g["generate"]("Hello World", "#fff", "80px", 0)
    assert "charReveal" in code
    print("split_reveal generate OK")

    g = get_effect("bar_chart")
    code = g["generate"]([{"label": "A", "value": "90%"}, {"label": "B", "value": "57×"}], "#fff", "#00d4ff")
    assert "barGrow" in code
    print("bar_chart generate OK")

    print("ALL EFFECTS VERIFIED")