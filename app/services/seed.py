"""Versioned, explicitly illustrative dataset. No official curriculum claims."""
from app.extensions import db
from app.models import Major, Curriculum, Course, CurriculumCourse, Skill, Career, KnowledgeNode, KnowledgeEdge, Settings

MAJORS = [('7480101','Khoa học máy tính'), ('7480201','Công nghệ thông tin'), ('7480202','An toàn thông tin'), ('7480104','Hệ thống thông tin'), ('EP17','Kỹ thuật phần mềm')]
SKILLS = {'python':'Python', 'algorithms':'Thuật toán', 'sql':'SQL', 'database':'Thiết kế cơ sở dữ liệu', 'web':'Lập trình web', 'api':'REST API', 'oop':'Lập trình hướng đối tượng', 'security':'Bảo mật', 'network':'Mạng máy tính', 'linux':'Linux', 'ml':'Học máy', 'data':'Phân tích dữ liệu', 'ui':'Thiết kế giao diện', 'testing':'Kiểm thử', 'cloud':'Điện toán đám mây', 'git':'Git', 'requirements':'Phân tích yêu cầu', 'math':'Toán ứng dụng'}
# All content, skill assertions and prerequisite links below are authored DEMO fixtures.
COURSES = [
 ('PY','Lập trình Python','python',1,{'python':1,'algorithms':.5,'git':.4},[], 'Làm quen tư duy lập trình, kiểu dữ liệu, hàm và xử lý tệp với Python.'),
 ('DSA','Cấu trúc dữ liệu và giải thuật','algorithms',1,{'algorithms':1,'python':.5,'math':.3},['PY'],'Xây dựng nền tảng cấu trúc dữ liệu, phân tích độ phức tạp và giải quyết bài toán.'),
 ('DB','Cơ sở dữ liệu','database',1,{'sql':1,'database':.9,'data':.4},[],'Thiết kế mô hình dữ liệu quan hệ và thực hành truy vấn với ngôn ngữ SQL.'),
 ('OOP','Lập trình hướng đối tượng','oop',1,{'oop':1,'python':.7,'testing':.3},['PY'],'Mô hình hóa phần mềm với lớp, đối tượng, kế thừa và các nguyên lý thiết kế.'),
 ('WEB','Phát triển ứng dụng web','web',2,{'web':1,'api':.8,'ui':.6,'git':.7},['PY'],'Xây dựng ứng dụng web, xử lý yêu cầu HTTP và kết nối cơ sở dữ liệu.'),
 ('ADB','Hệ quản trị cơ sở dữ liệu','database',2,{'database':1,'sql':.9,'security':.4},['DB'],'Tối ưu truy vấn, quản lý giao dịch, chỉ mục và vận hành hệ quản trị dữ liệu.'),
 ('API','Thiết kế và phát triển API','api',2,{'api':1,'web':.8,'testing':.5,'security':.4},['WEB'],'Thiết kế REST API, xác thực, phân quyền và kiểm thử dịch vụ phía máy chủ.'),
 ('NET','Mạng máy tính','network',1,{'network':1,'security':.4,'linux':.3},[],'Tìm hiểu mô hình mạng, giao thức TCP/IP, định tuyến và truyền dữ liệu.'),
 ('OS','Hệ điều hành','linux',2,{'linux':1,'network':.5,'security':.3},['PY'],'Nắm vững tiến trình, bộ nhớ, hệ thống tệp và môi trường Linux.'),
 ('SEC','An toàn và bảo mật thông tin','security',3,{'security':1,'network':.7,'linux':.5},['NET'],'Phân tích nguy cơ, cơ chế bảo mật và nguyên tắc bảo vệ hệ thống thông tin.'),
 ('ML','Học máy và trí tuệ nhân tạo','ml',3,{'ml':1,'python':.9,'math':.8,'data':.7},['DSA'],'Khám phá các mô hình học có giám sát, đánh giá mô hình và ứng dụng thực tế.'),
 ('DA','Phân tích và trực quan dữ liệu','data',2,{'data':1,'sql':.7,'python':.8,'math':.5},['DB','PY'],'Làm sạch, phân tích và kể câu chuyện từ dữ liệu bằng biểu đồ trực quan.'),
 ('UX','Thiết kế giao diện người dùng','ui',2,{'ui':1,'web':.5,'requirements':.8},[],'Nghiên cứu người dùng, thiết kế tương tác và xây dựng nguyên mẫu giao diện.'),
 ('QA','Kiểm thử và đảm bảo chất lượng','testing',3,{'testing':1,'requirements':.7,'git':.6,'oop':.4},['OOP'],'Thiết kế ca kiểm thử, kiểm thử tự động và đảm bảo chất lượng phần mềm.'),
 ('CLOUD','Điện toán đám mây và DevOps','cloud',3,{'cloud':1,'linux':.9,'git':1,'network':.7,'api':.5},['OS','NET'],'Triển khai ứng dụng, tự động hóa quy trình và vận hành hạ tầng đám mây.'),
]
CAREERS = [
 ('backend','Lập trình viên Backend','Backend Developer','server',{'api':1,'sql':.95,'database':.9,'python':.9,'oop':.75,'web':.8,'security':.65,'testing':.6,'git':.5,'algorithms':.7}),
 ('frontend','Lập trình viên Frontend','Frontend Developer','panels-top-left',{'web':1,'ui':1,'api':.65,'git':.7,'testing':.7,'algorithms':.4,'requirements':.6}),
 ('fullstack','Lập trình viên Full-stack','Full-stack Developer','layers',{'web':1,'api':1,'ui':.85,'database':.9,'sql':.8,'python':.8,'git':.8,'testing':.7}),
 ('mobile','Lập trình viên di động','Mobile Developer','smartphone',{'oop':1,'ui':.9,'api':.9,'testing':.8,'algorithms':.7,'database':.5,'git':.6}),
 ('analyst','Chuyên viên phân tích dữ liệu','Data Analyst','chart-no-axes-combined',{'data':1,'sql':1,'math':.9,'python':.8,'database':.7,'requirements':.6,'ui':.4}),
 ('scientist','Nhà khoa học dữ liệu','Data Scientist','flask-conical',{'data':1,'ml':1,'math':1,'python':1,'sql':.8,'algorithms':.7}),
 ('ai','Kỹ sư trí tuệ nhân tạo','AI / Machine Learning Engineer','brain-circuit',{'ml':1,'math':1,'python':1,'algorithms':.9,'data':.85,'cloud':.6,'api':.5}),
 ('security','Kỹ sư an toàn thông tin','Cybersecurity Engineer','shield-check',{'security':1,'network':1,'linux':.9,'python':.6,'cloud':.5,'database':.4,'testing':.5}),
 ('devops','Kỹ sư DevOps','DevOps Engineer','cloud',{'cloud':1,'linux':1,'network':.9,'git':1,'security':.8,'api':.6,'python':.6}),
 ('tester','Kỹ sư kiểm thử phần mềm','Software Tester / QA','bug',{'testing':1,'requirements':1,'oop':.7,'api':.7,'web':.7,'git':.6,'sql':.5}),
 ('dba','Quản trị cơ sở dữ liệu','Database Administrator','database',{'sql':1,'database':1,'security':.8,'linux':.8,'cloud':.6,'data':.5}),
 ('business','Chuyên viên phân tích nghiệp vụ','Business Analyst','briefcase-business',{'requirements':1,'data':.9,'sql':.7,'ui':.8,'testing':.6,'database':.6}),
 ('system','Chuyên viên phân tích hệ thống','System Analyst','workflow',{'requirements':1,'database':.9,'network':.7,'oop':.8,'security':.7,'api':.7}),
 ('network','Kỹ sư mạng','Network Engineer','network',{'network':1,'linux':1,'security':.9,'cloud':.8,'python':.5}),
 ('designer','Nhà thiết kế UI/UX','UI/UX Designer','pen-tool',{'ui':1,'requirements':1,'web':.85,'testing':.65,'data':.4}),
]

