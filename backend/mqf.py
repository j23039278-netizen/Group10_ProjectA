"""
SEAGAS — Link from our skills to the MQF learning-outcome clusters (MQA)

The Malaysian Qualifications Framework, 2nd edition (MQA circular 5/2024), describes
learning outcomes in five clusters (para. 46), the same five that COPPA 2nd edition
(2017) standard 1.1.4 asks every programme's learning outcomes to correspond to. The MQF
was reviewed in 2017 to align with the ASEAN Qualifications Reference Framework (AQRF),
so reporting skill gaps by these clusters lets a university read SEAGAS results in the
terms of its accreditation and of the regional framework (docs/JOB_READINESS_SCORE.md, section 4).

Each skill is linked to ONE cluster (or functional-work-skill focus), its main one. This is
our own preliminary mapping, not an MQA ruling. Skills not listed here (e.g. added by an
advisor) follow their category: Technical -> practical, AI / Digital -> digital,
Analytical -> cognitive, Soft -> personal and entrepreneurial.
"""

# Cluster ids in the order of the MQF (3a-3f are the six focuses of functional work skills)
CLUSTERS = [
    ("1",  "Knowledge and understanding"),
    ("2",  "Cognitive skills"),
    ("3a", "Functional work skills: practical skills"),
    ("3b", "Functional work skills: interpersonal skills"),
    ("3c", "Functional work skills: communication skills"),
    ("3d", "Functional work skills: digital skills"),
    ("3e", "Functional work skills: numeracy skills"),
    ("3f", "Functional work skills: leadership, autonomy and responsibility"),
    ("4",  "Personal and entrepreneurial skills"),
    ("5",  "Ethics and professionalism"),
]

BY_CATEGORY = {"Technical": "3a", "AI_Digital": "3d", "Analytical": "2", "Soft": "4"}

# Skills whose main cluster differs from their category's default
BY_SKILL = {
    # Knowledge and understanding: bodies of knowledge rather than tools
    "Data Structures & Algorithms": "1", "Object-Oriented Programming": "1", "Cryptography": "1",
    "Security Frameworks": "1", "OWASP Top 10": "1", "Accounting": "1", "Auditing": "1",
    "Taxation": "1", "Employment Law": "1", "Financial Reporting": "1",
    # Numeracy: working with numbers and data
    "Statistical Analysis": "3e", "Data Analysis": "3e", "Data Cleaning": "3e", "Data Mining": "3e",
    "Data Modelling": "3e", "Financial Analysis": "3e", "Financial Modelling": "3e",
    "Budgeting & Forecasting": "3e", "A/B Testing": "3e",
    # Soft skills by MQF focus
    "Communication": "3c", "Presentation Skills": "3c", "Stakeholder Communication": "3c",
    "Documentation": "3c", "Negotiation": "3c",
    "Teamwork": "3b", "Interpersonal Skills": "3b", "Customer Focus": "3b",
    "Leadership": "3f", "Project Management": "3f", "Agile / Scrum": "3f",
    "Organisational Skills": "3f", "Time Management": "3f",
    "Adaptability": "4", "Creativity": "4", "Self-Motivation": "4", "Attention to Detail": "4",
    # Ethics and professionalism
    "Responsible AI": "5",
}


def cluster_of(skill_name, category):
    return BY_SKILL.get(skill_name) or BY_CATEGORY.get(category, "3a")


def summarise(rows):
    """Per-skill rows (skill_name, category, gap/developing/strong counts) -> one row per
    cluster, in MQF order, with the skills that are most often a gap and every skill of the
    cluster (most gaps first) for the detail view"""
    out = {cid: {"cluster": cid, "name": name, "gap_count": 0, "developing_count": 0, "strong_count": 0,
                 "total": 0, "skills": []} for cid, name in CLUSTERS}
    for r in rows:
        c = out[cluster_of(r["skill_name"], r["category"])]
        for k in ("gap_count", "developing_count", "strong_count"):
            c[k] += r[k]
        c["total"] += r["gap_count"] + r["developing_count"] + r["strong_count"]
        c["skills"].append(r)
    result = []
    for cid, _ in CLUSTERS:
        c = out[cid]
        skills = sorted(c.pop("skills"), key=lambda s: (-s["gap_count"], s["skill_name"]))
        c["top_gaps"] = [{"skill_name": s["skill_name"], "gap_count": s["gap_count"]} for s in skills if s["gap_count"]][:3]
        c["skills"] = []
        for s in skills:
            total = s["gap_count"] + s["developing_count"] + s["strong_count"]
            c["skills"].append({"skill_id": str(s["skill_id"]) if s.get("skill_id") else None,
                                "skill_name": s["skill_name"], "category": s["category"],
                                "gap_count": s["gap_count"], "developing_count": s["developing_count"],
                                "strong_count": s["strong_count"], "total": total,
                                "gap_percentage": round(s["gap_count"] * 100.0 / total, 1) if total else None})
        c["gap_percentage"] = round(c["gap_count"] * 100.0 / c["total"], 1) if c["total"] else None
        result.append(c)
    return result
