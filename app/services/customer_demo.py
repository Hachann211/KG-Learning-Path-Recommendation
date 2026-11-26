"""Explicitly provision synthetic presentation accounts; never run on ordinary startup."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import User, Course, Progress, RecommendationRun, LearningPath, AuditLog, KnowledgeEdge
from app.services.recommendation_service import recommend

DEMO_MARKER = 'customer-demo-v1'
MANIFEST = Path(__file__).resolve().parents[1] / 'static/data/demo-accounts.json'


def demo_accounts():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))['accounts']


def prepare_customer_demo(reset=False):
    """Add missing demo fixtures atomically. Reset only explicitly tagged demo records."""
    accounts = demo_accounts()
    # Check every identity before changing anything; do not take over existing accounts.
    for account in accounts:
        user = User.query.filter_by(email=account['email']).first()
        if user and (user.profile or {}).get('demo_seed') != DEMO_MARKER:
            raise ValueError(f"Email đã tồn tại ngoài bộ demo: {account['email']}")
    try:
        _enrich_demo_courses(reset)
        # Draft proposals let the presenter demonstrate moderation without altering recommendations.
        for source,target,weight in [('course:DEMO-API','skill:requirements',.35),('course:DEMO-DA','skill:ui',.4)]:
            proposal=KnowledgeEdge.query.filter_by(source_id=source,target_id=target,relation='TEACHES').first()
            if proposal is None:
                db.session.add(KnowledgeEdge(source_id=source,target_id=target,relation='TEACHES',weight=weight,
                    confidence=.65,approved=False,provenance=DEMO_MARKER+': đề xuất giả lập để trình diễn kiểm duyệt, chưa phải quan hệ đã xác nhận'))
            elif reset and proposal.provenance.startswith(DEMO_MARKER+':'):
                proposal.approved=False
                proposal.weight=weight
        result = []
        today = datetime.now(timezone.utc)
        for account in accounts:
            user = User.query.filter_by(email=account['email']).first()
            new_user = user is None
            if new_user:
                user = User(email=account['email'], name=account['name'], role=account['role'], profile={})
                db.session.add(user)
            if new_user or reset:
                user.name = account['name']
                user.role = account['role']
                user.password_hash = generate_password_hash(account['password'])
                user.profile = {'demo_seed': DEMO_MARKER, 'major_id': '7480201', 'cohort': 'K66 - 2024',
                    'career_id': 'backend' if account['key']=='user' else 'ai',
                    'skills': ['python','sql'], 'interests': ['api','data']}
                user.created_at = today - timedelta(days=45)
            db.session.flush()
            statuses = {'DEMO-PY':'completed', 'DEMO-DB':'completed', 'DEMO-DSA':'completed',
                'DEMO-OOP':'completed', 'DEMO-WEB':'in_progress', 'DEMO-ADB':'in_progress'} if account['key']=='user' else {}
            if reset:
                for progress in Progress.query.filter_by(user_id=user.id).all():
                    progress.status = statuses.get(progress.course_id,'not_started')
                    progress.updated_at = today
            for index, (cid, status) in enumerate(statuses.items()):
                progress = db.session.get(Progress, (user.id, cid))
                if progress is None:
                    progress = Progress(user_id=user.id, course_id=cid)
                    db.session.add(progress)
                    progress.status = status
                    progress.updated_at = today - timedelta(days=14-index*2)
                elif reset:
                    progress.status = status
                    progress.updated_at = today - timedelta(days=14-index*2)
            db.session.flush()
            completed = sorted(p.course_id for p in Progress.query.filter_by(user_id=user.id,status='completed').all())
            plans = [('backend','Backend Developer · Hành trình chính',1),
                ('analyst','Data Analyst · Khám phá dữ liệu',7),
                ('fullstack','Full-stack Developer · Mở rộng kỹ năng',14)] if account['key']=='user' else [('ai','Lộ trình tư vấn mẫu · Kỹ sư AI',3)]
            for career, name, days in plans:
                run_id = f"demo-{account['key']}-{career}"
                run = db.session.get(RecommendationRun, run_id)
                if run and run.user_id != user.id:
                    raise ValueError('Mã lộ trình demo đã thuộc tài khoản khác.')
                if run is None or reset:
                    inputs = {'curriculum_id':'DEMO-7480201-K66','career_id':career,'current_semester':3,
                        'completed':completed,'interests':['api','data'],'existing_skills':['python','sql']}
                    payload = recommend(**inputs)
                    if run is None:
                        run = RecommendationRun(id=run_id, user_id=user.id)
                        db.session.add(run)
                    run.inputs = inputs
                    run.result = payload
                    run.created_at = today - timedelta(days=days)
                db.session.flush()
                path = LearningPath.query.filter_by(user_id=user.id,run_id=run_id).first()
                if path is None:
                    path = LearningPath(user_id=user.id,run_id=run_id,name=name,created_at=today-timedelta(days=days))
                    db.session.add(path)
                elif reset:
                    path.name = name
                    path.created_at = today - timedelta(days=days)
            if not AuditLog.query.filter_by(user_id=user.id,action='prepare_customer_demo').first():
                db.session.add(AuditLog(user_id=user.id,action='prepare_customer_demo',
                    detail={'source':DEMO_MARKER,'note':'Tạo hồ sơ và lộ trình giả lập phục vụ trình diễn; không phải dữ liệu sinh viên thật.'}))
            result.append({'email':user.email,'role':user.role,'plans':len(plans),'progress':len(statuses)})
        db.session.commit()
        return result
    except Exception:
        db.session.rollback()
        raise


def _enrich_demo_courses(reset):
    content = json.loads((Path(__file__).with_name('customer_demo_content.json')).read_text(encoding='utf-8'))
    for code, data in content.items():
        course = db.session.get(Course, 'DEMO-'+code)
        if not course or course.source != 'DEMO':
            raise ValueError('Thiếu học phần minh họa: '+code)
        detail = course.detail or {}
        if detail.get('demo_content_version') == DEMO_MARKER and not reset:
            continue
        course.detail = {**detail, 'demo_content_version':DEMO_MARKER,
            'outcomes':data['outcomes'],
            'lessons':[{'title':title,'hours':hours} for title,hours in zip(data['lessons'],[9,12,15,9])],
            'source_note':'Đề cương và dự án minh họa phục vụ demo khách hàng; không phải đề cương chính thức của NEU.'}
