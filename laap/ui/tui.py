"""LAAP - Golden Dragon TUI with Hermes-inspired design"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
import time
import threading
import re
import psutil
from datetime import datetime
from pathlib import Path
from rich.text import Text
from rich.style import Style
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Input, Button, Label
from textual.reactive import reactive
from textual.screen import Screen
from textual.binding import Binding
from textual.color import Color

# ============================================
# Color Scheme - Professional Dark Theme
# ============================================
class Colors:
    # Main colors
    GOLD = "#FFD700"
    GOLD_BRIGHT = "#FFE55C"
    GOLD_DARK = "#B8960C"
    GOLD_LIGHT = "#FFED80"
    
    # Status colors
    CRITICAL = "#DC143C"
    SUCCESS = "#00D68F"
    INFO = "#4FC1FF"
    WARNING = "#FFA500"
    
    # Backgrounds - Gradient palette
    BG_DARK = "#0D0D1A"
    BG_MEDIUM = "#1A1A2E"
    BG_LIGHT = "#252540"
    BG_HIGHLIGHT = "#2A2A4E"
    
    # Text
    TEXT = "#C8C8C8"
    TEXT_DIM = "#8888A0"
    TEXT_BRIGHT = "#FFFFFF"

# ============================================
# Windows Terminal Compatibility
# ============================================
import sys as _sys
if _sys.platform == "win32":
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        STD_OUTPUT_HANDLE = -11
        handle = k32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_uint32()
        k32.GetConsoleMode(handle, ctypes.byref(mode))
        k32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass

# ============================================
# Agent Singleton
# ============================================
_agent_instance = None
_avatar_bridge = None

def get_avatar_bridge():
    global _avatar_bridge
    if _avatar_bridge is None:
        from laap.ui.avatar_3d import AvatarBridge
        _avatar_bridge = AvatarBridge()
    return _avatar_bridge

def get_or_create_agent():
    global _agent_instance
    if _agent_instance is not None:
        return _agent_instance
    try:
        from laap.cli.config_manager import config_manager
        config_manager.apply_to_environment()
        provider = os.environ.get("LAAP_PROVIDER", "deepseek")
        model = os.environ.get("LAAP_MODEL", "deepseek-v4-flash")
        from laap.llm.factory import LLMFactory
        factory = LLMFactory(default_provider=provider, default_model=model or None)
        from laap.agent.lifelike import LifelikeAgent, LifelikeConfig
        config = LifelikeConfig(name="Ao", verbose=False)
        _agent_instance = LifelikeAgent(config=config, llm_factory=factory, show_banner=False)
        return _agent_instance
    except Exception as e:
        logging.getLogger("laap.tui").error(f"Agent init: {e}")
        return None

# ============================================
# Markdown Rendering Helpers
# ============================================
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_CODE = re.compile(r"`([^`]+)`")
_RE_ANSI = re.compile(r"\x1b\[.*?m")

def strip_ansi(text):
    """Remove ANSI escape sequences from text."""
    return _RE_ANSI.sub("", text)

def md_render(t):
    """Render markdown-like text with rich formatting."""
    t = strip_ansi(t)
    r = Text()
    i = 0
    while i < len(t):
        m = _RE_BOLD.search(t, i)
        n = _RE_CODE.search(t, i)
        next_match = None
        if m and n:
            next_match = m if m.start() < n.start() else n
        elif m:
            next_match = m
        elif n:
            next_match = n
        if not next_match:
            r.append(t[i:])
            break
        if next_match.start() > i:
            r.append(t[i:next_match.start()])
        g = next_match.group(1)
        if next_match.lastindex == 1:
            r.append(g, style=Style(bold=True, color=Colors.GOLD))
        else:
            r.append(g, style=Style(color=Colors.GOLD_LIGHT, bgcolor="#2A2A3E"))
        i = next_match.end()
    return r

def md_inline(t):
    return md_render(t)

# ============================================
# Logo Rendering
# ============================================
def render_logo():
    """Render the LAAP dragon logo with gradient effect."""
    logo = [
        f"  [{Colors.GOLD}]██╗      █████╗  █████╗ ██████╗   █████╗  ██████╗ ███████╗███╗   ██╗████████║[/]",
        f"  [{Colors.GOLD}]██║     ██╔══██╗██╔══██╗██╔══██╗  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝[/]",
        f"  [{Colors.GOLD_DARK}]██║     ███████║███████║██████╔╝ ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║[/]",
        f"  [{Colors.GOLD_DARK}]██║     ██╔══██║██╔══██║██╔═══╝  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║[/]",
        f"  [{Colors.GOLD_LIGHT}]███████╗██║  ██║██║  ██║██║      ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║[/]",
        f"  [{Colors.GOLD_LIGHT}]╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝[/]",
    ]
    return "\n".join(logo)

# ============================================
# Status Bar Component
# ============================================
class StatusBar(Static):
    """Enhanced status bar with system metrics."""
    model = reactive("")
    provider = reactive("")
    status = reactive("idle")
    tokens = reactive(0)
    elapsed = reactive(0.0)
    cpu_usage = reactive(0)
    memory_usage = reactive(0)
    
    def render(self):
        r = Text()
        # Model info
        r.append(f"  {self.model or '?'} ", style=Style(color=Colors.GOLD_DARK))
        r.append(f"| {self.provider or '?'} ", style=Style(color=Colors.INFO))
        
        # Status indicator
        st = {"idle": "Idle", "thinking": "Thinking...", "working": "Working..."}\
            .get(self.status, f"{self.status}")
        c = {"idle": Colors.SUCCESS, "thinking": Colors.GOLD, "working": Colors.GOLD_LIGHT}\
            .get(self.status, Colors.TEXT)
        r.append(st, style=Style(color=c, bold=True))
        
        # System metrics
        r.append(f" | CPU: {self.cpu_usage}%", style=Style(color=Colors.TEXT_DIM))
        r.append(f" | MEM: {self.memory_usage}%", style=Style(color=Colors.TEXT_DIM))
        
        # Token count
        r.append(f" | Tokens: {self.tokens}", style=Style(color=Colors.GOLD_DARK))
        if self.elapsed:
            r.append(f" | {self.elapsed:.1f}s", style=Style(color=Colors.GOLD_DARK))
        
        return r

# ============================================
# Tool Status Panel
# ============================================
class ToolStatusPanel(ScrollableContainer):
    """Panel showing status of available tools."""
    
    def __init__(self, id=None):
        super().__init__(id=id)
        self.tools = [
            {"name": "Code", "status": "active", "count": 6},
            {"name": "Git", "status": "active", "count": 5},
            {"name": "Shell", "status": "active", "count": 3},
            {"name": "Web", "status": "active", "count": 2},
            {"name": "Memory", "status": "active", "count": 3},
        ]
    
    def compose(self):
        yield Static("Tools", id="panel_title")
        for tool in self.tools:
            status_color = Colors.SUCCESS if tool["status"] == "active" else Colors.CRITICAL
            line = Text(f"  [{tool['name']}] ")
            line.append(f"{tool['count']} tools", style=Style(color=Colors.TEXT_DIM))
            line.append(" ●", style=Style(color=status_color))
            m = Static(line)
            m.styles.color = Colors.TEXT
            yield m

# ============================================
# System Metrics Panel
# ============================================
class SystemMetricsPanel(ScrollableContainer):
    """Real-time system metrics monitoring panel."""
    
    def __init__(self, id=None):
        super().__init__(id=id)
        self._update_interval = 2  # Update every 2 seconds
        self._running = True
    
    def on_mount(self):
        """Start the metrics update loop."""
        asyncio.create_task(self._update_loop())
    
    async def _update_loop(self):
        """Update system metrics periodically."""
        while self._running:
            try:
                # CPU usage
                cpu = psutil.cpu_percent(interval=0.1)
                # Memory usage
                mem = psutil.virtual_memory().percent
                # Update the panel
                self.update_metrics(cpu, mem)
            except Exception:
                pass
            await asyncio.sleep(self._update_interval)
    
    def update_metrics(self, cpu, mem):
        """Update displayed metrics."""
        self.query_one("#cpu_val", Static).update(f"{cpu}%")
        self.query_one("#mem_val", Static).update(f"{mem}%")
        self.query_one("#cpu_bar", Static).update(self._make_bar(cpu))
        self.query_one("#mem_bar", Static).update(self._make_bar(mem))
    
    def _make_bar(self, percent):
        """Create a progress bar string."""
        filled = int(percent / 5)
        empty = 20 - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def compose(self):
        yield Static("System", id="panel_title")
        
        cpu_label = Static("CPU:")
        cpu_label.styles.color = Colors.TEXT_DIM
        yield cpu_label
        
        cpu_val = Static("0%", id="cpu_val")
        cpu_val.styles.color = Colors.INFO
        yield cpu_val
        
        cpu_bar = Static("[░░░░░░░░░░░░░░░░░░░░]", id="cpu_bar")
        cpu_bar.styles.color = Colors.INFO
        yield cpu_bar
        
        mem_label = Static("Memory:")
        mem_label.styles.color = Colors.TEXT_DIM
        yield mem_label
        
        mem_val = Static("0%", id="mem_val")
        mem_val.styles.color = Colors.WARNING
        yield mem_val
        
        mem_bar = Static("[░░░░░░░░░░░░░░░░░░░░]", id="mem_bar")
        mem_bar.styles.color = Colors.WARNING
        yield mem_bar

# ============================================
# Chat Log Component
# ============================================
class ChatLog(ScrollableContainer):
    """Enhanced chat log with improved formatting."""
    
    def compose(self):
        yield Static("", id="msgs")
    
    def add_logo(self):
        """Add the LAAP logo to the chat log."""
        r = render_logo()
        m = Static(r)
        m.styles.margin = (0, 2, 1, 2)
        self.mount(m)
        self.scroll_end()
    
    def clear_all(self):
        """Clear all messages."""
        try:
            for w in list(self.query("Static")):
                if w.id != "msgs":
                    w.remove()
            self.add_logo()
        except Exception:
            pass
    
    def add_user(self, text):
        """Add a user message."""
        r = Text(f"  > {text}", style=Style(color=Colors.GOLD, bold=True))
        m = Static(r)
        m.styles.margin = (1, 2, 0, 2)
        m.styles.padding = (0, 0, 0, 2)
        m.styles.bgcolor = Colors.BG_LIGHT
        self.mount(m)
        self.scroll_end()
    
    def stream_assistant(self, text, append=False):
        """Stream assistant response. Updates the #response widget if it exists."""
        try:
            resp = self.query_one("#response", Static)
            resp.update(md_inline(f"  {text}"))
            self.scroll_end()
            return
        except Exception:
            pass
        # Fallback: create new response widget
        try:
            m = Static(md_inline(f"  {text}"), id="response")
            m.styles.margin = (1, 2, 0, 2)
            m.styles.padding = (0, 2, 0, 2)
            m.styles.bgcolor = Colors.BG_MEDIUM
            self.mount(m)
            self.scroll_end()
        except Exception:
            pass
    
    def add_assistant(self, text):
        """Add a complete assistant message."""
        r = md_inline(f"  {text}")
        m = Static(r)
        m.styles.margin = (1, 2, 0, 2)
        m.styles.padding = (0, 2, 0, 2)
        m.styles.bgcolor = Colors.BG_MEDIUM
        self.mount(m)
        self.scroll_end()
    
    def add_tool(self, name, ok=True):
        """Add a tool usage message."""
        marker = chr(0x25CF) if ok else chr(0x2717)
        color = Colors.SUCCESS if ok else Colors.CRITICAL
        r = Text(f"  {marker} {name}", style=Style(color=color))
        m = Static(r)
        m.styles.margin = (0, 2, 0, 4)
        self.mount(m)
        self.scroll_end()
    
    def add_sys(self, text):
        """Add a system message."""
        r = Text(f"  {text}", style=Style(color=Colors.GOLD_DARK))
        m = Static(r)
        m.styles.margin = (0, 2, 0, 2)
        m.styles.italic = True
        self.mount(m)
        self.scroll_end()
    
    def add_thinking(self):
        """Add thinking indicator."""
        r = Text("  Ao is thinking...", style=Style(color=Colors.GOLD_DARK, italic=True))
        m = Static(r, id="thinking")
        m.styles.margin = (0, 2, 0, 2)
        self.mount(m)
        self.scroll_end()

    def start_response(self):
        """Create response container widget that streaming tokens update."""
        try:
            # Remove old response if any
            try:
                old = self.query_one("#response")
                old.remove()
            except Exception:
                pass
            m = Static("", id="response")
            m.styles.margin = (1, 2, 0, 2)
            m.styles.padding = (0, 2, 0, 2)
            m.styles.bgcolor = Colors.BG_MEDIUM
            self.mount(m)
            self.scroll_end()
            return True
        except Exception:
            return False
    
    def remove_thinking(self):
        """Remove thinking indicator."""
        try:
            w = self.query_one("#thinking")
            w.remove()
        except Exception:
            pass

