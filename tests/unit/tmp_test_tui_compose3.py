import asyncio
from unittest.mock import patch
from textual.app import App
from laap.ui.tui import MainScreen

def test_main_screen_composes_mock_agent():
    class TestApp(App):
        def get_default_screen(self):
            return MainScreen()

    async def main():
        with patch('laap.ui.tui.get_or_create_agent', return_value=None):
            app = TestApp()
            async with app.run_test() as pilot:
                await pilot.pause()
                assert app.query_one("#chat_log") is not None

    asyncio.run(main())
