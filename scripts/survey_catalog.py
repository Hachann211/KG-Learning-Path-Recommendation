"""Read the real catalog UI and capture network route evidence, without submitting user data."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    routes = []
    page.on('response',lambda r: routes.append(r.url) if '/api/' in r.url else None)
    page.goto('https://courses.neu.edu.vn/',wait_until='networkidle',timeout=30000)
    page.get_by_text('Học phần',exact=True).click()
    page.locator('input[placeholder="Tìm kiếm (ngành, môn học, khoa,...)"]').fill('Cơ sở dữ liệu')
    page.wait_for_timeout(2400)
    print(page.locator('body').inner_text()[:7000])
    links = page.locator('a').evaluate_all('(els)=>els.map(e=>({text:e.innerText,href:e.getAttribute("href")}))')
    Path('docs/api_samples/catalog_links.json').write_text(json.dumps({'links':links,'routes':routes},ensure_ascii=False,indent=2),encoding='utf-8')
    page.screenshot(path='docs/screenshots/neu-catalog.png',full_page=True)
    print('ROUTES',routes)
    page.get_by_text('TIKT1130 - Cơ sở dữ liệu',exact=True).click()
    page.wait_for_load_state('networkidle')
    Path('docs/api_samples/syllabus_routes.json').write_text(json.dumps({'url':page.url,'routes':routes,'text':page.locator('body').inner_text()[:6000]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('SYLLABUS ROUTES',routes[-12:])
    browser.close()
