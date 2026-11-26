from app.extensions import db
from app.models import Course, Curriculum, SyncJob, KnowledgeNode, KnowledgeEdge
from app.services.neu_api_client import NEUApiClient

def sync_courses(query='lập trình', transport=None):
    client = NEUApiClient(transport=transport)
    try:
        subjects,source = client.search(query)
        # Dedup by business code. Search data has no curriculum membership or credits.
        dedup = {s['code']:s for s in subjects}
        for code, data in dedup.items():
            cid = 'NEU:'+code
            course = db.session.get(Course,cid)
            if course is None:
                course = Course(id=cid,code=code,source='NEU',name=data['name'])
                db.session.add(course)
            course.name = data['name']
            course.detail = {'cohorts':data['cohorts'],'api_source':source,'source_note':'Tên và mã môn từ API NEU. Tín chỉ, nhóm tự chọn, kỹ năng và ID đề cương chưa xác minh.'}
        job = SyncJob(status='success',source=source,records=len(dedup),detail={'attempts':client.attempts,'query':query,'note':'Chỉ đồng bộ danh mục; không suy diễn nhóm tự chọn.'})
        db.session.add(job)
        db.session.commit()
        return job
    except Exception as exc:
        db.session.rollback()
        job = SyncJob(status='failed',source='cache',records=0,detail={'error':str(exc),'attempts':client.attempts,'cache_preserved':True})
        db.session.add(job)
        db.session.commit()
        return job

def sync_curricula(cohort='K66 - 2024',transport=None):
    client=NEUApiClient(transport=transport)
    try:
        programs=client.curricula(cohort)
        for program in programs:
            cid='NEU:'+program['id']
            row=db.session.get(Curriculum,cid)
            if row is None:
                row=Curriculum(id=cid,major_id=program['major_id'],cohort=program['cohort'],source='NEU',verified=False)
                db.session.add(row)
            row.name=program['name']
            db.session.merge(KnowledgeNode(id='curriculum:'+cid,kind='Curriculum',label=program['name']+' · '+cohort,properties={'source':'NEU','slug':program['slug']}))
        job=SyncJob(status='success',source='primary',records=len(programs),detail={'cohort':cohort,'attempts':client.attempts,'note':'Chương trình chính thức; nhóm môn tự chọn chưa được xác minh.'})
        db.session.add(job);db.session.commit()
        return job
    except Exception as exc:
        db.session.rollback()
        job=SyncJob(status='failed',source='cache',records=0,detail={'error':str(exc),'cache_preserved':True,'attempts':client.attempts})
        db.session.add(job);db.session.commit()
        return job
