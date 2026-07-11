import pytest
from textual.app import App
from laap.ui.tui import MainScreen

@pytest.mark.asyncio
async def test_main_screen_composes():
    class TestApp(App):
        def get_default_screen(self):
            return MainScreen()

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#chat_log") is not None
