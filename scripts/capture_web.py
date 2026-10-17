"""Capture real browser rendering of the running Django server (Chrome required)."""
import html
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence'
log_path = OUT / 'server-tests.txt'
if log_path.exists():
    log = log_path.read_text()
    start = log.find('test_anonymous_cannot_write')
    if start >= 0: log = log[start:]
    (OUT / 'server-tests.html').write_text('<meta charset="utf-8"><style>body{padding:30px;background:#15231b;color:#d5e8d8;font:16px monospace}pre{white-space:pre-wrap}</style><h1>Django · 실제 자동 테스트 로그</h1><pre>' + html.escape(log) + '</pre>')
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1100}, device_scale_factor=1)
    page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
    page.locator('.card img').first.wait_for()
    page.screenshot(path=str(OUT / '05-server-gallery.png'), full_page=True)
    page.goto('http://127.0.0.1:8000/api/posts/', wait_until='networkidle')
    page.screenshot(path=str(OUT / '01-api-browser.png'), full_page=True)
    for name in ['02-api-validation', '03-api-validation', 'server-tests']:
        path = OUT / (name + '.html')
        if path.exists():
            page.goto(path.as_uri(), wait_until='load')
            page.screenshot(path=str(OUT / (name + '.png')), full_page=True)
    browser.close()
