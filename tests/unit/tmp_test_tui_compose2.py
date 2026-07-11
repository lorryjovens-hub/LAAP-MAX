import asyncio
from textual.app import App
from laap.ui.tui import MainScreen

def test_main_screen_composes_sync():
    class TestApp(App):
        def get_default_screen(self):
            return MainScreen()

    async def main():
        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.query_one("#chat_log") is not None

    asyncio.run(main())
