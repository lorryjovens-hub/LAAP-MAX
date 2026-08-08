"""
Baselines — 真实 LLM 对照组（裸 LLM / RAG+CoT / Few-Shot）
==============================================================

P0 #2 的核心文件——实现 LAAP 的真正竞争对手：
  1. RawLLMAdapter       — 已在 laap_adapter.py 中实现，纯 LLM 直答
  2. CoTLLMAdapter       — Chain-of-Thought 增强版
  3. RAGCoTLLMAdapter    — RAG + CoT 双重增强（论文承认的真正竞争对手）
  4. FewShotAdapter      — Few-shot prompting

接口与 RealLAAPAdapter.answer(task) 完全一致，便于公平对比。

设计原则:
    1. 所有对照组使用同一个底层 LLM（同一 LLMBridge），确保差异来自策略
    2. RAG 实现采用简单的关键词检索（避免引入 sentence-transformer 重依赖）
       后续可升级为向量检索
    3. CoT 使用 "Let's think step by step" 标准模板（Wei et al. 2022）
    4. 评判时记录策略名，便于后续分析
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional

from benchmarks.runtime.laap_adapter import RawLLMAdapter

logger = logging.getLogger("benchmarks.baselines")

__all__ = ["CoTLLMAdapter", "RAGCoTLLMAdapter", "FewShotAdapter"]


# ════════════════════════════════════════════════════════════
#  CoT — Chain-of-Thought 增强
# ════════════════════════════════════════════════════════════


COT_TEMPLATE = """Let's think step by step.

Question: {question}

Reasoning:
1. First, let me understand what is being asked...
2. ...
3. ...

Answer:"""


class CoTLLMAdapter:
    """Chain-of-Thought 增强 LLM——通过 prompt 工程让 LLM 显式推理。

    论文§7.3.1 承认："后续工作将引入 RAG/CoT 增强版对比"。
    本类就是 CoT 对照组的实现。
    """

    STRATEGY = "cot"

    def __init__(self, llm_bridge, system_prompt: Optional[str] = None):
        self.bridge = llm_bridge
        self._system_prompt = system_prompt
        self._call_count = 0

    def answer(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = task["prompt"]
        task_id = task.get("id", f"task-{self._call_count}")

        # 应用 CoT 模板
        cot_prompt = COT_TEMPLATE.format(question=prompt)

        t0 = time.time()
        original_sys = self.bridge._system_prompt
        if self._system_prompt:
            self.bridge.set_system_prompt(self._system_prompt)

        try:
            full_response = self.bridge.chat(cot_prompt)
            # 提取最终答案（"Answer:" 之后的部分）
            answer = _extract_final_answer(full_response)
            error = None
        except Exception as e:
            full_response = ""
            answer = ""
            error = str(e)

        self.bridge._system_prompt = original_sys
        self._call_count += 1

        return {
            "task_id": task_id,
            "answer": answer,
            "full_response": full_response,
            "time_ms": (time.time() - t0) * 1000,
            "mode": "cot",
            "mode_reason": "Chain-of-Thought prompting",
            "strategy": self.STRATEGY,
            "psi_trace": {},
            "agent_state": {},
            "iteration": self._call_count,
            "llm_metrics": self.bridge.stats(),
            "error": error,
        }

    def reset(self) -> None:
        self.bridge.metrics = {
            "calls": 0, "total_chars_in": 0, "total_chars_out": 0,
            "total_latency_ms": 0.0, "errors": 0,
        }
        self._call_count = 0

    def stats(self) -> Dict[str, Any]:
        return {
            "calls": self._call_count,
            "llm_bridge": self.bridge.stats(),
            "mode": "cot",
            "model": self.bridge.model_name,
        }


# ════════════════════════════════════════════════════════════
#  RAG + CoT — 检索增强 + 推理链
# ════════════════════════════════════════════════════════════


RAG_COT_TEMPLATE = """Use the following retrieved context to answer the question.
If the context is insufficient, use your own knowledge.

Context:
{context}

Question: {question}

Let's think step by step.
Reasoning:
1. ...
2. ...

