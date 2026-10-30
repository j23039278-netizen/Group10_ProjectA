"""Checks for derive_evidence(): project, internship and certification evidence
derived from a student's records, no false evidence from generic words, stored
evidence kept, the proof flag, and the reason that names the source.

Run: python -m pytest nlp/tests/test_evidence.py -q   (no model needed)
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from nlp import config, derive_evidence, match_skills  # noqa: E402


def student(name, level="beginner", evidence=None, skill_id=None):
    return {"skill_id": skill_id, "skill_name": name, "proficiency_level": level,
            "evidence_type": evidence}


def project(title, description="", technologies=(), project_type="academic", proof_count=0):
    return {"project_title": title, "description": description, "technologies": list(technologies),
            "project_type": project_type, "proof_count": proof_count}


def cert(name, issuer=None, proof_count=0):
    return {"cert_name": name, "issuer": issuer, "proof_count": proof_count}


def evidence_of(skills, projects=(), certifications=(), **kw):
    """{skill_name: evidence_type} after derive_evidence()."""
    return {s["skill_name"]: s["evidence_type"]
            for s in derive_evidence(skills, projects, certifications, **kw)}


# ── Projects ──────────────────────────────────────────────────
def test_technologies_resolve_aliases():
    skills = [student("PostgreSQL"), student("Power BI"), student("Node.js"), student("Docker")]
    projects = [project("Shop", technologies=["Postgres", "PowerBI", "nodejs"])]
    assert evidence_of(skills, projects) == {
        "PostgreSQL": ["project"], "Power BI": ["project"], "Node.js": ["project"], "Docker": []}


def test_technologies_given_as_postgres_array_literal():
    skills = [student("SQL"), student("Excel")]
    projects = [{"project_title": "Report", "technologies": '{"SQL","Excel","ETL"}'}]
    assert evidence_of(skills, projects) == {"SQL": ["project"], "Excel": ["project"]}


def test_title_and_description_use_keyword_extraction():
    skills = [student("Kubernetes"), student("Docker"), student("Python"), student("Tableau")]
    projects = [project("Kubernetes Microservice Deployment",
                        "Containerised the services with Docker and Python 3 scripts.")]
    assert evidence_of(skills, projects) == {
        "Kubernetes": ["project"], "Docker": ["project"], "Python": ["project"], "Tableau": []}


def test_internship_project_gives_internship_not_project():
    skills = [student("SQL"), student("Excel")]
    projects = [project("Acme Data Internship", technologies=["SQL"], project_type="internship"),
                project("Budget", technologies=["Excel"], project_type="personal")]
    assert evidence_of(skills, projects) == {"SQL": ["internship"], "Excel": ["project"]}


def test_skill_on_several_records_gets_every_type_and_title():
    [sql] = derive_evidence(
        [student("SQL")],
        [project("Sales Dashboard", technologies=["SQL"]),
         project("Acme Internship", technologies=["SQL"], project_type="internship"),
         project("Churn Analysis", "Queried the warehouse with SQL.")],
        [cert("Meta Back-End Developer", "Meta")])
    assert sql["evidence_type"] == ["project", "internship"]
    assert sql["evidence_sources"] == {"project": ["Sales Dashboard", "Churn Analysis"],
                                       "internship": ["Acme Internship"]}


# ── Certifications ────────────────────────────────────────────
def test_certification_name_gives_skill_and_cloud_platform_implies_cloud_computing():
    skills = [student("AWS"), student("Cloud Computing"), student("Azure"), student("Python")]
    certs = [cert("AWS Certified Cloud Practitioner", "Amazon Web Services")]
    assert evidence_of(skills, (), certs) == {
        "AWS": ["certification"], "Cloud Computing": ["certification"], "Azure": [], "Python": []}


@pytest.mark.parametrize("name, issuer, evidenced", [
    ("PCEP – Certified Entry-Level Python Programmer", "Python Institute", {"Python"}),
    ("Splunk Core Certified User", "Splunk", {"Splunk"}),
    ("Microsoft Certified: Azure Fundamentals (AZ-900)", "Microsoft", {"Azure", "Cloud Computing"}),
    ("Google Cybersecurity Professional Certificate", "Google / Coursera", {"Cybersecurity"}),
    ("Cloud Practitioner", "Amazon Web Services", {"AWS", "Cloud Computing"}),   # issuer: name gives nothing
])
def test_certification_names(name, issuer, evidenced):
    skills = [student(s) for s in ("Python", "Splunk", "Azure", "Cloud Computing", "Cybersecurity", "AWS")]
    got = evidence_of(skills, (), [cert(name, issuer)])
    assert {s for s, ev in got.items() if ev} == evidenced


@pytest.mark.parametrize("name, issuer, not_evidenced", [
    ("Certified Kubernetes Administrator (CKA)", "CNCF / Linux Foundation", "Linux"),
    ("Machine Learning Specialization", "DeepLearning.AI / Coursera", "Deep Learning"),
    ("Tableau Desktop Specialist", "Tableau / Salesforce", "CRM Software"),
])
def test_issuer_is_not_read_when_the_name_gives_a_skill(name, issuer, not_evidenced):
    [s] = derive_evidence([student(not_evidenced)], (), [cert(name, issuer)])
    assert s["evidence_type"] == []


# ── No false evidence ─────────────────────────────────────────
@pytest.mark.parametrize("text", [
    "Worked in a team of four; I led the project and communicated with the client.",
    "Good communication and teamwork skills were needed. Presented the results.",
    "Excel at problem solving under pressure.",
    "A group project on data for a course.",
    "Used R and Go.",
])
def test_generic_words_give_no_evidence(text):
    skills = [student(s) for s in ("Communication", "Teamwork", "Leadership", "Presentation Skills",
                                   "Problem Solving", "Excel", "R", "Go", "Data Analysis")]
    got = evidence_of(skills, [project("Group Assignment", text)], [cert(text, text)])
    assert {s for s, ev in got.items() if ev} == set()


def test_soft_skill_listed_in_technologies_counts():
    skills = [student("Teamwork"), student("Communication")]
    projects = [project("CTF", "Good communication throughout.", technologies=["Teamwork"])]
    assert evidence_of(skills, projects) == {"Teamwork": ["project"], "Communication": []}


def test_similar_words_are_not_the_same_skill():
    skills = [student("Java"), student("SQL"), student("Linux")]
    projects = [project("Web App", "A JavaScript front end on MySQL.", technologies=["Kali Linux"])]
    assert evidence_of(skills, projects) == {"Java": [], "SQL": [], "Linux": []}


def test_skills_are_never_added():
    out = derive_evidence([student("SQL")], [project("Stack", technologies=["SQL", "Docker", "React"])])
    assert [s["skill_name"] for s in out] == ["SQL"]


# ── Stored evidence ───────────────────────────────────────────
@pytest.mark.parametrize("stored, expected", [
    (None, ["project"]),
    ([], ["project"]),
    (["coursework"], ["coursework", "project"]),
    ("{coursework,certification}", ["coursework", "certification", "project"]),
    (["project", "coursework"], ["project", "coursework"]),            # no duplicate type
])
def test_stored_evidence_is_kept_first(stored, expected):
    [s] = derive_evidence([student("SQL", evidence=stored)], [project("Report", technologies=["SQL"])])
    assert s["evidence_type"] == expected
    assert s["evidence_sources"] == {"project": ["Report"]}


def test_input_is_not_changed_and_other_fields_pass_through():
    original = {"skill_id": "id-1", "skill_name": "SQL", "proficiency_level": "beginner",
                "evidence_type": ["coursework"], "category": "Technical"}
    [out] = derive_evidence([original], [project("Report", technologies=["SQL"])])
    assert original["evidence_type"] == ["coursework"] and "evidence_sources" not in original
    assert out["skill_id"] == "id-1" and out["category"] == "Technical"


def test_no_records_leaves_evidence_unchanged():
    out = derive_evidence([student("SQL", evidence=["coursework"]), student("Excel")])
    assert [(s["evidence_type"], s["evidence_sources"]) for s in out] == [(["coursework"], {}), ([], {})]
    assert derive_evidence([], [project("Report", technologies=["SQL"])]) == []


def test_skill_outside_the_catalogue_matches_a_listed_technology():
    [s] = derive_evidence([student("Acme Workflow Studio")],
                          [project("Automation", technologies=["acme workflow studio"])])
    assert s["evidence_type"] == ["project"]


# ── Proof flag ────────────────────────────────────────────────
def test_require_proof_counts_only_records_with_a_file_or_link():
    skills = [student("SQL"), student("AWS")]
    projects = [project("No Proof", technologies=["SQL"])]
    certs = [cert("AWS Certified Cloud Practitioner", proof_count=1)]
    assert evidence_of(skills, projects, certs, require_proof=True) == {"SQL": [], "AWS": ["certification"]}
    assert evidence_of(skills, projects, certs, require_proof=False) == {
        "SQL": ["project"], "AWS": ["certification"]}


def test_require_proof_defaults_to_config(monkeypatch):
    skills, projects = [student("SQL")], [project("No Proof", technologies=["SQL"])]
    assert config.DERIVED_EVIDENCE_NEEDS_PROOF is False
    assert evidence_of(skills, projects) == {"SQL": ["project"]}
    monkeypatch.setattr(config, "DERIVED_EVIDENCE_NEEDS_PROOF", True)
    assert evidence_of(skills, projects) == {"SQL": []}


# ── With match_skills() ───────────────────────────────────────
def test_derived_evidence_makes_a_beginner_strong_and_names_the_source():
    skills = derive_evidence([student("Power BI"), student("Python", evidence=["coursework"])],
                             [project("Sales Dashboard", technologies=["Power BI"])])
    pbi, py = match_skills(skills, [{"skill_name": "Power BI", "importance": "required"},
                                    {"skill_name": "Python", "importance": "required"}], "keyword")
    assert pbi["match_status"] == "strong"
    assert pbi["reason"] == ("You list Power BI (beginner, with project evidence from Sales Dashboard), "
                             "which matches this skill, so this is marked Strong.")
    assert py["match_status"] == "developing"           # coursework only: rule C unchanged


def test_reason_names_at_most_two_titles():
    skills = derive_evidence([student("SQL")], [project(t, technologies=["SQL"]) for t in ("A", "B", "C", "D")])
    [r] = match_skills(skills, [{"skill_name": "SQL", "importance": "required"}], "keyword")
    assert "with project evidence from A, B and 2 more)" in r["reason"]


def test_reason_unchanged_without_evidence_sources():
    [r] = match_skills([student("SQL", "advanced", ["project"])],
                       [{"skill_name": "SQL", "importance": "required"}], "keyword")
    assert r["reason"].startswith("You list SQL (advanced, with project evidence), which")


def test_malformed_evidence_sources_is_a_value_error():
    bad = dict(student("SQL"), evidence_sources=["Sales Dashboard"])
    with pytest.raises(ValueError, match="evidence_sources"):
        match_skills([bad], [{"skill_name": "SQL", "importance": "required"}], "keyword")
