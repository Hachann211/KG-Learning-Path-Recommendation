from datetime import datetime, timezone
from functools import wraps
from io import BytesIO
import re
from uuid import uuid4
from flask import Blueprint, request, jsonify, abort, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from sqlalchemy.exc import IntegrityError
import networkx as nx
from app.extensions import db
from app.models import *
from app.services.recommendation_service import recommend, RecommendationError, course_dict
from app.services.graph_service import load_graph, serialize_graph, explanation_paths, prerequisite_graph
from app.services.sync_service import sync_courses, sync_curricula

api = Blueprint('api',__name__,url_prefix='/api')

def body():
    value = request.get_json(silent=True)
    if not isinstance(value,dict):
        abort(400,description='Dữ liệu JSON không hợp lệ.')
    return value

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args,**kwargs):
        if current_user.role!='admin':
            abort(403,description='Chức năng chỉ dành cho quản trị viên.')
        return fn(*args,**kwargs)
    return wrapper

@api.post('/auth/register')
def register():
    data = body()
    email = str(data.get('email','')).strip().lower()
    name = str(data.get('name','')).strip()
    password = data.get('password','')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(email)>254 or not 1<=len(name)<=100:
        abort(400,description='Vui lòng nhập họ tên và email hợp lệ.')
    if not isinstance(password,str) or not 8<=len(password)<=128:
        abort(400,description='Mật khẩu cần có từ 8 đến 128 ký tự.')
    user = User(email=email,name=name,password_hash=generate_password_hash(password),role='student',profile={})
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409,description='Email này đã được sử dụng.')
    login_user(user)
    return jsonify(data={'name':user.name,'role':user.role}),201

@api.post('/auth/login')
def login():
    data = body()
    email = str(data.get('email','')).strip().lower()
    password = data.get('password','')
    user = User.query.filter_by(email=email).first()
    if not isinstance(password,str) or len(password)>128 or not user or not check_password_hash(user.password_hash,password):
        abort(401,description='Email hoặc mật khẩu không chính xác.')
    login_user(user)
    return jsonify(data={'name':user.name,'role':user.role})

