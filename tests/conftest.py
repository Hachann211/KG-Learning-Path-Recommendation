import pytest
from flask import g
from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':'sqlite://','WTF_CSRF_ENABLED':False,'SECRET_KEY':'test-only-secret'})
    @app.teardown_request
    def clear_cached_login(error):
        # The fixture retains one outer app context for direct DB assertions;
        # production requests naturally use separate g objects.
        g.pop('_login_user',None)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def student(client):
    client.post('/api/auth/register',json={'email':'student@example.test','name':'Sinh viên','password':'TestingPass123!'})
    return client

@pytest.fixture
def admin(client):
    db.session.add(User(email='admin@example.test',name='Admin',role='admin',password_hash=generate_password_hash('TestingPass123!'),profile={}))
    db.session.commit()
    client.post('/api/auth/login',json={'email':'admin@example.test','password':'TestingPass123!'})
    return client
