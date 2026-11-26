import json
import sqlite3
from contextlib import closing
import pytest
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from app.models import User, Course, Progress, RecommendationRun, LearningPath, AuditLog, KnowledgeEdge
from app.services.customer_demo import prepare_customer_demo, demo_accounts, DEMO_MARKER
from scripts.package_project import validate_demo_users


def test_customer_demo_credentials_data_and_permissions(app,client):
    prepare_customer_demo()
    assert User.query.count()==2
    assert LearningPath.query.count()==4
    assert RecommendationRun.query.count()==4
    assert KnowledgeEdge.query.filter_by(approved=False).count()==2
    for account in demo_accounts():
        user=User.query.filter_by(email=account['email']).one()
        assert check_password_hash(user.password_hash,account['password'])
        assert user.password_hash!=account['password']
        assert user.profile['demo_seed']==DEMO_MARKER
        assert client.post('/api/auth/login',json={'email':account['email'],'password':account['password']}).status_code==200
        assert client.get('/api/admin/stats').status_code==(200 if account['role']=='admin' else 403)
        paths=client.get('/api/roadmaps').json['data']
        assert len(paths)==(1 if account['role']=='admin' else 3)
        for path in paths:
            run=client.get('/api/recommendations/'+path['run_id']).json['data']
            assert len([c for c in run['items'] if c['selected']])==10
        if account['role']=='student':
            progress=client.get('/api/progress').json['data']
            assert sum(p['status']=='completed' for p in progress)==4
            assert sum(p['status']=='in_progress' for p in progress)==2
            assert client.get('/api/recommendations/demo-admin-ai').status_code==403
        client.post('/api/auth/logout',json={})
    for course in Course.query.filter_by(source='DEMO').all():
        assert len(course.detail['outcomes'])==3
        assert sum(lesson['hours'] for lesson in course.detail['lessons'])==45
        assert len({lesson['title'] for lesson in course.detail['lessons']})==4


def test_customer_demo_idempotency_preserves_edits_and_reset(app):
    prepare_customer_demo()
    counts=(User.query.count(),LearningPath.query.count(),RecommendationRun.query.count(),AuditLog.query.count())
    user=User.query.filter_by(email='user@neu-demo.test').one()
    progress=db.session.get(Progress,(user.id,'DEMO-WEB'))
    progress.status='completed'
    db.session.add(Progress(user_id=user.id,course_id='DEMO-NET',status='completed'))
    user.name='Tên đã sửa trong buổi demo'
    db.session.commit()
    prepare_customer_demo()
    assert counts==(User.query.count(),LearningPath.query.count(),RecommendationRun.query.count(),AuditLog.query.count())
    assert user.name=='Tên đã sửa trong buổi demo'
    assert progress.status=='completed'
    prepare_customer_demo(reset=True)
    assert counts==(User.query.count(),LearningPath.query.count(),RecommendationRun.query.count(),AuditLog.query.count())
    assert user.name=='Nguyễn Minh Anh'
    assert progress.status=='in_progress'
    assert db.session.get(Progress,(user.id,'DEMO-NET')).status=='not_started'


def test_demo_collision_does_not_overwrite_existing_account(app):
    db.session.add(User(email='user@neu-demo.test',name='Existing user',role='student',password_hash=generate_password_hash('ExistingPass123!'),profile={}))
    db.session.commit()
    with pytest.raises(ValueError,match='Email'):
        prepare_customer_demo(reset=True)
    user=User.query.one()
    assert user.name=='Existing user'
    assert check_password_hash(user.password_hash,'ExistingPass123!')
    assert RecommendationRun.query.count()==0


def test_packaging_allows_public_demo_but_rejects_other_users(app):
    prepare_customer_demo()
    with closing(sqlite3.connect(':memory:')) as connection:
        connection.execute('CREATE TABLE users(email,role,profile,password_hash)')
        for user in User.query.all():
            connection.execute('INSERT INTO users VALUES(?,?,?,?)',(user.email,user.role,json.dumps(user.profile),user.password_hash))
        validate_demo_users(connection)
        connection.execute('INSERT INTO users VALUES(?,?,?,?)',('personal@example.test','student','{}','hash'))
        with pytest.raises(ValueError,match='personal accounts'):
            validate_demo_users(connection)
