from pydantic import BaseModel, Field, ConfigDict, ValidationError

class ObservedSubject(BaseModel):
    model_config = ConfigDict(extra='ignore')
    type: str
    name: str = Field(min_length=1, max_length=200)
    subjectCode: str = Field(min_length=1,max_length=50)
    curriculums: list[dict] = []

def primary_search_adapter(payload):
    if not isinstance(payload,list):
        raise ValueError('NEU search: expected the observed top-level JSON array.')
    results = []
    for item in payload:
        if not isinstance(item,dict) or item.get('type')!='subject':
            continue
        subject = ObservedSubject.model_validate(item)
        results.append({'code':subject.subjectCode,'name':subject.name,'cohorts':sorted({c['year'] for c in subject.curriculums if isinstance(c.get('year'),str)})})
    return results

def fallback_search_adapter(payload):
    # No verified fallback route/schema was provided by the remote API (404 at inspection).
    raise ValueError('Fallback schema unverified. Provide an observed adapter before importing this source.')

def primary_curricula_adapter(payload, cohort):
    """Observed /curriculum-curricula schema, distinct from /search/curriculum."""
    if not isinstance(payload,dict) or not isinstance(payload.get('data'),list):
        raise ValueError('Curriculum schema differs from the inspected response.')
    selected={'7480101','7480201','7480202','7480104','EP17'}
    results=[]
    for row in payload['data']:
        a=row.get('attributes',{})
        code=a.get('admissionCode')
        if code in selected and a.get('year')==cohort:
            results.append({'id':row['id'],'major_id':code,'name':a['name'],'cohort':a['year'],'slug':a.get('slug')})
    if len({r['major_id'] for r in results})!=5:
        raise ValueError('The response does not identify all five configured programs for this cohort.')
    return results
