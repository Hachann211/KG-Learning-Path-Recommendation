import pytest
from app.extensions import db
from app.models import User, Progress, KnowledgeEdge, Course, CurriculumCourse
from app.services.graph_service import load_graph, prerequisite_graph
from app.services.skill_extractor import extract_skills
from app.models import Skill

INPUT={'curriculum_id':'DEMO-7480201-K66','career_id':'backend'}

@pytest.mark.parametrize('url',['/','/home','/courses','/careers','/graph','/saved','/profile','/dashboard','/api/majors','/api/curricula','/api/careers','/api/skills','/api/courses','/api/courses/DEMO-PY','/api/careers/backend','/api/graph','/api/graph/path'])
def test_public_routes(client,url):
    assert client.get(url).status_code==200

def test_auth_passwords_and_role_assignment(student):
    user=User.query.filter_by(email='student@example.test').one()
    assert user.password_hash!='TestingPass123!'
    assert user.password_hash.startswith('scrypt:')
    assert student.get('/api/admin/stats').status_code==403
    student.post('/api/auth/logout',json={})
    assert student.post('/api/auth/login',json={'email':user.email,'password':'wrong'}).status_code==401
    assert student.get('/api/roadmaps').status_code==401
    assert student.post('/api/auth/register',json={'name':'Attack','email':'attack@test.local','password':'Password123','role':'admin'}).status_code==201
    assert User.query.filter_by(email='attack@test.local').one().role=='student'

def test_invalid_and_duplicate_registration(student):
    assert student.post('/api/auth/register',json={'name':'A','email':'student@example.test','password':'Password123'}).status_code==409
    assert student.post('/api/auth/register',json={'name':'A','email':'bad','password':'123'}).status_code==400

def test_private_roadmaps_and_updates(student,app):
    run=student.post('/api/recommendations',json=INPUT).json['data']
    response=student.post('/api/roadmaps',json={'name':'Lộ trình thử','run_id':run['run_id']})
    assert response.status_code==201
    pid=response.json['data']['id']
    assert len(student.get('/api/roadmaps').json['data'])==1
    assert student.patch('/api/roadmaps/'+str(pid),json={'name':'Tên mới'}).json['data']['name']=='Tên mới'
    other=app.test_client()
    other.post('/api/auth/register',json={'name':'Other','email':'other@test.local','password':'Password123'})
    assert other.get('/api/roadmaps/'+str(pid)).status_code==403
    assert other.get('/api/recommendations/'+run['run_id']).status_code==403
    assert other.delete('/api/roadmaps/'+str(pid)).status_code==403
    assert student.delete('/api/roadmaps/'+str(pid)).status_code==200

def test_progress_and_pdf(student):
    assert student.patch('/api/progress/DEMO-PY',json={'status':'completed'}).status_code==200
    run=student.post('/api/recommendations',json=INPUT).json['data']
    assert 'DEMO-PY' in run['completed']
    pdf=student.get('/api/recommendations/'+run['run_id']+'/pdf')
    assert pdf.status_code==200
    assert pdf.content_type=='application/pdf'
    assert pdf.data.startswith(b'%PDF')
    assert len(pdf.data)>10000
    assert student.patch('/api/progress/DEMO-PY',json={'status':'fake'}).status_code==400
    assert student.patch('/api/progress/DEMO-UNKNOWN',json={'status':'completed'}).status_code==404

def test_recommendation_input_and_score_tampering(client):
    assert client.post('/api/recommendations',json={**INPUT,'current_semester':99}).status_code==400
    assert client.post('/api/recommendations',json={**INPUT,'score':100}).status_code==400
    assert client.post('/api/recommendations',json={**INPUT,'career_id':'unknown'}).status_code==422
    assert client.post('/api/recommendations',json={**INPUT,'completed':['invalid']}).status_code==400

