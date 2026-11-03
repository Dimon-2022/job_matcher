import re
from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance

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

def calculate_score(job, resume_skills):
    job_skills = set(job.skills.all())
    job.matched_skills = job_skills & resume_skills
    job.missing_skills = job_skills - resume_skills

    if job_skills:
        skill_score = len(job.matched_skills) / len(job_skills)
    else:
        skill_score = 0

    semantic = 1 - job.distance
    return round((0.6 * skill_score + 0.4 * semantic) * 100)

def find_matching_jobs(resume, threshold=60):
    from jobs.models import Job

    resume_skills = set(resume.skills.all())
    jobs = Job.objects.annotate(
        distance=CosineDistance("embedding", resume.embedding)
    ).prefetch_related("skills")

    matched = []
    for job in jobs:
        job.score = calculate_score(job, resume_skills)
        if job.score >= threshold:
            matched.append(job)

    return sorted(matched, key=lambda job: job.score, reverse=True)