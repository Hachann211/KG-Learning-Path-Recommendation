from flask import Blueprint, render_template, abort
from flask_login import current_user
from app.models import Major, Career, Curriculum

pages = Blueprint('pages',__name__)

@pages.get('/')
@pages.get('/<page>')
def index(page='roadmap'):
    if page not in ['roadmap','home','dashboard','courses','careers','graph','saved','profile','admin']:
        abort(404)
    if page=='admin' and (not current_user.is_authenticated or current_user.role!='admin'):
        abort(403,description='Bạn không có quyền truy cập trang quản trị.')
    return render_template('index.html',page=page,majors=Major.query.all(),careers=Career.query.all(),curricula=Curriculum.query.filter_by(source='DEMO').all())
