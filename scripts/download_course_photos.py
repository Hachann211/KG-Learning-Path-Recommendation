"""Fetch the curated real photographs once; the application serves local assets offline."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'app/static/images/courses'
# Historic Unsplash photographs, not generated imagery. Verify the downloaded images visually.
PHOTOS=[
    ('python','1515879218367-8466d910aaa4','Lập trình Python'),
    ('algorithms','1509228627152-72ae9ae6848d','Cấu trúc dữ liệu và giải thuật'),
    ('database','1607799279861-4dd421887fb3','Cơ sở dữ liệu'),
    ('oop','1555066931-4365d14bab8c','Lập trình hướng đối tượng'),
    ('web','1461749280684-dccba630e2f6','Phát triển ứng dụng web'),
    ('database-admin','1558494949-ef010cbdcc31','Hệ quản trị cơ sở dữ liệu'),
    ('api','1555949963-aa79dcee981c','Thiết kế và phát triển API'),
    ('network','1544197150-b99a580bb7a8','Mạng máy tính'),
    ('linux','1629654297299-c8506221ca97','Hệ điều hành'),
    ('security','1550751827-4bd374c3f58b','An toàn và bảo mật thông tin'),
    ('ml','1485827404703-89b55fcc595e','Học máy và trí tuệ nhân tạo'),
    ('data','1551288049-bebda4e38f71','Phân tích và trực quan dữ liệu'),
    ('ui','1581291518857-4e27b48ff24e','Thiết kế giao diện người dùng'),
    ('testing','1498050108023-c5249f4df085','Kiểm thử và đảm bảo chất lượng'),
    ('cloud','1506399558188-acca6f8cbf41','Điện toán đám mây và DevOps'),
]

def download(record):
    key,photo,subject=record
    url=f'https://images.unsplash.com/photo-{photo}?auto=format&fit=crop&w=1100&q=84&fm=webp'
    response=httpx.get(url,timeout=30,follow_redirects=True)
    response.raise_for_status()
    if not response.headers.get('content-type','').startswith('image/'):
        raise ValueError(f'{key}: expected a real image response')
    path=DEST/f'{key}.webp'
    path.write_bytes(response.content)
    print(key,response.status_code,len(response.content),flush=True)
    return {'file':path.name,'subject':subject,'provider':'Unsplash','photo_id':photo,
        'source_url':url,'license':'Unsplash License','license_url':'https://unsplash.com/license',
        'sha256':hashlib.sha256(response.content).hexdigest()}

if __name__=='__main__':
    DEST.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results=list(pool.map(download,PHOTOS))
    (DEST/'sources.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
