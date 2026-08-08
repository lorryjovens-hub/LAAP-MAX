# -*- coding: utf-8 -*-
"""记忆 Recall 基线采集（P0-2 成绩单基线）。

⚠️ 已迁移: 本脚本已泛化为开源基准包 ``recall-bench/``（recall_bench 包），
支持任意记忆后端。本文件保留为 LAAP 内部工具（生产库 live 模式），
新功能请优先在 recall-bench 中开发。

设计
----
跨会话 recall 抽查集：写入 N 条带唯一标记的记忆事实（模拟"上个会话存下的
内容"），再用不含标记的自然语言 query 检索，统计命中率。

场景
----
- clean（默认）: monkeypatch DB_PATH 到临时库，零污染，测检索机制本身
- live（--live）: 写入生产记忆库（D:/LAAP/laap/memory_vault/），带唯一标记
  RB_YYYYMMDD_NN，测完自动清理删除

指标
----
- recall_rate: 命中 / 总数（命中 = 检索结果中含对应唯一标记）
- avg_latency_ms: 单次检索平均延迟
- 按主题域 / query 长度分组的命中率

用法
----
    python benchmarks/recall_baseline.py              # 隔离场景
    python benchmarks/recall_baseline.py --live       # 生产库场景（自动清理）
    python benchmarks/recall_baseline.py --json out.json
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
import time
import uuid

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 注意：不能用 ``from laap.memory_vault import vault_manager`` —— 包的 __init__
# 里 ``from .vault_manager import VaultManager`` 会把 ``vault_manager`` 名字
# 覆盖为类，必须从 sys.modules 取真正的模块对象。
importlib.import_module("laap.memory_vault.vault_manager")
vault_manager = sys.modules["laap.memory_vault.vault_manager"]  # noqa: E402
from laap.memory_vault.vault_manager import MemoryVault  # noqa: E402

# ─── 抽查集 ───────────────────────────────────────────────────────────────
# 中性事实：不涉及真实个人信息；每条约含 3~6 个关键词；query 模拟"跨会话
# 提问"（保留大意、不含唯一标记）。

def build_probe_set(tag: str) -> list[dict]:
    """构造抽查集。tag 形如 RB_20260802，追加到每条事实，用于命中判定与清理。"""
    facts = [
        # (内容, 主题域, 检索 query)
        ("用户近期在调研量子记忆压缩算法的能耗表现", "技术",
         "量子记忆压缩的能耗研究进展如何"),
        ("LAAP 的记忆系统设计了四层分级架构", "项目",
         "LAAP 记忆系统的分层设计"),
        ("lorry 习惯在深夜进行架构设计讨论", "习惯",
         "lorry 一般什么时候做架构设计"),
        ("团队计划在下季度发布认知引擎的公开评测报告", "目标",
         "认知引擎的评测报告什么时候发布"),
        ("arisa 的桌面助手最近迁移到了新的会话框架", "项目",
         "桌面助手迁移到了什么框架"),
        ("实验室采购了一批新的 GPU 用于推理加速", "资源",
         "新采购的 GPU 用在哪里"),
        ("lorry 偏好深色主题的终端配色方案", "偏好",
         "lorry 喜欢什么颜色的终端"),
        ("上周完成了错误反思管线的第一轮迭代", "事件",
         "错误反思管线迭代到第几轮了"),
        ("认知引擎在长上下文场景下 token 消耗明显下降", "技术",
         "认知引擎长上下文的 token 效率"),
        ("记忆巩固任务安排在每日凌晨四时执行", "习惯",
         "记忆巩固什么时候跑"),
        ("用户认为评估器应当独立于改进循环之外", "观点",
         "评估器应该放在循环里面还是外面"),
        ("多智能体编排层支持并行子任务回收", "项目",
         "编排层能不能并行回收子任务"),
        ("lorry 关注递归自我改进的安全边界问题", "兴趣",
         "递归自我改进有什么安全问题"),
        ("桌面端的会话记录同步到了移动端", "事件",
         "会话记录同步到哪些端"),
        ("记忆检索使用了向量索引与关键词混合策略", "技术",
         "记忆检索用的是什么策略"),
        ("新模型在代码生成基准上提升了三成", "目标",
         "新模型的代码生成能力提升多少"),
        ("lorry 最近在调试跨平台记忆同步", "项目",
         "跨平台记忆同步调试得怎样"),
        ("原型沙箱启用了只读文件系统保护", "技术",
         "原型沙箱的文件保护方式"),
        ("会议记录存放在了项目仓库的文档目录", "习惯",
         "会议记录存放在哪里"),
        ("lorry 正在准备认知架构的对照笔记", "目标",
         "认知架构对照笔记写得如何"),
    ]
    probe = []
    for i, (content, domain, query) in enumerate(facts):
        token = f"{tag}_{i:02d}"
        probe.append({
            "token": token,
            "content": f"{content}（标记:{token}）",
            "domain": domain,
            "query": query,
            "tags": f"baseline,{domain}",
        })
    return probe


# ─── 执行 ─────────────────────────────────────────────────────────────────

def run_baseline(live: bool, tag: str) -> dict:
    probe = build_probe_set(tag)
    cleanup_ids: list[int] = []

    if live:
        # 生产库：直接使用 MemoryVault（_get_connection 硬编码模块 DB_PATH）
        vault = MemoryVault()
        print(f"[live] 生产库: {vault_manager.DB_PATH}")
    else:
        # 隔离场景：patch 模块级 DB_PATH 到临时文件
        tmp_db = os.path.join(tempfile.mkdtemp(prefix="recall_baseline_"), "vault.db")
        vault_manager.DB_PATH = tmp_db
        vault = MemoryVault(db_path=tmp_db)
        print(f"[clean] 临时库: {tmp_db}")

    session_id = vault.start_session(title=f"recall_baseline_{tag}")

    # 写入
    t0 = time.time()
    for item in probe:
        eid = vault.store(
            role="aris", content=item["content"], tags=item["tags"],
            session_id=session_id,
        )
        item["entry_id"] = eid
        cleanup_ids.append(eid)
    write_ms = (time.time() - t0) * 1000

    # 检索
    results_per_item = []
    hits = 0
    latencies: list[float] = []
    for item in probe:
        t0 = time.time()
        rows = vault.search(item["query"], limit=10)
        lat_ms = (time.time() - t0) * 1000
        latencies.append(lat_ms)
        hit = any(item["token"] in r.content for r in rows)
        if hit:
            hits += 1
        results_per_item.append({
            "domain": item["domain"],
            "query": item["query"],
            "query_len": len(item["query"]),
            "hit": hit,
            "latency_ms": round(lat_ms, 1),
            "top_result": (rows[0].content[:60] if rows else ""),
        })

    # 清理（live 模式删除写入的记录；clean 模式临时库直接丢弃）
    if live:
        conn = vault_manager._get_connection()
        try:
            placeholders = ",".join("?" for _ in cleanup_ids)
            cur = conn.execute(
                f"DELETE FROM conversations WHERE id IN ({placeholders})",
                cleanup_ids,
            )
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            print(f"[live] 已清理 {cur.rowcount} 条基线记录")
        finally:
            conn.close()

    # 汇总
    n = len(probe)
    by_domain: dict[str, dict] = {}
    for r in results_per_item:
        d = by_domain.setdefault(r["domain"], {"total": 0, "hit": 0, "lat": []})
        d["total"] += 1
        d["hit"] += 1 if r["hit"] else 0
        d["lat"].append(r["latency_ms"])
    domain_stats = {
        d: {
            "recall_rate": round(v["hit"] / v["total"], 3),
            "total": v["total"], "hit": v["hit"],
            "avg_latency_ms": round(sum(v["lat"]) / len(v["lat"]), 1),
        }
        for d, v in sorted(by_domain.items())
    }

    short_q = [r for r in results_per_item if r["query_len"] <= 10]
    long_q = [r for r in results_per_item if r["query_len"] > 10]

    report = {
        "baseline": "recall_v0.1",
        "tag": tag,
        "mode": "live" if live else "clean",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": n,
        "hits": hits,
        "recall_rate": round(hits / n, 3),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1),
        "write_ms_total": round(write_ms, 1),
        "by_domain": domain_stats,
        "by_query_len": {
            "short<=10": {
                "total": len(short_q),
                "recall_rate": round(sum(1 for r in short_q if r["hit"]) / len(short_q), 3) if short_q else None,
            },
            "long>10": {
                "total": len(long_q),
                "recall_rate": round(sum(1 for r in long_q if r["hit"]) / len(long_q), 3) if long_q else None,
            },
        },
        "per_item": results_per_item,
    }
    return report


def _print_report(report: dict) -> None:
    print("\n" + "=" * 52)
    print(f"RECALL BASELINE  ({report['mode']})  {report['timestamp']}")
    print(f"  总量 {report['total']} | 命中 {report['hits']} | "
          f"recall_rate = {report['recall_rate']:.1%}")
    print(f"  平均延迟 {report['avg_latency_ms']} ms | 写入 {report['write_ms_total']} ms")
    print("-" * 52)
    for domain, s in report["by_domain"].items():
        bar = "#" * int(s["recall_rate"] * 20)
        print(f"  {domain:<6} {s['recall_rate']:6.1%}  {bar:<20} {s['hit']}/{s['total']}")
    print("=" * 52)


def main() -> int:
    ap = argparse.ArgumentParser(description="记忆 recall 基线采集")
    ap.add_argument("--live", action="store_true", help="使用生产库（自动清理）")
    ap.add_argument("--json", default="", help="JSON 报告输出路径")
    args = ap.parse_args()

    tag = f"RB_{time.strftime('%Y%m%d')}"
    report = run_baseline(live=args.live, tag=tag)
    _print_report(report)

    if args.json:
        out = args.json
    else:
        out_dir = os.path.join(_ROOT, "benchmarks", "results")
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(
            out_dir, f"recall_baseline_{tag}_{'live' if args.live else 'clean'}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"报告已写入: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
