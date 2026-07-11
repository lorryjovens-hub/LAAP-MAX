import asyncio
from textual.app import App
from laap.ui.tui import MainScreen, LAAPApp, GatewayStatusPanel

async def main():
    app = LAAPApp()
    try:
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.query_one('#chat_log') is not None
            print('OK')
    except Exception as e:
        print('ERROR', type(e).__name__, e)
        try:
            gw = app.query_one('#gateway_panel', GatewayStatusPanel)
            print('children:', list(gw.children))
            print('layout:', gw.styles.layout)
            print('is_container:', gw.is_container)
            print('render:', gw.render())
            print('_render:', gw._render())
        except Exception as e2:
            print('inspect error', e2)

asyncio.run(main())
