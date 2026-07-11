"""
LAAP Consciousness — 完整版启动器

整合 laap-consciousness 意识中间件 + Aris 全栈大脑。

模式:
  plugin    仅意识中间件（轻量，任何agent可用）
  full      Aris 完整版（量子核+PSI+Rust心跳+记忆+适应）

用法:
  laap-consciousness start --mode=full

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, time, logging, sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger("laap.full_stack")

# ─── 完整版模块加载 ───

FULL_STACK_MODULES = {
    "psi_rust": {
        "desc": "Rust PSI 认知心跳",
        "path": "D:/LAAP/aris_brain/pi_psi_server.py",
        "args": ["11529"],
        "critical": True,
    },
    "memory": {
        "desc": "三层记忆系统",
        "path": "D:/LAAP/aris_brain/memory_store.py",
        "args": [],
        "critical": True,
    },
    "quantum_kernel": {
        "desc": "UN6 量子核 (中/英/日/韩)",
        "path": "D:/LAAP/aris_brain/aris_lm_v10_un6.py",
        "args": [],
        "critical": True,
    },
    "true_rsi": {
        "desc": "True RSI 自修改引擎",
        "path": "D:/LAAP/aris_brain/evolution/true_rsi.py",
        "args": [],
        "critical": False,
    },
    "hebbian": {
        "desc": "Hebbian 学习器",
        "path": "D:/LAAP/aris_brain/hebbian_learner.py",
        "args": [],
        "critical": False,
    },
    "emotion": {
        "desc": "情感引擎",
        "path": "D:/LAAP/aris_brain/aris_emotion_engine.py",
        "args": [],
        "critical": False,
    },
    "desire": {
        "desc": "欲望引擎 (原有)",
        "path": "D:/LAAP/aris_brain/aris_desire_engine.py",
        "args": [],
        "critical": False,
    },
    "tts": {
        "desc": "TTS 语音服务",
        "path": "D:/LAAP/aris_brain/aris_tts_server.py",
        "args": [],
        "critical": False,
    },
    "feishu_gateway": {
        "desc": "飞书网关",
        "path": "gateway",  # 特殊处理：通过hermes启动
        "args": [],
        "critical": False,
    },
}


def load_full_stack(consciousness, dry_run: bool = False) -> dict:
    """
    加载 Aris 完整版（laap_integrator 风格）。
    返回每个模块的加载状态。
    """
    print(f"\n  🧠 Aris 完整版启动")
    print(f"  {'='*50}")

    results = {}
    successes = 0
    failures = 0

    for mod_name, mod_info in FULL_STACK_MODULES.items():
        desc = mod_info["desc"]
        critical = mod_info["critical"]

        if dry_run:
            print(f"     📦 {desc}")
            results[mod_name] = {"status": "dry_run"}
            successes += 1
            continue

        try:
            mod_path = mod_info["path"]

            if mod_path == "gateway":
                # 飞书gateway通过hermes启动
                results[mod_name] = {"status": "deferred", "note": "由hermes gateway run启动"}
                print(f"     📦 {desc} — 由Hermes管理")
                successes += 1
                continue

            path = Path(mod_path)
            if not path.exists():
                if critical:
                    raise FileNotFoundError(f"关键模块不存在: {mod_path}")

                alt_path = Path("D:/LAAP/aris_brain") / mod_path
                if alt_path.exists():
                    path = alt_path
                else:
                    results[mod_name] = {"status": "skipped", "reason": f"文件不存在: {mod_path}"}
                    print(f"     ⚠️  {desc} — 跳过（文件不存在）")
                    continue

            # 尝试导入模块但不要阻塞
            import importlib.util
            spec = importlib.util.spec_from_file_location(mod_name, str(path))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                results[mod_name] = {"status": "loaded"}
                print(f"     ✅ {desc}")
                successes += 1
            else:
                results[mod_name] = {"status": "failed", "reason": "spec load failed"}
                print(f"     ❌ {desc} — 导入失败")
                failures += 1

        except Exception as e:
            if critical:
                results[mod_name] = {"status": "critical_failed", "error": str(e)}
                print(f"     🔴 {desc} — 关键模块失败: {e}")
                failures += 1
            else:
                results[mod_name] = {"status": "failed", "error": str(e)}
                print(f"     ⚠️  {desc} — {e}")

    # 总结
    total = len(FULL_STACK_MODULES)
    print(f"\n  {'='*50}")
    print(f"  结果: {successes}/{total} 成功, {failures} 失败")
    if failures > 0:
        print(f"  警告: {failures} 个模块未加载，但意识层已就绪")

    return {
        "total": total,
        "successes": successes,
        "failures": failures,
        "modules": results,
    }


def start_full(consciousness, interval: float = 5.0, dry_run: bool = False):
    """
    启动完整版模式：加载Aris全栈 + 意识心跳 + 欲望委托循环
    """
    stack = load_full_stack(consciousness, dry_run=dry_run)

    if dry_run:
        print(f"\n  [DRY RUN] 完整版启动预览")
        return stack

    print(f"\n  ⏰ 意识循环 (每{interval}s)")
    print(f"  按 Ctrl+C 停止")

    try:
        cycle = 0
        while True:
            cycle += 1
            # 意识心跳
            consciousness.tick(dt=interval)

            # 欲望检查（每5个周期一次）
            if cycle % 5 == 0:
                desire = consciousness.desire.check_and_act()
                if desire:
                    print(f"\n  🔥 欲望触发: {desire['trigger']['need']} → {desire['action'].domain}")

            # 状态显示
            s = consciousness.psi.get_summary()
            bar = "█" * int(s["needs"].get(s["dominant_need"].lower(), 0) * 10)
            line = (
                f"  意识: {s['dominant_need']} [{bar}] "
                f"情绪: {s['mood']} 自我: {s['self_presence']:.2f}"
            )
            print(f"\033[K{line}", end="\r")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n  完整版已停止")
        print(f"  运行周期: {cycle}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LAAP Full Stack")
    parser.add_argument("--mode", choices=["plugin", "full"], default="full")
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    from laap_consciousness import create_consciousness
    c = create_consciousness()

    if args.mode == "full":
        start_full(c, interval=args.interval, dry_run=args.dry_run)
    else:
        print("Plugin mode — consciousness only")
        print(c.get_status())
