"""Download curated career photographs once for offline use."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import httpx

DEST=Path(__file__).resolve().parents[1]/'app/static/images/careers'
PHOTOS=[
    ('team','1522071820081-009f0129c71c','Nhóm đồng nghiệp cùng làm việc với máy tính'),
    ('fullstack','1519389950473-47ba0277781c','Nhóm phát triển sản phẩm làm việc cùng các thiết bị số'),
    ('mobile','1512941937669-90a1b58e7e9c','Điện thoại thông minh và ứng dụng di động'),
    ('data-scientist','1454165804606-c3d57bc86b40','Phân tích tài liệu và dữ liệu tại bàn làm việc'),
    ('business-analyst','1552664730-d307ca884978','Đồng nghiệp trao đổi và phân tích nhu cầu công việc'),
    ('system-analyst','1553877522-43269d4ea984','Nhóm chuyên môn thảo luận và lập kế hoạch hệ thống')
]

def download(record):
    key,photo,description=record
    url=f'https://images.unsplash.com/photo-{photo}?auto=format&fit=crop&w=1200&q=84&fm=webp'
    response=httpx.get(url,timeout=30,follow_redirects=True)
    response.raise_for_status()
    if not response.headers.get('content-type','').startswith('image/'):
        raise ValueError('Image expected: '+key)
    (DEST/(key+'.webp')).write_bytes(response.content)
    print(key,len(response.content),flush=True)
    return {'file':key+'.webp','description':description,'provider':'Unsplash','source_url':url,
        'license':'Unsplash License','license_url':'https://unsplash.com/license',
        'sha256':hashlib.sha256(response.content).hexdigest()}

if __name__=='__main__':
    DEST.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows=list(pool.map(download,PHOTOS))
    (DEST/'sources.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
