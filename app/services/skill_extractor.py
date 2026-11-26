import re
import unicodedata

def normalize(text):
    return ' '.join(unicodedata.normalize('NFC', text or '').casefold().split())

def extract_skills(text, skills):
    """Propose links with text evidence; never auto-approve inferred assertions."""
    text = normalize(text)
    proposals = []
    for skill in skills:
        for alias in [skill.name, *(skill.aliases or [])]:
            if re.search(r'(?<!\w)'+re.escape(normalize(alias))+r'(?!\w)',text):
                proposals.append({'skill_id':skill.id,'evidence':alias,'confidence':.7,'approved':False,'source':'keyword-extractor-v1'})
                break
    return proposals
