"""Unit tests for laap launch subcommand."""

from __future__ import annotations

import argparse
import contextlib
import io

import pytest
from unittest.mock import patch

from laap.cli.subcommands import launch_cmd


class TestLaunchCmd:
    def test_add_parser_registers_subcommand(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        launch_cmd.add_parser(subparsers)

        args = parser.parse_args(["launch"])
        assert args.command == "launch"

    def test_add_parser_default_values(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        launch_cmd.add_parser(subparsers)

        args = parser.parse_args(["launch"])
        assert args.host == "0.0.0.0"
        assert args.http_port == 8000
        assert args.mcp_port == 8766
        assert args.bus_port == 11550
        assert args.no_bus is False
        assert args.no_mcp is False
        assert args.mcp_transport == "sse"

    def test_add_parser_custom_values(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        launch_cmd.add_parser(subparsers)

        args = parser.parse_args(
            [
                "launch",
                "--host",
                "127.0.0.1",
                "--http-port",
                "9000",
                "--mcp-port",
                "9001",
                "--bus-port",
                "9002",
                "--no-bus",
                "--no-mcp",
                "--mcp-transport",
                "stdio",
            ]
        )
        assert args.host == "127.0.0.1"
        assert args.http_port == 9000
        assert args.mcp_port == 9001
        assert args.bus_port == 9002
        assert args.no_bus is True
        assert args.no_mcp is True
        assert args.mcp_transport == "stdio"

    def test_add_parser_sets_func(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        launch_cmd.add_parser(subparsers)

        args = parser.parse_args(["launch"])
        assert hasattr(args, "func")
        assert args.func is launch_cmd.run

    def test_add_parser_mcp_transport_choices(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        launch_cmd.add_parser(subparsers)

        with pytest.raises(SystemExit):
            parser.parse_args(["launch", "--mcp-transport", "bogus"])

    @patch("laap.launcher.launch_full_entity")
    def test_run_calls_launch_full_entity(self, mock_launch):
        args = argparse.Namespace(
            host="0.0.0.0",
            http_port=8000,
            mcp_port=8766,
            bus_port=11550,
            no_bus=False,
            no_mcp=False,
            mcp_transport="sse",
        )
        launch_cmd.run(args)
        mock_launch.assert_called_once_with(
            host="0.0.0.0",
            http_port=8000,
            mcp_port=8766,
            bus_port=11550,
            no_bus=False,
            no_mcp=False,
            mcp_transport="sse",
        )

    @patch("laap.launcher.launch_full_entity")
    def test_run_passes_custom_values(self, mock_launch):
        args = argparse.Namespace(
            host="test",
            http_port=9999,
            mcp_port=8888,
            bus_port=7777,
            no_bus=True,
            no_mcp=True,
            mcp_transport="stdio",
        )
        launch_cmd.run(args)
        mock_launch.assert_called_once_with(
            host="test",
            http_port=9999,
            mcp_port=8888,
            bus_port=7777,
            no_bus=True,
            no_mcp=True,
            mcp_transport="stdio",
        )

    def test_main_commands_dict_includes_launch(self):
        """验证 main.py 的 COMMANDS 字典包含 launch。"""
        from laap.cli.main import COMMANDS

        assert "launch" in COMMANDS
        assert COMMANDS["launch"]["module"] == "launch_cmd"

    def test_main_build_parser_includes_launch(self):
        """验证 main.py build_parser() 注册了 launch 子命令及其参数。"""
        from laap.cli.main import build_parser

        parser = build_parser()
        args = parser.parse_args(["launch", "--host", "127.0.0.1", "--no-bus"])
        assert args.command == "launch"
        assert args.host == "127.0.0.1"
        assert args.no_bus is True

    @patch("laap.launcher.launch_full_entity")
    def test_main_dispatch_launch_invocation(self, mock_launch):
        """通过 main.py 主入口 dispatch 调用 laap launch（不真正启动 uvicorn）。"""
        from laap.cli.main import build_parser

        parser = build_parser()
        args = parser.parse_args(
            [
                "launch",
                "--host",
                "0.0.0.0",
                "--http-port",
                "8000",
                "--mcp-port",
                "8766",
                "--bus-port",
                "11550",
                "--no-bus",
                "--no-mcp",
                "--mcp-transport",
                "stdio",
            ]
        )
        # 模拟 main() 中的 dispatch 逻辑
        mod = __import__(
            "laap.cli.subcommands.launch_cmd",
            fromlist=["run"],
        )
        mod.run(args)
        mock_launch.assert_called_once_with(
            host="0.0.0.0",
            http_port=8000,
            mcp_port=8766,
            bus_port=11550,
            no_bus=True,
            no_mcp=True,
            mcp_transport="stdio",
        )


class TestLaunchCmdHelp:
    def test_launch_help_includes_all_args(self):
        """验证 --help 输出包含所有参数。"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        launch_cmd.add_parser(subparsers)

        help_out = io.StringIO()
        with contextlib.redirect_stdout(help_out):
            with pytest.raises(SystemExit):
                parser.parse_args(["launch", "--help"])
        help_text = help_out.getvalue()
        assert "--host" in help_text
        assert "--http-port" in help_text
        assert "--mcp-port" in help_text
        assert "--bus-port" in help_text
        assert "--no-bus" in help_text
        assert "--no-mcp" in help_text
        assert "--mcp-transport" in help_text
