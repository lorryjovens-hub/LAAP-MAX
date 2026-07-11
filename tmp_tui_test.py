import asyncio
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual.reactive import reactive

class P(Vertical):
    telegram_status = reactive('disabled')
    feishu_status = reactive('disabled')

    def compose(self):
        yield Static('Gateways')
        yield Static('Telegram:')
        yield Static('disabled')
        yield Static('Feishu:')
        yield Static('disabled')

class T(App):
    CSS = """
    Screen { background: #0D0D1A; }
    #sidebar { width: 26; height: 100%; background: #1A1A2E; border-right: solid #333; padding: 1; }
    P { height: auto; background: #252540; padding: 1; margin-bottom: 1; }
    """
    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id='sidebar'):
                yield P(id='gateway_panel')
            yield Static('main', id='main')

async def main():
    async with T().run_test() as pilot:
        await pilot.pause()
        print('OK')

asyncio.run(main())