def test_sql_injection_and_html_escaping(client):
    assert client.get('/api/courses?q=%27%20OR%201%3D1%20--').json['data']==[]
    assert client.post('/api/auth/login',json={'email':"' OR 1=1 --",'password':'abc'}).status_code==401
    client.post('/api/auth/register',json={'email':'xss@test.local','name':'<script>alert(1)</script>','password':'TestingPass123!'})
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in client.get('/').data

def test_csrf_rejects_mutation_without_token(app):
    app.config['WTF_CSRF_ENABLED']=True
    client=app.test_client()
    assert client.post('/api/auth/register',json={'name':'A','email':'a@b.test','password':'Password123'}).status_code==400

def test_admin_crud_graph_and_weights(admin):
    assert admin.get('/admin').status_code==200
    assert admin.get('/api/admin/stats').json['data']['cycles']==[]
    assert admin.post('/api/admin/skills',json={'id':'new-skill','name':'Kỹ năng mới','aliases':[]}).status_code==200
    assert admin.patch('/api/admin/skills/new-skill',json={'name':'Kỹ năng cập nhật'}).status_code==200
    assert admin.delete('/api/admin/skills/new-skill').status_code==200
    assert admin.post('/api/admin/majors',json={'id':'sixth','name':'No'}).status_code==422
    assert admin.patch('/api/admin/weights',json={'skills':1}).status_code==400
    assert admin.patch('/api/admin/weights',json={'skills':.4,'topics':.3,'graph':.15,'foundation':.1,'interests':.05}).status_code==200

def test_admin_prevents_cycles_and_bad_edges(admin):
    response=admin.post('/api/admin/edges',json={'source_id':'course:DEMO-DSA','target_id':'course:DEMO-PY','relation':'PREREQUISITE_OF','weight':1,'provenance':'test','confidence':1,'approved':True})
    assert response.status_code==400
    assert KnowledgeEdge.query.filter_by(source_id='course:DEMO-DSA',target_id='course:DEMO-PY',relation='PREREQUISITE_OF').count()==0
    assert admin.post('/api/admin/edges',json={'source_id':'career:backend','target_id':'skill:sql','relation':'FAKE','provenance':'test'}).status_code==400

def test_graph_persistence_types_and_unapproved_exclusion(app):
    graph=load_graph()
    assert {data['kind'] for _,data in graph.nodes(data=True)}=={'Major','Curriculum','Course','Topic','Skill','Career','Lesson','LearningOutcome'}
    assert {'BELONGS_TO','HAS_COURSE','PREREQUISITE_OF','TEACHES','COVERS','REQUIRES','HAS_LESSON','SUPPORTS_OUTCOME','RELATED_TO'} <= {p['relation'] for *_,p in graph.edges(data=True)}
    db.session.expire_all()
    assert set(graph.edges(keys=True))==set(load_graph().edges(keys=True))
    edge=KnowledgeEdge.query.filter_by(source_id='course:DEMO-DB',target_id='skill:sql',relation='TEACHES').one()
    edge.approved=False;db.session.commit()
    assert not load_graph().has_edge(edge.source_id,edge.target_id,'TEACHES')

def test_keyword_extractor_retains_evidence_and_requires_review(app):
    results=extract_skills('Học Python và thực hành SQL.',Skill.query.all())
    assert {'python','sql'} <= {x['skill_id'] for x in results}
    assert all(not x['approved'] and x['evidence'] for x in results)

def test_profile_preserves_settings_and_validates_skills(student):
    assert student.patch('/api/profile',json={'major_id':'7480201','skills':['python']}).status_code==200
    assert student.patch('/api/profile',json={'name':'Tên mới'}).status_code==200
    profile=student.get('/api/profile').json['data']['profile']
    assert profile['skills']==['python'] and profile['major_id']=='7480201'
    assert student.patch('/api/profile',json={'skills':['unknown-skill']}).status_code==400
    assert student.patch('/api/profile',json={'old_password':'bad','password':'NewPassword123'}).status_code==400
    assert student.patch('/api/profile',json={'old_password':'TestingPass123!','password':'NewPassword123'}).status_code==200
