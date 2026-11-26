from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db

def now():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student', nullable=False)
    profile = db.Column(db.JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime, default=now)

class Major(db.Model):
    __tablename__ = 'majors'
    id = db.Column(db.String(30), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)

class Curriculum(db.Model):
    __tablename__ = 'curricula'
    id = db.Column(db.String(80), primary_key=True)
    major_id = db.Column(db.String(30), db.ForeignKey('majors.id'), nullable=False, index=True)
    cohort = db.Column(db.String(30), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    source = db.Column(db.String(30), nullable=False)
    elective_count = db.Column(db.Integer)
    choose_count = db.Column(db.Integer)
    verified = db.Column(db.Boolean, default=False)
    __table_args__ = (db.UniqueConstraint('major_id', 'cohort', 'source'),)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.String(80), primary_key=True)
    code = db.Column(db.String(50), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    credits = db.Column(db.Integer)
    semester = db.Column(db.Integer)
    level = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)
    syllabus_id = db.Column(db.String(100))
    source = db.Column(db.String(30), nullable=False)
    detail = db.Column(db.JSON, default=dict)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

class CurriculumCourse(db.Model):
    __tablename__ = 'curriculum_courses'
    curriculum_id = db.Column(db.String(80), db.ForeignKey('curricula.id'), primary_key=True)
    course_id = db.Column(db.String(80), db.ForeignKey('courses.id'), primary_key=True)
    group = db.Column(db.String(40), default='elective')

class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.String(60), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    aliases = db.Column(db.JSON, default=list)

class Career(db.Model):
    __tablename__ = 'careers'
    id = db.Column(db.String(60), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    english = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(40), default='code-xml')

class KnowledgeNode(db.Model):
    __tablename__ = 'knowledge_nodes'
    id = db.Column(db.String(160), primary_key=True)
    kind = db.Column(db.String(30), nullable=False, index=True)
    label = db.Column(db.String(200), nullable=False)
    properties = db.Column(db.JSON, default=dict)

class KnowledgeEdge(db.Model):
    __tablename__ = 'knowledge_edges'
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String(160), db.ForeignKey('knowledge_nodes.id'), nullable=False, index=True)
    target_id = db.Column(db.String(160), db.ForeignKey('knowledge_nodes.id'), nullable=False, index=True)
    relation = db.Column(db.String(40), nullable=False)
    weight = db.Column(db.Float, default=1)
    provenance = db.Column(db.String(200), nullable=False)
    confidence = db.Column(db.Float, default=1)
    approved = db.Column(db.Boolean, default=True)
    __table_args__ = (db.UniqueConstraint('source_id', 'target_id', 'relation'),)

class RecommendationRun(db.Model):
    __tablename__ = 'recommendation_runs'
    id = db.Column(db.String(40), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    inputs = db.Column(db.JSON, nullable=False)
    result = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=now)

class LearningPath(db.Model):
    __tablename__ = 'learning_paths'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    run_id = db.Column(db.String(40), db.ForeignKey('recommendation_runs.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=now)

class Progress(db.Model):
    __tablename__ = 'student_course_progress'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    course_id = db.Column(db.String(80), db.ForeignKey('courses.id'), primary_key=True)
    status = db.Column(db.String(20), default='not_started')
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

class SyncJob(db.Model):
    __tablename__ = 'sync_jobs'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(30), nullable=False)
    source = db.Column(db.String(100))
    records = db.Column(db.Integer, default=0)
    detail = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=now)

class AuditLog(db.Model):
    __tablename__ = 'admin_audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(120), nullable=False)
    detail = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=now)

class Settings(db.Model):
    __tablename__ = 'settings'
    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.JSON, nullable=False)
