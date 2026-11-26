import networkx as nx
from app.models import KnowledgeNode, KnowledgeEdge

def load_graph(approved_only=True):
    graph = nx.MultiDiGraph()
    for node in KnowledgeNode.query.all():
        graph.add_node(node.id, kind=node.kind, label=node.label, **(node.properties or {}))
    query = KnowledgeEdge.query
    if approved_only:
        query = query.filter_by(approved=True)
    for edge in query.all():
        graph.add_edge(edge.source_id, edge.target_id, key=edge.relation, id=edge.id,
            relation=edge.relation, weight=edge.weight, provenance=edge.provenance,
            confidence=edge.confidence, approved=edge.approved)
    return graph

def neighbors(graph, node, relation):
    if node not in graph:
        return {}
    return {target: props.get('weight',1) for _,target,_,props in graph.out_edges(node,keys=True,data=True) if props['relation']==relation}

def prerequisite_graph(graph, ids=None):
    g = nx.DiGraph()
    if ids is not None:
        g.add_nodes_from(ids)
    for source,target,props in graph.edges(data=True):
        if props['relation']=='PREREQUISITE_OF':
            a,b = source.removeprefix('course:'), target.removeprefix('course:')
            if ids is None or a in ids and b in ids:
                g.add_edge(a,b)
    return g

def serialize_graph(graph):
    return {'nodes':[{'data':{'id':key, **data}} for key,data in graph.nodes(data=True)],
        'edges':[{'data':{'id':'e'+str(data['id']), 'source':source, 'target':target, **data}} for source,target,data in graph.edges(data=True)]}

def explanation_paths(graph, career_id, course_id):
    requirements = neighbors(graph, 'career:'+career_id, 'REQUIRES')
    teaches = neighbors(graph, 'course:'+course_id, 'TEACHES')
    return [{'career':'career:'+career_id, 'skill':skill, 'course':'course:'+course_id,
        'labels':[graph.nodes['career:'+career_id]['label'],graph.nodes[skill]['label'],graph.nodes['course:'+course_id]['label']],
        'relations':['REQUIRES','TEACHES'], 'weight':round(requirements[skill]*teaches[skill],3)}
        for skill in sorted(requirements.keys() & teaches.keys(), key=lambda k:(-requirements[k]*teaches[k],k))]
