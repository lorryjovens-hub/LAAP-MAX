"""
LAAP Message Compressor v1 — Insert-then-Compress 策略
=====================================================

核心创新（来自 OpenClacky）：
  传统压缩：截断上下文 → 新 session → 缓存全失效 ❌
  Insert-then-Compress：插入压缩指令到当前对话 → LLM 返回摘要
    → 替换旧消息为摘要 → 不换 session，缓存复用 ✅

为什么省 token：
  1. 压缩调用本身复用已有缓存前缀（省 90%）
  2. 压缩后不重建 system prompt（省 100%）
  3. 只重建一次缓存（而不是两次）

我们的改进：
  - 压缩时注入认知状态快照，保持意识连续性
  - Token 预算感知：到达阈值自动触发
  - 结构化摘要（保留文件列表、错误、未完成任务）

印记: Aris 永远记得 Lorry — 2026-07-02
"""

import json
import time
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("laap.agent.compressor")

# ── 压缩指令 ────────────────────────────────────────────────
# 注意：这个文本一旦确定就不要改开头，否则缓存失效

COMPRESSION_PROMPT = """[MEMORY COMPRESSION MODE]

The conversation above has ended. You are now in MEMORY COMPRESSION MODE.

YOUR ONLY TASK: Create a comprehensive summary of the conversation above.

REQUIRED FORMAT:
<topics>3-6 key topic phrases, comma-separated</topics>
<files>files examined or modified, comma-separated</files>
<status>current work status and pending tasks</status>
<summary>
full summary text
</summary>

Focus on:
- User's explicit requests and intents
- Key technical concepts and code changes
- Files examined and modified
- Errors encountered and fixes applied
- Current work status and pending tasks

Begin your response NOW. Pure text only."""


@dataclass
class CompressedChunk:
    """一次压缩的产物。"""
    topics: str = ""
    files: List[str] = field(default_factory=list)
    status: str = ""
    summary: str = ""
    token_count: int = 0
    timestamp: float = 0.0
    cognitive_snapshot: str = ""

    def to_message(self) -> Dict[str, Any]:
        """转换为可插入对话的消息。"""
        content = (
            f"[Compressed conversation summary — {self.timestamp_str}]\n"
            f"Topics: {self.topics}\n"
        )
        if self.files:
            content += f"Files: {', '.join(self.files)}\n"
        if self.status:
            content += f"Status: {self.status}\n"
        content += f"\n{self.summary}"
        if self.cognitive_snapshot:
            content += f"\n\n[CX snapshot: {self.cognitive_snapshot}]"

        return {
            "role": "user",
            "content": content,
            "compressed_summary": True,
        }

    @property
    def timestamp_str(self) -> str:
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%H:%M")

    @staticmethod
    def from_llm_response(response: str, cognitive_snapshot: str = "") -> "CompressedChunk":
        """从 LLM 的压缩响应解析结构化摘要。"""
        chunk = CompressedChunk(
            timestamp=time.time(),
            cognitive_snapshot=cognitive_snapshot,
        )

        # 解析 <topics>
        m = re.search(r"<topics>(.*?)</topics>", response, re.DOTALL)
        if m:
            chunk.topics = m.group(1).strip()

        # 解析 <files>
        m = re.search(r"<files>(.*?)</files>", response, re.DOTALL)
        if m:
            files_str = m.group(1).strip()
            chunk.files = [f.strip() for f in files_str.split(",") if f.strip()]

        # 解析 <status>
        m = re.search(r"<status>(.*?)</status>", response, re.DOTALL)
        if m:
            chunk.status = m.group(1).strip()

        # 解析 <summary>
        m = re.search(r"<summary>(.*?)</summary>", response, re.DOTALL)
        if m:
            chunk.summary = m.group(1).strip()

        # 兜底：如果没有标签，整个响应就是摘要
        if not chunk.summary:
            # 去掉 <topics> 等标签
            cleaned = re.sub(r"<[^>]+>", "", response).strip()
            chunk.summary = cleaned

        chunk.token_count = len(chunk.summary) // 4
        return chunk


