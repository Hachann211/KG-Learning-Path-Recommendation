import os
from pathlib import Path
import secrets
import sqlite3
from flask import Flask, jsonify, request, render_template
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.exceptions import HTTPException
from flask_wtf.csrf import CSRFError
from app.extensions import db, login_manager, csrf, migrate

@event.listens_for(Engine, 'connect')
def foreign_keys(connection, record):
    if isinstance(connection, sqlite3.Connection):
        connection.execute('PRAGMA foreign_keys=ON')

def create_app(config=None):
    from dotenv import load_dotenv
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    keyfile = Path(app.instance_path) / '.secret_key'
    if not keyfile.exists():
        keyfile.write_text(secrets.token_hex(32), encoding='utf-8')
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or keyfile.read_text(),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///learning.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False, SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=1024*1024,
        WTF_CSRF_TIME_LIMIT=None, TEMPLATES_AUTO_RELOAD=True,
        SEND_FILE_MAX_AGE_DEFAULT=0)
    if config:
        app.config.update(config)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify(error='Vui lòng đăng nhập để tiếp tục.'), 401
    from app.routes.api import api
    from app.routes.pages import pages
    app.register_blueprint(api)
    app.register_blueprint(pages)
    @app.after_request
    def fresh_html(response):
        if response.mimetype=='text/html':
            response.cache_control.no_store=True
        return response
    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return jsonify(error='Phiên bảo mật không hợp lệ. Vui lòng tải lại trang.'), 400
    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description), error.code
        return render_template('error.html', code=error.code, message=error.description), error.code
    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return jsonify(error='Có lỗi xử lý. Vui lòng thử lại.'), 500
    if app.config.get('AUTO_INIT_DB', os.getenv('DB_AUTO_INIT','1')=='1'):
        with app.app_context():
            db.create_all()
            from app.services.seed import seed_demo
            seed_demo()
    return app
