"""Inspect observed responses without assuming a remote schema."""
import concurrent.futures
import argparse
import json
import os
from pathlib import Path
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'primary': os.getenv('NEU_API_PRIMARY', 'https://courses.neu.edu.vn/api'),
    'mirror': os.getenv('NEU_API_MIRROR', 'http://10.2.11.23:1340/api'),
    'fallback': os.getenv('NEU_API_FALLBACK', 'http://101.96.66.222:8025/api/v1'),
}
PATHS = ['/search?q=c%C6%A1%20s%E1%BB%9F%20d%E1%BB%AF%20li%E1%BB%87u&limit=5', '/search/curriculum', '/search/major']

def probe(source, base, path):
    start = time.monotonic()
    record = dict(source=source, url=base + path)
    try:
        response = httpx.get(base + path, timeout=8, follow_redirects=True)
        record.update(status=response.status_code, content_type=response.headers.get('content-type'))
        try:
            data = response.json()
            record['json_type'] = type(data).__name__
            record['keys'] = list(data)[:30] if isinstance(data, dict) else None
            if response.is_success:
                target = ROOT / 'docs/api_samples' / (source + '_' + path.split('?')[0].replace('/', '_') + '.json')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
                record['sample'] = str(target.relative_to(ROOT))
        except ValueError:
            record['error'] = 'Response is not JSON; no adapter can be verified.'
    except httpx.HTTPError as exc:
        record['error'] = type(exc).__name__ + ': ' + str(exc)
    record['elapsed_seconds'] = round(time.monotonic() - start, 2)
    return record

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--syllabus-id',help='An independently verified syllabus ID; never infer it from the subject code.')
    args=parser.parse_args()
    paths=list(PATHS)
    if args.syllabus_id:
        import re
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,100}',args.syllabus_id):
            parser.error('Invalid syllabus ID.')
        paths += ['/public/d3-syllabus/syllabus/'+args.syllabus_id,'/public/d3-syllabus/syllabus/'+args.syllabus_id+'/teaching-plans']
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
        tasks = [executor.submit(probe, source, base, path) for source, base in SOURCES.items() for path in paths]
        records = [task.result() for task in tasks]
    if not args.syllabus_id:
        records.append({'source':'primary','status':'NOT_VERIFIED','url':SOURCES['primary']+'/public/d3-syllabus/syllabus/{id}',
            'error':'No verified syllabus ID was observed. Rerun with --syllabus-id after confirming the subject-code/ID mapping. The teaching-plans endpoint is also unverified.'})
    out = ROOT / 'docs/api_samples/inspection.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    for r in records:
        print(r['source'], r['status'] if 'status' in r else 'ERROR', r['url'], r.get('keys'), r.get('error', ''))

if __name__ == '__main__':
    main()
