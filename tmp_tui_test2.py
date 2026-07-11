import asyncio
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Input
from textual.reactive import reactive
from textual.screen import Screen
from rich.text import Text
from rich.style import Style

class Colors:
    GOLD = '#FFD700'
    TEXT_DIM = '#8888A0'
    SUCCESS = '#00D68F'
    BG_LIGHT = '#252540'
    BG_MEDIUM = '#1A1A2E'

class ToolStatusPanel(Vertical):
    def __init__(self, id=None):
        super().__init__(id=id)
    def compose(self):
        yield Static('Tools', id='panel_title')
        yield Static('  [general] 1 ●')

class SystemMetricsPanel(Vertical):
    def compose(self):
        yield Static('System', id='panel_title')
        yield Static('CPU:')

class CognitiveStatePanel(Vertical):
    dominant_feeling = reactive('neutral')
    def compose(self):
        yield Static('Cognitive State', id='panel_title')
        yield Static('Feeling:')

class GatewayStatusPanel(Vertical):
    telegram_status = reactive('disabled')
    feishu_status = reactive('disabled')
    def compose(self):
        yield Static('Gateways', id='panel_title')
        yield Static('Telegram:')
        yield Static('disabled', id='gw_telegram')
        yield Static('Feishu:')
        yield Static('disabled', id='gw_feishu')

class ChatLog(ScrollableContainer):
    def compose(self):
        yield Static('', id='msgs')

class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id='sidebar', classes='sidebar'):
                yield ToolStatusPanel(id='tool_panel')
                yield SystemMetricsPanel(id='metrics_panel')
                yield CognitiveStatePanel(id='cognitive_panel')
                yield GatewayStatusPanel(id='gateway_panel')
            with Vertical(id='main_content'):
                yield ChatLog(id='chat_log')
                yield Input(placeholder='msg', id='input_box')
                yield Static('status', id='status_bar')

class T(App):
    CSS = """
    Screen { background: #0D0D1A; color: #C8C8C8; }
    #main_content { width: 1fr; height: 100%; layout: vertical; }
    #sidebar { width: 26; height: 100%; background: #1A1A2E; border-right: solid #333; padding: 1; }
    ToolStatusPanel, SystemMetricsPanel, CognitiveStatePanel, GatewayStatusPanel { height: auto; background: #252540; padding: 1; margin-bottom: 1; }
    #panel_title { color: #FFD700; margin-bottom: 1; padding-bottom: 1; border-bottom: solid #333; }
    #chat_log { height: 1fr; background: transparent; padding: 0; }
    #input_box { height: 3; background: #1A1A2E; color: #FFD700; border: solid #333; }
    Static { color: #C8C8C8; }
    """
    def get_default_screen(self):
        return MainScreen()

async def main():
    async with T().run_test() as pilot:
        await pilot.pause()
        print('OK')
asyncio.run(main())
