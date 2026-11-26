from itertools import combinations
import networkx as nx
from app.extensions import db
from app.models import Curriculum, CurriculumCourse, Course, Career, Settings
from app.services.graph_service import load_graph, neighbors, prerequisite_graph, explanation_paths

class RecommendationError(ValueError):
    pass

def course_dict(course):
    return {'id':course.id,'code':course.code,'name':course.name,'credits':course.credits,
        'semester':course.semester,'level':course.level,'description':course.description,
        'source':course.source,'syllabus_id':course.syllabus_id,'detail':course.detail or {}}

def recommend(curriculum_id, career_id, completed=None, interests=None, current_semester=3, existing_skills=None, graph=None):
    curriculum = db.session.get(Curriculum,curriculum_id)
    career = db.session.get(Career,career_id)
    if not curriculum or not career:
        raise RecommendationError('Ngành, khóa học hoặc nghề nghiệp không hợp lệ.')
    if curriculum.source!='DEMO' and not curriculum.verified:
        raise RecommendationError('Chưa xác minh nhóm học phần tự chọn của chương trình chính thức. Vui lòng kiểm duyệt dữ liệu trước khi tạo lộ trình.')
    if curriculum.elective_count!=15 or curriculum.choose_count!=10:
        raise RecommendationError('Chương trình này chưa được xác nhận áp dụng quy tắc chọn 10/15 môn.')
    courses = Course.query.join(CurriculumCourse).filter(CurriculumCourse.curriculum_id==curriculum_id, CurriculumCourse.group=='elective').order_by(Course.id).all()
    if len(courses)!=15:
        raise RecommendationError(f'Nhóm tự chọn có {len(courses)} môn; cần đúng 15 môn đã xác minh. Không bổ sung môn ngoài nhóm.')
    if any(c.source!=curriculum.source for c in courses):
        raise RecommendationError('Nguồn môn học không khớp chương trình. Không trộn dữ liệu NEU và dữ liệu minh họa.')
    ids = {c.id for c in courses}
    completed = set(completed or [])
    fixed = completed & ids
    if len(fixed)>10:
        raise RecommendationError('Bạn đã hoàn thành hơn 10 môn trong nhóm. Cần kiểm tra quy chế lựa chọn trước khi lập lộ trình.')
    graph = graph if graph is not None else load_graph()
    prerequisites = prerequisite_graph(graph)
    if not nx.is_directed_acyclic_graph(prerequisites):
        raise RecommendationError('Phát hiện chu trình môn tiên quyết. Cần quản trị viên kiểm tra dữ liệu.')
    req = neighbors(graph,'career:'+career_id,'REQUIRES')
    if not req:
        raise RecommendationError('Nghề nghiệp chưa có kỹ năng đã kiểm duyệt trong đồ thị.')
    denominator = sum(req.values())
    skill_sets = {c.id:neighbors(graph,'course:'+c.id,'TEACHES') for c in courses}
    if curriculum.source!='DEMO' and any(not skill_sets[c.id] for c in courses):
        raise RecommendationError('Một số học phần chưa có ánh xạ kỹ năng đã kiểm duyệt. Cần bổ sung bằng chứng từ đề cương trước khi gợi ý chính thức.')
    topic_req = neighbors(graph,'career:'+career_id,'RELATED_TO')
    weights = db.session.get(Settings,'weights').value
    interests = set(interests or [])
    existing_skills = {'skill:'+s for s in (existing_skills or [])}
    scores, components, paths = {},{},{}
    for course in courses:
        skills = skill_sets[course.id]
        skill_relevance = sum(req[k]*v for k,v in skills.items() if k in req)/denominator
        topics = neighbors(graph,'course:'+course.id,'COVERS')
        topic_relevance = sum(topic_req.get(k,0)*v for k,v in topics.items())/max(sum(topic_req.values()),1)
        paths[course.id] = explanation_paths(graph,career_id,course.id)
        relation = min(1, sum(p['weight'] for p in paths[course.id])/max(max(req.values())*2,1))
        pre = list(prerequisites.predecessors(course.id)) if course.id in prerequisites else []
        foundation = 1 if all(p in completed for p in pre) else .5
        personal = sum(1 for s in skills if s.removeprefix('skill:') in interests)/max(len(skills),1) if interests else .5
        # Existing skills encourage complementary courses without pretending they are course completion.
        if existing_skills and skills:
            personal = (personal + sum(s not in existing_skills for s in skills)/len(skills))/2
        comp = dict(skills=skill_relevance,topics=topic_relevance,graph=relation,foundation=foundation,interests=personal)
        scores[course.id] = sum(weights[k]*v for k,v in comp.items())*100
        components[course.id] = {k:round(v*100,2) for k,v in comp.items()}

    def objective(selected):
        coverage = sum(weight*max((skill_sets[c].get(skill,0) for c in selected), default=0) for skill,weight in req.items())/denominator
        relevance = sum(scores[c] for c in selected)/len(selected)/100
        fulfilled, total = 0,0
        for c in selected:
            for pre in prerequisites.predecessors(c) if c in prerequisites else []:
                total += 1
                fulfilled += pre in selected or pre in completed
        coherence = fulfilled/total if total else 1
        return .65*coverage+.25*relevance+.10*coherence, coverage

    best, best_value, best_coverage, examined, feasible = None,-1,0,0,0
    for selected in combinations(sorted(ids),10):
        examined += 1
        subset = set(selected)
        if not fixed.issubset(subset):
            continue
        # Elective prerequisite closure; external compulsory prerequisites are scheduled separately.
        if any(pre in ids and pre not in subset and pre not in completed for c in selected for pre in (list(prerequisites.predecessors(c)) if c in prerequisites else [])):
            continue
        feasible += 1
        value, coverage = objective(selected)
        if value>best_value+1e-12:
            best,best_value,best_coverage = selected,value,coverage
    if best is None:
        raise RecommendationError('Không tồn tại tổ hợp 10 môn đáp ứng các ràng buộc tiên quyết và môn đã học.')
    ordering = list(nx.lexicographical_topological_sort(prerequisite_graph(graph,set(best))))
    semesters = {}
    for cid in ordering:
        course = next(c for c in courses if c.id==cid)
        pre = list(prerequisites.predecessors(cid)) if cid in prerequisites else []
        semesters[cid] = max([max(current_semester,course.semester or current_semester)] + [semesters[p]+1 for p in pre if p in semesters and p not in completed])
    items = []
    for course in sorted(courses,key=lambda c:(-scores[c.id],c.id)):
        pre = list(prerequisites.predecessors(course.id)) if course.id in prerequisites else []
        matched = [p['labels'][1] for p in paths[course.id]]
        items.append({**course_dict(course),'score':round(scores[course.id],1),'components':components[course.id],
            'selected':course.id in best,'paths':paths[course.id],'skills':[graph.nodes[s]['label'] for s in skill_sets[course.id]],
            'prerequisites':pre,'missing_prerequisites':[p for p in pre if p not in completed],
            'ready':all(p in completed for p in pre),'proposed_semester':semesters.get(course.id),
            'reason':f'Học phần phát triển {", ".join(matched[:3])}, phù hợp với định hướng {career.name.lower()}.' if matched else 'Chưa tìm thấy quan hệ kỹ năng trực tiếp với nghề nghiệp trong đồ thị.',
            'exclusion_reason':None if course.id in best else 'Tổ hợp được chọn có mức bao phủ kỹ năng và tính liên tục tốt hơn; môn này chưa tối ưu cho mục tiêu hiện tại.'})
    return {'curriculum_id':curriculum_id,'curriculum_name':curriculum.name,'cohort':curriculum.cohort,
        'career_id':career.id,'career_name':career.name,'career_english':career.english,'source':curriculum.source,
        'candidate_count':15,'selected_count':10,'coverage':round(best_coverage*100,1),
        'credits':sum(c.credits or 0 for c in courses if c.id in best),'objective':round(best_value*100,6),
        'combinations_evaluated':examined,'feasible_combinations':feasible,'ordering':ordering,
        'items':items,'weights':weights,'completed':sorted(completed),
        'skills':[{'id':s.removeprefix('skill:'),'name':graph.nodes[s]['label'],'weight':w,
            'coverage':round(max(skill_sets[c].get(s,0) for c in best)*100)} for s,w in sorted(req.items(),key=lambda p:-p[1])]}