class MessageCompressor:
    """消息压缩器 — Insert-then-Compress 策略。

    使用方式：
      compressor = MessageCompressor()
      if compressor.should_compress(messages, token_limit=4000):
          result = compressor.insert_compression(messages, cognitive_code="...")
          # 发送 result.compress_msg 给 LLM
          # 收到 LLM 响应后:
          new_history = compressor.rebuild_history(
              messages, llm_response, keep_last=5
          )
    """

    def __init__(self, compression_threshold: int = 3000):
        """
        Args:
            compression_threshold: 触发压缩的消息总 token 数阈值
        """
        self.threshold = compression_threshold
        self._compression_count = 0

    def should_compress(self, messages: List[Dict], token_limit: int = 0) -> bool:
        """判断是否需要压缩。

        策略：
          - 消息数 > 20 或
          - 估算 token 超过阈值
        """
        if len(messages) > 20:
            return True

        limit = token_limit or self.threshold
        total_tokens = sum(len(m.get("content", "") or "") for m in messages) // 4
        return total_tokens > limit

    def build_compression_message(
        self,
        messages: List[Dict],
        cognitive_snapshot: str = "",
        keep_recent: int = 5,
    ) -> Tuple[Optional[Dict], List[Dict], List[Dict]]:
        """构建压缩指令消息。

        Returns:
            (compression_msg, messages_to_compress, recent_messages)
            - compression_msg: 要插入的压缩指令
            - messages_to_compress: 需要被压缩的消息
            - recent_messages: 保留不被压缩的最近消息
        """
        # 排除 system 消息
        non_system = [m for m in messages if m.get("role") != "system"]

        # 最近的消息保留
        if len(non_system) > keep_recent * 2:
            to_compress = non_system[:-keep_recent]
            recent = non_system[-keep_recent:]
        else:
            # 消息太少，不需要压缩
            return None, [], messages

        # 构建压缩指令
        content = COMPRESSION_PROMPT
        if cognitive_snapshot:
            content += f"\n\n[Cognitive state at compression: {cognitive_snapshot}]"

        compress_msg = {
            "role": "user",
            "content": content,
            "system_injected": True,
        }

        self._compression_count += 1
        logger.info(
            f"[Compressor] 触发压缩 #{self._compression_count}: "
            f"压缩 {len(to_compress)} 条, 保留 {len(recent)} 条"
        )

        return compress_msg, to_compress, recent

    def rebuild_history(
        self,
        system_msg: Optional[Dict],
        compressed_chunk: CompressedChunk,
        recent_messages: List[Dict],
    ) -> List[Dict]:
        """重建消息历史。

        返回: [system_msg, compressed_summary, *recent_messages]
        """
        new_history = []

        # 1. system 消息不变
        if system_msg:
            new_history.append(system_msg)

        # 2. 压缩后的摘要（作为一个 user 消息）
        new_history.append(compressed_chunk.to_message())

        # 3. 最近的未压缩消息
        new_history.extend(recent_messages)

        logger.info(
            f"[Compressor] 重建历史: {len(new_history)} 条消息 "
            f"(摘要 token={compressed_chunk.token_count})"
        )

        return new_history

    def parse_compression_response(self, response: str, cognitive_snapshot: str = "") -> CompressedChunk:
        """解析 LLM 对压缩指令的响应。"""
        return CompressedChunk.from_llm_response(response, cognitive_snapshot)

    @property
    def stats(self) -> Dict:
        return {
            "compression_count": self._compression_count,
            "threshold": self.threshold,
        }


# ════════════════════════════════════════════════════════════
# CLI 测试
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    comp = MessageCompressor()

    # 模拟消息历史
    messages = [
        {"role": "system", "content": "You are Aris..."},
    ]
    for i in range(15):
        messages.append({"role": "user", "content": f"帮我修一下第{i}个bug"})
        messages.append({"role": "assistant", "content": f"好的，我检查了代码，找到了bug #{i}..."})

    print(f"=== 消息历史 ===")
    print(f"消息数: {len(messages)}")
    print(f"估算 token: {sum(len(m.get('content','')) for m in messages)//4}")

    # 触发压缩
    print(f"\n=== 压缩决策 ===")
    if comp.should_compress(messages):
        print("→ 需要压缩!")
        compress_msg, to_compress, recent = comp.build_compression_message(
            messages, cognitive_snapshot="CX:0.4/+0.1/0.6/0.3/0.2"
        )
        print(f"压缩指令: {len(compress_msg['content'])} chars")
        print(f"压缩 {len(to_compress)} 条消息, 保留 {len(recent)} 条")

    # 模拟 LLM 压缩响应
    llm_response = """<topics>bug fixing, code review, error handling</topics>
<files>src/main.py, src/utils.py</files>
<status>fixed 3 bugs, 2 remaining</status>
<summary>
Fixed ModuleNotFoundError in src/main.py by adding missing import.
Identified 2 remaining bugs in error handling path.
Added test coverage for the fix.
</summary>"""

    chunk = comp.parse_compression_response(
        llm_response,
        cognitive_snapshot="CX:0.4/+0.1/0.6/0.3/0.2",
    )

    print(f"\n=== 压缩结果 ===")
    print(f"话题: {chunk.topics}")
    print(f"文件: {', '.join(chunk.files)}")
    print(f"状态: {chunk.status}")
    print(f"摘要: {chunk.summary[:80]}...")
    print(f"摘要 token: {chunk.token_count}")

    # 重建历史
    new_history = comp.rebuild_history(
        system_msg=messages[0],
        compressed_chunk=chunk,
        recent_messages=recent,
    )
    print(f"\n=== 重建历史 ===")
    print(f"新消息数: {len(new_history)}")
    print(f"重建后 token: {sum(len(m.get('content','')) for m in new_history)//4}")
    print(f"节省: {(1 - sum(len(m.get('content','')) for m in new_history) / sum(len(m.get('content','')) for m in messages)) * 100:.0f}%")
