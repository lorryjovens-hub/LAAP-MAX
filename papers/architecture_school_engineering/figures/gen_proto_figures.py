# -*- coding: utf-8 -*-
"""
Living Runtime 与认知编排系统原型架构 - 配图生成脚本
生成 5 幅 300 DPI 配图，色盲友好配色，中文标签。
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, Ellipse
import matplotlib.patheffects as pe
import networkx as nx

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 10

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# 色盲友好调色板（cividis / tab10 派生）
C_MIND = "#3B0F70"      # 意识层 紫黑
C_MIND2 = "#7D2E8E"     # 意识层辅
C_BODY = "#1F6C8A"      # 身体层 青
C_BODY2 = "#35A6BE"     # 身体层辅
C_BUS = "#B8410B"       # 总线 橙
C_MEM = "#5E9C3A"       # 记忆 绿
C_ALIGN = "#A52A2A"     # 对齐 红棕
C_PROTOCOL = "#3A3A8E"  # 协议 深蓝紫
C_MIG = "#8C564B"       # 迁移 棕
C_LIFE = "#4F4F4F"      # 生命周期 灰
C_ACCENT = "#E6AB02"    # 强调 金黄
C_GREEN = "#66A61E"
C_BLUE = "#1F78B4"
C_RED = "#E31A1C"


# ----------------------------------------------------------------------------
# 图 1: Living Runtime 整体架构（8 组件分层）
# ----------------------------------------------------------------------------
def fig1_architecture():
    fig, ax = plt.subplots(figsize=(13, 9), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # 标题
    ax.text(7, 9.5, "Living Runtime 整体架构：意识-身体双层 + 8 核心组件",
            ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(7, 9.05, "Mind Layer 唯一连续可迁移 | Body Layer 可替换 | CognitiveBus 频率失配处理",
            ha="center", va="center", fontsize=9, color="#555")

    # 意识层背景
    mind_bg = FancyBboxPatch((0.3, 5.3), 13.4, 3.4,
                            boxstyle="round,pad=0.02,rounding_size=0.15",
                            linewidth=1.4, edgecolor=C_MIND, facecolor=C_MIND, alpha=0.06)
    ax.add_patch(mind_bg)
    ax.text(0.5, 8.55, "意识层 Mind Layer（唯一连续可迁移）",
            fontsize=11, color=C_MIND, fontweight="bold")

    # 身体层背景
    body_bg = FancyBboxPatch((0.3, 0.4), 13.4, 4.6,
                            boxstyle="round,pad=0.02,rounding_size=0.15",
                            linewidth=1.4, edgecolor=C_BODY, facecolor=C_BODY, alpha=0.06)
    ax.add_patch(body_bg)
    ax.text(0.5, 4.85, "身体层 Body Layer（感知 / 执行 / 可替换 / 跨端）",
            fontsize=11, color=C_BODY, fontweight="bold")

    # 意识层组件（5 个：MindLayer / MemoryVault / AlignmentGuard / ProtocolStack / LifecycleManager）
    mind_comps = [
        ("MindLayer\n意识状态", 1.6, 6.7, C_MIND2),
        ("MemoryVault\nMeMo 记忆", 4.0, 6.7, C_MEM),
        ("AlignmentGuard\n对齐守卫", 6.4, 6.7, C_ALIGN),
        ("ProtocolStack\n8 协议族", 8.8, 6.7, C_PROTOCOL),
        ("LifecycleManager\n生命周期", 11.2, 6.7, C_LIFE),
    ]
    for name, x, y, c in mind_comps:
        box = FancyBboxPatch((x - 0.95, y - 0.55), 1.9, 1.1,
                            boxstyle="round,pad=0.02,rounding_size=0.08",
                            linewidth=1.6, edgecolor=c, facecolor="white")
        ax.add_patch(box)
        ax.text(x, y, name, ha="center", va="center", fontsize=9, fontweight="bold", color=c)

    # CognitiveBus 横贯总线
    bus = FancyBboxPatch((0.6, 4.95), 12.8, 0.35,
                        boxstyle="round,pad=0.01,rounding_size=0.05",
                        linewidth=1.0, edgecolor=C_BUS, facecolor=C_BUS, alpha=0.85)
    ax.add_patch(bus)
    ax.text(7, 5.13, "CognitiveBus 认知总线  (PSI 1-2kHz  <-->  Harness 0.1-1Hz  |  TTL=30s  |  断路器 100 drops/s)",
            ha="center", va="center", fontsize=9, color="white", fontweight="bold")

    # 身体层组件（2 个 + 迁移服务）
    body_comps = [
        ("BodyLayer\n感知 / 执行", 2.5, 2.6, C_BODY2),
        ("MigrationService\n热迁移 < 2s", 7.0, 2.6, C_MIG),
        ("外部设备 A\nWeb / Desktop", 11.0, 3.4, C_BODY),
        ("外部设备 B\nIoT / 车载", 11.0, 1.6, C_BODY),
    ]
    for name, x, y, c in body_comps:
        box = FancyBboxPatch((x - 1.05, y - 0.5), 2.1, 1.0,
                            boxstyle="round,pad=0.02,rounding_size=0.08",
                            linewidth=1.6, edgecolor=c, facecolor="white")
        ax.add_patch(box)
        ax.text(x, y, name, ha="center", va="center", fontsize=8.5, fontweight="bold", color=c)

    # 连接箭头：意识层 ↔ Bus
    for x in [1.6, 4.0, 6.4, 8.8, 11.2]:
        ax.annotate("", xy=(x, 5.32), xytext=(x, 6.15),
                    arrowprops=dict(arrowstyle="<->", color=C_MIND, lw=1.0, alpha=0.7))
    # 身体层 ↔ Bus
    for x in [2.5, 7.0]:
        ax.annotate("", xy=(x, 4.95), xytext=(x, 3.1),
                    arrowprops=dict(arrowstyle="<->", color=C_BODY, lw=1.0, alpha=0.7))
    # MigrationService → 设备 A/B
    ax.annotate("", xy=(9.95, 3.4), xytext=(8.05, 2.6),
                arrowprops=dict(arrowstyle="->", color=C_MIG, lw=1.2, ls="--"))
    ax.annotate("", xy=(9.95, 1.6), xytext=(8.05, 2.6),
                arrowprops=dict(arrowstyle="->", color=C_MIG, lw=1.2, ls="--"))
    # MindLayer ↔ MigrationService 跨层调用
    ax.annotate("", xy=(6.0, 2.6), xytext=(1.6, 6.15),
                arrowprops=dict(arrowstyle="<->", color=C_ACCENT, lw=1.0, ls=":",
                                connectionstyle="arc3,rad=0.25"))

    # 图例
    legend_items = [
        mpatches.Patch(color=C_MIND2, label="意识层组件"),
        mpatches.Patch(color=C_BODY2, label="身体层组件"),
        mpatches.Patch(color=C_BUS, label="认知总线"),
        mpatches.Patch(color=C_MIG, label="迁移服务"),
    ]
    ax.legend(handles=legend_items, loc="lower center", ncol=4, fontsize=8.5, frameon=False,
              bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "living_runtime_arch.png")
    plt.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved:", out)


# ----------------------------------------------------------------------------
# 图 2: 跨端热迁移时序图（含 < 2s 关键路径分解）
# ----------------------------------------------------------------------------
def fig2_migration_sequence():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9.5)
    ax.axis("off")

    ax.text(7, 9.1, "跨端热迁移时序图：设备 A → 云端 → 设备 B  (< 2s 关键路径)",
            ha="center", fontsize=14, fontweight="bold")
    ax.text(7, 8.7, "snapshot 0.3s + 传输 0.8s + restore 0.3s + 验证 0.2s + 恢复 0.3s = 1.9s",
            ha="center", fontsize=10, color=C_ALIGN, fontweight="bold")

    # 4 条生命线
    actors = [
        ("设备 A BodyLayer", 1.5, C_BODY),
        ("MindLayer\n+ LifecycleManager", 4.5, C_MIND2),
        ("云端 MigrationService", 8.0, C_MIG),
        ("设备 B BodyLayer", 11.5, C_BODY2),
    ]
    y_top = 8.2
    y_bot = 0.6
    for name, x, c in actors:
        box = FancyBboxPatch((x - 1.1, y_top), 2.2, 0.5,
                            boxstyle="round,pad=0.02,rounding_size=0.06",
                            linewidth=1.5, edgecolor=c, facecolor="white")
        ax.add_patch(box)
        ax.text(x, y_top + 0.25, name, ha="center", va="center", fontsize=9, fontweight="bold", color=c)
        ax.plot([x, x], [y_top, y_bot], color=c, lw=1.0, ls="--", alpha=0.6)

    # 步骤（y, source, target, label, color, duration_text）
    steps = [
        (7.6, 1.5, 4.5, "① pause() 暂停执行", C_BODY, "0.05s"),
        (6.95, 4.5, 4.5, "② snapshot() 认知状态快照\n(状态JSON + MeMo权重 + 因果图)", C_MIND2, "0.30s"),
        (6.25, 4.5, 8.0, "③ 上传快照 + LAAP-SYNC", C_MIG, "0.40s"),
        (5.65, 8.0, 8.0, "④ 增量同步 + 校验哈希", C_MIG, "0.40s"),
        (4.95, 8.0, 11.5, "⑤ 下发至设备 B + LAAP-ID 验证", C_BODY2, "0.20s"),
        (4.25, 11.5, 4.5, "⑥ restore(snap) 状态恢复", C_MIND2, "0.30s"),
        (3.55, 4.5, 4.5, "⑦ AlignmentGuard KL 校验 < 0.5", C_ALIGN, "0.20s"),
        (2.85, 4.5, 11.5, "⑧ 绑定设备 B + resume() 恢复执行", C_BODY2, "0.30s"),
        (2.15, 11.5, 1.5, "⑨ 通知设备 A 进入 suspended", C_BODY, "异步"),
    ]
    for y, src, dst, label, c, dur in steps:
        # 自调用
        if src == dst:
            rect = FancyBboxPatch((src - 0.9, y - 0.25), 1.8, 0.5,
                                boxstyle="round,pad=0.02,rounding_size=0.04",
                                linewidth=1.0, edgecolor=c, facecolor=c, alpha=0.12)
            ax.add_patch(rect)
            ax.text(src, y, label, ha="center", va="center", fontsize=8, color=c)
            ax.text(src + 1.05, y, dur, ha="left", va="center", fontsize=7.5, color=c, fontweight="bold")
        else:
            ax.annotate("", xy=(dst, y), xytext=(src, y),
                        arrowprops=dict(arrowstyle="->", color=c, lw=1.4))
            midx = (src + dst) / 2
            ax.text(midx, y + 0.12, label, ha="center", va="bottom", fontsize=8, color=c)
            ax.text(midx, y - 0.18, dur, ha="center", va="top", fontsize=7.5, color=c, fontweight="bold")

    # 关键路径时间带
    ax.add_patch(Rectangle((0.3, 1.6), 13.4, 6.3, linewidth=1.2, edgecolor=C_ALIGN,
                          facecolor="none", ls="--"))
    ax.text(0.4, 1.45, "关键路径同步耗时窗口 = 1.9s < 2s 目标", fontsize=9.5, color=C_ALIGN, fontweight="bold")

    # 异常处理标注
    ax.text(7, 0.85, "异常处理：哈希校验失败 → LifecycleManager.rollback() → 重试 1 次 / 超时降级设备 A",
            ha="center", fontsize=8.5, color="#555", style="italic")

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "migration_sequence.png")
    plt.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved:", out)


# ----------------------------------------------------------------------------
# 图 3: 认知任务编排流程图
# ----------------------------------------------------------------------------
def fig3_cognitive_orchestration():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    ax.text(7, 8.1, "认知任务编排流程图：意图 → 感知 → 推理 → 决策 → 执行 → 验证 → 反馈",
            ha="center", fontsize=14, fontweight="bold")
    ax.text(7, 7.75, "对应论文 9 段流水线（PRE_PERCEPTION → ... → SELF_IMPROVING）",
            ha="center", fontsize=9, color="#555")

    nodes = [
        # (id, x, y, label, color, w, h)
        ("user", 1.0, 4.0, "用户意图", C_ACCENT, 1.4, 0.8),
        ("body", 2.7, 4.0, "BodyLayer\n感知", C_BODY, 1.5, 0.8),
        ("bus", 4.4, 4.0, "CognitiveBus\n频率失配", C_BUS, 1.5, 0.8),
        ("mind", 6.3, 5.4, "MindLayer\n状态", C_MIND2, 1.5, 0.8),
        ("memo", 6.3, 3.6, "MemoryVault\nMeMo 查询", C_MEM, 1.5, 0.8),
        ("causal", 8.2, 4.5, "因果图\n推理", C_PROTOCOL, 1.5, 0.8),
        ("align", 9.9, 5.4, "AlignmentGuard\n六维检查", C_ALIGN, 1.6, 0.8),
        ("decide", 9.9, 3.6, "决策\n(ReAct + RSI)", C_LIFE, 1.6, 0.8),
        ("exec", 11.7, 4.5, "执行\nTool/COM", C_BODY2, 1.4, 0.8),
        ("verify", 11.7, 2.6, "验证\nKL 监控", C_ALIGN, 1.4, 0.8),
        ("feedback", 6.3, 1.8, "反馈循环\n(self_improve)", C_GREEN, 1.5, 0.8),
    ]

    pos = {n[0]: (n[1], n[2]) for n in nodes}
    for nid, x, y, label, c, w, h in nodes:
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                            boxstyle="round,pad=0.02,rounding_size=0.1",
                            linewidth=1.6, edgecolor=c, facecolor="white")
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=8.5, fontweight="bold", color=c)

    edges = [
        ("user", "body"), ("body", "bus"), ("bus", "mind"), ("bus", "memo"),
        ("mind", "causal"), ("memo", "causal"),
        ("causal", "align"), ("causal", "decide"),
        ("align", "exec"), ("decide", "exec"),
        ("exec", "verify"), ("verify", "feedback"),
        ("feedback", "memo"), ("feedback", "mind"),
    ]
    for s, t in edges:
        x1, y1 = pos[s]
        x2, y2 = pos[t]
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=1.2,
                                    connectionstyle="arc3,rad=0.08"))

    # 时间轴标注（关键步骤）
    annotations = [
        (4.4, 4.6, "TTL=30s", C_BUS),
        (6.3, 4.05, "0-token 算法\n90% 节省", C_MEM),
        (9.9, 5.85, "KL<0.5\nmax_rev=5", C_ALIGN),
        (11.7, 5.0, "MCP 兼容", C_BODY2),
        (6.3, 1.3, "σ 稳定性 5×\n速度 57×", C_GREEN),
    ]
    for x, y, t, c in annotations:
        ax.text(x, y, t, ha="center", va="center", fontsize=7.5, color=c,
                style="italic", fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2, foreground="white")])

    # 图例
    legend = [
        mpatches.Patch(color=C_MIND2, label="意识层"),
        mpatches.Patch(color=C_BODY, label="感知/执行"),
        mpatches.Patch(color=C_BUS, label="认知总线"),
        mpatches.Patch(color=C_MEM, label="记忆"),
        mpatches.Patch(color=C_ALIGN, label="对齐守卫"),
        mpatches.Patch(color=C_GREEN, label="反馈循环"),
    ]
    ax.legend(handles=legend, loc="lower center", ncol=6, fontsize=8, frameon=False,
              bbox_to_anchor=(0.5, -0.03))

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "cognitive_orchestration.png")
    plt.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved:", out)


# ----------------------------------------------------------------------------
# 图 4: 8 组件接口契约图
# ----------------------------------------------------------------------------
def fig4_component_interfaces():
    fig, ax = plt.subplots(figsize=(13.5, 9), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9.5)
    ax.axis("off")

    ax.text(7, 9.1, "8 核心组件接口契约图",
            ha="center", fontsize=14, fontweight="bold")
    ax.text(7, 8.75, "职责 / 接口契约 / 关键数据 / 状态机 / 失败处理",
            ha="center", fontsize=10, color="#555")

    # 4 列 × 2 行
    comps = [
        # (name, x, y, color, interfaces, key_data)
        ("1. MindLayer\n意识层", 1.8, 6.7, C_MIND2,
         "snapshot()\nrestore(snap)\nmigrate_to(target)",
         "认知状态 JSON\nMeMo 权重\n因果图快照"),
        ("2. BodyLayer\n身体层", 5.2, 6.7, C_BODY,
         "perceive()\nact(action)",
         "Web / Desktop\nIoT 多形态"),
        ("3. CognitiveBus\n认知总线", 8.6, 6.7, C_BUS,
         "publish(event)\nsubscribe(filter)\nrate_limit(TTL=30s)",
         "断路器 100 drops/s\nPSI 1-2kHz\nHarness 0.1-1Hz"),
        ("4. MemoryVault\n记忆保险库", 12.0, 6.7, C_MEM,
         "memo_query(query)\nconsolidate(exp)",
         "Qwen2.5-0.5B\n3 epochs / lr=1e-4"),
        ("5. AlignmentGuard\n对齐守卫", 1.8, 3.2, C_ALIGN,
         "check_before(action)\nmonitor_drift()\nrollback()",
         "KL=0.5 / rev=5\nmax_incr=0.2\ncov=0.7"),
        ("6. ProtocolStack\n协议族栈", 5.2, 3.2, C_PROTOCOL,
         "send(protocol, msg)\nrecv(protocol)",
         "LIFE/EVO/ID/COOP\n/SYNC/COM/TOOL/UI"),
        ("7. MigrationService\n迁移服务", 8.6, 3.2, C_MIG,
         "begin_migration(target)\ncommit()\nrollback()",
         "预拷贝 + 增量同步\n< 2s 热迁移"),
        ("8. LifecycleManager\n生命周期", 12.0, 3.2, C_LIFE,
         "spawn(parent)\nterminate(id)\nfork(parent)",
         "embryo/alive\nsuspended/forked\nterminated"),
    ]
    for name, x, y, c, iface, data in comps:
        box = FancyBboxPatch((x - 1.45, y - 1.35), 2.9, 2.7,
                            boxstyle="round,pad=0.02,rounding_size=0.08",
                            linewidth=1.8, edgecolor=c, facecolor="white")
        ax.add_patch(box)
        ax.text(x, y + 1.05, name, ha="center", va="center", fontsize=9.5, fontweight="bold", color=c)
        # 接口
        ax.add_patch(Rectangle((x - 1.3, y + 0.25), 2.6, 0.65, linewidth=0.5,
                              edgecolor=c, facecolor=c, alpha=0.08))
        ax.text(x - 1.25, y + 0.92, "接口:", fontsize=7, color=c, fontweight="bold")
        ax.text(x - 1.25, y + 0.55, iface, fontsize=7.2, color="#222", va="center")
        # 数据
        ax.add_patch(Rectangle((x - 1.3, y - 1.25), 2.6, 0.95, linewidth=0.5,
                              edgecolor=c, facecolor=c, alpha=0.04))
        ax.text(x - 1.25, y - 0.45, "关键数据:", fontsize=7, color=c, fontweight="bold")
        ax.text(x - 1.25, y - 0.85, data, fontsize=7.2, color="#222", va="center")

    # 组件间依赖箭头
    dep_edges = [
        (1.8, 5.35, 1.8, 4.55, C_MIND2, "snapshot/restore"),  # MindLayer ↔ MigrationService
        (5.2, 5.35, 8.6, 4.55, C_BODY, "publish"),  # BodyLayer → Bus
        (8.6, 5.35, 5.2, 4.55, C_BUS, "events"),  # Bus → ProtocolStack
        (12.0, 5.35, 12.0, 4.55, C_MEM, "memo_query"),  # MemoryVault → LifecycleManager
        (1.8, 3.2, 5.2, 3.2, C_ALIGN, "check_before"),  # Align → Protocol
        (8.6, 3.2, 12.0, 3.2, C_MIG, "begin_migration"),
    ]
    for x1, y1, x2, y2, c, lbl in dep_edges:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="<->", color=c, lw=1.0, ls="--", alpha=0.7))
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, lbl, fontsize=7, color=c,
                ha="center", va="center",
                path_effects=[pe.withStroke(linewidth=2, foreground="white")])

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "component_interfaces.png")
    plt.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved:", out)


# ----------------------------------------------------------------------------
# 图 5: 3 种部署形态对比图
# ----------------------------------------------------------------------------
def fig5_deployment_forms():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    ax.text(7, 7.1, "Living Runtime 三种部署形态对比",
            ha="center", fontsize=14, fontweight="bold")

    forms = [
        # (title, x, color, resources, mind_loc, body_loc, use_case)
        ("形态 1：单机形态\n个人知识生命", 2.4, C_BLUE,
         "CPU 4 核 / 内存 8GB\n存储 100GB",
         "MindLayer 本地驻留",
         "BodyLayer = 桌面 App",
         "个人助手\n知识管理"),
        ("形态 2：集群形态\n数字员工 SaaS", 7.0, C_GREEN,
         "Kubernetes 集群 / N 节点\nStatefulSet",
         "MindLayer 在 StatefulSet",
         "BodyLayer = Web",
         "企业数字员工\nSaaS 服务"),
        ("形态 3：边缘形态\nIoT 设备", 11.6, C_RED,
         "CPU 2 核 / 内存 1GB\n存储 10GB",
         "MindLayer 仅在云端",
         "BodyLayer 在边缘",
         "智能家居 / 车载\n工厂"),
    ]
    for title, x, c, res, mind, body, uc in forms:
        # 主框
        outer = FancyBboxPatch((x - 1.7, 0.5), 3.4, 6.0,
                             boxstyle="round,pad=0.02,rounding_size=0.1",
                             linewidth=2.0, edgecolor=c, facecolor=c, alpha=0.05)
        ax.add_patch(outer)
        # 标题
        header = FancyBboxPatch((x - 1.6, 5.7), 3.2, 0.7,
                              boxstyle="round,pad=0.02,rounding_size=0.06",
                              linewidth=0, facecolor=c, alpha=0.85)
        ax.add_patch(header)
        ax.text(x, 6.05, title, ha="center", va="center", fontsize=10.5, color="white", fontweight="bold")
        # 资源
        ax.text(x, 5.2, "资源配置", ha="center", fontsize=8.5, color=c, fontweight="bold")
        ax.text(x, 4.75, res, ha="center", fontsize=8.5, color="#222")
        # Mind
        ax.text(x, 4.0, "意识层位置", ha="center", fontsize=8.5, color=c, fontweight="bold")
        ax.text(x, 3.55, mind, ha="center", fontsize=8.5, color=C_MIND2)
        # Body
        ax.text(x, 2.8, "身体层位置", ha="center", fontsize=8.5, color=c, fontweight="bold")
        ax.text(x, 2.35, body, ha="center", fontsize=8.5, color=C_BODY)
        # 适用
        ax.text(x, 1.55, "适用场景", ha="center", fontsize=8.5, color=c, fontweight="bold")
        ax.text(x, 1.1, uc, ha="center", fontsize=8.5, color="#222")

    # 对比箭头
    ax.annotate("", xy=(5.3, 3.5), xytext=(4.1, 3.5),
                arrowprops=dict(arrowstyle="<->", color="#888", lw=1.2))
    ax.text(4.7, 3.7, "扩展", fontsize=8, color="#555", ha="center")
    ax.annotate("", xy=(9.9, 3.5), xytext=(8.7, 3.5),
                arrowprops=dict(arrowstyle="<->", color="#888", lw=1.2))
    ax.text(9.3, 3.7, "下沉", fontsize=8, color="#555", ha="center")

    # 底部统一标注
    ax.text(7, 0.18, "三种形态共享同一 ProtocolStack 八协议族接口 + AlignmentGuard 推理时对齐 + MeMo 记忆范式",
            ha="center", fontsize=9, color="#555", style="italic")

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "deployment_forms.png")
    plt.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved:", out)


if __name__ == "__main__":
    fig1_architecture()
    fig2_migration_sequence()
    fig3_cognitive_orchestration()
    fig4_component_interfaces()
    fig5_deployment_forms()
    print("ALL DONE")
