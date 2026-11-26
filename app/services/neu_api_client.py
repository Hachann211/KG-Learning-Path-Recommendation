import os
import time
import httpx
from app.services.api_adapters import primary_search_adapter, fallback_search_adapter

class SourceUnavailable(RuntimeError):
    pass

class NEUApiClient:
    def __init__(self, transport=None):
        self.timeout = httpx.Timeout(float(os.getenv('NEU_READ_TIMEOUT','8')),connect=float(os.getenv('NEU_CONNECT_TIMEOUT','3')))
        self.client = httpx.Client(timeout=self.timeout,follow_redirects=True,transport=transport)
        self.sources = [('primary',os.getenv('NEU_API_PRIMARY','https://courses.neu.edu.vn/api'),'/search',primary_search_adapter),
            ('mirror',os.getenv('NEU_API_MIRROR','http://10.2.11.23:1340/api'),'/search',primary_search_adapter)]
        fallback_path = os.getenv('NEU_FALLBACK_SEARCH_PATH')
        if fallback_path:
            self.sources.append(('fallback',os.getenv('NEU_API_FALLBACK','http://101.96.66.222:8025/api/v1'),fallback_path,fallback_search_adapter))
        self.attempts = []

    def curricula(self,cohort):
        from app.services.api_adapters import primary_curricula_adapter
        try:
            response=self.client.get(self.sources[0][1].rstrip('/')+'/curriculum-curricula',params={
                'pagination[withCount]':'true','populate':'*','filters[year]':cohort,'locale':'vi',
                'pagination[page]':1,'pagination[pageSize]':500})
            self.attempts.append({'source':'primary','status':response.status_code,'endpoint':'curriculum-curricula'})
            response.raise_for_status()
            if len(response.content)>10_000_000:
                raise ValueError('Curriculum response exceeds 10 MB.')
            return primary_curricula_adapter(response.json(),cohort)
        finally:
            self.client.close()

    def syllabus(self,syllabus_id):
        """Keep raw unverified fields intact; only a verified ID may be supplied by an admin."""
        import re
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,100}',syllabus_id):
            self.client.close()
            raise ValueError('ID đề cương không hợp lệ.')
        try:
            base=self.sources[0][1].rstrip('/')+'/public/d3-syllabus/syllabus/'+syllabus_id
            result={}
            for key,suffix in [('syllabus',''),('teaching_plans','/teaching-plans')]:
                response=self.client.get(base+suffix)
                self.attempts.append({'source':'primary','status':response.status_code,'endpoint':key})
                response.raise_for_status()
                if len(response.content)>5_000_000:
                    raise ValueError('Syllabus response exceeds 5 MB.')
                result[key]=response.json()
            return result
        finally:
            self.client.close()

    def search(self, query, limit=99):
        try:
            for name, base, route, adapter in self.sources:
                start = time.monotonic()
                try:
                    response = self.client.get(base.rstrip('/')+route,params={'q':query,'limit':limit})
                    self.attempts.append({'source':name,'status':response.status_code,'elapsed':round(time.monotonic()-start,2)})
                    if response.status_code>=500 or response.status_code==429:
                        continue
                    response.raise_for_status()  # A bad query / missing resource must not switch sources.
                    if len(response.content)>5_000_000:
                        raise ValueError('Phản hồi vượt quá giới hạn 5 MB.')
                    data = adapter(response.json())
                    if not data:
                        raise ValueError('Phản hồi rỗng chưa được xác nhận; giữ nguyên dữ liệu đã lưu.')
                    return data,name
                except (httpx.TimeoutException,httpx.NetworkError) as exc:
                    self.attempts.append({'source':name,'error':type(exc).__name__})
            raise SourceUnavailable('Các nguồn đã xác minh không khả dụng. Dữ liệu SQLite được giữ nguyên.')
        finally:
            self.client.close()
