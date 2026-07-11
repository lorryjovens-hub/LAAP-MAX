"""
MEMO 三阶段结构化多轮查询协议

实现 MEMO (arXiv:2605.15156) 的核心创新之二：EXECUTIVE 模型把复杂查询拆解为
原子子问题，向 MEMORY 模型多轮提问，最后合成答案。

三阶段协议：
1. 基础建立 (grounding): EXECUTIVE 把复杂查询拆解为 2-5 个原子子问题
2. 实体识别 (entity identification): 根据初步答案迭代追问确定关键实体
3. 答案合成 (answer synthesis): 针对确认的实体向 MEMORY 模型索取支持事实并合成

检索成本与语料规模解耦：单次查询的子问题数量与总 token 开销不随语料增长。
"""

import inspect
import json
import re
from typing import Any, List, Optional

from src.utils.logger import get_logger


class MemoQueryProtocol:
    """MEMO 三阶段结构化多轮查询协议"""

    def __init__(self, max_subqueries: int = 5):
        """
        Args:
            max_subqueries: 基础建立阶段拆解的最大原子子问题数量
        """
        self.max_subqueries = max_subqueries
        self.logger = get_logger(__name__)

    # ================================================================
    # Stage 1: 基础建立 (Grounding)
    # ================================================================

    def stage1_grounding(self, executive_llm, query) -> List[str]:
        """
        基础建立阶段：调用 EXECUTIVE 模型把复杂查询拆解为原子子问题列表（同步）。

        Args:
            executive_llm: EXECUTIVE 模型，callable(prompt) -> str
            query: 复杂查询字符串

        Returns:
            原子子问题字符串列表，最多 max_subqueries 个
        """
        self.logger.info(f"[MemoQueryProtocol] stage1 grounding start: {query}")

        if executive_llm is not None:
            try:
                prompt = self._build_grounding_prompt(query)
                response = executive_llm(prompt)
                if inspect.iscoroutine(response):
                    self.logger.warning(
                        "[MemoQueryProtocol] stage1 got coroutine in sync context, "
                        "use stage1_grounding_async instead; falling back to rules"
                    )
                else:
                    sub_questions = self._parse_json_list(response)
                    if sub_questions is not None:
                        limited = sub_questions[: self.max_subqueries]
                        self.logger.info(
                            f"[MemoQueryProtocol] stage1 parsed {len(limited)} sub-questions from LLM"
                        )
                        return limited
                    self.logger.warning(
                        f"[MemoQueryProtocol] stage1 JSON parse failed, "
                        f"falling back to rules. response={str(response)[:120]}"
                    )
            except Exception as e:
                self.logger.warning(
                    f"[MemoQueryProtocol] stage1 exec_llm failed: {e}, falling back to rules"
                )

        return self._rule_based_split(query)

    async def stage1_grounding_async(self, executive_llm, query) -> List[str]:
        """基础建立阶段（异步版本，兼容 async exec_llm）"""
        self.logger.info(f"[MemoQueryProtocol] stage1 grounding (async) start: {query}")

        if executive_llm is not None:
            try:
                prompt = self._build_grounding_prompt(query)
                response = executive_llm(prompt)
                if inspect.iscoroutine(response):
                    response = await response
                sub_questions = self._parse_json_list(response)
                if sub_questions is not None:
                    limited = sub_questions[: self.max_subqueries]
                    return limited
                self.logger.warning(
                    f"[MemoQueryProtocol] stage1 async JSON parse failed, "
                    f"falling back to rules. response={str(response)[:120]}"
                )
            except Exception as e:
                self.logger.warning(
                    f"[MemoQueryProtocol] stage1 async exec_llm failed: {e}"
                )

        return self._rule_based_split(query)

    def _build_grounding_prompt(self, query: str) -> str:
        return (
            "你是 EXECUTIVE 模型。请把以下复杂查询拆解为 2-5 个原子子问题，"
            "每个子问题应当能独立向 MEMORY 模型提问。\n"
            "输出格式：JSON 数组，例如 [\"子问题1\", \"子问题2\"]\n"
            "不要输出任何其他文本。\n\n"
            f"复杂查询：{query}"
        )

    def _rule_based_split(self, query: str) -> List[str]:
        """规则拆解：按连接词切分（executive_llm 不可用时的回退）"""
        if not query:
            return []
        parts = re.split(r"(?:并|且|对比|以及|和|，|,|;|；)", query)
        parts = [p.strip() for p in parts if p and p.strip()]
        if not parts:
            return [query]
        return parts[: self.max_subqueries]

    # ================================================================
    # Stage 2: 实体识别 (Entity Identification)
    # ================================================================

    def stage2_entity_identification(
        self, executive_llm, sub_answers: List[str]
    ) -> List[str]:
        """
        实体识别阶段：根据初步答案，迭代追问确定关键实体（同步）。

        Args:
            executive_llm: EXECUTIVE 模型
            sub_answers: stage1 中各子问题的 MEMORY 模型回答

        Returns:
            关键实体字符串列表
        """
        self.logger.info("[MemoQueryProtocol] stage2 entity identification start")

        if executive_llm is not None:
            try:
                prompt = self._build_entity_prompt(sub_answers)
                response = executive_llm(prompt)
                if inspect.iscoroutine(response):
                    self.logger.warning(
                        "[MemoQueryProtocol] stage2 got coroutine in sync context, "
                        "use stage2_entity_identification_async instead; falling back to regex"
                    )
                else:
                    entities = self._parse_json_list(response)
                    if entities is not None:
                        return entities
                    # JSON 解析失败：若响应非空，将整段响应作为单个实体
                    if response and str(response).strip():
                        return [str(response).strip()]
                    self.logger.warning(
                        "[MemoQueryProtocol] stage2 empty response, falling back to regex"
                    )
            except Exception as e:
                self.logger.warning(
                    f"[MemoQueryProtocol] stage2 exec_llm failed: {e}, falling back to regex"
                )

        return self._regex_extract_entities(sub_answers)

    async def stage2_entity_identification_async(
        self, executive_llm, sub_answers: List[str]
    ) -> List[str]:
        """实体识别阶段（异步版本）"""
        self.logger.info("[MemoQueryProtocol] stage2 entity identification (async) start")

        if executive_llm is not None:
            try:
                prompt = self._build_entity_prompt(sub_answers)
                response = executive_llm(prompt)
                if inspect.iscoroutine(response):
                    response = await response
                entities = self._parse_json_list(response)
                if entities is not None:
                    return entities
                if response and str(response).strip():
                    return [str(response).strip()]
            except Exception as e:
                self.logger.warning(
                    f"[MemoQueryProtocol] stage2 async exec_llm failed: {e}"
                )

        return self._regex_extract_entities(sub_answers)

    def _build_entity_prompt(self, sub_answers: List[str]) -> str:
        answers_text = "\n".join(f"- {a}" for a in sub_answers if a)
        return (
            "你是 EXECUTIVE 模型。请从以下 MEMORY 模型的回答中识别关键实体，"
            "包括 task_id、framework、component_type、设计 token 名称等。\n"
            "输出格式：JSON 数组，例如 [\"React\", \"Button\", \"task_001\"]\n"
            "不要输出任何其他文本。\n\n"
            f"MEMORY 模型回答：\n{answers_text}"
        )

    def _regex_extract_entities(self, texts: List[str]) -> List[str]:
        """正则提取实体：引号内内容、大写开头的词、标识符等"""
        entities: List[str] = []
        combined = "\n".join(t for t in texts if t)
        if not combined:
            return entities
        # 引号内内容
        entities.extend(re.findall(r'["\']([^"\']+)["\']', combined))
        # 大写开头的拉丁字母词
        entities.extend(re.findall(r"\b([A-Z][a-zA-Z]+)\b", combined))
        # 标识符如 task_001、component_xxx
        entities.extend(re.findall(r"\b([a-z]+_[a-zA-Z0-9]+)\b", combined))
        # 去重保序
        seen = set()
        unique = []
        for e in entities:
            if e and e not in seen:
                seen.add(e)
                unique.append(e)
        return unique

    # ================================================================
    # Stage 3: 答案合成 (Answer Synthesis)
    # ================================================================

    def stage3_answer_synthesis(
        self, executive_llm, memory_model, entities: List[str]
    ) -> str:
        """
        答案合成阶段：针对确认的实体向 memory_model 索取支持事实，并合成最终答案（同步）。

        Args:
            executive_llm: EXECUTIVE 模型
            memory_model: 已加载的 MEMORY 小参数模型
            entities: stage2 识别的关键实体列表

        Returns:
            合成的最终答案字符串
        """
        self.logger.info("[MemoQueryProtocol] stage3 answer synthesis start")

        # 对每个实体向 MEMORY 模型索取支持事实
        supporting_facts: List[str] = []
        for entity in entities:
            fact = self._query_memory_model(memory_model, entity)
            if fact:
                supporting_facts.append(fact)

        context = "\n".join(supporting_facts)

        # executive_llm 不可用：简单拼接支持事实作为答案
        if executive_llm is None:
            self.logger.info(
                "[MemoQueryProtocol] stage3 exec_llm None, joining facts as answer"
            )
            return context

        try:
            prompt = self._build_synthesis_prompt(entities, supporting_facts)
            synthesis = executive_llm(prompt)
            if inspect.iscoroutine(synthesis):
                self.logger.warning(
                    "[MemoQueryProtocol] stage3 got coroutine in sync context, "
                    "use stage3_answer_synthesis_async instead"
                )
                synthesis = ""
            if synthesis:
                return str(synthesis)
        except Exception as e:
            self.logger.warning(f"[MemoQueryProtocol] stage3 exec_llm failed: {e}")

        # exec_llm 返回空或调用失败时的回退：
        # entities 在 stage2 fallback 路径下可能携带原始合成文本，
        # 优先返回最相关的实体信息
        if entities:
            return entities[0]
        return context

    async def stage3_answer_synthesis_async(
        self, executive_llm, memory_model, entities: List[str]
    ) -> str:
        """答案合成阶段（异步版本，memory_model 仍按同步处理）"""
        self.logger.info("[MemoQueryProtocol] stage3 answer synthesis (async) start")

        supporting_facts: List[str] = []
        for entity in entities:
            fact = self._query_memory_model(memory_model, entity)
            if fact:
                supporting_facts.append(fact)

        context = "\n".join(supporting_facts)

        if executive_llm is None:
            return context

        try:
            prompt = self._build_synthesis_prompt(entities, supporting_facts)
            synthesis = executive_llm(prompt)
            if inspect.iscoroutine(synthesis):
                synthesis = await synthesis
            if synthesis:
                return str(synthesis)
        except Exception as e:
            self.logger.warning(
                f"[MemoQueryProtocol] stage3 async exec_llm failed: {e}"
            )

        if entities:
            return entities[0]
        return context

    def _build_synthesis_prompt(
        self, entities: List[str], supporting_facts: List[str]
    ) -> str:
        facts_text = (
            "\n".join(f"- {f}" for f in supporting_facts) if supporting_facts else "(无)"
        )
        entities_text = ", ".join(entities) if entities else "(无)"
        return (
            "你是 EXECUTIVE 模型。请基于以下支持事实合成最终答案。\n"
            "要求：综合所有事实，给出完整、连贯的答案。\n\n"
            f"关键实体：{entities_text}\n\n"
            f"支持事实：\n{facts_text}\n\n"
            "最终答案："
        )

    # ================================================================
    # Memory Model Helper
    # ================================================================

    def _query_memory_model(self, memory_model, question: str) -> str:
        """
        向 MEMORY 模型提问的辅助方法。

        - memory_model 为 None → 返回空字符串
        - 有 generate 方法 → 调用 memory_model.generate(question)
        - 可调用 → 调用 memory_model(question)
        - 否则返回空字符串并日志告警
        """
        if memory_model is None:
            return ""
        try:
            if hasattr(memory_model, "generate") and callable(memory_model.generate):
                result = memory_model.generate(question)
                return str(result) if result is not None else ""
            if callable(memory_model):
                result = memory_model(question)
                return str(result) if result is not None else ""
            self.logger.warning(
                "[MemoQueryProtocol] memory_model has no generate/__call__ interface"
            )
            return ""
        except Exception as e:
            self.logger.warning(
                f"[MemoQueryProtocol] memory_model query failed: {e}"
            )
            return ""

    # ================================================================
    # Full Pipeline
    # ================================================================

    def query(self, query, executive_llm, memory_model) -> str:
        """
        串联三阶段：基础建立 → 实体识别 → 答案合成。

        Args:
            query: 复杂查询字符串
            executive_llm: EXECUTIVE 模型 (callable(prompt)->str)
            memory_model: 已加载的 MEMORY 模型

        Returns:
            合成的最终答案字符串
        """
        self.logger.info(f"[MemoQueryProtocol] stage1 grounding: {query}")
        sub_questions = self.stage1_grounding(executive_llm, query)

        self.logger.info(
            f"[MemoQueryProtocol] stage1 got {len(sub_questions)} sub-questions"
        )
        sub_answers = []
        for sq in sub_questions:
            answer = self._query_memory_model(memory_model, sq)
            sub_answers.append(answer)

        self.logger.info("[MemoQueryProtocol] stage2 entity identification")
        entities = self.stage2_entity_identification(executive_llm, sub_answers)

        self.logger.info("[MemoQueryProtocol] stage3 answer synthesis")
        final_answer = self.stage3_answer_synthesis(
            executive_llm, memory_model, entities
        )
        return final_answer

    async def query_async(self, query, executive_llm, memory_model) -> str:
        """串联三阶段（异步版本）"""
        self.logger.info(f"[MemoQueryProtocol] stage1 grounding (async): {query}")
        sub_questions = await self.stage1_grounding_async(executive_llm, query)

        self.logger.info(
            f"[MemoQueryProtocol] stage1 got {len(sub_questions)} sub-questions"
        )
        sub_answers = []
        for sq in sub_questions:
            answer = self._query_memory_model(memory_model, sq)
            sub_answers.append(answer)

        self.logger.info("[MemoQueryProtocol] stage2 entity identification (async)")
        entities = await self.stage2_entity_identification_async(
            executive_llm, sub_answers
        )

        self.logger.info("[MemoQueryProtocol] stage3 answer synthesis (async)")
        final_answer = await self.stage3_answer_synthesis_async(
            executive_llm, memory_model, entities
        )
        return final_answer

    # ================================================================
    # JSON Parsing Helper
    # ================================================================

    def _parse_json_list(self, text: Any) -> Optional[List[str]]:
        """
        解析 JSON 数组，返回字符串列表或 None（解析失败）。

        依次尝试：直接解析 → 提取首个 JSON 数组 → 提取 ```json``` 代码块。
        """
        if not text or not isinstance(text, str):
            return None
        raw = text.strip()
        # 直接解析
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(item) for item in data]
        except json.JSONDecodeError:
            pass
        # 提取首个 JSON 数组片段
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, list):
                    return [str(item) for item in data]
            except json.JSONDecodeError:
                pass
        # 提取 ```json ... ``` 代码块
        match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list):
                    return [str(item) for item in data]
            except json.JSONDecodeError:
                pass
        return None
