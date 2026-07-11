"""Unit tests for laap_brain.enhance(return_adapter=...) enhancement."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from laap_brain import LaapBrain, enhance


class TestEnhanceReturnAdapter:
    def test_enhance_default_returns_brain_only(self):
        """默认 return_adapter=False 返回 LaapBrain（向后兼容）"""
        result = enhance()
        assert isinstance(result, LaapBrain)

    def test_enhance_return_adapter_true_returns_tuple(self):
        """return_adapter=True 返回 (LaapBrain, adapter_or_None) 元组"""
        result = enhance(return_adapter=True)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], LaapBrain)
        # result[1] 可能是 AgentAdapter 实例或 None

    def test_enhance_return_adapter_true_with_generic_fallback(self, monkeypatch):
        """auto 模式下应回退到 GenericAdapter（兜底）"""
        # 清理可能的环境变量，避免误检测到 hermes
        monkeypatch.delenv("HERMES_HOME", raising=False)
        brain, adapter = enhance(return_adapter=True)
        # GenericAdapter 是兜底，应该返回
        assert adapter is not None
        assert adapter.name() == "generic"

    def test_enhance_default_does_not_call_mount_brain(self):
        """return_adapter=False 时不调用 mount_brain_to_agent"""
        with patch("laap.sdk.mount_brain_to_agent") as mock_mount:
            enhance()
            mock_mount.assert_not_called()

    def test_enhance_return_adapter_true_calls_mount_brain(self):
        """return_adapter=True 时调用 mount_brain_to_agent"""
        with patch("laap.sdk.mount_brain_to_agent") as mock_mount:
            mock_adapter = MagicMock()
            mock_mount.return_value = (MagicMock(), mock_adapter)
            brain, adapter = enhance(return_adapter=True)
            mock_mount.assert_called_once()
            assert isinstance(brain, LaapBrain)
            assert adapter is mock_adapter

    def test_enhance_return_adapter_handles_exception(self):
        """mount_brain_to_agent 异常时返回 (brain, None)"""
        with patch(
            "laap.sdk.mount_brain_to_agent", side_effect=Exception("test error")
        ):
            brain, adapter = enhance(return_adapter=True)
            assert isinstance(brain, LaapBrain)
            assert adapter is None

    def test_enhance_backward_compat_no_return_adapter_arg(self):
        """不传 return_adapter 参数时保持原行为"""
        # 旧代码调用方式
        result = enhance()
        assert isinstance(result, LaapBrain)
