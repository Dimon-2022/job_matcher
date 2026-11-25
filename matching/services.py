import re
from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance

from functools import lru_cache

from sentence_transformers import util

MIN_SIMILARITY = 0.42

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
    jobs = Job.objects.filter(is_open=True).annotate(
        distance=CosineDistance("embedding", resume.embedding)
    ).prefetch_related("skills")

    matched = []
    for job in jobs:
        job.score = calculate_score(job, resume_skills)
        if job.score >= threshold:
            matched.append(job)

    return sorted(matched, key=lambda job: job.score, reverse=True)

CATEGORY_EXAMPLES = {
    # IT categories
    "backend": ["Backend developer", "Python Django developer", "Java Spring engineer", "Node.js backend engineer", "Go backend developer", "Softwareentwickler", "Java Backend Developer", "Cloud Developer",
"SAP ABAP Entwickler", "Protocol Software Engineer", "Embedded Software Engineer",
"Development Engineer Software",],
    "frontend": ["Frontend developer", "React developer", "Vue.js engineer", "Angular developer", "UI engineer TypeScript"],
    "fullstack": ["Full-stack developer", "Fullstack engineer", "React and Node.js developer", "Full stack Ruby on Rails engineer", "Full-stack web developer"],
    "mobile": ["iOS developer", "Android developer", "Flutter developer", "React Native engineer", "Mobile app developer"],
    "devops": ["DevOps engineer", "Site reliability engineer", "Platform engineer Kubernetes", "Cloud infrastructure engineer", "SRE"],
    "data_engineer": ["Data engineer", "ETL developer", "Big data engineer", "Data pipeline engineer"],
    "data_science": ["Data scientist", "Machine learning researcher", "Applied scientist statistics"],
    "ml_ai": ["Machine learning engineer", "AI engineer", "Deep learning engineer", "LLM engineer"],
    "data_analyst": ["Data analyst", "Business intelligence analyst", "SQL analyst", "Power BI developer"],
    "qa_automation": ["QA automation engineer", "Test automation engineer", "SDET", "QA engineer"],
    "security": ["Security engineer", "Penetration tester", "Cybersecurity analyst", "Application security engineer", "Incident Response Consultant", "Digital Forensics Analyst", "SOC Analyst",
],
    "support": ["IT support engineer", "Service desk engineer", "Helpdesk technician", "Technical support specialist", "IT-Systemadministrator", "Systemadministrator", "IT-Support Mitarbeiter",],
    "ui_ux": ["UX designer", "UI designer", "Product designer Figma"],
    "product": ["Product manager", "Technical product owner", "Product owner"],
    "project": ["Project manager", "Scrum master", "Delivery manager", "Agile coach", "Projektleitung IT", "Data & AI Project Lead", "IT-Projektmanager",],
    "other": ["Head of engineering", "Engineering manager", "CTO", "VP of engineering"],
    # Not IT
    "not_it_service": ["Customer service representative", "Call center agent", "Customer support agent", "Safety Inspector", "Fachkraft für Arbeitssicherheit", "Bauleiter",
"Laser Engineer", "Mechanical Engineer", "Construction Project Coordinator", "Bauprojektkoordination",],
    "not_it_sales": ["Sales representative", "Account executive", "Inside sales contractor", "Business development representative","Vertriebsberater", "Sales Consultant", "Account Manager",
"Marketing Manager", "Event Manager", "Marketing Manager Lead Generation", "Vertriebsberater Software", "Vertriebsmitarbeiter",
],
    "not_it_writing": ["Copywriter", "Content writer", "Freelance writer", "Content reviewer"],
    "not_it_health": ["Nurse", "Patient care advocate", "Medical assistant"],
    "not_it_admin": ["Office assistant", "Administrative assistant", "Data entry clerk", "Virtual assistant","Buchhalter", "Senior Buchhalter", "Accountant", "Controller", "Leitung Controlling", "HR Business Partner", "Personalreferent",],
    "not_it_annotation": ["Video annotation specialist", "AI trainer data labeling", "Image annotator"],
}


@lru_cache(maxsize=1)
def _example_vectors():
    labels = []
    texts = []
    for category, examples in CATEGORY_EXAMPLES.items():
        for example in examples:
            labels.append(category)
            texts.append(example)
    return labels, model.encode(texts)

KEYWORD_RULES = [
    ("fullstack", ["full-stack", "full stack", "fullstack"]),
    ("devops", ["devops", "site reliability"]),
    ("qa_automation", ["sdet", "test automation", "qa automation"]),
    ("data_engineer", ["data engineer"]),
    ("data_science", ["data scientist"]),
]


MIN_SIMILARITY = 0.5  # підберемо точніше на реальних даних нижче


def classify_job_with_score(title, description=""):
    lowered = title.lower()
    for category, keywords in KEYWORD_RULES:
        if any(keyword in lowered for keyword in keywords):
            return category, 1.0

    labels, vectors = _example_vectors()
    job_vector = model.encode(title)
    scores = util.cos_sim(job_vector, vectors)[0]
    best = int(scores.argmax())
    score = float(scores[best])

    if score < MIN_SIMILARITY:
        return "not_it_unknown", score
    return labels[best], score


def classify_job(title, description=""):
    category, _ = classify_job_with_score(title, description)
    return category