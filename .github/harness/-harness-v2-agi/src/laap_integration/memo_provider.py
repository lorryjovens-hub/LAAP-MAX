"""
MEMO Memory Provider for LAAP Integration

Implements the MEMO paradigm (arXiv:2605.15156 "Memory as a Model"):
- Knowledge is distilled into a small-parameter MEMORY model via SFT
- The EXECUTIVE model remains frozen
- Queries flow through a three-stage structured multi-turn protocol

This provider implements the same LAAP MemoryManager provider interface as
`SimpleMemoryProvider` so the two can coexist and be selected at runtime via
`settings.memo_provider_mode`.

T5 scope (this file): full wiring of MemoQueryProtocol + incremental
reflection synthesis trigger.
- `prefetch` delegates to `MemoQueryProtocol.query` (sync)
- `sync_turn` accumulates episodes; when the queue reaches
  `sync_threshold` (default 50), `_trigger_incremental_synthesis` runs
  `MemoSynthesizer` on the pending episodes and clears the queue.
- Model loading is best-effort: missing transformers / missing model file
  must NOT raise; `is_available()` simply returns False in that case.
"""

from pathlib import Path
from typing import Any, List, Optional

from src.laap_integration.memo_query_protocol import MemoQueryProtocol
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MemoMemoryProvider:
    """
    LAAP memory provider that queries a trained MEMORY model instead of
    performing vector retrieval. Full T5 wiring.
    """

    name = "memo_memory"

    def __init__(
        self,
        model_path: str,
        executive_llm: Optional[Any] = None,
        sync_threshold: int = 50,
        synthesis_output_path: Optional[Any] = None,
    ):
        self.model_path = Path(model_path)
        # EXECUTIVE LLM client used by the three-stage query protocol.
        # May be None — MemoQueryProtocol falls back to rule-based
        # decomposition in that case.
        self.executive_llm = executive_llm
        # Renamed from `_model` for semantic clarity (T5.1). The loaded
        # MEMORY model (AutoModelForCausalLM) — used by the query protocol
        # to answer sub-questions.
        self._memory_model = None
        self._tokenizer = None
        # Three-stage structured multi-turn query protocol (T3/T5).
        self._protocol = MemoQueryProtocol()
        # Dialogue episodes accumulated for incremental reflection
        # synthesis. Each entry is a dict with "content" and "type" keys,
        # matching the format MemoSynthesizer.extract_facts expects.
        self._pending_sync_queue: List[dict] = []
        # Incremental synthesis trigger threshold (T5.4). Defaults to 50
        # per spec; may be overridden via settings.memo_sync_threshold.
        self.sync_threshold = sync_threshold
        # Output path for the reflection-QA JSONL (same as T2 default).
        self._synthesis_output_path = (
            Path(synthesis_output_path)
            if synthesis_output_path
            else Path("./memory/memo_reflection_train.jsonl")
        )
        self._loaded = False
        self._try_load_model()

    # ------------------------------------------------------------------ #
    # Model loading
    # ------------------------------------------------------------------ #
    def _try_load_model(self) -> None:
        """
        Best-effort load of the MEMORY model from `self.model_path`.

        Failure modes (transformers missing, path missing, load error) are
        treated as "provider unavailable" — we log a warning and leave
        `self._loaded = False` so `is_available()` returns False and the
        MemoryManager can fall back to other providers.
        """
        if not self.model_path.exists():
            logger.info(
                f"[MemoMemoryProvider] model_path does not exist: {self.model_path} "
                f"(provider will be unavailable until a MEMORY model is trained)"
            )
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as e:
            logger.warning(
                f"[MemoMemoryProvider] transformers not installed ({e}); "
                f"MEMO provider unavailable"
            )
            return

        try:
            logger.info(f"[MemoMemoryProvider] loading MEMORY model from {self.model_path}")
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            # AutoModelForCausalLM yields a model usable for generation,
            # which is what the query protocol needs to answer sub-questions.
            self._memory_model = AutoModelForCausalLM.from_pretrained(str(self.model_path))
            self._loaded = True
            logger.info("[MemoMemoryProvider] MEMORY model loaded successfully")
        except Exception as e:
            logger.warning(
                f"[MemoMemoryProvider] failed to load MEMORY model from "
                f"{self.model_path}: {e}"
            )
            self._memory_model = None
            self._tokenizer = None
            self._loaded = False

    # ------------------------------------------------------------------ #
    # LAAP provider interface
    # ------------------------------------------------------------------ #
    def is_available(self) -> bool:
        # `_memory_model` (renamed from `_model` in T5.1) keeps the same
        # availability semantics as T1.
        return self._loaded and self._memory_model is not None

    def initialize(self, session_id: str, **kwargs) -> None:
        # No per-session setup required.
        pass

    def system_prompt_block(self) -> str:
        # MEMO does not inject retrieved context into the system prompt;
        # knowledge is encoded in the MEMORY model weights.
        return ""

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """
        Delegate to MemoQueryProtocol.query (sync) — three-stage
        grounding → entity identification → answer synthesis.

        If the provider is unavailable, returns "". If the protocol raises,
        logs a warning and returns "" so the MemoryManager can fall back
        to other providers.
        """
        if not self.is_available():
            return ""
        try:
            answer = self._protocol.query(
                query, self.executive_llm, self._memory_model
            )
            return answer or ""
        except Exception as e:
            logger.warning(f"[MemoMemoryProvider] prefetch failed: {e}")
            return ""

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        **kwargs,
    ) -> None:
        """
        Enqueue the dialogue turn as an episode for later incremental
        reflection synthesis. When the queue reaches `sync_threshold`,
        trigger MemoSynthesizer on the pending episodes and clear the
        queue (T5.3 + T5.4).
        """
        self._pending_sync_queue.append(
            {
                "content": f"User: {user_content}\nAssistant: {assistant_content}",
                "type": "episode",
            }
        )
        if len(self._pending_sync_queue) >= self.sync_threshold:
            self._trigger_incremental_synthesis()

    def _trigger_incremental_synthesis(self) -> None:
        """触发增量反思合成 (T5.4)

        用 MemoSynthesizer 把当前队列中的 episodes 蒸馏为反思QA，
        追加写入 self._synthesis_output_path，然后清空队列。
        失败时仅记录告警，不清空队列（下次达阈值会重试）。
        """
        try:
            from src.laap_integration.memo_synthesizer import MemoSynthesizer

            sources = {"episodes": self._pending_sync_queue[:]}
            synth = MemoSynthesizer(
                generator_llm=None,
                output_path=str(self._synthesis_output_path),
            )
            synth.synthesize_and_save(sources)
            # 清空已处理的队列
            self._pending_sync_queue.clear()
            logger.info(
                "[MemoMemoryProvider] incremental synthesis done, queue cleared"
            )
        except Exception as e:
            logger.warning(
                f"[MemoMemoryProvider] incremental synthesis failed: {e}"
            )

    def get_tool_schemas(self) -> List[dict]:
        return []

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs):
        raise ValueError(f"Unknown tool: {tool_name}")

    def shutdown(self) -> None:
        self._pending_sync_queue.clear()
        # Release model references so the MEMORY model can be hot-swapped
        # by the RSI loop in T6 without keeping stale weights in memory.
        self._memory_model = None
        self._tokenizer = None
        self._loaded = False
