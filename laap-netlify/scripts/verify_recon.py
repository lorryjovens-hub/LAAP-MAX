from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    page.goto('http://localhost:5173/')
    page.wait_for_load_state('networkidle')
    print('URL:', page.url)
    print('Title:', page.title())
    buttons = page.locator('button').all()
    print('Buttons:', [b.text_content().strip() for b in buttons if b.text_content().strip()])
    links = page.locator('a').all()
    print('Links:', [l.text_content().strip() for l in links if l.text_content().strip()])
    page.screenshot(path='d:/LAAP/laap-netlify/scripts/recon_home.png', full_page=True)
    print('Screenshot saved to scripts/recon_home.png')
    browser.close()
