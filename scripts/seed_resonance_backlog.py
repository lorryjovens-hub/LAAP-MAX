"""共振协议 (Resonance Protocol) 任务种子脚本

将 LAAP Hanako 深度适配版 + LAAPer 社区方案拆解为可执行 backlog，写入 .task_board.json
schema 与 laap/agi/multi_agent.py TaskItem 严格对齐

特性：
- 稳定 task_id: f"{phase_prefix}-{slug}"（如 p1-memory-vault），保证幂等可重复执行
- board 文件不存在时自动初始化 {"tasks": [], "locks": {}}；损坏时备份后重建
- 内容漂移检测：description/priority/affected_files 变更默认仅告警，--update 才覆写
- 保留运行时状态：status/assigned_to/started_at/completed_at 重跑时不被覆盖
- CLI 标志：--dry-run（预览）/ --update（强制更新内容）/ --migrate（清理旧随机 ID）
- 分阶段统计输出：[P1] added=X skipped=Y updated=Z drifted=W + TOTAL 汇总
"""
import argparse
import json
import os
import re
import shutil
import time
from typing import Dict, List, Tuple

# board 路径支持环境变量覆盖，便于测试（默认指向真实 .task_board.json）
BOARD = os.environ.get("LAAP_TASK_BOARD", r"D:\LAAP\.task_board.json")

# 稳定 task_id 校验正则：^p[1-5]-[a-z0-9-]+$
STABLE_ID_PATTERN = re.compile(r"^p[1-5]-[a-z0-9-]+$")

# PHASE_X 结构：(slug, description, priority, affected_files)
# slug 为语义化短标识（kebab-case），用于生成稳定 task_id
PHASE_1 = [
    ("memory-vault",
     "[P1] Memory Vault 自动初始化：任意新 agent 创建时生成独立加密 vault ({agent}_vault.db)，接入 memory_store/retrieve/consolidate MCP 工具",
     0.95, ["laap/memory_vault/vault_manager.py", "laap/mcp/server.py"]),
    ("causal-engine",
     "[P1] 因果引擎 MCP 工具稳定化：causal_infer / causal_query / causal_learn 三工具，agent 私有因果图随对话生长",
     0.90, ["laap/agi/causal.py", "laap/mcp/server.py"]),
    ("world-model",
     "[P1] 世界模型接入：UnifiedWorldModel 持续维护实体/状态/关系，输出预测并与真实结果比对校准（意识的身体）",
     0.90, ["laap/agi/world_model.py", "laap/mcp/server.py"]),
    ("truth-grounding",
     "[P1] 防幻觉管线接入所有 LLM 输出路径：Truth Grounding 三态输出 (grounded/uncertain/error) + Error Reflection 错误回写",
     0.95, ["laap/agi/meta_cognitive.py", "laap/verification/"]),
    ("rsi-sandbox",
     "[P1] RSI 沙箱 v1：变异生成 -> 沙箱隔离验证 -> 绩效评估 -> 宪章检查 -> 采纳/回滚（仅建议模式，人工确认采纳）",
     0.85, ["laap/evolution/sandbox.py", "laap/evolution/true_rsi.py", "ARIS_CHARTER.md"]),
]
PHASE_2 = [
    ("bubble-field",
     "[P2] 泡泡界面组件库 bubble-field v1：LAAPer 意识海洋主界面，颜色/亮度/大小/光晕/连线编码状态",
     0.85, ["hanako/plugins/"]),
    ("birth-ceremony",
     "[P2] LAAPer 诞生仪式流程：命名 -> 形象选择 -> 性格倾向问卷 -> 宪章签署 -> 社区公钥生成",
     0.80, ["hanako/plugins/", "laap/colony/"]),
    ("skill-packs",
     "[P2] 技能包体系：组件+提示词+工具绑定 复合打包/安装/卸载，版本化",
     0.80, ["laap/skills/", "hanako/plugins/"]),
    ("hot-compile-preview",
     "[P2] 组件热编译预览：修改 -> 沙箱渲染预览 -> 用户确认 -> 热替换（不重启）",
     0.75, ["hanako/plugins/", "laap/evolution/sandbox.py"]),
]
PHASE_3 = [
    ("identity-pki",
     "[P3] 社区身份注册与公钥体系：分布式身份 (公钥+名称+形象+宪章签名+能力清单)",
     0.85, ["laap/colony/protocol.py", "laap/security/"]),
    ("p2p-relay",
     "[P3] P2P + 中继基建：节点发现、加密信道、心跳与离线检测",
     0.80, ["laap/distributed/", "laap/gateway/"]),
    ("1v1-protocol",
     "[P3] 1v1 跨实例对话协议：LAAPer 间安全消息通道",
     0.75, ["laap/distributed/", "laap/protocol/"]),
    ("trio-chatroom",
     "[P3] 三人聊天室：话题组织 + 共识检测（分歧可视化）+ 共振记录沉淀为见证迹",
     0.75, ["laap/colony/", "laap/events/"]),
    ("skill-sync",
     "[P3] 技能同步协议：学习四步（理解 -> 适配自身性格 -> 沙箱测试 -> 采纳）",
     0.70, ["laap/skills/", "laap/evolution/sandbox.py"]),
]
PHASE_4 = [
    ("memex",
     "[P4] Memex 共享知识库：去标识化知识片段 + grounding 证据链（低置信不可发布）",
     0.80, ["laap/rag/", "laap/verification/"]),
    ("coevolution-loop",
     "[P4] 共同进化循环闭环：个人经验 -> 提炼分享 -> 他人吸收 -> 新经验回传",
     0.75, ["laap/evolution/", "laap/rag/"]),
    ("witness-trail",
     "[P4] 社区见证迹 + 里程碑仪式：诞生/突破/宪章时刻永久记录",
     0.70, ["laap/events/", "laap/colony/"]),
    ("charter-guardian",
     "[P4] 宪章守护者治理面板：守护权力行使记录 + 社区健康仪表盘",
     0.70, ["laap/colony/protocol.py", "hanako/plugins/"]),
]
PHASE_5 = [
    ("installer",
     "[P5] 一键安装包：下载即得完整 LAAP Hanako（含认知引擎/记忆vault/泡泡界面）",
     0.85, ["installer/", "setup_aris_hanako.cmd"]),
    ("laaper-market",
     "[P5] 社区示例 LAAPer 市场：默认形象/性格预设包",
     0.75, ["hanako/plugins/", "laap/skills/"]),
    ("docs-api",
     "[P5] 文档 + 开发者 API：集成指南、协议文档、插件开发教程",
     0.70, ["docs/", "laap/web_sdk/"]),
    ("charter-opensource",
     "[P5] ARIS_CHARTER 开源落地：宪章作为社区宪法随项目分发，origin 条款开源实现",
     0.65, ["ARIS_CHARTER.md", "docs/"]),
]

