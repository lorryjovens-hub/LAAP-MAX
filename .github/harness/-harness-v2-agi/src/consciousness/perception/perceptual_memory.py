"""感知记忆 - 长期缓存爬虫感知结果

作为 LAAPDesignSystemMemory 的扩展层，避免重复爬取相同 URL。
支持两种存储模式：
  - "laap":  复用 LAAPDesignSystemMemory 的存储后端（不重复造轮子）
  - "file":  独立 JSON 文件存储（无 LAAP 依赖时的回退路径）

核心机制：
  1. TTL 过期（默认 7 天，可配置）
  2. 内容指纹去重（URL 哈希 + 内容 SHA256）
  3. has_fresh_perception() 供主动调度器快速判断
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.api.models import CrawlerSnapshot, DesignToken
from src.config import get_settings
from src.utils.logger import get_logger


class PerceptualMemory:
    """
    感知记忆 - 长期缓存爬虫感知结果

    设计原则：
    1. 复用 LAAPDesignSystemMemory 的存储后端（不重复造轮子）
    2. TTL 过期机制（默认 7 天，可配置）
    3. 内容指纹去重（URL 哈希 + 内容 SHA256）
    4. 提供 has_fresh_perception() 快速判断接口，供主动调度器使用
    """

    def __init__(self, design_memory: Optional[Any] = None):
        """
        Args:
            design_memory: 可选的 LAAPDesignSystemMemory 实例。
                          若不提供，则使用独立的 JSON 文件存储。
        """
        self.settings = get_settings()
        self.logger = get_logger("perception.perceptual_memory")
        self.ttl_days: int = self.settings.perceptual_memory_ttl_days

        # 复用 LAAP 后端或独立 JSON 文件
        if design_memory is not None:
            self.design_memory = design_memory
            self._storage_mode = "laap"
        else:
            self.design_memory = None
            self._storage_mode = "file"
            self.memory_file = Path("./memory/perceptual_memory.json")
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            f"PerceptualMemory initialized (mode={self._storage_mode}, ttl={self.ttl_days}d)"
        )

    # ===================================================================
    # 公共接口
    # ===================================================================

    async def store_perception(
        self,
        url: str,
        snapshot: CrawlerSnapshot,
        ttl: Optional[int] = None,
    ) -> None:
        """
        存储感知快照

        Args:
            url: 目标 URL
            snapshot: 爬虫快照
            ttl: 自定义 TTL 天数，None 使用默认值
        """
        ttl_days = ttl if ttl is not None else self.ttl_days
        expires_at = datetime.utcnow() + timedelta(days=ttl_days)

        entry: Dict[str, Any] = {
            "url": url,
            "url_hash": self._hash_url(url),
            "fingerprint": snapshot.fingerprint,
            "snapshot": snapshot.model_dump(mode="json"),
            "stored_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl_days": ttl_days,
        }

        if self._storage_mode == "laap":
            # 复用 LAAP memory 后端
            await self._store_via_laap(url, entry)
        else:
            # 独立 JSON 文件
            self._store_via_file(url, entry)

        self.logger.info(f"Stored perception for {url} (expires: {expires_at})")

    async def get_perception(self, url: str) -> Optional[CrawlerSnapshot]:
        """
        获取未过期的感知数据，过期则返回 None

        Args:
            url: 目标 URL

        Returns:
            未过期的 CrawlerSnapshot，若不存在或已过期则返回 None
        """
        entry = await self._load_entry(url)
        if entry is None:
            return None

        if self._is_expired(entry):
            self.logger.info(f"Perception for {url} expired")
            return None

        return CrawlerSnapshot(**entry["snapshot"])

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """检查条目是否过期"""
        expires_at = datetime.fromisoformat(entry["expires_at"])
        return datetime.utcnow() > expires_at

    async def deduplicate(self, url: str, fingerprint: str) -> bool:
        """
        检查并去重

        Args:
            url: 目标 URL
            fingerprint: 新爬取内容的内容指纹（SHA256）

        Returns:
            True 表示内容未变化（仅刷新 TTL）
            False 表示内容已变化或无缓存
        """
        entry = await self._load_entry(url)
        if entry is None:
            return False

        if entry.get("fingerprint") == fingerprint:
            # 内容未变化，仅刷新 TTL
            entry["expires_at"] = (
                datetime.utcnow() + timedelta(days=self.ttl_days)
            ).isoformat()
            entry["last_refreshed"] = datetime.utcnow().isoformat()
            await self._save_entry(url, entry)
            self.logger.info(f"Content unchanged for {url}, TTL refreshed")
            return True

        return False

    async def has_fresh_perception(self, url: str) -> bool:
        """快速判断是否有新鲜感知数据（供主动调度器使用）"""
        entry = await self._load_entry(url)
        if entry is None:
            return False
        return not self._is_expired(entry)

    # ===================================================================
    # 辅助方法
    # ===================================================================

    def _hash_url(self, url: str) -> str:
        """URL 标准化后 SHA256"""
        normalized = (
            url.lower().rstrip("/").replace("https://", "").replace("http://", "")
        )
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def _load_entry(self, url: str) -> Optional[Dict[str, Any]]:
        """加载条目"""
        if self._storage_mode == "laap":
            return await self._load_via_laap(url)
        else:
            return self._load_via_file(url)

    async def _save_entry(self, url: str, entry: Dict[str, Any]) -> None:
        """保存条目"""
        if self._storage_mode == "laap":
            await self._store_via_laap(url, entry)
        else:
            self._store_via_file(url, entry)

    # -------------------------------------------------------------------
    # 文件存储辅助方法
    # -------------------------------------------------------------------

    def _load_via_file(self, url: str) -> Optional[Dict[str, Any]]:
        """从 JSON 文件加载条目"""
        if not self.memory_file.exists():
            return None

        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(self._hash_url(url))
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning(f"Failed to load perception file: {e}")
            return None

    def _store_via_file(self, url: str, entry: Dict[str, Any]) -> None:
        """存储条目到 JSON 文件"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}
        else:
            data = {}

        data[self._hash_url(url)] = entry

        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # -------------------------------------------------------------------
    # LAAP 存储辅助方法（使用 design_memory 的存储后端）
    # -------------------------------------------------------------------

    async def _store_via_laap(self, url: str, entry: Dict[str, Any]) -> None:
        """
        通过 LAAPDesignSystemMemory 存储

        将 entry 序列化为 JSON 字符串，包装成单个 DesignToken：
          - name      = perception_cache_<url_hash>
          - value     = entry 的 JSON 字符串
          - type      = "perception_cache"
          - semantics = url
        然后调用 store_tokens(task_id=url_hash, ...) 存储。
        """
        url_hash = self._hash_url(url)
        token = DesignToken(
            name=f"perception_cache_{url_hash}",
            value=json.dumps(entry, ensure_ascii=False),
            type="perception_cache",
            semantics=url,
            usage=["perceptual_memory", "crawler_snapshot"],
            confidence=1.0,
        )
        await self.design_memory.store_tokens(
            task_id=url_hash,
            tokens=[token],
            project_type="perception_cache",
        )

    async def _load_via_laap(self, url: str) -> Optional[Dict[str, Any]]:
        """
        通过 LAAPDesignSystemMemory 加载

        先用 retrieve_similar_tokens 检索（语义路径）；
        若未命中，则回退到直接读取 LAAPDesignSystemMemory 的缓存文件（精确路径）。
        """
        url_hash = self._hash_url(url)
        token_name = f"perception_cache_{url_hash}"

        try:
            results: List[Dict[str, Any]] = (
                await self.design_memory.retrieve_similar_tokens(
                    query=url_hash,
                    project_type="perception_cache",
                    n=20,
                )
            )

            for result in results:
                token = result.get("token", {}) if isinstance(result, dict) else {}

                # 路径 A: fallback 检索返回完整 DesignToken dict（含 value 字段）
                if token.get("name") == token_name and "value" in token:
                    try:
                        return json.loads(token["value"])
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse token value: {e}")
                        continue

                # 路径 B: 主检索返回 {"content": line}
                #         content 形如 "Design tokens for task <hash>: [{...}]"
                if "content" in token:
                    entry = self._extract_entry_from_content(token["content"], url_hash)
                    if entry is not None:
                        return entry

            # 路径 C: 精确回退 - 直接读取 LAAPDesignSystemMemory 缓存文件
            return self._load_via_laap_cache(url_hash, token_name)

        except Exception as e:
            self.logger.warning(f"LAAP retrieval failed: {e}")
            return None

    def _extract_entry_from_content(
        self, content: str, url_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        从 LAAP prefetch 内容中提取条目

        Content 形如:
            Design tokens for task <hash>: [{"name": "...", "value": "<json>", ...}]
        """
        try:
            start = content.find("[")
            end = content.rfind("]")
            if start == -1 or end == -1 or end <= start:
                return None

            tokens = json.loads(content[start : end + 1])
            if not isinstance(tokens, list):
                return None

            target_name = f"perception_cache_{url_hash}"
            for token_data in tokens:
                if (
                    isinstance(token_data, dict)
                    and token_data.get("name") == target_name
                    and "value" in token_data
                ):
                    return json.loads(token_data["value"])
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.debug(f"Failed to extract entry from content: {e}")
        return None

    def _load_via_laap_cache(
        self, url_hash: str, token_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        直接从 LAAPDesignSystemMemory 的缓存文件加载

        当语义检索未命中时使用，保证精确查找。
        """
        try:
            cache = self.design_memory._load_cache()
            entry_data = cache.get(url_hash)
            if entry_data is None:
                return None
            for token_data in entry_data.get("tokens", []):
                if token_data.get("name") == token_name:
                    return json.loads(token_data["value"])
        except Exception as e:
            self.logger.warning(f"Direct cache access failed: {e}")
        return None