# ============================================
# Main Screen with Sidebar Layout
# ============================================
class MainScreen(Screen):
    """Main application screen with Hermes-inspired layout."""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("ctrl+w", "toggle_sidebar", "Toggle Sidebar"),
    ]
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self._buf = ""
        self._buf_lock = threading.Lock()
        self._history = []
        self._sidebar_visible = True
    
    def compose(self):
        with Horizontal():
            # Sidebar - collapsed by default on small screens
            with Vertical(id="sidebar", classes="sidebar"):
                yield ToolStatusPanel(id="tool_panel")
                yield SystemMetricsPanel(id="metrics_panel")
            
            # Main content area
            with Vertical(id="main_content"):
                yield ChatLog(id="chat_log")
                yield Input(
                    placeholder="  Message Ao (or /help)...",
                    id="input_box"
                )
                yield StatusBar(id="status_bar")
    
    def on_mount(self):
        """Initialize the screen."""
        # Initialize chat log
        self.query_one("#chat_log", ChatLog).add_logo()
        
        # Initialize agent info
        sb = self.query_one("#status_bar", StatusBar)
        agent = get_or_create_agent()
        if agent and agent.llm:
            sb.model = agent.llm.model
            sb.provider = type(agent.llm).__name__.replace("Provider", "")
        
        # Focus input
        self.query_one("#input_box", Input).focus()
    
    def on_input_submitted(self, ev):
        """Handle input submission."""
        text = ev.value.strip()
        ev.input.value = ""
        if not text:
            return
        
        chat_log = self.query_one("#chat_log", ChatLog)
        status_bar = self.query_one("#status_bar", StatusBar)
        
        if text.startswith("/"):
            self._handle_command(text, chat_log, status_bar)
            return
        
        chat_log.add_user(text)
        status_bar.status = "thinking"
        self._buf = ""
        chat_log.add_thinking()
        asyncio.create_task(self._chat(text, chat_log, status_bar))
    
    def _handle_command(self, cmd, chat_log, status_bar):
        """Handle slash commands."""
        c = cmd.lower().split()[0]
        
        if c in ("/exit", "/quit"):
            self.app.exit()
        elif c == "/help":
            help_text = """**LAAP Commands**

`/new` or `/clear` - New session
`/config` - Show configuration
`/cost` - Usage statistics
`/model` - Current model info
`/avatar` - Load 3D avatar model
`/sidebar` - Toggle sidebar
`/exit` - Quit

**Keyboard Shortcuts**
Ctrl+L - Clear screen
Ctrl+C - Quit
Ctrl+W - Toggle sidebar"""
            chat_log.add_assistant(help_text)
        elif c in ("/new", "/clear"):
            chat_log.clear_all()
            agent = get_or_create_agent()
            if agent:
                agent._conversation = []
            chat_log.add_sys("Session cleared. Started new conversation.")
            self._buf = ""
            # Reset response widget
            try:
                old = chat_log.query_one("#response")
                old.remove()
            except Exception:
                pass
        elif c == "/config":
            agent = get_or_create_agent()
            m = agent.llm.model if agent and agent.llm else "?"
            p = type(agent.llm).__name__ if agent and agent.llm else "?"
            k = "OK" if agent and agent.llm and agent.llm.api_key else "NONE"
            chat_log.add_sys(f"Model: {m} | Provider: {p} | Key: {k}")
        elif c == "/cost":
            chat_log.add_assistant(f"**Usage**\nTokens: {status_bar.tokens} | Time: {status_bar.elapsed:.0f}s")
        elif c == "/model":
            agent = get_or_create_agent()
            m = agent.llm.model if agent and agent.llm else "N/A"
            chat_log.add_sys(f"Model: {m}")
        elif c == "/sidebar":
            self._toggle_sidebar()
        elif c == "/avatar":
            path = cmd[7:].strip() if len(cmd) > 7 else ""
            if not path:
                chat_log.add_sys("Usage: /avatar <path_to_pmx_file>")
                return
            bridge = get_avatar_bridge()
            if not bridge.is_running:
                bridge.start(path)
                chat_log.add_sys(f"Avatar started with: {os.path.basename(path)}")
            else:
                bridge.load_model(path)
                chat_log.add_sys(f"Avatar loaded: {os.path.basename(path)}")
        elif c == "/avatar_stop":
            bridge = get_avatar_bridge()
            bridge.stop()
            chat_log.add_sys("Avatar stopped")
        else:
            chat_log.add_sys(f"Unknown command: {c}")
    
    def _toggle_sidebar(self):
        """Toggle sidebar visibility."""
        sidebar = self.query_one("#sidebar")
        if self._sidebar_visible:
            sidebar.styles.display = "none"
        else:
            sidebar.styles.display = "block"
        self._sidebar_visible = not self._sidebar_visible
    
    def action_clear(self):
        """Clear the chat log."""
        self.query_one("#chat_log", ChatLog).clear_all()
    
    def action_toggle_sidebar(self):
        """Toggle sidebar visibility via keyboard shortcut."""
        self._toggle_sidebar()
    
    async def _chat(self, text, chat_log, status_bar):
        """Process chat message with the agent."""
        agent = get_or_create_agent()
        if not agent or not agent.llm:
            chat_log.remove_thinking()
            chat_log.add_sys("No LLM configured. Run: laap --config")
            status_bar.status = "idle"
            return
        
        start = time.time()
        loop = asyncio.get_running_loop()
        
        # Create a dedicated response widget (not tied to thinking indicator)
        loop.call_soon_threadsafe(chat_log.start_response)
        self._buf = ""
        
        try:
            from laap.ui.stream_handler import StreamHandler
            
            sh = StreamHandler(verbose=False, use_spinner=False)
            
            def on_tok(tok):
                self._buf += tok
                loop.call_soon_threadsafe(chat_log.stream_assistant, self._buf)
            
            def on_tool_start(name, args):
                loop.call_soon_threadsafe(chat_log.add_tool, name, True)
            
            sh.on_token = on_tok
            sh.on_tool_call = on_tool_start
            
            # Execute chat in thread pool
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                full_response = await loop.run_in_executor(pool, agent.chat, text, "", None, None, sh)
        
        except Exception as e:
            loop.call_soon_threadsafe(chat_log.remove_thinking)
            loop.call_soon_threadsafe(chat_log.add_sys, "Error: " + str(e))
            status_bar.status = "idle"
            return
        
        # Remove thinking indicator, keep response widget intact
        loop.call_soon_threadsafe(chat_log.remove_thinking)
        # Final update with full response
        if full_response:
            self._buf = full_response
            loop.call_soon_threadsafe(chat_log.stream_assistant, full_response)
        status_bar.status = "idle"
        status_bar.tokens += max(1, len(full_response or "") // 4)
        status_bar.elapsed = time.time() - start
    
    def q(self, widget):
        """Quick query helper."""
        if isinstance(widget, str):
            return self.query_one("#" + widget)
        return self.query_one(widget)

# ============================================
# Main Application with Enhanced CSS
# ============================================
class LAAPApp(App):
    """LAAP Application with Hermes-inspired design."""
    
    TITLE = "LAAP - Golden Dragon Agent"
    
    # Enhanced CSS with Textual-compatible styling
    CSS = """
    /* Base screen styling */
    Screen {
        background: #0D0D1A;
        color: #C8C8C8;
    }

    /* Main layout containers */
    #main_content {
        width: 1fr;
        height: 100%;
        layout: vertical;
    }

    /* Sidebar styling */
    #sidebar {
        width: 24;
        height: 100%;
        background: #1A1A2E;
        border-right: solid #333;
        padding: 1;
    }

    /* Sidebar panels */
    ToolStatusPanel, SystemMetricsPanel {
        height: auto;
        background: #252540;
        padding: 1;
    }

    /* Panel titles */
    #panel_title {
        color: #FFD700;
        margin-bottom: 1;
        padding-bottom: 1;
        border-bottom: solid #333;
    }

    /* Chat log styling */
    #chat_log {
        height: 1fr;
        background: transparent;
        padding: 0;
    }

    /* Input box styling */
    #input_box {
        height: 3;
        background: #1A1A2E;
        color: #FFD700;
        border: solid #333;
        padding: 0 2;
        margin: 1;
    }

    #input_box:focus {
        border: solid #FFD700;
    }

    /* Status bar styling */
    #status_bar {
        height: 1;
        background: #1A1A2E;
        border-top: solid #333;
        padding: 0 2;
    }

    /* Static widget styling */
    Static {
        color: #C8C8C8;
    }

    /* Scrollbar styling */
    ScrollableContainer {
        scrollbar-color: #FFD700;
        scrollbar-size: 1 1;
    }

    /* Button styling */
    Button {
        background: #252540;
        border: solid #333;
        color: #C8C8C8;
    }

    Button:hover {
        background: #2A2A4E;
        border: solid #FFD700;
    }
    """
    
    def get_default_screen(self):
        return MainScreen()

# ============================================
# TUI Runner Class
# ============================================
class LAAP_TUI:
    """LAAP TUI runner class."""
    
    def __init__(self, agent=None, config_manager=None):
        self.agent = agent
        self.config_manager = config_manager
    
    def run(self):
        """Run the TUI application."""
        LAAPApp().run()

# ============================================
# Module Entry Point
# ============================================
def run_tui():
    """Run the LAAP TUI."""
    LAAPApp().run()

if __name__ == "__main__":
    run_tui()
