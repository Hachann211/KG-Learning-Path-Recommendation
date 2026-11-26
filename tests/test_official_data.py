import httpx
import pytest
from app.extensions import db
from app.models import Course, Curriculum, CurriculumCourse
from app.services.api_adapters import primary_curricula_adapter
from app.services.neu_api_client import NEUApiClient
from app.services.sync_service import sync_curricula

COHORT='K66 - 2024'
PAYLOAD={'data':[{'id':'id-'+code,'attributes':{'name':'Program '+code,'admissionCode':code,'year':COHORT,'slug':'program-'+code}} for code in ['7480101','7480201','7480202','7480104','EP17']]}

def test_curricula_adapter_requires_five_and_correct_cohort():
    assert len(primary_curricula_adapter(PAYLOAD,COHORT))==5
    with pytest.raises(ValueError):primary_curricula_adapter(PAYLOAD,'K67 - 2025')
    with pytest.raises(ValueError):primary_curricula_adapter({'data':PAYLOAD['data'][:4]},COHORT)
    with pytest.raises(ValueError):primary_curricula_adapter([],COHORT)

def test_curricula_sync_keeps_demo_separate_and_never_invents_elective_rule(app):
    for _ in range(2):
        job=sync_curricula(COHORT,httpx.MockTransport(lambda req:httpx.Response(200,json=PAYLOAD)))
        assert job.status=='success'
    assert Curriculum.query.filter_by(source='DEMO').count()==20
    assert Curriculum.query.filter_by(source='NEU').count()==5
    official=Curriculum.query.filter_by(source='NEU').first()
    assert official.elective_count is None and official.choose_count is None and not official.verified
    assert CurriculumCourse.query.filter_by(curriculum_id=official.id).count()==0

def test_curricula_failure_keeps_existing_rows(app):
    before=Curriculum.query.count()
    job=sync_curricula(COHORT,httpx.MockTransport(lambda req:httpx.Response(500)))
    assert job.status=='failed' and Curriculum.query.count()==before

def test_syllabus_uses_verified_id_and_preserves_distinct_teaching_response():
    seen=[]
    def handler(req):
        seen.append(req.url.path)
        return httpx.Response(200,json={'lessons':[]} if req.url.path.endswith('teaching-plans') else {'id':'verified-id','content':'SQL'})
    raw=NEUApiClient(httpx.MockTransport(handler)).syllabus('verified-id')
    assert raw['syllabus']['id']=='verified-id'
    assert raw['teaching_plans']=={'lessons':[]}
    assert seen==['/api/public/d3-syllabus/syllabus/verified-id','/api/public/d3-syllabus/syllabus/verified-id/teaching-plans']

@pytest.mark.parametrize('value',['https://evil.test','../secret','x/y',''])
def test_syllabus_id_cannot_supply_a_url(value):
    with pytest.raises(ValueError):NEUApiClient(httpx.MockTransport(lambda req:pytest.fail('Unexpected HTTP request'))).syllabus(value)

def test_admin_membership_validation_and_graph_persistence(admin):
    cid='DEMO-7480201-K66'
    existing=admin.get('/api/admin/curricula/'+cid+'/courses').json['data']
    assert len(existing)==15
    assert admin.put('/api/admin/curricula/'+cid+'/courses',json={'items':existing,'provenance':'fixture-v1'}).status_code==200
    bad=[{'course_id':'nonexistent','group':'elective'}]
    assert admin.put('/api/admin/curricula/'+cid+'/courses',json={'items':bad,'provenance':'test'}).status_code==400
    assert len(admin.get('/api/admin/curricula/'+cid+'/courses').json['data'])==15
    assert admin.put('/api/admin/curricula/'+cid+'/courses',json={'items':existing,'provenance':''}).status_code==400

def test_syllabus_admin_rejects_missing_mapping_and_demo(admin):
    assert admin.post('/api/admin/syllabus/DEMO-PY',json={'syllabus_id':'x'}).status_code==400
    db.session.add(Course(id='NEU:TEST',code='TEST',source='NEU',name='Test'));db.session.commit()
    assert admin.post('/api/admin/syllabus/NEU:TEST',json={}).status_code==422

def test_offline_client_uses_only_local_assets(page_placeholder=None):
    # Runtime asset URLs are local. Browser networking is also checked in the E2E suite.
    from pathlib import Path
    text=(Path(__file__).resolve().parents[1]/'app/templates/index.html').read_text(encoding='utf-8')
    assert '<script src="https://' not in text and '<link rel="stylesheet" href="https://' not in text