def add_node(key, kind, label, **properties):
    db.session.merge(KnowledgeNode(id=key, kind=kind, label=label, properties=properties))

def add_edge(source, target, relation, weight=1, approved=True):
    db.session.add(KnowledgeEdge(source_id=source, target_id=target, relation=relation, weight=weight,
        provenance='demo-expert-v1: dữ liệu minh họa do tác giả cấu hình', approved=approved))

def seed_demo():
    if db.session.get(Settings, 'seed_version'):
        return
    for code, name in MAJORS:
        db.session.add(Major(id=code, name=name))
        add_node('major:'+code, 'Major', name)
    for key, name in SKILLS.items():
        db.session.add(Skill(id=key, name=name, aliases=[key, name]))
        add_node('skill:'+key, 'Skill', name)
        add_node('topic:'+key, 'Topic', name)
    for key, vi, en, icon, requirements in CAREERS:
        db.session.add(Career(id=key, name=vi, english=en, description=f'Phát triển năng lực chuyên môn và xây dựng sự nghiệp {vi.lower()}.', icon=icon))
        add_node('career:'+key, 'Career', vi)
    for code, name, theme, level, skills, prereqs, desc in COURSES:
        cid = 'DEMO-'+code
        db.session.add(Course(id=cid, code=cid, name=name, credits=3, semester=level+2, level=level,
            description=desc, source='DEMO', detail={'theme':theme, 'skills':skills,
            'prerequisites':['DEMO-'+p for p in prereqs], 'outcomes':[f'Vận dụng kiến thức {name.lower()} vào bài toán thực hành.', 'Phân tích vấn đề và trình bày giải pháp có cơ sở.'],
            'lessons':[{'title':'Tổng quan và các khái niệm nền tảng','hours':6}, {'title':'Phương pháp và kỹ thuật cốt lõi','hours':15}, {'title':'Thực hành và giải quyết bài toán','hours':18}, {'title':'Dự án và đánh giá kết quả','hours':6}],
            'source_note':'Đề cương minh họa, không phải đề cương chính thức của NEU.'}))
        add_node('course:'+cid, 'Course', name, course_id=cid)
        add_node('lesson:'+cid, 'Lesson', 'Thực hành '+name.lower())
        add_node('outcome:'+cid, 'LearningOutcome', 'Vận dụng '+name.lower())
    db.session.flush()
    for major, name in MAJORS:
        for cohort in ['K65 - 2023','K66 - 2024','K67 - 2025','K68 - 2026']:
            cid = f'DEMO-{major}-{cohort[:3]}'
            db.session.add(Curriculum(id=cid, major_id=major, cohort=cohort, name=name, source='DEMO', elective_count=15, choose_count=10, verified=False))
            add_node('curriculum:'+cid, 'Curriculum', name+' · '+cohort)
    db.session.flush()
    for curriculum in Curriculum.query.all():
        add_edge('curriculum:'+curriculum.id, 'major:'+curriculum.major_id, 'BELONGS_TO')
        for code, *_ in COURSES:
            cid = 'DEMO-'+code
            db.session.add(CurriculumCourse(curriculum_id=curriculum.id, course_id=cid))
            add_edge('curriculum:'+curriculum.id, 'course:'+cid, 'HAS_COURSE')
            add_edge('course:'+cid, 'curriculum:'+curriculum.id, 'BELONGS_TO')
    for key, vi, en, icon, requirements in CAREERS:
        for skill, weight in requirements.items():
            add_edge('career:'+key, 'skill:'+skill, 'REQUIRES', weight)
            add_edge('career:'+key, 'topic:'+skill, 'RELATED_TO', weight)
    for code, name, theme, level, skills, prereqs, desc in COURSES:
        node = 'course:DEMO-'+code
        for skill, weight in skills.items():
            add_edge(node, 'skill:'+skill, 'TEACHES', weight)
            add_edge(node, 'topic:'+skill, 'COVERS', weight)
        for pre in prereqs:
            add_edge('course:DEMO-'+pre, node, 'PREREQUISITE_OF')
        add_edge(node, 'lesson:DEMO-'+code, 'HAS_LESSON')
        add_edge(node, 'outcome:DEMO-'+code, 'SUPPORTS_OUTCOME')
    db.session.add(Settings(key='seed_version', value=1))
    db.session.add(Settings(key='weights', value={'skills':.45,'topics':.25,'graph':.15,'foundation':.1,'interests':.05}))
    db.session.commit()