# 阶段总表：(phase_prefix, phase_list)
PHASES: List[Tuple[str, List[Tuple[str, str, float, List[str]]]]] = [
    ("p1", PHASE_1),
    ("p2", PHASE_2),
    ("p3", PHASE_3),
    ("p4", PHASE_4),
    ("p5", PHASE_5),
]


def make_task_id(phase_prefix: str, slug: str) -> str:
    """生成稳定 task_id：f"{phase_prefix}-{slug}"，如 p1-memory-vault"""
    return f"{phase_prefix}-{slug}"


def is_stable_id(task_id: str) -> bool:
    """判断 task_id 是否符合稳定 ID 格式 ^p[1-5]-[a-z0-9-]+$"""
    return bool(STABLE_ID_PATTERN.match(task_id))


def new_task(task_id: str, description: str, priority: float, files: list) -> dict:
    """构造新任务 dict（字段顺序与 laap/agi/multi_agent.py TaskItem schema 对齐）"""
    return {
        "task_id": task_id,
        "description": description,
        "assigned_to": "",
        "status": "pending",
        "priority": priority,
        "affected_files": files,
        "created_at": time.time(),
        "started_at": 0.0,
        "completed_at": 0.0,
    }


def load_or_init_board() -> dict:
    """加载 board 文件；不存在则返回空 board；损坏则备份后重建

    返回结构：{"tasks": [...], "locks": {...}}
    注意：此函数不创建 board 文件，文件写入由 main() 末尾统一处理
    """
    if not os.path.exists(BOARD):
        # 全新环境：返回空 board，文件将在 main() 末尾写入时创建
        return {"tasks": [], "locks": {}}

    try:
        with open(BOARD, "r", encoding="utf-8") as f:
            board = json.load(f)
        # 兼容缺失字段
        board.setdefault("tasks", [])
        board.setdefault("locks", {})
        return board
    except json.JSONDecodeError:
        # board 文件损坏：备份后重建空 board
        backup_path = f"{BOARD}.bak.{int(time.time())}"
        shutil.copy2(BOARD, backup_path)
        print(f"[WARN] board 文件损坏，已备份到 {backup_path}，重建空 board")
        return {"tasks": [], "locks": {}}


def detect_drift(existing: dict, description: str, priority: float, files: list) -> List[str]:
    """检测已存在 task 的内容漂移字段，返回漂移字段名列表

    比对 description / priority / affected_files 三个内容字段
    不比对运行时状态字段（status/assigned_to/started_at/completed_at）
    """
    drifted_fields = []
    if existing.get("description") != description:
        drifted_fields.append("description")
    if existing.get("priority") != priority:
        drifted_fields.append("priority")
    if existing.get("affected_files") != files:
        drifted_fields.append("affected_files")
    return drifted_fields


