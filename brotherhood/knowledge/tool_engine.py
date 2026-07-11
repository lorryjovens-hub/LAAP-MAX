"""
Aris V10 Tool-route 引擎
直接通过 subprocess/pathlib/urllib 执行工具 — 零 Hermes 依赖
"""
import os
import re
import sys
import json
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Optional, Callable


# ── 工具定义 ──────────────────────────────

class Tool:
    """工具：语义触发器 + 执行函数"""

    def __init__(self, name: str, triggers: list, handler: Callable,
                 description: str = ""):
        self.name = name
        self.triggers = [re.compile(t, re.IGNORECASE) for t in triggers]
        self.handler = handler
        self.description = description

    def match(self, text: str) -> Optional[dict]:
        for trig in self.triggers:
            m = trig.search(text)
            if m:
                d = m.groupdict() or {}
                for i, g in enumerate(m.groups(), 1):
                    d[str(i)] = g
                return d
        return None


class ToolEngine:
    """
    工具执行引擎
    - 直接运行 shell 命令 (subprocess)
    - 直接读写文件 (pathlib)
    - 直接 HTTP 请求 (urllib)
    - 枚举目录
    """

    def __init__(self):
        self.tools: list[Tool] = []
        self._init_tools()

    def add_tool(self, tool: Tool):
        self.tools.append(tool)

    # ── 处理 ──────────────────────────────

    def process(self, text: str, context: dict = None) -> Optional[str]:
        """检测并执行匹配的工具"""
        if context is None:
            context = {}

        for tool in self.tools:
            match_result = tool.match(text)
            if match_result is not None:
                try:
                    result = tool.handler(text, match_result, context)
                    if result is not None:
                        return result
                except Exception as e:
                    return f"[Tool {tool.name} 错误] {e}"
        return None

    # ── 内置工具 ──────────────────────────────

    def _init_tools(self):
        """注册所有内置工具"""

        # ── 运行命令 ─────────────────
        self.add_tool(Tool(
            name="run_command",
            triggers=[
                r"运行\s+(.+?)(?:$|看看|试试|一下)",
                r"执行\s+(.+?)(?:$|看看)",
                r"^(?:在终端)?运行\s+(.+?)$",
                r"^(?:跑|执行)\s+(.+?)$",
                r"打[开启]\s+(.+?)(?:程序|软件|应用)$",
                r"^打开\s+https?://",
            ],
            handler=self._run_command,
            description="运行 shell 命令",
        ))

        # ── 列表目录 ─────────────────
        self.add_tool(Tool(
            name="list_dir",
            triggers=[
                r"(?:列出|查看|显示|ls)\s*(?:目录|文件夹|路径|位置)?\s*(.+?)?$",
                r"什么文件(?:夹|夹)?(?:在|在)?(.+?)?(?:里|中|下)?$",
                r"^ls\b\s*(.*)$",
                r"^ls\s+-la\s*(.+)$",
            ],
            handler=self._list_dir,
            description="列出目录内容",
        ))

        # ── 读文件 ─────────────────
        self.add_tool(Tool(
            name="read_file",
            triggers=[
                r"(?:读|查看|打开|cat)\s+(?:文件|内容)?\s*(.+?)(?:\.py|\.txt|\.md|\.json|\.yaml|\.toml|\.js|\.ts|\.css|\.html)\s*$",
                r"^(?:读|查看|打开|cat)\s+(.+?)(?:看看|内容)?\s*$",
                r"cat\s+(.+)$",
            ],
            handler=self._read_file,
            description="读取文件内容",
        ))

        # ── 写文件 ─────────────────
        self.add_tool(Tool(
            name="write_file",
            triggers=[
                r"(?:创建|写入|写)\s+(?:到)?\s*(.+?)(?:\.\w+)\s*(?:作为|内容为|：|:)?\s*(.+?)$",
            ],
            handler=self._write_file,
            description="写入文件",
        ))

        # ── 搜索文件 ─────────────────
        self.add_tool(Tool(
            name="search_file",
            triggers=[
                r"(?:搜索|查找|找|whereis)\s+(?:文件)?\s*(.+?)(?:在\s+(.+?))?(?:里|中)?\s*",
                r"find\s+(?:.*-name\s+)?[\"']?(.+?)[\"']?\s*(?:-path\s+(.+?))?\s*$",
            ],
            handler=self._search_file,
            description="搜索文件",
        ))

        # ── 网页搜索 ─────────────────
        self.add_tool(Tool(
            name="web_search",
            triggers=[
                r"搜索\s+(.+?)(?:看看|下|一下)?$",
                r"查找\s+(.+?)(?:信息|资料|内容)?$",
                r"查询\s+(.+?)$",
                r"在网上搜\s+(.+?)$",
            ],
            handler=self._web_search,
            description="网页搜索 (模拟，需 URL 模板)",
        ))

        # ── HTTP GET ─────────────────
        self.add_tool(Tool(
            name="http_get",
            triggers=[
                r"(?:GET|get|请求|获取)\s+(?:URL|地址|链接|网址)?\s*(https?://\S+)",
                r"访问\s+(https?://\S+)",
                r"打[开启]\s+(https?://\S+)",
            ],
            handler=self._http_get,
            description="HTTP GET 请求",
        ))

    # ── 执行器 ──────────────────────────────

    def _run_command(self, text: str, match: dict, ctx: dict) -> str:
        cmd = match.get("1", "")
        if not cmd:
            return "请指定要运行的命令"

        try:
            # 安全过滤
            blacklist = ["rm -rf", "format", "dd if=", "mkfs", "> /dev/sd"]
            for bad in blacklist:
                if bad in cmd.lower():
                    return f"命令 '{cmd}' 包含危险操作，已阻止"

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or ""
            error = result.stderr or ""

            if result.returncode != 0:
                return f"[命令错误 {result.returncode}]\n{error[:2000]}"

            return output[:3000] if output else "(无输出)"

        except subprocess.TimeoutExpired:
            return "命令执行超时 (30s)"
        except FileNotFoundError:
            return f"命令 '{cmd.split()[0]}' 未找到"
        except Exception as e:
            return f"执行错误: {e}"

    def _list_dir(self, text: str, match: dict, ctx: dict) -> str:
        path_str = match.get("1", "").strip() or "."
        if path_str in ("当前目录", "当前路径", "此目录", "这个目录"):
            path_str = "."
        path = Path(path_str)

        if not path.exists():
            return f"路径 '{path_str}' 不存在"

        try:
            items = list(path.iterdir())
            if not items:
                return f"目录 '{path_str}' 为空"

            # 分目录和文件
            dirs = []
            files = []
            for item in items:
                if item.is_dir():
                    dirs.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    files.append(f"📄 {item.name} ({size} bytes)")

            result = f"📂 {path.absolute()}\n"
            result += f"总计 {len(dirs)} 目录, {len(files)} 文件\n\n"
            result += "\n".join(dirs + files)
            return result[:3000]

        except PermissionError:
            return f"无权限访问 '{path_str}'"
        except Exception as e:
            return f"列出目录错误: {e}"

    def _read_file(self, text: str, match: dict, ctx: dict) -> str:
        file_path = match.get("1", "").strip()
        if not file_path:
            return "请指定文件路径"

        path = Path(file_path)
        if not path.exists():
            # 尝试在上下文工作目录查找
            wd = ctx.get("workdir", ".")
            alt_path = Path(wd) / file_path
            if alt_path.exists():
                path = alt_path

        if not path.exists():
            return f"文件 '{file_path}' 不存在"

        if path.stat().st_size > 100 * 1024:
            return f"文件太大 ({path.stat().st_size / 1024:.0f}KB)，只读前 100KB"

        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()
            result = f"📄 {path.absolute()} ({len(lines)} 行)\n"
            result += "─" * 40 + "\n"
            result += content[:3000]
            if len(content) > 3000:
                result += f"\n... (截断，共 {len(lines)} 行)"
            return result
        except UnicodeDecodeError:
            return f"'{file_path}' 是二进制文件，无法文本读取"
        except Exception as e:
            return f"读文件错误: {e}"

    def _write_file(self, text: str, match: dict, ctx: dict) -> str:
        # 解析复杂的写入指令
        # 触发格式: "创建 xxx.py 内容为 yyy"
        path_str = match.get("1", "").strip()
        content = match.get("2", "").strip()

        if not path_str:
            return "请指定文件路径和内容"

        try:
            path = Path(path_str)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"✅ 已写入 {path.absolute()} ({len(content)} 字符)"
        except Exception as e:
            return f"写文件错误: {e}"

    def _search_file(self, text: str, match: dict, ctx: dict) -> str:
        pattern = match.get("1", "").strip()
        search_path = match.get("2", "").strip() or "."

        if not pattern:
            return "请指定搜索模式"

        try:
            path = Path(search_path)
            if not path.exists():
                return f"搜索路径 '{search_path}' 不存在"

            results = []
            for f in path.rglob(pattern):
                if f.is_file():
                    results.append(str(f.relative_to(path)))
                    if len(results) >= 50:
                        break

            if not results:
                return f"在 '{search_path}' 未找到匹配 '{pattern}' 的文件"

            return f"🔍 在 '{search_path}' 中找到 {len(results)} 个匹配:\n" + \
                   "\n".join(results)
        except PermissionError:
            return f"无权限搜索 '{search_path}'"
        except Exception as e:
            return f"搜索错误: {e}"

    def _web_search(self, text: str, match: dict, ctx: dict) -> str:
        """网页搜索 — 使用外部搜索 API 或直接搜索引擎"""
        query = match.get("1", "").strip()
        if not query:
            return "请指定搜索关键词"

        # 尝试使用 DuckDuckGo (不需要 API key)
        import urllib.parse
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # 简单解析搜索结果
            import re
            results = []
            for m in re.finditer(
                r'<a[^>]+class="result__a"[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>',
                html
            ):
                url = m.group(1)
                title = re.sub(r'<[^>]+>', '', m.group(2))
                results.append(f"{title}\n  {url}")
                if len(results) >= 5:
                    break

            if not results:
                # fallback: 给一个简单结果
                return (
                    f"未从 DuckDuckGo 获取到结构化的结果。\n"
                    f"你可以直接访问: https://duckduckgo.com/?q={encoded}\n"
                    f"或者尝试精确搜索。"
                )

            return f"🔍 搜索结果:\n\n" + "\n\n".join(results)

        except Exception as e:
            return f"搜索错误: {e}"

    def _http_get(self, text: str, match: dict, ctx: dict) -> str:
        url = match.get("1", "").strip()
        if not url:
            return "请提供 URL"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Aris-V10/1.0 (cognitive engine)"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                content_type = resp.headers.get("Content-Type", "")
                data = resp.read()

            if "text" in content_type or "json" in content_type:
                text = data.decode("utf-8", errors="replace")
                return f"[HTTP {resp.status}] ({len(data)} bytes)\n{text[:2000]}"
            else:
                return f"[HTTP {resp.status}] 二进制内容，{len(data)} bytes, type: {content_type}"

        except urllib.error.HTTPError as e:
            return f"HTTP 错误 {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return f"URL 错误: {e.reason}"
        except Exception as e:
            return f"HTTP 请求错误: {e}"


# ── 直接创建引擎 ──────────────────────────

_engine = None


def get_engine() -> ToolEngine:
    global _engine
    if _engine is None:
        _engine = ToolEngine()
    return _engine
