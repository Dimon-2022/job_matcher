import re
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def get_embedding(text):
    return model.encode(text)

def extract_skills(text):
    from jobs.models import Skill

    if not text:
        return []

    found = []
    for skill in Skill.objects.all():
        pattern = r"(?<!\w)" + re.escape(skill.name) + r"(?!\w)"
        if re.search(pattern, text, re.IGNORECASE):
            found.append(skill)
    return found