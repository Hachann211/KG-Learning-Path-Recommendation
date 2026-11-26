import httpx
import pytest
from app.extensions import db
from app.models import Course
from app.services.neu_api_client import NEUApiClient, SourceUnavailable
from app.services.sync_service import sync_courses
from app.services.api_adapters import primary_search_adapter, fallback_search_adapter

PAYLOAD=[{'type':'subject','name':'Môn thật','subjectCode':'TEST001','curriculums':[{'year':'K66 - 2024'},{'year':'K67 - 2025'}]}]

def response(status=200,data=PAYLOAD):
    return httpx.Response(status,json=data)

def test_primary_success_and_type_filter():
    data,source=NEUApiClient(httpx.MockTransport(lambda req:response(data=[*PAYLOAD,{'type':'major','name':'Skip'}]))).search('x')
    assert source=='primary' and len(data)==1
    assert data[0]['cohorts']==['K66 - 2024','K67 - 2025']

@pytest.mark.parametrize('mode',['timeout','500'])
def test_primary_failure_mirror_success(mode):
    def handler(req):
        if req.url.host=='courses.neu.edu.vn':
            if mode=='timeout':raise httpx.ReadTimeout('mock timeout')
            return response(500)
        return response()
    data,source=NEUApiClient(httpx.MockTransport(handler)).search('x')
    assert source=='mirror'

def test_all_failed_preserves_cache(app):
    db.session.add(Course(id='NEU:OLD',code='OLD',name='Cached',source='NEU'));db.session.commit()
    def handler(req):raise httpx.ConnectTimeout('mock offline')
    job=sync_courses('x',httpx.MockTransport(handler))
    assert job.status=='failed' and job.source=='cache'
    assert db.session.get(Course,'NEU:OLD') is not None
    assert job.detail['cache_preserved']

@pytest.mark.parametrize('payload',[[],{},[{'type':'subject','name':'Missing code'}],{'results':PAYLOAD}])
def test_empty_invalid_schema_preserves_data(app,payload):
    count=Course.query.count()
    job=sync_courses('x',httpx.MockTransport(lambda req:response(data=payload)))
    assert job.status=='failed'
    assert Course.query.count()==count

def test_idempotent_sync_dedup_and_no_invented_fields(app):
    for _ in range(2):
        job=sync_courses('x',httpx.MockTransport(lambda req:response(data=PAYLOAD*2)))
        assert job.status=='success' and job.records==1
    assert Course.query.filter_by(code='TEST001',source='NEU').count()==1
    course=db.session.get(Course,'NEU:TEST001')
    assert course.credits is None and course.syllabus_id is None
    assert course.detail['cohorts']==['K66 - 2024','K67 - 2025']

def test_400_does_not_blindly_fallback():
    seen=[]
    def handler(req):seen.append(req.url);return response(400)
    with pytest.raises(httpx.HTTPStatusError):NEUApiClient(httpx.MockTransport(handler)).search('x')
    assert len(seen)==1

def test_unverified_fallback_never_guesses_schema():
    with pytest.raises(ValueError,match='unverified'):fallback_search_adapter({'results':PAYLOAD})

def test_oversized_response_is_rejected(app):
    huge=httpx.Response(200,content=b' '*5_000_001)
    job=sync_courses('x',httpx.MockTransport(lambda req:huge))
    assert job.status=='failed'
