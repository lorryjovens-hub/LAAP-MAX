import asyncio
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

class P(Vertical):
    def compose(self):
        yield Static('A')
        yield Static('B')

class T(App):
    CSS = """
    Screen { background: #000; }
    P { height: auto; background: #111; padding: 1; }
    """
    def compose(self) -> ComposeResult:
        yield Horizontal(Vertical(Static('x')), P(id='p'))

def test_textual_vertical():
    async def main():
        async with T().run_test() as pilot:
            await pilot.pause()
            assert True
    asyncio.run(main())