Answer:"""


class SimpleRetriever:
    """简单的关键词检索器——避免引入重依赖。

    使用 TF-IDF 风格的词频匹配检索相关文档。
    生产环境可替换为向量检索（sentence-transformer + faiss）。
    """

    def __init__(self, documents: List[Dict[str, str]] = None):
        """documents: [{"id": str, "content": str, "domain": str (optional)}]"""
        self.documents: List[Dict[str, str]] = documents or []
        # 简单的英文停用词
        self._stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "and", "or", "but", "if", "then", "of", "in", "on", "at",
            "to", "for", "with", "by", "from", "as", "that", "this",
            "what", "which", "how", "why", "when", "where", "who",
            "的", "是", "在", "和", "与", "或", "但", "如", "果", "那",
            "什", "么", "为", "什", "么", "怎", "样", "如何",
        }

    def add(self, doc: Dict[str, str]) -> None:
        self.documents.append(doc)

    def add_many(self, docs: List[Dict[str, str]]) -> None:
        self.documents.extend(docs)

    def _tokenize(self, text: str) -> List[str]:
        # 中英文混合 tokenization
        # 英文：按非字母分割
        # 中文：按字分割
        tokens = []
        # 英文 tokens
        en_tokens = re.findall(r"[a-zA-Z_]+", text.lower())
        tokens.extend([t for t in en_tokens if t not in self._stop_words and len(t) > 1])
        # 中文 tokens（按字）
        zh_tokens = re.findall(r"[\u4e00-\u9fff]", text)
        tokens.extend(zh_tokens)
        return tokens

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """检索 top_k 相关文档。返回 [{content, score, id}]。"""
        if not self.documents:
            return []
        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return []

        scored: List[Dict[str, Any]] = []
        for doc in self.documents:
            doc_tokens = set(self._tokenize(doc.get("content", "")))
            # Jaccard 相似度
            if not doc_tokens:
                score = 0.0
            else:
                intersection = len(query_tokens & doc_tokens)
                union = len(query_tokens | doc_tokens)
                score = intersection / union if union else 0.0
            scored.append({
                "id": doc.get("id", ""),
                "content": doc.get("content", ""),
                "domain": doc.get("domain", ""),
                "score": round(score, 4),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class RAGCoTLLMAdapter:
    """RAG + CoT 双重增强 LLM——LAAP 的真正竞争对手。

    论文§7.3.1 自承："后续工作将引入真实 LLM 基线，特别是与 RAG/CoT 增强版对比"
    本类实现 RAG（检索增强生成）+ CoT（思维链）双重 prompt 工程。

    Args:
        llm_bridge: LLMBridge 实例
        retriever: 检索器（默认 SimpleRetriever）
        top_k: 检索文档数（默认 3）
        system_prompt: 可选 system prompt
    """

    STRATEGY = "rag_cot"

    def __init__(self, llm_bridge, retriever: Optional[SimpleRetriever] = None,
                 top_k: int = 3, system_prompt: Optional[str] = None):
        self.bridge = llm_bridge
        self.retriever = retriever or SimpleRetriever()
        self.top_k = top_k
        self._system_prompt = system_prompt
        self._call_count = 0

    def add_documents(self, docs: List[Dict[str, str]]) -> None:
        """添加检索文档。"""
        self.retriever.add_many(docs)

    def answer(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = task["prompt"]
        task_id = task.get("id", f"task-{self._call_count}")
        domain = task.get("domain", "general")

        # 1. RAG 检索
        t_retrieve = time.time()
        retrieved = self.retriever.search(prompt, top_k=self.top_k)
        retrieve_ms = (time.time() - t_retrieve) * 1000

        # 2. 构建 RAG + CoT prompt
        if retrieved:
            context = "\n\n".join(
                f"[{i+1}] (score={r['score']}) {r['content'][:500]}"
                for i, r in enumerate(retrieved)
            )
        else:
            context = "(no relevant context retrieved)"

        augmented_prompt = RAG_COT_TEMPLATE.format(context=context, question=prompt)

        # 3. 调用 LLM
        t0 = time.time()
        original_sys = self.bridge._system_prompt
        if self._system_prompt:
            self.bridge.set_system_prompt(self._system_prompt)

        try:
            full_response = self.bridge.chat(augmented_prompt)
            answer = _extract_final_answer(full_response)
            error = None
        except Exception as e:
            full_response = ""
            answer = ""
            error = str(e)

        self.bridge._system_prompt = original_sys
        self._call_count += 1

        return {
            "task_id": task_id,
            "answer": answer,
            "full_response": full_response,
            "retrieved_docs": retrieved,
            "retrieve_ms": retrieve_ms,
            "time_ms": (time.time() - t0) * 1000 + retrieve_ms,
            "mode": "rag_cot",
            "mode_reason": f"RAG (top_k={self.top_k}) + CoT prompting",
            "strategy": self.STRATEGY,
            "psi_trace": {},
            "agent_state": {},
            "iteration": self._call_count,
            "llm_metrics": self.bridge.stats(),
            "error": error,
        }

    def reset(self) -> None:
        self.bridge.metrics = {
            "calls": 0, "total_chars_in": 0, "total_chars_out": 0,
            "total_latency_ms": 0.0, "errors": 0,
        }
        self._call_count = 0

    def stats(self) -> Dict[str, Any]:
        return {
            "calls": self._call_count,
            "llm_bridge": self.bridge.stats(),
            "mode": "rag_cot",
            "model": self.bridge.model_name,
            "documents": len(self.retriever.documents),
        }


# ════════════════════════════════════════════════════════════
#  Few-Shot — 少样本学习
# ════════════════════════════════════════════════════════════


FEW_SHOT_TEMPLATE = """Here are some examples:

