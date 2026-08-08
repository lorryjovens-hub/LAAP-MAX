"""
Memory Adapter: Bridge between Harness-v2-agi's DesignSystemMemory and LAAP's MemoryManager

LAAP's MemoryManager provides:
- Multiple memory provider orchestration
- Context injection from all providers
- Tool routing for memory operations
- Background prefetch for performance
- Conversation memory storage

This adapter maps Harness-v2-agi's DesignSystemMemory interface to LAAP's MemoryManager
while maintaining backward compatibility.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from laap.memory.manager import MemoryManager
from laap.memory.persistent import MemoryEntry

from src.api.models import DesignToken
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _build_executive_llm_sync():
    """Wrap LAAPLLMClient (async) into a sync callable for MemoQueryProtocol.

    MemoQueryProtocol.query() is sync and calls `executive_llm(prompt) -> str`.
    LAAPLLMClient.chat_completion is async. We bridge by running the
    coroutine in a worker thread with its own event loop, which is safe
    whether the caller is sync or already inside an event loop.

    Returns None on construction failure — MemoQueryProtocol then falls
    back to rule-based query decomposition.
    """
    try:
        from src.laap_integration.llm_adapter import LAAPLLMClient

        client = LAAPLLMClient()
    except Exception as e:
        logger.warning(
            f"[LAAPDesignSystemMemory] executive_llm init failed: {e}"
        )
        return None

    import asyncio
    import concurrent.futures

    def call(prompt: str) -> str:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(
                asyncio.run,
                client.chat_completion(
                    [{"role": "user", "content": prompt}],
                    stage="reasoning",
                ),
            )
            return future.result(timeout=60)

    return call


class LAAPDesignSystemMemory:
    """
    LAAP-powered Design System Memory for Harness-v2-agi
    
    Adapts laap.memory.manager.MemoryManager to match the original 
    DesignSystemMemory interface, while adding LAAP's unified memory capabilities.
    """

    def __init__(self):
        self.settings = get_settings()
        self.memory_manager = MemoryManager()
        self.memory_file = Path("./memory/design_system_cache.json")
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        # MEMO provider mode: "rag" (default) keeps existing RAG behaviour;
        # "memo" additionally registers MemoMemoryProvider ahead of the RAG
        # provider so queries can be routed to the MEMORY model in T5.
        self.memory_provider_mode = getattr(self.settings, "memo_provider_mode", "rag")
        logger.info(
            f"[LAAPDesignSystemMemory] memory_provider_mode={self.memory_provider_mode}"
        )
        logger.info("[LAAPDesignSystemMemory] Initialized with LAAP MemoryManager")

    async def initialize(self):
        """Initialize memory providers"""
        try:
            from laap.memory.persistent import PersistentMemoryEngine, MemoryEntry
            
            class SimpleMemoryProvider:
                name = "harness_design_memory"
                
                def __init__(self, db_path):
                    self.engine = PersistentMemoryEngine(db_path)
                
                def is_available(self):
                    return True
                
                def initialize(self, session_id, **kwargs):
                    pass
                
                def system_prompt_block(self):
                    return ""
                
                def prefetch(self, query, *, session_id=""):
                    entries = self.engine.search(query, limit=5)
                    return "\n".join(f"- {e.content}" for e in entries)
                
                def sync_turn(self, user_content, assistant_content, *, session_id="", **kwargs):
                    self.engine.store(MemoryEntry(
                        content=f"User: {user_content}\nAssistant: {assistant_content}",
                        memory_type="episode",
                        importance=0.7,
                        tags=["harness", session_id]
                    ))
                
                def get_tool_schemas(self):
                    return []
                
                def handle_tool_call(self, tool_name, args, **kwargs):
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                def shutdown(self):
                    self.engine.close()
            
            persistent_provider = SimpleMemoryProvider(
                Path(self.memory_file.parent / "harness_memory.db")
            )
            self.memory_manager.add_provider(persistent_provider)

            # MEMO provider: registered only when mode=="memo". Registered
            # AFTER the RAG provider so `is_available()` controls whether
            # the MemoryManager actually routes to it; T5 will wire the
            # mode-based query routing inside `retrieve_similar_tokens`.
            if self.memory_provider_mode == "memo":
                try:
                    from src.laap_integration.memo_provider import MemoMemoryProvider
                    memo_path = getattr(self.settings, "memo_model_path", "./memory/memo_model_v1")
                    # T5: wire the EXECUTIVE LLM (from llm_adapter) and the
                    # reflection-QA output path into the MEMO provider. The
                    # protocol accepts executive_llm=None and falls back to
                    # rule-based decomposition, so a None return from the
                    # builder is graceful.
                    executive_llm = _build_executive_llm_sync()
                    memo_provider = MemoMemoryProvider(
                        model_path=memo_path,
                        executive_llm=executive_llm,
                        synthesis_output_path="./memory/memo_reflection_train.jsonl",
                    )
                    self.memory_manager.add_provider(memo_provider)
                    logger.info(
                        f"[LAAPDesignSystemMemory] MemoMemoryProvider registered "
                        f"(model_path={memo_path}, available={memo_provider.is_available()}, "
                        f"executive_llm={'on' if executive_llm else 'off'})"
                    )
                except Exception as e:
                    logger.warning(
                        f"[LAAPDesignSystemMemory] MemoMemoryProvider registration failed: {e}"
                    )

            self.memory_manager.initialize_all("harness_session")
            logger.info("[LAAPDesignSystemMemory] LAAP memory providers initialized")
        except Exception as e:
            logger.warning(f"[LAAPDesignSystemMemory] LAAP memory init failed: {e}")

    async def store_tokens(
        self, task_id: str, tokens: List[DesignToken], project_type: str
    ):
        """Store design tokens to memory"""
        cache = self._load_cache()
        cache[task_id] = {
            "tokens": [t.model_dump() for t in tokens],
            "project_type": project_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._save_cache(cache)

        token_data = json.dumps([t.model_dump() for t in tokens], ensure_ascii=False)
        user_content = f"Design tokens for task {task_id}: {token_data}"
        assistant_content = f"Stored {len(tokens)} tokens for {project_type} project"
        
        try:
            self.memory_manager.sync_all(user_content, assistant_content, session_id="harness_session")
        except Exception as e:
            logger.warning(f"LAAP memory sync failed: {e}")

        logger.info(f"[LAAPDesignSystemMemory] Stored {len(tokens)} tokens for task {task_id}")

    async def retrieve_similar_tokens(
        self, query: str, project_type: Optional[str] = None, n: int = 5
    ) -> List[Dict]:
        """Semantic search for similar design tokens"""
        # Mode routing (T5): when `self.memory_provider_mode == "memo"` and a
        # MemoMemoryProvider is available, route the query through the
        # MEMORY model + three-stage protocol instead of the RAG prefetch_all
        # call below. For T1 we keep the existing RAG path so behavior is
        # unchanged until the query protocol lands in T3/T5.
        try:
            context = self.memory_manager.prefetch_all(query, session_id="harness_session")
            if not context:
                return []
            
            lines = context.split("\n")
            results = []
            for i, line in enumerate(lines[:n]):
                if line.strip():
                    results.append({
                        "token": {"content": line.strip()},
                        "distance": 0.1 + i * 0.1,
                    })
            return results
        except Exception as e:
            logger.warning(f"LAAP memory retrieval failed: {e}")
            return self._fallback_retrieve(query, project_type, n)

    async def get_component_template(
        self, component_type: str, framework: str
    ) -> Optional[str]:
        """Get component code template"""
        templates = self._load_component_templates()
        key = f"{framework}_{component_type}"
        template = templates.get(key)
        if template:
            return template.get("code", template)
        return None

    async def store_component_template(
        self, component_type: str, framework: str, code: str, quality_score: float
    ):
        """Store high-quality component template"""
        templates = self._load_component_templates()
        key = f"{framework}_{component_type}"
        
        existing = templates.get(key, {})
        if not existing or quality_score > existing.get("score", 0):
            templates[key] = {
                "code": code,
                "score": quality_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._save_component_templates(templates)
            logger.info(f"[LAAPDesignSystemMemory] Stored template: {key} (score: {quality_score})")

    def get_system_prompt_context(self) -> str:
        """Get memory context for system prompt injection"""
        try:
            return self.memory_manager.build_system_prompt()
        except Exception as e:
            logger.warning(f"System prompt context failed: {e}")
            return ""

    def _load_cache(self) -> Dict:
        if self.memory_file.exists():
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self, cache: Dict):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    def _load_component_templates(self) -> Dict:
        template_file = Path("./memory/component_templates.json")
        if template_file.exists():
            with open(template_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_component_templates(self, templates: Dict):
        template_file = Path("./memory/component_templates.json")
        template_file.parent.mkdir(parents=True, exist_ok=True)
        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

    def _fallback_retrieve(self, query: str, project_type: Optional[str], n: int) -> List[Dict]:
        cache = self._load_cache()
        results = []
        for task_id, data in cache.items():
            if project_type and data.get("project_type") != project_type:
                continue
            for token_data in data.get("tokens", []):
                token_text = f"{token_data.get('name', '')} {token_data.get('semantics', '')} {token_data.get('value', '')}"
                if query.lower() in token_text.lower():
                    results.append({
                        "token": token_data,
                        "distance": 0.3,
                    })
                    if len(results) >= n:
                        return results
        return results

    async def close(self):
        """Close memory connections"""
        try:
            self.memory_manager.shutdown_all()
        except Exception as e:
            logger.warning(f"Memory shutdown failed: {e}")

    def stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        cache = self._load_cache()
        templates = self._load_component_templates()
        return {
            "task_count": len(cache),
            "template_count": len(templates),
            "total_tokens": sum(len(d.get("tokens", [])) for d in cache.values()),
        }