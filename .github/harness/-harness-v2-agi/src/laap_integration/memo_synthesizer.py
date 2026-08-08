"""MEMO 反思QA合成流水线

实现五步反思QA合成：事实抽取 → 合并 → 实体显化 → 验证 → 跨文档合成。
对应 MEMO 论文 (arXiv:2605.15156) 的反思QA训练集构造方法，把
design_system_cache.json + component_templates.json + harness_memory.db episodes
蒸馏为结构化的反思QA训练集，捕获跨文档关系。
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from src.utils.logger import get_logger


class MemoSynthesizer:
    """五步反思QA合成流水线

    把 design_system_cache.json + component_templates.json + harness_memory.db episodes
    蒸馏为反思QA训练集。五步方法：
      1. extract_facts       — 事实抽取
      2. consolidate_facts   — 事实合并（按 semantics 聚类）
      3. surface_entities    — 实体显化
      4. synthesize_cross_doc — 跨文档 QA 合成
      5. verify_qa           — GENERATOR 自验证
    """

    def __init__(
        self,
        generator_llm=None,
        output_path: str = "./memory/memo_reflection_train.jsonl",
    ):
        """
        generator_llm: 用于验证 QA 的 GENERATOR 模型（可以是 LLM client 或 None）
                      若为 None 则跳过验证步骤（仅做规则过滤）
        output_path: 反思QA训练集 JSONL 输出路径
        """
        self.generator_llm = generator_llm
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        self._filter_log: List[Dict[str, Any]] = []  # 记录被滤除的 QA 及原因

    # ------------------------------------------------------------------
    # T2.2 事实抽取
    # ------------------------------------------------------------------
    def extract_facts(self, sources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从三个数据源抽取原子事实

        sources 是 dict，键为数据源名称，值为对应数据：
        - "design_system_cache": dict[task_id, {tokens, project_type, timestamp}]
        - "component_templates": dict[key, {code, score, timestamp}]
        - "episodes": list[episode] 或 dict[episode_id, episode]
        """
        facts: List[Dict[str, Any]] = []

        # 1. design_system_cache.json
        dsc = sources.get("design_system_cache") or {}
        if isinstance(dsc, dict):
            for task_id, data in dsc.items():
                if not isinstance(data, dict):
                    continue
                project_type = data.get("project_type", "unknown")
                for token in data.get("tokens", []) or []:
                    if not isinstance(token, dict):
                        continue
                    facts.append(
                        {
                            "type": "design_token",
                            "task_id": task_id,
                            "name": token.get("name", ""),
                            "semantics": token.get("semantics", ""),
                            "value": token.get("value", ""),
                            "project_type": token.get("project_type", project_type),
                        }
                    )

        # 2. component_templates.json
        ct = sources.get("component_templates") or {}
        if isinstance(ct, dict):
            for key, data in ct.items():
                if not isinstance(data, dict):
                    continue
                framework, component_type = self._parse_template_key(key)
                facts.append(
                    {
                        "type": "component_template",
                        "key": key,
                        "framework": framework,
                        "component_type": component_type,
                        "code": data.get("code", ""),
                        "score": data.get("score", 0.0),
                    }
                )

        # 3. harness_memory.db episodes
        episodes = sources.get("episodes") or []
        if isinstance(episodes, list):
            for idx, ep in enumerate(episodes):
                if not isinstance(ep, dict):
                    continue
                facts.append(
                    {
                        "type": "episode",
                        "episode_id": ep.get("episode_id", f"ep_{idx}"),
                        "content": ep.get("content", ""),
                        "tags": list(ep.get("tags", []) or []),
                    }
                )
        elif isinstance(episodes, dict):
            for ep_id, ep in episodes.items():
                if not isinstance(ep, dict):
                    continue
                facts.append(
                    {
                        "type": "episode",
                        "episode_id": ep_id,
                        "content": ep.get("content", ""),
                        "tags": list(ep.get("tags", []) or []),
                    }
                )

        self.logger.info(f"[MemoSynthesizer] extract_facts: {len(facts)} facts")
        return facts

    @staticmethod
    def _parse_template_key(key: str) -> tuple:
        """解析模板键 'react_Button' -> ('react', 'Button')"""
        if "_" in key:
            framework, _, component_type = key.partition("_")
            return framework, component_type
        return key, "unknown"

    # ------------------------------------------------------------------
    # T2.3 事实合并
    # ------------------------------------------------------------------
    def consolidate_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并重复事实

        按 design token 的 semantics 字段聚类，相同 semantics 的事实合并为一条，
        记录 occurrence_count 和 source_task_ids。其他类型事实原样保留。
        """
        consolidated: List[Dict[str, Any]] = []
        token_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for fact in facts:
            if fact.get("type") == "design_token":
                semantics = fact.get("semantics", "") or ""
                token_groups[semantics].append(fact)
            else:
                # 非设计 token 事实原样保留
                consolidated.append(dict(fact))

        # 合并 design token（按 semantics 聚类）
        for semantics, group in token_groups.items():
            if not group:
                continue
            task_ids_seen: List[str] = []
            values_list: List[Dict[str, Any]] = []
            for f in group:
                tid = f.get("task_id", "")
                if tid not in task_ids_seen:
                    task_ids_seen.append(tid)
                values_list.append(
                    {
                        "task_id": tid,
                        "value": f.get("value", ""),
                        "name": f.get("name", ""),
                        "project_type": f.get("project_type", ""),
                    }
                )
            # 取第一条作为基底，附加聚合字段
            base = dict(group[0])
            base["occurrence_count"] = len(group)
            base["source_task_ids"] = task_ids_seen
            base["values"] = values_list
            consolidated.append(base)

        self.logger.info(
            f"[MemoSynthesizer] consolidate_facts: {len(consolidated)} consolidated facts "
            f"(from {len(facts)} raw)"
        )
        return consolidated

    # ------------------------------------------------------------------
    # T2.4 实体显化
    # ------------------------------------------------------------------
    def surface_entities(self, facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """显化实体，按类型分组（set 转为 sorted list 便于序列化）"""
        task_ids: set = set()
        frameworks: set = set()
        component_types: set = set()
        semantics_keywords: set = set()

        for fact in facts:
            ftype = fact.get("type")
            if ftype == "design_token":
                tid = fact.get("task_id", "")
                if tid:
                    task_ids.add(tid)
                pt = fact.get("project_type", "")
                if pt:
                    frameworks.add(pt)
                sem = fact.get("semantics", "")
                if sem:
                    semantics_keywords.add(sem)
            elif ftype == "component_template":
                fw = fact.get("framework", "")
                if fw:
                    frameworks.add(fw)
                ct = fact.get("component_type", "")
                if ct:
                    component_types.add(ct)

        return {
            "task_ids": sorted(task_ids),
            "frameworks": sorted(frameworks),
            "component_types": sorted(component_types),
            "semantics_keywords": sorted(semantics_keywords),
        }

    # ------------------------------------------------------------------
    # T2.5 QA 验证
    # ------------------------------------------------------------------
    def verify_qa(self, qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """用 GENERATOR 模型自验证 QA 对

        - 若 self.generator_llm 为 None，仅做规则过滤：过滤掉空 question 或空 answer
        - 若 generator_llm 可用，对每个 QA 对：用 question 调用 generator_llm，
          检查返回是否包含 answer 的关键信息（简单字符串包含或关键词重叠 > 50%）
        - 过滤的 QA 记录到 self._filter_log，含 {qa, reason} 字段
        """
        verified: List[Dict[str, Any]] = []

        for qa in qa_pairs:
            question = (qa.get("question") or "").strip()
            answer = (qa.get("answer") or "").strip()

            if not question:
                self._filter_log.append({"qa": qa, "reason": "empty_question"})
                continue
            if not answer:
                self._filter_log.append({"qa": qa, "reason": "empty_answer"})
                continue

            if self.generator_llm is None:
                verified.append(qa)
                continue

            # 用 generator_llm 验证
            try:
                response = self._call_generator(question)
            except Exception as e:
                self._filter_log.append(
                    {"qa": qa, "reason": f"generator_error: {e}"}
                )
                continue

            if not self._response_matches(response, answer):
                self._filter_log.append({"qa": qa, "reason": "answer_mismatch"})
                continue

            verified.append(qa)

        self.logger.info(
            f"[MemoSynthesizer] verify_qa: {len(verified)}/{len(qa_pairs)} passed, "
            f"{len(self._filter_log)} filtered"
        )
        return verified

    def _call_generator(self, prompt: str) -> str:
        """调用 generator_llm，兼容多种 LLM 接口（callable / generate / complete）"""
        llm = self.generator_llm
        if llm is None:
            return ""
        if callable(llm):
            result = llm(prompt)
        elif hasattr(llm, "generate"):
            result = llm.generate(prompt)
        elif hasattr(llm, "complete"):
            result = llm.complete(prompt)
        else:
            return str(llm)

        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            return (
                result.get("text")
                or result.get("content")
                or result.get("response")
                or ""
            )
        return str(result)

    @staticmethod
    def _response_matches(response: str, expected_answer: str) -> bool:
        """检查 response 是否包含 answer 的关键信息（字符串包含或关键词重叠 > 50%）"""
        if not response:
            return False
        response_lower = response.lower()
        answer_lower = expected_answer.lower()
        # 简单字符串包含
        if answer_lower in response_lower:
            return True
        # 关键词重叠
        answer_keywords = set(_tokenize(answer_lower))
        response_keywords = set(_tokenize(response_lower))
        if not answer_keywords:
            return False
        overlap = answer_keywords & response_keywords
        overlap_ratio = len(overlap) / len(answer_keywords)
        return overlap_ratio > 0.5

    # ------------------------------------------------------------------
    # T2.6 跨文档 QA 合成
    # ------------------------------------------------------------------
    def synthesize_cross_doc(
        self, facts: List[Dict[str, Any]], entities: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成跨 task_id / 跨 framework 的组合 QA 对

        - 找出共享相同 semantics 但不同 task_id 的 design tokens，生成对比 QA
        - 找出相同 component_type 但不同 framework 的模板，生成对比 QA
        - 单一来源的事实生成单文档 QA
        - 每个 QA 标注 supporting_documents
        """
        qa_pairs: List[Dict[str, Any]] = []

        # 1. design tokens
        for fact in facts:
            if fact.get("type") != "design_token":
                continue
            source_task_ids = fact.get("source_task_ids") or []
            values_list = fact.get("values") or []
            if len(source_task_ids) >= 2 and len(values_list) >= 2:
                # 跨文档对比 QA：两两组合
                for i in range(len(values_list)):
                    for j in range(i + 1, len(values_list)):
                        v1 = values_list[i]
                        v2 = values_list[j]
                        t1 = v1.get("task_id", "")
                        t2 = v2.get("task_id", "")
                        if t1 == t2:
                            continue
                        semantics = fact.get("semantics", "")
                        qa_pairs.append(
                            {
                                "question": (
                                    f"对比 {t1} 和 {t2} 中 semantics='{semantics}' "
                                    f"的 design token 取值差异"
                                ),
                                "answer": (
                                    f"{t1} 中 semantics='{semantics}' 的 design token "
                                    f"(name={v1.get('name', '')}, "
                                    f"project_type={v1.get('project_type', '')}) "
                                    f"取值为 '{v1.get('value', '')}'；"
                                    f"{t2} 中 (name={v2.get('name', '')}, "
                                    f"project_type={v2.get('project_type', '')}) "
                                    f"取值为 '{v2.get('value', '')}'。"
                                ),
                                "supporting_documents": [t1, t2],
                                "type": "cross_doc",
                            }
                        )
            else:
                # 单文档 QA
                qa_pairs.extend(self._gen_single_doc_token_qa(fact))

        # 2. component templates：按 component_type 分组
        template_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for fact in facts:
            if fact.get("type") != "component_template":
                continue
            ct = fact.get("component_type", "")
            if ct:
                template_groups[ct].append(fact)

        for ct, group in template_groups.items():
            if len(group) >= 2:
                # 跨框架对比 QA
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        t1 = group[i]
                        t2 = group[j]
                        f1 = t1.get("framework", "")
                        f2 = t2.get("framework", "")
                        if f1 == f2:
                            continue
                        qa_pairs.append(
                            {
                                "question": (
                                    f"对比 {f1} 和 {f2} 框架中 {ct} 组件模板的实现差异"
                                ),
                                "answer": (
                                    f"{f1} 的 {ct} 模板 (score={t1.get('score', 0)})：\n"
                                    f"{t1.get('code', '')}\n"
                                    f"{f2} 的 {ct} 模板 (score={t2.get('score', 0)})：\n"
                                    f"{t2.get('code', '')}"
                                ),
                                "supporting_documents": [f"{f1}_{ct}", f"{f2}_{ct}"],
                                "type": "cross_doc",
                            }
                        )
            else:
                # 单文档 QA
                qa_pairs.extend(self._gen_single_doc_template_qa(group[0]))

        # 3. episodes：单文档 QA
        for fact in facts:
            if fact.get("type") != "episode":
                continue
            content = fact.get("content", "")
            if not content:
                continue
            ep_id = fact.get("episode_id", "")
            qa_pairs.append(
                {
                    "question": "以下 episode 记录了什么内容？",
                    "answer": content,
                    "supporting_documents": [ep_id] if ep_id else ["harness_memory.db"],
                    "type": "single_doc",
                }
            )

        self.logger.info(
            f"[MemoSynthesizer] synthesize_cross_doc: {len(qa_pairs)} QA pairs "
            f"({sum(1 for q in qa_pairs if q['type'] == 'cross_doc')} cross_doc)"
        )
        return qa_pairs

    def _gen_single_doc_token_qa(
        self, fact: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """为单一 design token 事实生成 QA"""
        semantics = fact.get("semantics", "")
        name = fact.get("name", "")
        value = fact.get("value", "")
        task_id = fact.get("task_id", "")
        project_type = fact.get("project_type", "")
        if not semantics and not name:
            return []
        return [
            {
                "question": (
                    f"task {task_id} 中 semantics='{semantics}' 的 design token 取值是什么？"
                ),
                "answer": (
                    f"task {task_id} (project_type={project_type}) 中 "
                    f"semantics='{semantics}' 的 design token name='{name}'，"
                    f"取值为 '{value}'。"
                ),
                "supporting_documents": [task_id] if task_id else [],
                "type": "single_doc",
            }
        ]

    def _gen_single_doc_template_qa(
        self, fact: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """为单一 component_template 事实生成 QA"""
        ct = fact.get("component_type", "")
        fw = fact.get("framework", "")
        code = fact.get("code", "")
        score = fact.get("score", 0)
        if not ct:
            return []
        return [
            {
                "question": f"{fw} 框架中 {ct} 组件模板的实现是什么？",
                "answer": f"{fw} 的 {ct} 模板 (score={score})：\n{code}",
                "supporting_documents": [f"{fw}_{ct}"],
                "type": "single_doc",
            }
        ]

    # ------------------------------------------------------------------
    # T2.7 输出 JSONL
    # ------------------------------------------------------------------
    def save(self, qa_pairs: List[Dict[str, Any]]) -> None:
        """把 QA 列表追加写入 self.output_path（JSONL 格式，每行一个 JSON 对象）"""
        with open(self.output_path, "a", encoding="utf-8") as f:
            for qa in qa_pairs:
                serializable = _make_serializable(qa)
                f.write(json.dumps(serializable, ensure_ascii=False) + "\n")
        self.logger.info(
            f"[MemoSynthesizer] save: {len(qa_pairs)} QA pairs appended to {self.output_path}"
        )

    def synthesize_and_save(self, sources: Dict[str, Any]) -> str:
        """串联五步并返回输出路径

        1. extract_facts       — 事实抽取
        2. consolidate_facts   — 事实合并
        3. surface_entities    — 实体显化
        4. synthesize_cross_doc — 跨文档 QA 合成
        5. verify_qa           — GENERATOR 自验证
        最后 save 到 JSONL。
        """
        # 重置过滤日志（每次完整合成重新计数）
        self._filter_log = []

        # Step 1: 事实抽取
        facts = self.extract_facts(sources)
        # Step 2: 事实合并
        consolidated = self.consolidate_facts(facts)
        # Step 3: 实体显化
        entities = self.surface_entities(facts)
        # Step 4: 跨文档 QA 合成
        qa_pairs = self.synthesize_cross_doc(consolidated, entities)
        # Step 5: GENERATOR 自验证
        verified = self.verify_qa(qa_pairs)
        # 保存
        self.save(verified)
        self.logger.info(
            f"[MemoSynthesizer] synthesize_and_save: {len(verified)} QA pairs "
            f"saved to {self.output_path}"
        )
        return str(self.output_path)


# ----------------------------------------------------------------------
# 模块级辅助函数
# ----------------------------------------------------------------------
def _tokenize(text: str) -> List[str]:
    """简易分词：按空格切分英文 token，逐字切分中文字符"""
    tokens: List[str] = []
    for word in text.split():
        if word:
            tokens.append(word)
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            tokens.append(ch)
    return tokens


def _make_serializable(obj: Any) -> Any:
    """递归地把 set 转为 sorted list，便于 JSON 序列化"""
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    if isinstance(obj, tuple):
        return [_make_serializable(v) for v in obj]
    return obj
