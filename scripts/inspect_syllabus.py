"""Inspect a syllabus URL observed in the official catalog UI."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

out=Path(__file__).resolve().parents[1]/'docs/api_samples'
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    observations=[]
    def record(response):
        if '/api/' not in response.url:return
        item={'url':response.url,'status':response.status}
        try:
            data=response.json()
            item['keys']=list(data) if isinstance(data,dict) else None
            if 'syllabus' in response.url or 'subject' in response.url:
                target=out/f'syllabus_{len(observations)}.json'
                target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
                item['sample']=target.name
        except Exception:
            item['json']=False
        observations.append(item)
    page.on('response',record)
    page.goto('https://courses.neu.edu.vn/syllabus/K67/vi/ACCT%20201',wait_until='networkidle',timeout=30000)
    page.wait_for_timeout(2500)
    out.joinpath('syllabus_inspection.json').write_text(json.dumps({'url':page.url,'observations':observations,'text':page.locator('body').inner_text()[:6000]},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(observations,ensure_ascii=False,indent=2))
    browser.close()