{examples}

Now answer this question:

Question: {question}
Answer:"""


class FewShotAdapter:
    """Few-shot 增强 LLM——通过示例引导 LLM 学习任务模式。

    Args:
        llm_bridge: LLMBridge 实例
        examples: List[{"question": str, "answer": str}] 少样本示例
    """

    STRATEGY = "few_shot"

    def __init__(self, llm_bridge, examples: List[Dict[str, str]] = None,
                 system_prompt: Optional[str] = None):
        self.bridge = llm_bridge
        self.examples = examples or []
        self._system_prompt = system_prompt
        self._call_count = 0

    def add_examples(self, examples: List[Dict[str, str]]) -> None:
        self.examples.extend(examples)

    def answer(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = task["prompt"]
        task_id = task.get("id", f"task-{self._call_count}")

        # 构建 few-shot prompt
        if self.examples:
            examples_text = "\n\n".join(
                f"Question: {ex['question']}\nAnswer: {ex['answer']}"
                for ex in self.examples[:3]  # 最多 3 个示例
            )
        else:
            examples_text = "(no examples provided)"

        augmented_prompt = FEW_SHOT_TEMPLATE.format(
            examples=examples_text, question=prompt
        )

        t0 = time.time()
        original_sys = self.bridge._system_prompt
        if self._system_prompt:
            self.bridge.set_system_prompt(self._system_prompt)

        try:
            full_response = self.bridge.chat(augmented_prompt)
            answer = _extract_final_answer(full_response)
            error = None
        except Exception as e:
            full_response = ""
            answer = ""
            error = str(e)

        self.bridge._system_prompt = original_sys
        self._call_count += 1

        return {
            "task_id": task_id,
            "answer": answer,
            "full_response": full_response,
            "time_ms": (time.time() - t0) * 1000,
            "mode": "few_shot",
            "mode_reason": f"Few-shot ({len(self.examples[:3])} examples)",
            "strategy": self.STRATEGY,
            "psi_trace": {},
            "agent_state": {},
            "iteration": self._call_count,
            "llm_metrics": self.bridge.stats(),
            "error": error,
        }

    def reset(self) -> None:
        self.bridge.metrics = {
            "calls": 0, "total_chars_in": 0, "total_chars_out": 0,
            "total_latency_ms": 0.0, "errors": 0,
        }
        self._call_count = 0

    def stats(self) -> Dict[str, Any]:
        return {
            "calls": self._call_count,
            "llm_bridge": self.bridge.stats(),
            "mode": "few_shot",
            "model": self.bridge.model_name,
            "examples": len(self.examples),
        }


# ════════════════════════════════════════════════════════════
#  辅助函数
# ════════════════════════════════════════════════════════════


def _extract_final_answer(response: str) -> str:
    """从 CoT/RAG-CoT 的完整响应中提取最终答案。

    策略:
        1. 找最后一个 "Answer:" 之后的文本（CoT 响应常含前缀 "I can answer:"）
        2. fallback: 返回完整响应
    """
    if not response:
        return ""

    # 1. 找所有 "Answer:" / "答案：" / "Final Answer:" 标记，取最后一个
    matches = list(re.finditer(
        r"(?:Final Answer|Answer|答案)[：:\s]+",
        response, re.IGNORECASE
    ))
    if matches:
        last_match = matches[-1]
        # 取标记之后的所有文本
        answer_text = response[last_match.end():].strip()
        # 截到下一个空行（避免抓到下一题）
        first_blank = answer_text.find("\n\n")
        if 0 < first_blank < 500:
            answer_text = answer_text[:first_blank].strip()
        if answer_text:
            return answer_text

    # 2. fallback: 返回完整响应
    return response.strip()
