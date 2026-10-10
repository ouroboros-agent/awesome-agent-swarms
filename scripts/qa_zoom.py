#!/usr/bin/env python3
"""Exercise the real generated figure viewer with JavaScript disabled."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(Path.home() / 'Library/Caches/ms-playwright'))
rows = []
with sync_playwright() as p:
    for engine in ('chromium', 'webkit'):
        browser = getattr(p, engine).launch(**({'channel': 'chrome'} if engine == 'chromium' else {}))
        for lang in ('ru', 'en'):
            context = browser.new_context(viewport={'width': 393, 'height': 659}, java_script_enabled=False, has_touch=True)
            page = context.new_page()
            page.goto((ROOT / 'site' / lang / 'ch01.html').as_uri())
            page.locator('#fig-2 a.zoom').click()
            page.locator('#zoom-2 label[for="actual-2"]').click()
            facts = page.evaluate('''() => {
                const box = document.querySelector('#zoom-2');
                const scroller = box.querySelector('.lb-img');
                const image = scroller.querySelector('img');
                scroller.scrollLeft = 350; scroller.scrollTop = 100;
                return {checked: box.querySelector('input').checked,
                    natural: image.naturalWidth, width: image.width,
                    viewport: scroller.clientWidth, scrollWidth: scroller.scrollWidth,
                    panX: scroller.scrollLeft, panY: scroller.scrollTop,
                    original: box.querySelector('.lb-tools a').href};
            }''')
            assert facts['checked'] and facts['natural'] == facts['width'] > facts['viewport'], facts
            assert facts['panX'] > 0 and facts['panY'] > 0, facts
            page.locator('#zoom-2 .lb-close').click()
            assert not page.locator('#zoom-2').is_visible()
            rows.append({'engine': engine, 'lang': lang, **facts, 'closed': True})
            context.close()
        browser.close()
print(json.dumps({'status': 'pass', 'cases': rows}, ensure_ascii=False))
