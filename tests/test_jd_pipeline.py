"""Checks for the JD dataset helpers (run: python -m pytest tests -q)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data" / "jd_dataset"))
from jd_common import SkillMatcher, classify_role, classify_seniority, clean_text, text_hash  # noqa: E402


def test_clean_text_removes_contact_details_and_company():
    raw = ("<p>Acme Analytics Sdn Bhd is hiring.</p><ul><li>SQL</li></ul>"
           "Email jobs@acme.example or call +60 3-1234 5678. See https://acme.example/jobs")
    t = clean_text(raw, companies={"Acme Analytics"})
    assert "@" not in t and "5678" not in t and "https" not in t
    assert "Acme" not in t and "[COMPANY]" in t
    assert "<" not in t and "- SQL" in t


def test_text_hash_ignores_whitespace_and_case():
    assert text_hash("Python  and\nSQL") == text_hash("python and sql")


def test_classify_role_and_seniority():
    assert classify_role("Junior SOC Analyst") == "CYBER_ANALYST"
    assert classify_role("Associate Cloud Engineer") == "CLOUD_ENGINEER"
    assert classify_role("Graduate Data Scientist") == "DATA_SCIENTIST"
    assert classify_role("BI Analyst") == "DATA_ANALYST"
    assert classify_role("Frontend Developer") == "WEB_DEV"
    assert classify_role("Backend Software Engineer") == "SOFTWARE_DEV"
    assert classify_role("Marketing Executive") is None
    assert classify_seniority("Senior Data Analyst") == "senior"
    assert classify_seniority("Data Analyst Intern") == "entry"
    assert classify_seniority("Junior Web Developer") == "junior"


def test_matcher_skips_ambiguous_and_prefers_longest():
    m = SkillMatcher()
    found = m.skills_in("Your CV should show you excel at teamwork; go the extra mile and rest well.")
    assert "Computer Vision" not in found and "Excel" not in found
    assert "Go" not in found and "REST API" not in found
    assert "Teamwork" in found
    found = m.skills_in("Experience with security monitoring, Microsoft Excel and C++ is required.")
    assert "Security Operations (SOC)" in found and "Monitoring & Observability" not in found
    assert "Excel" in found and "C++" in found
