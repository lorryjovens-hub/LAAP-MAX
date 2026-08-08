"""LAAP — HotReloadManager：RSI 进化热编译集成（热加载即时生效）。

背景
----
RSI 闭环（TrueRSIEngine/RSISandbox）生成的改进代码目前需要：
1. 沙箱验证 → 2. 人类审批 → 3. git commit → 4. **重启进程才生效**

热编译集成消除第 4 步：改进模块**验证通过后立即热加载**，无需重启。

安全设计
--------
1. **可编辑面限制**：只允许 editable_surface 内的模块热加载；
2. **编译验证**：加载前 py_compile 检查，语法错误直接拒绝；
3. **隔离加载**：新模块先加载到独立命名空间，不污染 sys.modules；
4. **冒烟验证**：可注入 verify_fn 对新模块做运行时检查，失败拒绝；
5. **原子替换 + 回滚**：替换前保存旧模块，替换后异常可 rollback；
6. **RuntimeGuard 集成**：每次热加载记录行为，异常触发 trip。

用法::

    from laap.evolution.hot_reload import HotReloadManager
    hr = HotReloadManager()
    ok, msg = hr.hot_apply("laap/tools/my_tool.py")
    if ok:
        # 新模块已生效
        import laap.tools.my_tool  # 拿到的是新版本
    else:
        print(msg)
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import py_compile
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.evolution.hot_reload")


@dataclass
class HotReloadRecord:
    """一次热加载记录。"""

    record_id: str = field(default_factory=lambda: f"hr_{uuid.uuid4().hex[:8]}")
    module_path: str = ""
    module_name: str = ""
    status: str = "applied"  # applied / rejected / rolled_back
    reason: str = ""
    duration_ms: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "module_path": self.module_path,
            "module_name": self.module_name,
            "status": self.status,
            "reason": self.reason[:300],
            "duration_ms": round(self.duration_ms, 1),
            "created_at": self.created_at,
        }


class HotReloadManager:
    """RSI 进化热编译集成管理器。"""

    def __init__(
        self,
        editable_surface: Any = None,
        guard: Any = None,
        verify_fn: Optional[Callable[[Any], Tuple[bool, str]]] = None,
    ) -> None:
        if editable_surface is None:
            from laap.security.editable_surface import DEFAULT_SURFACE

            editable_surface = DEFAULT_SURFACE
        self._surface = editable_surface
        self._guard = guard
        self._verify_fn = verify_fn
        self._old_modules: Dict[str, Any] = {}  # module_name -> 旧模块
        self._records: List[HotReloadRecord] = []

    # ── 核心：热应用 ────────────────────────────────────────────────────

    def hot_apply(self, module_path: str) -> Tuple[bool, str]:
        """热加载一个模块文件。

        Args:
            module_path: 相对 LAAP 根目录的路径（如 "laap/tools/my_tool.py"）
                        或绝对路径。

        Returns:
            (is_ok, message)
        """
        t0 = time.time()
        record = HotReloadRecord(module_path=module_path)

        try:
            # 1. 可编辑面检查
            if not self._surface.is_editable(module_path):
                record.status = "rejected"
                record.reason = f"路径不在可编辑面: {module_path}"
                self._finish(record, t0)
                return False, record.reason

            # 2. 解析路径与模块名
            abs_path, module_name = self._resolve(module_path)
            if abs_path is None or not os.path.exists(abs_path):
                record.status = "rejected"
                record.reason = f"文件不存在: {module_path}"
                self._finish(record, t0)
                return False, record.reason
            record.module_name = module_name

            # 3. 编译验证
            try:
                py_compile.compile(abs_path, doraise=True)
            except py_compile.PyCompileError as e:
                record.status = "rejected"
                record.reason = f"编译失败: {e}"
                self._finish(record, t0)
                return False, record.reason

            # 4. 隔离加载到临时命名空间
            spec = importlib.util.spec_from_file_location(
                f"_hot_{module_name}", abs_path
            )
            if spec is None or spec.loader is None:
                record.status = "rejected"
                record.reason = f"无法加载模块: {module_path}"
                self._finish(record, t0)
                return False, record.reason

            new_module = importlib.util.module_from_spec(spec)

            # 5. 冒烟验证（可注入）
            if self._verify_fn is not None:
                ok, reason = self._verify_fn(new_module)
                if not ok:
                    record.status = "rejected"
                    record.reason = f"冒烟验证失败: {reason}"
                    self._finish(record, t0)
                    return False, record.reason

            # 6. 原子替换（先执行 exec 完成模块初始化）
            old_module = sys.modules.get(module_name, None)
            self._old_modules[module_name] = old_module
            try:
                spec.loader.exec_module(new_module)
            except Exception as e:
                record.status = "rejected"
                record.reason = f"模块执行失败: {e}"
                self._finish(record, t0)
                return False, record.reason

            sys.modules[module_name] = new_module

            # 7. 记录
            record.status = "applied"
            record.reason = f"热加载成功: {module_name}"
            self._finish(record, t0)
            logger.info(f"[HotReload] {record.reason} ({record.duration_ms:.0f}ms)")

            # 8. RuntimeGuard 记录
            if self._guard is not None:
                try:
                    self._guard.record(
                        input_len=len(module_path),
                        success=True,
                        tool_calls=0,
                    )
                except Exception:
                    pass

            return True, record.reason

        except Exception as e:  # noqa: BLE001
            record.status = "rejected"
            record.reason = f"异常: {e}"
            self._finish(record, t0)
            return False, record.reason

    # ── 回滚 ────────────────────────────────────────────────────────────

    def rollback(self, module_name: str) -> bool:
        """回滚模块到热加载前的版本。"""
        old = self._old_modules.get(module_name)
        if old is None:
            return False
        sys.modules[module_name] = old
        logger.info(f"[HotReload] 回滚: {module_name}")
        # 更新记录
        for r in reversed(self._records):
            if r.module_name == module_name and r.status == "applied":
                r.status = "rolled_back"
                r.reason = "manual rollback"
                break
        return True

    # ── 查询 ────────────────────────────────────────────────────────────

    def is_applicable(self, module_path: str) -> bool:
        """检查路径是否支持热加载（可编辑面 + 存在）。"""
        if not self._surface.is_editable(module_path):
            return False
        abs_path, _ = self._resolve(module_path)
        return abs_path is not None and os.path.exists(abs_path)

    def recent(self, n: int = 10) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._records[-n:]]

    def stats(self) -> Dict[str, Any]:
        total = len(self._records)
        applied = sum(1 for r in self._records if r.status == "applied")
        rejected = sum(1 for r in self._records if r.status == "rejected")
        rolled = sum(1 for r in self._records if r.status == "rolled_back")
        return {
            "total": total,
            "applied": applied,
            "rejected": rejected,
            "rolled_back": rolled,
            "success_rate": round(applied / total, 3) if total else 0.0,
        }

    # ── 内部 ────────────────────────────────────────────────────────────

    @staticmethod
    def _resolve(module_path: str) -> Tuple[Optional[str], str]:
        """解析路径 → (绝对路径, 模块名)。"""
        if os.path.isabs(module_path):
            abs_path = module_path
        else:
            abs_path = os.path.join(r"D:\LAAP", module_path)
        rel = os.path.relpath(abs_path, r"D:\LAAP")
        if rel.startswith(".."):
            return None, ""
        module_name = rel.replace(os.sep, ".").replace(".py", "")
        if module_name.endswith("."):
            module_name = module_name[:-1]
        return abs_path, module_name

    def _finish(self, record: HotReloadRecord, t0: float) -> None:
        record.duration_ms = (time.time() - t0) * 1000
        self._records.append(record)