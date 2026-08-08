# -*- coding: utf-8 -*-
"""LAAP-TOOL 协议接口契约测试"""
import pytest
from laap.protocol.laap_tool import (
    ToolProtocol, LaapTool, ToolPermissions, PermissionLevel,
    ToolCategory, ToolInvocationResult,
)


class DummyToolProtocol(ToolProtocol):
    def __init__(self):
        self.tools = {}

    def register_tool(self, tool, handler=None):
        self.tools[tool.name] = (tool, handler)

    def unregister_tool(self, name):
        if name in self.tools:
            del self.tools[name]
            return True
        return False

    def invoke_tool(self, name, args, invocation_context=None):
        if name not in self.tools:
            return ToolInvocationResult(
                tool_name=name, success=False, output=None, error="未找到工具"
            )
        tool, handler = self.tools[name]
        if handler is None:
            return ToolInvocationResult(
                tool_name=name, success=False, output=None, error="无处理器"
            )
        try:
            output = handler(**args)
            return ToolInvocationResult(tool_name=name, success=True, output=output)
        except Exception as e:
            return ToolInvocationResult(
                tool_name=name, success=False, output=None, error=str(e)
            )

    def list_tools(self, category=None, permissions_required=None):
        result = []
        for tool, _ in self.tools.values():
            if category and tool.category != category:
                continue
            if permissions_required and tool.permissions.level != permissions_required:
                continue
            result.append(tool)
        return result

    def adapt_mcp_tool(self, mcp_tool):
        perms = ToolPermissions(level=PermissionLevel.READ_ONLY)
        return LaapTool(
            name=getattr(mcp_tool, "name", "unknown"),
            description=getattr(mcp_tool, "description", ""),
            category=ToolCategory.EXTERNAL_API,
            input_schema=getattr(mcp_tool, "inputSchema", {}),
            output_schema={},
            permissions=perms,
            mcp_compatible=True,
        )


def test_laap_tool_dataclass():
    perms = ToolPermissions(level=PermissionLevel.EXECUTE, requires_approval=True)
    t = LaapTool(
        name="calc",
        description="计算器",
        category=ToolCategory.CODE_EXECUTION,
        input_schema={},
        output_schema={},
        permissions=perms,
    )
    assert t.permissions.requires_approval is True
    assert t.mcp_compatible is False


def test_tool_protocol_subclassed():
    tp = DummyToolProtocol()
    perms = ToolPermissions(level=PermissionLevel.READ_ONLY)
    tool = LaapTool(
        name="echo",
        description="回显",
        category=ToolCategory.FILESYSTEM,
        input_schema={},
        output_schema={},
        permissions=perms,
    )
    tp.register_tool(tool, handler=lambda **kwargs: "ok")
    result = tp.invoke_tool("echo", {"msg": "hi"})
    assert result.success is True
    assert result.output == "ok"
    assert tp.list_tools() == [tool]
    assert tp.unregister_tool("echo") is True


def test_adapt_mcp_tool():
    class FakeMcpTool:
        name = "mcp_tool"
        description = "测试 MCP 工具"
        inputSchema = {"type": "object"}
    tp = DummyToolProtocol()
    laap_tool = tp.adapt_mcp_tool(FakeMcpTool())
    assert laap_tool.name == "mcp_tool"
    assert laap_tool.mcp_compatible is True
