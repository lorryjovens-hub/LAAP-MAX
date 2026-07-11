"""主动感知调度器 - Active Perception Scheduler

自主决定"何时去感知什么"，从被动响应升级到主动探索。

三种决策路径：
1. 记忆命中跳过：目标在感知记忆层且未过期 → 直接复用缓存
2. 实时性强制爬取：任务显式要求实时数据（含 realtime/最新/竞品 等关键词）
3. 相关性主动爬取：目标与当前任务相关性 ≥ threshold

主动感知循环：
    推理层目标 → 主动搜索 Top N 站点 → 记忆层对比 → 决策层选择最优 → 写回记忆

设计原则：
- 依赖注入：crawler_organ / perceptual_memory 通过构造函数注入
- 优雅降级：crawler/memory 为 None 时不抛异常，仅记录警告
- 异步 I/O：should_crawl / run_active_perception 为 async；relevance / compare_perceptions 同步
"""

import json
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set

from src.api.models import CrawlerSnapshot
from src.config import get_settings
from src.utils.logger import get_logger


class ActivePerceptionScheduler:
    """主动感知调度器 - 自主决定"何时去感知什么"

    三种决策路径：
    1. 记忆命中跳过：目标在记忆层且未过期
    2. 实时性强制爬取：任务需要实时数据
    3. 相关性主动爬取：目标与当前任务相关性 > threshold

    主动感知循环：
    推理层目标 → 主动搜索 Top N 站点 → 记忆层对比 → 决策层选择最优
    """

    def __init__(
        self,
        crawler_organ: Optional[Any] = None,
        perceptual_memory: Optional[Any] = None,
    ) -> None:
        """
        Args:
            crawler_organ: CrawlerOrgan 实例（必需，缺失时降级跳过爬取）
            perceptual_memory: PerceptualMemory 实例（必需，缺失时降级跳过缓存）
        """
        self.settings = get_settings()
        self.logger = get_logger("perception.active_scheduler")
        self.crawler = crawler_organ
        self.memory = perceptual_memory
        self.relevance_threshold: float = (
            self.settings.active_perception_relevance_threshold
        )
        self.top_n: int = self.settings.active_perception_top_n

        if self.crawler is None:
            self.logger.warning(
                "ActivePerceptionScheduler initialized without crawler_organ"
            )
        if self.memory is None:
            self.logger.warning(
                "ActivePerceptionScheduler initialized without perceptual_memory"
            )

    # ==================================================================
    # SubTask 5.2: should_crawl 决策逻辑
    # ==================================================================

    async def should_crawl(
        self,
        target: str,
        current_task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """决策是否需要爬取目标

        Args:
            target: 目标 URL
            current_task: 当前任务上下文（可选）

        Returns:
            {
                "should_crawl": bool,
                "reason": str,  # memory_hit / force_realtime / high_relevance / low_relevance / no_task_context
                "relevance_score": float,
                "memory_hit": bool,
            }
        """
        # 1. 记忆命中检查 - 优先复用未过期缓存
        if self.memory is not None:
            try:
                if await self.memory.has_fresh_perception(target):
                    return {
                        "should_crawl": False,
                        "reason": "memory_hit",
                        "relevance_score": 0.0,
                        "memory_hit": True,
                    }
            except Exception as exc:
                self.logger.warning(
                    f"Memory freshness check failed for {target}: {exc}"
                )

        # 2. 无任务上下文 - 默认爬取
        if current_task is None:
            return {
                "should_crawl": True,
                "reason": "no_task_context",
                "relevance_score": 1.0,
                "memory_hit": False,
            }

        # 3. 实时性强制要求检查
        if self._requires_realtime(current_task):
            return {
                "should_crawl": True,
                "reason": "force_realtime",
                "relevance_score": 1.0,
                "memory_hit": False,
            }

        # 4. 相关性评分决策
        relevance = self.relevance(target, current_task)
        if relevance >= self.relevance_threshold:
            return {
                "should_crawl": True,
                "reason": "high_relevance",
                "relevance_score": relevance,
                "memory_hit": False,
            }

        return {
            "should_crawl": False,
            "reason": "low_relevance",
            "relevance_score": relevance,
            "memory_hit": False,
        }

    def _requires_realtime(self, task: Dict[str, Any]) -> bool:
        """检查任务是否需要实时数据

        通过关键词匹配识别任务对实时性的强制要求。
        """
        realtime_keywords = [
            "realtime",
            "实时",
            "竞品",
            "competitor",
            "latest",
            "最新",
            "current",
        ]
        task_str = json.dumps(task, ensure_ascii=False).lower()
        return any(kw.lower() in task_str for kw in realtime_keywords)

    # ==================================================================
    # SubTask 5.3: relevance 相关性评分
    # ==================================================================

    def relevance(self, target: str, current_task: Dict[str, Any]) -> float:
        """相关性评分（0.0-1.0）

        基于：
        1. 关键词匹配（target URL 中的词 vs 任务描述中的词）
        2. 主题相似度（task type vs target domain）

        使用 Jaccard 相似度，并放大 2 倍权重让 50% 重合即视为高相关。
        """
        # 1. 提取 target 关键词
        target_words = self._extract_keywords(target)

        # 2. 提取 task 关键词
        task_str = json.dumps(current_task, ensure_ascii=False).lower()
        task_words = self._extract_keywords(task_str)

        if not task_words:
            return 0.5  # 无任务信息，中性

        # 3. 计算 Jaccard 交集
        intersection = target_words & task_words
        union = target_words | task_words

        jaccard = len(intersection) / len(union) if union else 0.0

        # 4. 简单加权（可扩展为更复杂的 NLP 相似度）
        return min(jaccard * 2.0, 1.0)  # 放大权重，让 50% 重合也算高相关

    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词（简化版，支持中英文混合）

        - 移除 URL scheme 前缀
        - 英文按单词分词
        - 中文按 2-gram 分词
        - 移除常见停用词（域名后缀等）
        """
        # 移除 URL 前缀
        text = re.sub(r"https?://", "", text.lower())
        # 分词（中英文混合）
        words: Set[str] = set(re.findall(r"[a-z]+", text))
        # 添加中文词（每 2 字一组）
        chinese = re.findall(r"[\u4e00-\u9fff]+", text)
        for chunk in chinese:
            for i in range(len(chunk) - 1):
                words.add(chunk[i : i + 2])
        # 移除常见停用词
        stopwords = {"com", "www", "http", "https", "org", "net", "io"}
        return words - stopwords

    # ==================================================================
    # SubTask 5.4: run_active_perception 主动感知循环
    # ==================================================================

    async def run_active_perception(
        self,
        goal: Dict[str, Any],
        top_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """主动感知循环：根据推理层目标主动爬取 Top N 参考站点

        流程：
        1. 从 goal 提取目标站点列表（或基于 goal 关键词生成）
        2. 对每个目标调用 should_crawl 决策
        3. 决策为爬取的目标，调用 crawler_organ.perceive(url)
        4. 结果存入感知记忆
        5. 返回所有快照列表（含记忆命中和新鲜爬取）

        Args:
            goal: 推理层目标，含 "targets" (List[str]) 或 "keywords" (List[str]) 字段
            top_n: 限制爬取数量，None 使用配置默认值

        Returns:
            List[{"url": str, "snapshot": Optional[CrawlerSnapshot],
                  "source": str, "relevance": float}]
            source 取值: "memory" / "fresh_crawl" / "failed"
        """
        n = top_n or self.top_n

        # 提取或生成目标列表
        targets = goal.get("targets", [])
        if not targets:
            # 基于 keywords 生成（简化：仅记录，实际可接入搜索引擎 API）
            self.logger.info(
                f"No explicit targets in goal, keywords: "
                f"{goal.get('keywords', [])}"
            )
            return []

        results: List[Dict[str, Any]] = []
        for target in targets[:n]:
            # 决策
            decision = await self.should_crawl(target, goal)

            if not decision["should_crawl"]:
                # 记忆命中，从记忆加载
                if decision["memory_hit"] and self.memory is not None:
                    try:
                        snapshot = await self.memory.get_perception(target)
                    except Exception as exc:
                        self.logger.warning(
                            f"Memory load failed for {target}: {exc}"
                        )
                        snapshot = None
                    results.append(
                        {
                            "url": target,
                            "snapshot": snapshot,
                            "source": "memory",
                            "relevance": decision["relevance_score"],
                        }
                    )
                    self.logger.info(f"Memory hit for {target}")
                continue

            # 执行爬取
            if self.crawler is None:
                self.logger.warning(f"No crawler available, skip {target}")
                continue

            try:
                snapshot, signal = await self.crawler.perceive(target)

                # 存入记忆
                if self.memory is not None:
                    try:
                        await self.memory.store_perception(target, snapshot)
                    except Exception as exc:
                        self.logger.warning(
                            f"Memory store failed for {target}: {exc}"
                        )

                results.append(
                    {
                        "url": target,
                        "snapshot": snapshot,
                        "source": "fresh_crawl",
                        "relevance": decision["relevance_score"],
                    }
                )
                self.logger.info(
                    f"Fresh crawl for {target} "
                    f"(relevance: {decision['relevance_score']:.2f})"
                )
            except Exception as e:
                self.logger.error(f"Failed to crawl {target}: {e}")
                results.append(
                    {
                        "url": target,
                        "snapshot": None,
                        "source": "failed",
                        "relevance": decision["relevance_score"],
                    }
                )

        return results

    # ==================================================================
    # SubTask 5.5: compare_perceptions 批量对比分析
    # ==================================================================

    def compare_perceptions(
        self, snapshots: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量对比分析：提取共同模式与差异点

        Args:
            snapshots: run_active_perception 返回的结果列表

        Returns:
            {
                "common_tech_stack": List[str],        # 多站点共有的技术栈名称
                "common_design_tokens": List[Dict],    # 共有的设计令牌
                "content_types": Dict[str, int],       # 内容类型分布
                "avg_layout_complexity": float,        # 平均布局复杂度
                "differences": List[Dict],             # 差异点列表
            }
        """
        valid_snapshots: List[CrawlerSnapshot] = [
            r["snapshot"]
            for r in snapshots
            if r.get("snapshot") is not None
        ]

        if not valid_snapshots:
            return {
                "common_tech_stack": [],
                "common_design_tokens": [],
                "content_types": {},
                "avg_layout_complexity": 0.0,
                "differences": [],
            }

        # 1. 共有技术栈（在所有站点中都出现的）
        tech_stack_sets = [self._tech_stack_to_set(s) for s in valid_snapshots]
        common_tech: Set[str] = (
            set.intersection(*tech_stack_sets) if tech_stack_sets else set()
        )

        # 2. 共有设计令牌（重合度 > 50% 视为共有）
        common_tokens = self._find_common_design_tokens(valid_snapshots)

        # 3. 内容类型分布
        content_types: Dict[str, int] = {}
        for s in valid_snapshots:
            ct = s.content_structure.get("type", "unknown")
            content_types[ct] = content_types.get(ct, 0) + 1

        # 4. 平均布局复杂度（DOM 深度 + 元素密度）
        complexities: List[float] = []
        for s in valid_snapshots:
            depth = s.layout_analysis.get("depth", 0)
            density = s.layout_analysis.get("element_density", 0)
            complexities.append(depth * 0.5 + density * 0.5)
        avg_complexity: float = (
            sum(complexities) / len(complexities) if complexities else 0.0
        )

        # 5. 差异点
        differences = self._find_differences(valid_snapshots)

        return {
            "common_tech_stack": list(common_tech),
            "common_design_tokens": common_tokens,
            "content_types": content_types,
            "avg_layout_complexity": avg_complexity,
            "differences": differences,
        }

    def _tech_stack_to_set(self, snapshot: CrawlerSnapshot) -> Set[str]:
        """将技术栈转为名称集合"""
        return {t["name"] for t in snapshot.tech_stack if "name" in t}

    def _find_common_design_tokens(
        self, snapshots: List[CrawlerSnapshot]
    ) -> List[Dict[str, Any]]:
        """找出多站点共有的设计令牌

        按 (name, type) 分组，出现次数 ≥ 50% 站点数视为共有。
        """
        token_names: Counter = Counter()
        for s in snapshots:
            for t in s.design_tokens:
                token_names[(t.name, t.type)] += 1

        threshold = len(snapshots) * 0.5  # 50% 重合
        return [
            {"name": name, "type": type_, "occurrences": count}
            for (name, type_), count in token_names.items()
            if count >= threshold
        ]

    def _find_differences(
        self, snapshots: List[CrawlerSnapshot]
    ) -> List[Dict[str, Any]]:
        """找出差异点（每个站点独有的技术栈）"""
        differences: List[Dict[str, Any]] = []

        # 技术栈差异
        tech_stacks = [self._tech_stack_to_set(s) for s in snapshots]
        if len(tech_stacks) >= 2:
            # 找出每个站点独有的技术
            all_tech: Set[str] = set.union(*tech_stacks)
            for i, _ts in enumerate(tech_stacks):
                others = tech_stacks[:i] + tech_stacks[i + 1 :]
                if others:
                    intersection_others = set.intersection(*others)
                    unique = all_tech - intersection_others
                    if unique:
                        differences.append(
                            {
                                "type": "unique_tech_stack",
                                "snapshot_index": i,
                                "unique_tech": list(unique),
                            }
                        )

        return differences
