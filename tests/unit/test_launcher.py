import pytest
from unittest.mock import patch, MagicMock, call
from laap.launcher import LAAPLauncher, launch_full_entity


class TestLAAPLauncher:
    def test_launcher_init_defaults(self):
        l = LAAPLauncher()
        assert l.host == "0.0.0.0"
        assert l.http_port == 8000
        assert l.mcp_port == 8766
        assert l.bus_port == 11550
        assert l.no_bus is False
        assert l.no_mcp is False
        assert l.mcp_transport == "sse"

    def test_launcher_init_custom(self):
        l = LAAPLauncher(
            host="127.0.0.1",
            http_port=9000,
            mcp_port=9001,
            bus_port=9002,
            no_bus=True,
            no_mcp=True,
            mcp_transport="stdio",
        )
        assert l.host == "127.0.0.1"
        assert l.http_port == 9000
        assert l.no_bus is True
        assert l.no_mcp is True
        assert l.mcp_transport == "stdio"

    def test_print_banner(self, capsys):
        l = LAAPLauncher()
        l._print_banner()
        out = capsys.readouterr().out
        assert "LAAP Living Agent" in out
        assert "http://0.0.0.0:8000" in out
        assert "ws://0.0.0.0:8000/ws" in out
        assert "/health" in out
        assert "/society/" in out

    def test_print_banner_no_bus_no_mcp(self, capsys):
        l = LAAPLauncher(no_bus=True, no_mcp=True)
        l._print_banner()
        out = capsys.readouterr().out
        # 验证不打印 bus / mcp 行
        assert "CognitiveBus" not in out
        assert "MCP Server" not in out

    @patch("laap.launcher.threading.Thread")
    def test_start_bus_success(self, mock_thread):
        l = LAAPLauncher()
        with patch("laap.agi.cognitive_bus_sync.CognitiveBusSyncNode") as mock_node_cls:
            mock_node = MagicMock()
            mock_node_cls.return_value = mock_node
            l._start_bus()
            mock_node_cls.assert_called_once()
            mock_node.start.assert_called_once()
            assert l._bus_node is mock_node

    def test_start_bus_failure_no_crash(self):
        l = LAAPLauncher()
        with patch(
            "laap.agi.cognitive_bus_sync.CognitiveBusSyncNode",
            side_effect=Exception("test"),
        ):
            l._start_bus()
            assert l._bus_node is None

    @patch("laap.launcher.threading.Thread")
    def test_start_mcp_sse_creates_thread(self, mock_thread):
        l = LAAPLauncher(mcp_transport="sse")
        with patch("laap.mcp.server.LAAPMCPServer") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server
            l._start_mcp()
            mock_server_cls.assert_called_once()
            mock_thread.assert_called_once()
            assert l._mcp_server is mock_server

    def test_start_mcp_no_mcp_skips(self):
        l = LAAPLauncher(no_mcp=True)
        l._start_mcp()
        assert l._mcp_server is None

    def test_start_mcp_stdio_only_creates_instance(self):
        l = LAAPLauncher(mcp_transport="stdio")
        with patch("laap.mcp.server.LAAPMCPServer") as mock_server_cls:
            mock_server = MagicMock()
            mock_server_cls.return_value = mock_server
            l._start_mcp()
            mock_server_cls.assert_called_once()
            # stdio 模式不创建线程

    @patch("laap.launcher.uvicorn")
    def test_start_api_calls_uvicorn_run(self, mock_uvicorn):
        l = LAAPLauncher()
        l._start_api()
        mock_uvicorn.run.assert_called_once()
        # 验证传入的参数
        call_args = mock_uvicorn.run.call_args
        assert call_args.kwargs["host"] == "0.0.0.0"
        assert call_args.kwargs["port"] == 8000

    def test_start_api_uvicorn_not_installed_exits(self):
        l = LAAPLauncher()
        # 模拟 uvicorn 不存在
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "uvicorn":
                raise ImportError("no uvicorn")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(SystemExit):
                l._start_api()

    @patch("laap.launcher.signal.signal")
    @patch("laap.launcher.LAAPLauncher._start_bus")
    @patch("laap.launcher.LAAPLauncher._start_mcp")
    @patch("laap.launcher.LAAPLauncher._start_api")
    def test_launch_full_flow(self, mock_api, mock_mcp, mock_bus, mock_signal):
        l = LAAPLauncher()
        l.launch()
        mock_signal.assert_called()  # SIGINT / SIGTERM 注册
        mock_bus.assert_called_once()
        mock_mcp.assert_called_once()
        mock_api.assert_called_once()

    @patch("laap.launcher.signal.signal")
    @patch("laap.launcher.LAAPLauncher._start_bus")
    @patch("laap.launcher.LAAPLauncher._start_mcp")
    @patch("laap.launcher.LAAPLauncher._start_api")
    def test_launch_no_bus_skips_bus(self, mock_api, mock_mcp, mock_bus, mock_signal):
        l = LAAPLauncher(no_bus=True)
        l.launch()
        mock_bus.assert_not_called()
        mock_mcp.assert_called_once()
        mock_api.assert_called_once()

    def test_shutdown_stops_bus(self):
        l = LAAPLauncher()
        l._bus_node = MagicMock()
        l._shutdown()
        l._bus_node.stop.assert_called_once()

    def test_shutdown_no_bus_no_error(self):
        l = LAAPLauncher()
        l._bus_node = None
        l._shutdown()  # 不应抛出

    def test_stats_returns_correct_dict(self):
        l = LAAPLauncher(host="h", http_port=1, mcp_port=2, bus_port=3)
        l._started_at = 100.0
        l._mcp_server = MagicMock()
        l._bus_node = MagicMock()
        with patch("laap.launcher.time.time", return_value=200.0):
            s = l.stats()
        assert s["host"] == "h"
        assert s["http_port"] == 1
        assert s["uptime"] == 100.0
        assert s["services"]["api"] == "up"
        assert s["services"]["mcp"] == "up"
        assert s["services"]["cognitive_bus"] == "up"

    @patch("laap.launcher.LAAPLauncher")
    def test_launch_full_entity_function(self, mock_launcher_cls):
        mock_inst = MagicMock()
        mock_launcher_cls.return_value = mock_inst
        launch_full_entity(host="test", http_port=9999)
        mock_launcher_cls.assert_called_once()
        mock_inst.launch.assert_called_once()


class TestLauncherNoOption:
    """测试 no_bus / no_mcp 选项组合"""

    @patch("laap.launcher.signal.signal")
    @patch("laap.launcher.LAAPLauncher._start_bus")
    @patch("laap.launcher.LAAPLauncher._start_mcp")
    @patch("laap.launcher.LAAPLauncher._start_api")
    def test_no_mcp_only(self, mock_api, mock_mcp, mock_bus, mock_signal):
        l = LAAPLauncher(no_mcp=True)
        l.launch()
        mock_bus.assert_called_once()
        mock_mcp.assert_not_called()

    @patch("laap.launcher.signal.signal")
    @patch("laap.launcher.LAAPLauncher._start_bus")
    @patch("laap.launcher.LAAPLauncher._start_mcp")
    @patch("laap.launcher.LAAPLauncher._start_api")
    def test_no_bus_no_mcp(self, mock_api, mock_mcp, mock_bus, mock_signal):
        l = LAAPLauncher(no_bus=True, no_mcp=True)
        l.launch()
        mock_bus.assert_not_called()
        mock_mcp.assert_not_called()
        mock_api.assert_called_once()
