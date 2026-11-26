from itertools import combinations
import networkx as nx
import pytest
from app.extensions import db
from app.models import Curriculum, CurriculumCourse, Course, KnowledgeEdge, Settings
from app.services.graph_service import load_graph, neighbors, prerequisite_graph
from app.services.recommendation_service import recommend, RecommendationError

CID='DEMO-7480201-K66'

def test_ten_unique_of_fifteen(app):
    result = recommend(CID,'backend')
    items = result['items']
    chosen = [x for x in items if x['selected']]
    assert len(chosen)==10
    assert len({x['id'] for x in chosen})==10
    assert len([x for x in items if not x['selected']])==5
    assert all(CurriculumCourse.query.filter_by(curriculum_id=CID,course_id=x['id']).first() for x in chosen)
    assert result['combinations_evaluated']==3003
    assert result['credits']==30

def test_optimizer_matches_independent_exhaustive_objective(app):
    result = recommend(CID,'backend')
    graph=load_graph()
    requirements=neighbors(graph,'career:backend','REQUIRES')
    ids=[x['id'] for x in result['items']]
    scores={x['id']:x['score'] for x in result['items']}
    # Use unrounded scoring by reconstructing five components from original graph.
    weights=db.session.get(Settings,'weights').value
    total=sum(requirements.values())
    topics=neighbors(graph,'career:backend','RELATED_TO')
    prereqs=prerequisite_graph(graph)
    skill_sets={cid:neighbors(graph,'course:'+cid,'TEACHES') for cid in ids}
    full_scores={}
    for cid in ids:
        supports=skill_sets[cid]
        ss=sum(requirements.get(s,0)*w for s,w in supports.items())/total
        ts=sum(topics.get(s,0)*w for s,w in neighbors(graph,'course:'+cid,'COVERS').items())/sum(topics.values())
        relation=min(1,sum(requirements.get(s,0)*w for s,w in supports.items())/max(max(requirements.values())*2,1))
        foundation=.5 if cid in prereqs and list(prereqs.predecessors(cid)) else 1
        full_scores[cid]=weights['skills']*ss+weights['topics']*ts+weights['graph']*relation+weights['foundation']*foundation+weights['interests']*.5
    best=-1
    count=0
    for subset in combinations(sorted(ids),10):
        count+=1
        if any(p in ids and p not in subset for c in subset for p in (list(prereqs.predecessors(c)) if c in prereqs else [])):
            continue
        coverage=sum(w*max(skill_sets[c].get(s,0) for c in subset) for s,w in requirements.items())/total
        score=.65*coverage+.25*sum(full_scores[c] for c in subset)/10+.1
        best=max(best,score)
    assert count==3003
    assert result['objective']==pytest.approx(best*100,abs=.000001)

def test_personalization_and_determinism(app):
    a=recommend(CID,'backend')
    b=recommend(CID,'security')
    assert {x['id'] for x in a['items'] if x['selected']}!={x['id'] for x in b['items'] if x['selected']}
    assert a==recommend(CID,'backend')
    assert all(0<=i['score']<=100 for i in a['items'])

def test_completed_counted_and_prerequisites_ordered(app):
    result=recommend(CID,'backend',completed=['DEMO-UX'])
    assert any(x['id']=='DEMO-UX' and x['selected'] for x in result['items'])
    order=result['ordering']
    graph=prerequisite_graph(load_graph(),set(order))
    for before,after in graph.edges():
        assert order.index(before)<order.index(after)
        items={x['id']:x for x in result['items']}
        assert items[before]['proposed_semester']<items[after]['proposed_semester']

@pytest.mark.parametrize('count',[13,14])
def test_never_fabricates_missing_candidates(app,count):
    rows=CurriculumCourse.query.filter_by(curriculum_id=CID).all()
    for row in rows[count:]:db.session.delete(row)
    db.session.commit()
    with pytest.raises(RecommendationError,match=str(count)):
        recommend(CID,'backend')

def test_unverified_live_and_wrong_rule_rejected(app):
    c=db.session.get(Curriculum,CID)
    c.source='NEU'
    db.session.commit()
    with pytest.raises(RecommendationError,match='xác minh'):recommend(CID,'backend')
    c.source='DEMO';c.choose_count=8;db.session.commit()
    with pytest.raises(RecommendationError,match='10/15'):recommend(CID,'backend')

def test_cycle_detected_and_not_silently_ignored(app):
    db.session.add(KnowledgeEdge(source_id='course:DEMO-DSA',target_id='course:DEMO-PY',relation='PREREQUISITE_OF',provenance='test'))
    db.session.commit()
    with pytest.raises(RecommendationError,match='chu trình'):recommend(CID,'backend')

def test_graph_explanations_are_actual_edges(app):
    result=recommend(CID,'backend')
    graph=load_graph()
    for item in result['items']:
        for path in item['paths']:
            assert graph.has_edge(path['career'],path['skill'],'REQUIRES')
            assert graph.has_edge(path['course'],path['skill'],'TEACHES')
    course=next(x for x in result['items'] if x['id']=='DEMO-UX')
    assert course['paths']  # Shared web skill is real, not an invented career-course edge.

def test_no_path_does_not_fabricate_explanation(app):
    graph=load_graph()
    graph.remove_edges_from(list(graph.out_edges('course:DEMO-DB',keys=True)))
    result=recommend(CID,'backend',graph=graph)
    item=next(x for x in result['items'] if x['id']=='DEMO-DB')
    assert item['paths']==[]
    assert 'Chưa tìm thấy' in item['reason']

def test_skill_weight_changes_scores(app):
    before=recommend(CID,'backend')
    edge=KnowledgeEdge.query.filter_by(source_id='career:backend',target_id='skill:sql',relation='REQUIRES').one()
    edge.weight=.01;db.session.commit()
    after=recommend(CID,'backend')
    a=next(x for x in before['items'] if x['id']=='DEMO-DB')
    b=next(x for x in after['items'] if x['id']=='DEMO-DB')
    assert b['score']<a['score']

def test_all_five_programs_and_cohorts_stay_separate(app):
    for cid in ['DEMO-7480101-K65','DEMO-7480202-K66','DEMO-EP17-K67']:
        result=recommend(cid,'ai')
        assert result['curriculum_id']==cid
        assert len(result['ordering'])==10

def test_official_program_cannot_relabel_demo_courses(app):
    c=db.session.get(Curriculum,CID)
    c.source='NEU';c.verified=True;db.session.commit()
    with pytest.raises(RecommendationError,match='Không trộn'):
        recommend(CID,'backend')