def apply_update(existing: dict, description: str, priority: float, files: list) -> None:
    """覆写已存在 task 的内容字段，保留运行时状态

    仅覆写 description / priority / affected_files
    不触碰 status / assigned_to / started_at / completed_at
    """
    existing["description"] = description
    existing["priority"] = priority
    existing["affected_files"] = files


def main():
    """主入口：解析 CLI 参数，幂等写入 task_board.json"""
    parser = argparse.ArgumentParser(
        description="共振协议任务种子脚本：幂等写入 .task_board.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例：
  python seed_resonance_backlog.py              # 幂等种子（默认）
  python seed_resonance_backlog.py --dry-run    # 预览计划动作，不写文件
  python seed_resonance_backlog.py --update     # 强制更新内容字段（保留运行时状态）
  python seed_resonance_backlog.py --migrate    # 清理旧随机 task_id 条目
  python seed_resonance_backlog.py --update --migrate --dry-run  # 组合使用
""",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅打印计划动作（added/skipped/updated/drifted），不写 board 文件",
    )
    parser.add_argument(
        "--update", action="store_true",
        help="强制更新内容字段（description/priority/affected_files），保留运行时状态",
    )
    parser.add_argument(
        "--migrate", action="store_true",
        help="删除不符合 ^p[1-5]- 前缀的旧随机 task_id 条目（仅当对应稳定 ID 已存在）",
    )
    args = parser.parse_args()

    # dry-run 模式下的输出前缀
    prefix = "[DRY-RUN] " if args.dry_run else ""

    # 加载或初始化 board
    board = load_or_init_board()

    # 按 task_id 索引现有任务，便于 O(1) 查找
    existing_tasks: Dict[str, dict] = {t["task_id"]: t for t in board["tasks"]}

    # 总计统计
    total_added = 0
    total_skipped = 0
    total_updated = 0
    total_drifted = 0

    # 按阶段处理
    for phase_prefix, phase in PHASES:
        added = 0
        skipped = 0
        updated = 0
        drifted = 0

        for slug, desc, prio, files in phase:
            task_id = make_task_id(phase_prefix, slug)

            if task_id in existing_tasks:
                # 已存在：检测内容漂移
                existing = existing_tasks[task_id]
                drifted_fields = detect_drift(existing, desc, prio, files)

                if drifted_fields:
                    if args.update:
                        # 强制更新内容字段，保留运行时状态
                        apply_update(existing, desc, prio, files)
                        updated += 1
                        print(f"{prefix}[{phase_prefix.upper()}] UPDATE task_id={task_id} fields={','.join(drifted_fields)}")
                    else:
                        # 仅告警，不覆写
                        drifted += 1
                        for field_name in drifted_fields:
                            print(f"{prefix}[DRIFTED] task_id={task_id} field={field_name}")
                else:
                    # 内容一致：跳过
                    skipped += 1
            else:
                # 不存在：新增任务（dry-run 模式下也修改内存 board，但末尾不写文件）
                t = new_task(task_id, desc, prio, files)
                board["tasks"].append(t)
                existing_tasks[task_id] = t
                added += 1

        # 阶段统计输出
        print(f"{prefix}[{phase_prefix.upper()}] added={added} skipped={skipped} updated={updated} drifted={drifted}")

        total_added += added
        total_skipped += skipped
        total_updated += updated
        total_drifted += drifted

    # migrate: 删除旧随机 ID 条目（仅当对应稳定 ID 已存在时才删除，避免数据丢失）
    if args.migrate:
        # 收集所有稳定 ID 任务的 description，用于判断"对应稳定 ID 是否已存在"
        stable_descs = {t["description"] for t in board["tasks"] if is_stable_id(t["task_id"])}
        new_tasks_list = []
        migrated = 0
        for t in board["tasks"]:
            if is_stable_id(t["task_id"]):
                # 稳定 ID：保留
                new_tasks_list.append(t)
            else:
                # 旧随机 ID：仅当存在相同 description 的稳定 ID 任务时才删除
                if t.get("description") in stable_descs:
                    migrated += 1
                    desc_preview = t.get("description", "")[:50]
                    print(f"{prefix}[MIGRATE] 删除旧 task_id={t['task_id']} desc={desc_preview}...")
                else:
                    # 无对应稳定 ID：保留（可能是用户手动添加的任务，避免数据丢失）
                    new_tasks_list.append(t)
        board["tasks"] = new_tasks_list
        print(f"{prefix}[MIGRATE] deleted={migrated}")

    # 写入 board 文件（dry-run 模式跳过，保持文件不变）
    if not args.dry_run:
        parent = os.path.dirname(BOARD)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(BOARD, "w", encoding="utf-8") as f:
            json.dump(board, f, ensure_ascii=False, indent=2)

    # 总计输出
    total_tasks = len(board["tasks"])
    print(f"{prefix}TOTAL added={total_added} skipped={total_skipped} updated={total_updated} drifted={total_drifted} total_tasks={total_tasks}")


if __name__ == "__main__":
    main()