@api.post('/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify(data={'ok':True})

@api.route('/profile',methods=['GET','PATCH'])
@login_required
def profile():
    if request.method=='PATCH':
        data = body()
        if 'name' in data:
            name = str(data['name']).strip()
            if not 1<=len(name)<=100:
                abort(400,description='Họ tên không hợp lệ.')
            current_user.name = name
        if 'password' in data:
            if not check_password_hash(current_user.password_hash,str(data.get('old_password',''))):
                abort(400,description='Mật khẩu hiện tại không đúng.')
            password = data['password']
            if not isinstance(password,str) or not 8<=len(password)<=128:
                abort(400,description='Mật khẩu mới cần từ 8 đến 128 ký tự.')
            current_user.password_hash = generate_password_hash(password)
        updates={k:v for k,v in data.items() if k in ['major_id','cohort','career_id','skills','interests']}
        if 'major_id' in updates and not db.session.get(Major,updates['major_id']):
            abort(400,description='Ngành học không hợp lệ.')
        if 'career_id' in updates and not db.session.get(Career,updates['career_id']):
            abort(400,description='Nghề nghiệp không hợp lệ.')
        for key in ['skills','interests']:
            if key in updates and (not isinstance(updates[key],list) or len(updates[key])>50 or any(not isinstance(v,str) or not db.session.get(Skill,v) for v in updates[key])):
                abort(400,description='Danh sách kỹ năng không hợp lệ.')
        current_user.profile = {**(current_user.profile or {}),**updates}
        db.session.commit()
    return jsonify(data={'name':current_user.name,'email':current_user.email,'role':current_user.role,'profile':current_user.profile})

@api.get('/majors')
def majors():
    return jsonify(data=[{'id':x.id,'name':x.name,'confirmed':x.confirmed} for x in Major.query.all()])

@api.get('/curricula')
def curricula():
    query = Curriculum.query
    for key in ['major_id','cohort','source']:
        if request.args.get(key):
            query = query.filter(getattr(Curriculum,key)==request.args[key])
    return jsonify(data=[{'id':x.id,'major_id':x.major_id,'cohort':x.cohort,'name':x.name,'source':x.source,'verified':x.verified,'elective_count':x.elective_count,'choose_count':x.choose_count} for x in query.all()])

def career_dict(c):
    graph = load_graph()
    from app.services.graph_service import neighbors
    return {'id':c.id,'name':c.name,'english':c.english,'description':c.description,'icon':c.icon,
        'skills':[{'id':s.removeprefix('skill:'),'name':graph.nodes[s]['label'],'weight':w} for s,w in neighbors(graph,'career:'+c.id,'REQUIRES').items()]}

@api.get('/careers')
def careers():
    return jsonify(data=[career_dict(x) for x in Career.query.all()])

@api.get('/careers/<career_id>')
def career(career_id):
    return jsonify(data=career_dict(db.get_or_404(Career,career_id)))

@api.get('/skills')
def skills():
    return jsonify(data=[{'id':s.id,'name':s.name,'aliases':s.aliases} for s in Skill.query.all()])

@api.get('/courses')
def courses():
    query = Course.query
    if request.args.get('curriculum_id'):
        query = query.join(CurriculumCourse).filter(CurriculumCourse.curriculum_id==request.args['curriculum_id'])
    if request.args.get('source'):
        query = query.filter_by(source=request.args['source'])
    if request.args.get('q'):
        text = request.args['q'][:200]
        query = query.filter(Course.name.contains(text,autoescape=True)|Course.code.contains(text,autoescape=True))
    return jsonify(data=[course_dict(c) for c in query.order_by(Course.name).limit(250).all()])

@api.get('/courses/<path:course_id>')
def course(course_id):
    return jsonify(data=course_dict(db.get_or_404(Course,course_id)))

class RecommendationInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    curriculum_id: str = Field(max_length=80)
    career_id: str = Field(max_length=60)
    current_semester: int = Field(default=3,ge=1,le=12)
    completed: list[str] = Field(default_factory=list,max_length=200)
    interests: list[str] = Field(default_factory=list,max_length=50)
    existing_skills: list[str] = Field(default_factory=list,max_length=50)

@api.post('/recommendations')
def recommendations():
    try:
        inputs = RecommendationInput.model_validate(body()).model_dump()
    except ValidationError:
        abort(400,description='Thông tin tạo lộ trình không hợp lệ.')
    if current_user.is_authenticated:
        inputs['completed'] = sorted(set(inputs['completed']) | {p.course_id for p in Progress.query.filter_by(user_id=current_user.id,status='completed').all()})
    if any(not db.session.get(Course,c) for c in inputs['completed']):
        abort(400,description='Danh sách môn đã hoàn thành có mã không hợp lệ.')
    try:
        result = recommend(**inputs)
    except RecommendationError as exc:
        return jsonify(error=str(exc)),422
    run_id = uuid4().hex
    db.session.add(RecommendationRun(id=run_id,user_id=current_user.id if current_user.is_authenticated else None,inputs=inputs,result=result))
    db.session.commit()
    return jsonify(data={**result,'run_id':run_id}),201

def authorized_run(run_id):
    run = db.get_or_404(RecommendationRun,run_id)
    if run.user_id is not None and (not current_user.is_authenticated or current_user.id!=run.user_id):
        abort(403)
    return run

@api.get('/recommendations/<run_id>')
def recommendation(run_id):
    run = authorized_run(run_id)
    return jsonify(data={**run.result,'run_id':run.id})

@api.route('/roadmaps',methods=['GET','POST'])
@login_required
def roadmaps():
    if request.method=='GET':
        return jsonify(data=[{'id':r.id,'name':r.name,'run_id':r.run_id,'created_at':r.created_at.isoformat(),
            'career':db.session.get(RecommendationRun,r.run_id).result.get('career_name')} for r in LearningPath.query.filter_by(user_id=current_user.id).order_by(LearningPath.created_at.desc()).all()])
    data = body()
    run = authorized_run(str(data.get('run_id','')))
    name = str(data.get('name','Lộ trình của tôi')).strip()
    if not 1<=len(name)<=150:
        abort(400,description='Tên lộ trình cần có từ 1 đến 150 ký tự.')
    # Claim anonymous run on saving; it becomes owner-private.
    run.user_id = current_user.id
    path = LearningPath(user_id=current_user.id,run_id=run.id,name=name)
    db.session.add(path)
    db.session.commit()
    return jsonify(data={'id':path.id,'name':path.name}),201

@api.route('/roadmaps/<int:path_id>',methods=['GET','PATCH','DELETE'])
@login_required
def roadmap(path_id):
    path = db.get_or_404(LearningPath,path_id)
    if path.user_id!=current_user.id:
        abort(403)
    if request.method=='DELETE':
        db.session.delete(path)
        db.session.commit()
        return jsonify(data={'ok':True})
    if request.method=='PATCH':
        name = str(body().get('name','')).strip()
        if not 1<=len(name)<=150:
            abort(400,description='Tên lộ trình không hợp lệ.')
        path.name = name
        db.session.commit()
    return jsonify(data={'id':path.id,'name':path.name,'run_id':path.run_id})

@api.get('/progress')
@login_required
def get_progress():
    return jsonify(data=[{'course_id':p.course_id,'status':p.status} for p in Progress.query.filter_by(user_id=current_user.id).all()])

@api.patch('/progress/<path:course_id>')
@login_required
def progress(course_id):
    db.get_or_404(Course,course_id)
    status = body().get('status')
    if status not in ['not_started','in_progress','completed']:
        abort(400,description='Trạng thái học phần không hợp lệ.')
    item = db.session.get(Progress,(current_user.id,course_id))
    if not item:
        item = Progress(user_id=current_user.id,course_id=course_id)
        db.session.add(item)
    item.status = status
    db.session.commit()
    return jsonify(data={'course_id':course_id,'status':status})

@api.get('/graph')
def graph():
    graph = load_graph()
    career = request.args.get('career_id','backend')
    center = 'career:'+career
    if center not in graph:
        abort(404)
    from app.services.graph_service import neighbors
    skills = set(neighbors(graph,center,'REQUIRES'))
    nodes = {center}|skills
    cid = request.args.get('curriculum_id')
    allowed = {x.course_id for x in CurriculumCourse.query.filter_by(curriculum_id=cid).all()} if cid else None
    for source,target,props in graph.edges(data=True):
        if target in skills and props['relation']=='TEACHES' and (allowed is None or source.removeprefix('course:') in allowed):
            nodes.add(source)
    return jsonify(data=serialize_graph(graph.subgraph(nodes)))

@api.get('/graph/path')
def graph_path():
    return jsonify(data=explanation_paths(load_graph(),request.args.get('career_id','backend'),request.args.get('course_id','DEMO-DB')))

@api.get('/recommendations/<run_id>/pdf')
def export_pdf(run_id):
    from app.services.export_service import make_pdf
    run = authorized_run(run_id)
    return send_file(make_pdf(run),mimetype='application/pdf',as_attachment=True,download_name='lo-trinh-hoc-tap.pdf')

@api.post('/admin/sync')
@admin_required
def sync():
    data = body()
    query = str(data.get('q','lập trình'))[:100]
    kind=data.get('kind','courses')
    if kind=='curricula':
        cohort=data.get('cohort','K66 - 2024')
        if cohort not in ['K65 - 2023','K66 - 2024','K67 - 2025','K68 - 2026']:
            abort(400,description='Khóa tuyển sinh không hợp lệ.')
        job=sync_curricula(cohort)
    elif kind=='courses':
        job=sync_courses(query)
    else:
        abort(400,description='Loại đồng bộ không hợp lệ.')
    db.session.add(AuditLog(user_id=current_user.id,action='sync',detail={'job_id':job.id}))
    db.session.commit()
    return jsonify(data={'id':job.id,'status':job.status,'records':job.records,'detail':job.detail}),200 if job.status=='success' else 502

@api.post('/admin/syllabus/<path:course_id>')
@admin_required
def sync_syllabus(course_id):
    from app.services.neu_api_client import NEUApiClient
    from app.services.skill_extractor import extract_skills
    course=db.get_or_404(Course,course_id)
    if course.source!='NEU':
        abort(400,description='Chỉ đồng bộ đề cương cho môn thuộc nguồn NEU.')
    sid=body().get('syllabus_id') or course.syllabus_id
    if not isinstance(sid,str):
        abort(422,description='Chưa có ID đề cương được xác minh. Mã môn không tự động được coi là ID đề cương.')
    client=NEUApiClient()
    try:
        raw=client.syllabus(sid)
    except Exception:
        return jsonify(error='Chưa lấy được đề cương bằng ID này; dữ liệu đã lưu được giữ nguyên.'),502
    course.syllabus_id=sid
    course.detail={**(course.detail or {}),'raw_syllabus':raw,'source_note':'Nội dung thô từ API đề cương NEU; ánh xạ kỹ năng cần kiểm duyệt.'}
    db.session.add(AuditLog(user_id=current_user.id,action='sync_syllabus',detail={'course_id':course.id,'syllabus_id':sid}))
    db.session.commit()
    return jsonify(data={'course_id':course.id,'raw':raw,'skill_proposals':extract_skills(str(raw),Skill.query.all())})

@api.route('/admin/curricula/<path:curriculum_id>/courses',methods=['GET','PUT'])
@admin_required
def curriculum_membership(curriculum_id):
    curriculum=db.get_or_404(Curriculum,curriculum_id)
    if request.method=='GET':
        return jsonify(data=[{'course_id':m.course_id,'group':m.group} for m in CurriculumCourse.query.filter_by(curriculum_id=curriculum_id).all()])
    data=body()
    items=data.get('items')
    source_note=data.get('provenance')
    if not isinstance(items,list) or len(items)>200 or not isinstance(source_note,str) or not source_note.strip():
        abort(400,description='Cần danh sách môn hợp lệ và tài liệu nguồn để xác nhận thành viên chương trình.')
    ids=set()
    for item in items:
        if not isinstance(item,dict) or item.get('group') not in ['elective','required'] or item.get('course_id') in ids:
            abort(400,description='Môn bị trùng hoặc nhóm môn không hợp lệ.')
        c=db.session.get(Course,item.get('course_id'))
        if not c or c.source!=curriculum.source:
            abort(400,description='Không trộn học phần NEU và minh họa trong cùng chương trình.')
        ids.add(c.id)
    CurriculumCourse.query.filter_by(curriculum_id=curriculum_id).delete()
    node_id='curriculum:'+curriculum_id
    KnowledgeEdge.query.filter(((KnowledgeEdge.source_id==node_id)&(KnowledgeEdge.relation=='HAS_COURSE'))|((KnowledgeEdge.target_id==node_id)&(KnowledgeEdge.relation=='BELONGS_TO'))).delete()
    for item in items:
        c=db.session.get(Course,item['course_id'])
        db.session.merge(KnowledgeNode(id='course:'+c.id,kind='Course',label=c.name,properties={'course_id':c.id,'source':c.source}))
        db.session.add(CurriculumCourse(curriculum_id=curriculum_id,course_id=c.id,group=item['group']))
    db.session.flush()
    for item in items:
        db.session.add(KnowledgeEdge(source_id=node_id,target_id='course:'+item['course_id'],relation='HAS_COURSE',weight=1,provenance=source_note,approved=True))
        db.session.add(KnowledgeEdge(source_id='course:'+item['course_id'],target_id=node_id,relation='BELONGS_TO',weight=1,provenance=source_note,approved=True))
    curriculum.verified=False
    db.session.add(AuditLog(user_id=current_user.id,action='curriculum_membership',detail={'id':curriculum_id,'provenance':source_note,'count':len(items)}))
    db.session.commit()
    return jsonify(data={'ok':True,'verified':False})

@api.get('/admin/sync/status')
@admin_required
def sync_status():
    return jsonify(data=[{'id':s.id,'status':s.status,'records':s.records,'source':s.source,'detail':s.detail,'created_at':s.created_at.isoformat()} for s in SyncJob.query.order_by(SyncJob.id.desc()).limit(20).all()])

@api.get('/admin/stats')
@admin_required
def stats():
    graph = load_graph()
    pre = prerequisite_graph(graph)
    return jsonify(data={'users':User.query.count(),'courses':Course.query.count(),'careers':Career.query.count(),'roadmaps':LearningPath.query.count(),
        'nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),'components':nx.number_weakly_connected_components(graph),
        'cycles':list(nx.simple_cycles(pre)),'pending_edges':KnowledgeEdge.query.filter_by(approved=False).count(),
        'isolated':list(nx.isolates(graph)),'weights':db.session.get(Settings,'weights').value})

ADMIN_MODELS = {'careers':Career,'skills':Skill,'curricula':Curriculum,'majors':Major,'courses':Course,'nodes':KnowledgeNode,'edges':KnowledgeEdge,'users':User}
ADMIN_FIELDS = {'careers':['id','name','english','description','icon'],'skills':['id','name','aliases'],
    'curricula':['id','major_id','cohort','name','source','elective_count','choose_count','verified'],
    'majors':['id','name','confirmed'],'courses':['name','description','credits','syllabus_id','detail'],
    'nodes':['id','kind','label','properties'],'edges':['id','source_id','target_id','relation','weight','provenance','confidence','approved'],
    'users':['name','role']}

@api.route('/admin/<kind>',methods=['GET','POST'])
@api.route('/admin/<kind>/<path:item_id>',methods=['PATCH','DELETE'])
@admin_required
def admin_records(kind,item_id=None):
    model = ADMIN_MODELS.get(kind)
    if not model:
        abort(404)
    if request.method=='GET':
        return jsonify(data=[{column.name:getattr(row,column.name) for column in model.__table__.columns if column.name not in ['password_hash','created_at','updated_at']} for row in model.query.limit(250).all()])
    data = {} if request.method=='DELETE' else body()
    if set(data)-set(ADMIN_FIELDS[kind]):
        abort(400,description='Dữ liệu chứa trường không được phép sửa.')
    if kind=='majors' and request.method=='POST' and Major.query.count()>=5:
        abort(422,description='Hệ thống giới hạn đúng 5 ngành/chương trình. Hãy chỉnh sửa cấu hình hiện có.')
    if kind=='edges':
        if 'relation' in data and data['relation'] not in ['BELONGS_TO','HAS_COURSE','PREREQUISITE_OF','TEACHES','COVERS','REQUIRES','HAS_LESSON','SUPPORTS_OUTCOME','RELATED_TO']:
            abort(400,description='Loại quan hệ không hợp lệ.')
        for key in ['weight','confidence']:
            if key in data and (not isinstance(data[key],(int,float)) or not 0<=data[key]<=1):
                abort(400,description='Trọng số và độ tin cậy phải nằm trong khoảng 0–1.')
        if request.method=='POST' and not str(data.get('provenance','')).strip():
            abort(400,description='Cần ghi rõ nguồn cho quan hệ.')
    if kind=='users' and data.get('role') not in [None,'student','admin']:
        abort(400,description='Vai trò không hợp lệ.')
    record = None
    if item_id is not None:
        record = db.get_or_404(model,int(item_id) if kind in ['users','edges'] else item_id)
    if kind=='users' and record and record.id==current_user.id and (request.method=='DELETE' or data.get('role')=='student'):
        abort(400,description='Không thể xóa hoặc hạ quyền tài khoản đang quản trị.')
    if request.method=='DELETE':
        # Explicit relational cleanup keeps the persisted graph consistent.
        if kind in ['careers','skills']:
            prefix = 'career:' if kind=='careers' else 'skill:'
            node_id = prefix+record.id
            KnowledgeEdge.query.filter((KnowledgeEdge.source_id==node_id)|(KnowledgeEdge.target_id==node_id)).delete()
            node = db.session.get(KnowledgeNode,node_id)
            if node:
                db.session.delete(node)
        db.session.delete(record)
    else:
        if request.method=='POST':
            if kind in ['users','courses']:
                abort(400,description='Tạo người dùng qua đăng ký; thêm môn qua đồng bộ dữ liệu.')
            record = model()
            db.session.add(record)
        for key,value in data.items():
            setattr(record,key,value)
        if kind in ['careers','skills']:
            from app.services.seed import add_node
            add_node(('career:' if kind=='careers' else 'skill:')+record.id,'Career' if kind=='careers' else 'Skill',record.name)
    db.session.add(AuditLog(user_id=current_user.id,action=request.method+':'+kind,detail={'id':item_id or data.get('id')}))
    try:
        db.session.flush()
        if kind=='edges' and not nx.is_directed_acyclic_graph(prerequisite_graph(load_graph())):
            raise ValueError('Quan hệ tạo chu trình tiên quyết.')
        db.session.commit()
    except (IntegrityError,ValueError,TypeError) as exc:
        db.session.rollback()
        abort(400,description='Không thể lưu: dữ liệu thiếu, sai kiểu, trùng khóa hoặc đang được tham chiếu.')
    return jsonify(data={'ok':True})

@api.patch('/admin/weights')
@admin_required
def weights():
    data = body()
    expected = {'skills','topics','graph','foundation','interests'}
    if set(data)!=expected or any(not isinstance(v,(int,float)) or not 0<=v<=1 for v in data.values()) or abs(sum(data.values())-1)>.0001:
        abort(400,description='Năm trọng số cần nằm trong khoảng 0–1 và có tổng bằng 1.')
    db.session.get(Settings,'weights').value = data
    db.session.add(AuditLog(user_id=current_user.id,action='weights',detail=data))
    db.session.commit()
    return jsonify(data=data)
