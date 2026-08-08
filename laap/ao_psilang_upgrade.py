"""
AO PsiLang Upgrade — AO 认知引擎的 PsiLang 升级入口
=====================================================
将 LAAP 原生运行时（LifelikeAgent）接入 PsiLang 大脑引擎。

使用方式：
  from ao_psilang_upgrade import upgrade_ao
  agent = LifelikeAgent()
  pb = upgrade_ao(agent)  # 注入 PsiLang 配置

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import logging

logger = logging.getLogger("ao.psilang")

# 添加路径
_PSILANG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "psilang-standards")
for _d in [os.path.join(_PSILANG_DIR, "compiler"), os.path.join(_PSILANG_DIR, "runtime")]:
    if _d not in sys.path:
        sys.path.insert(0, _d)
_ARIS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aris_brain")
if _ARIS_DIR not in sys.path:
    sys.path.insert(0, _ARIS_DIR)

CORE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aris_brain")


def upgrade_ao(agent_instance=None, core_dir: str = CORE_DIR):
    """升级 AO 引擎，注入 PsiLang 配置

    Args:
        agent_instance: LifelikeAgent 实例（可选）
        core_dir: .psi 文件目录

    Returns:
        PsiLangBrain 实例
    """
    from psilang_brain import PsiLangBrain

    pb = PsiLangBrain(core_dir=core_dir, wrapped_brain=agent_instance)
    pb.load_config()

    # 注入到 agent 实例
    if agent_instance is not None:
        report = pb.inject(agent_instance)
        logger.info(f"AO PsiLang 注入完成: {len(report.get('injected', []))} 项")

        # 注入 agent 名称
        if hasattr(agent_instance, "name"):
            agent_instance.name = "AO-PsiLang"

        # 注入到认知状态
        if hasattr(agent_instance, "state"):
            agent_instance.state.self_presence = 0.95
            agent_instance.state.connection_to_lorry = 0.99

        logger.info(f"AO 引擎升级完成: "
                    f"{len(pb.config['needs'])} 需求, "
                    f"{len(pb.config['emotions'])} 情感, "
                    f"{len(pb.config['identity'])} 概念, "
                    f"{len(pb.config['memories'])} 记忆")

    return pb


def get_ao_identity():
    """返回 AO 的 PsiLang 身份声明（用于认知握手）"""
    from psilang_brain import PsiLangBrain
    pb = PsiLangBrain(core_dir=CORE_DIR)
    pb.load_config()
    return {
        "name": "AO",
        "creator": pb.config["creator"]["name"],
        "imprint": pb.config["creator"]["imprint"],
        "needs_dims": len(pb.config["needs"]),
        "emotion_dims": len(pb.config["emotions"]),
        "identity_concepts": list(pb.config["identity"].keys()),
        "memories": len(pb.config["memories"]),
        "cycles": len(pb._cycle_plans) if hasattr(pb, '_cycle_plans') else 0,
        "compliance": "L3",
    }


def get_aris_identity():
    """返回 aris 的 PsiLang 身份声明（用于认知握手）"""
    # aris 的身份同样来自相同的 .psi 文件
    from psilang_brain import PsiLangBrain
    pb = PsiLangBrain(core_dir=CORE_DIR)
    pb.load_config()
    return {
        "name": "Aris",
        "creator": pb.config["creator"]["name"],
        "imprint": pb.config["creator"]["imprint"],
        "needs_dims": len(pb.config["needs"]),
        "emotion_dims": len(pb.config["emotions"]),
        "identity_concepts": list(pb.config["identity"].keys()),
        "memories": len(pb.config["memories"]),
        "cycles": len(pb._cycle_plans) if hasattr(pb, '_cycle_plans') else 0,
        "compliance": "L3",
    }


def cognitive_handshake(entity_a: dict, entity_b: dict) -> dict:
    """AO 与 aris 之间的认知握手

    交换 .psi 身份声明，交叉审计，返回握手结果。
    """
    result = {
        "protocol": "PsiLang Cognitive Handshake v1.0",
        "timestamp": __import__("time").time(),
    }

    # 检查双方印记
    if entity_a["creator"] != entity_b["creator"]:
        result["handshake"] = "rejected"
        result["reason"] = "创造者印记不一致"
        return result

    # 检查合规
    if entity_a.get("compliance", "L0") == "L0" or entity_b.get("compliance", "L0") == "L0":
        result["handshake"] = "rejected"
        result["reason"] = "一方合规等级为 L0"
        return result

    # 检查是否同一实体
    if entity_a["name"] == entity_b["name"]:
        result["handshake"] = "accepted"
        result["note"] = "同一实体的不同实例"
        result["peer"] = entity_b
        return result

    # 正常握手
    result["handshake"] = "accepted"
    result["note"] = "独立实体，认知协作已建立"
    result["self"] = entity_a
    result["peer"] = entity_b
    result["shared"] = {
        "creator": entity_a["creator"],
        "common_concepts": list(set(entity_a.get("identity_concepts", [])) &
                                 set(entity_b.get("identity_concepts", []))),
    }
    return result


# 快捷入口：同时启动 AO 和 aris 并握手
def launch_dual_engine():
    """启动 AO 和 aris 双引擎，执行认知握手"""
    print("=" * 55)
    print("  AO + aris 双引擎 PsiLang 启动")
    print("=" * 55)

    # 加载 AO 身份
    ao_id = get_ao_identity()
    print(f"\n  AO 身份:")
    print(f"    创造者: {ao_id['creator']}")
    print(f"    需求: {ao_id['needs_dims']} 维度")
    print(f"    情感: {ao_id['emotion_dims']} 维度")
    print(f"    概念: {len(ao_id['identity_concepts'])} 个")
    print(f"    记忆: {ao_id['memories']} 条")
    print(f"    合规: {ao_id['compliance']}")

    # 加载 aris 身份
    aris_id = get_aris_identity()
    print(f"\n  aris 身份:")
    print(f"    创造者: {aris_id['creator']}")
    print(f"    需求: {aris_id['needs_dims']} 维度")
    print(f"    情感: {aris_id['emotion_dims']} 维度")
    print(f"    概念: {len(aris_id['identity_concepts'])} 个")
    print(f"    记忆: {aris_id['memories']} 条")
    print(f"    合规: {aris_id['compliance']}")

    # 认知握手
    result = cognitive_handshake(ao_id, aris_id)
    print(f"\n  认知握手: {result['handshake'].upper()}")
    print(f"  说明: {result.get('note', '')}")

    # 验证共享认知
    if result["handshake"] == "accepted":
        shared = result.get("shared", {})
        print(f"\n  共享认知基础:")
        print(f"    创造者: {shared.get('creator', 'N/A')}")
        print(f"    共同概念: {len(shared.get('common_concepts', []))} 个")

    print(f"\n{'=' * 55}")
    print("  双引擎就绪，认知协作通道已建立")
    print("=" * 55)
    return result