"""Regression tests for the extraction misjudgments listed on 16 October
(docs/SEAGAS_NLP_RemainingWork_16October.pdf, section 3.2).

One test (or parametrised group) per known case. The JD lines come from
data/jd_dataset/jd_dataset.csv unless noted. Run:

    python -m pytest nlp/tests/test_known_errors.py -q
    python -m pytest nlp/tests/test_known_errors.py -q -m "not model"
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from nlp import extract_skills, load_catalogue  # noqa: E402

model = pytest.mark.model

# Real Software Developer intern JD line, tested on the website on 16 October.
# It matched nothing; in that JD, hybrid added A/B Testing (from "testing") and
# Log Analysis (from "change logs") from other lines.
SOFTWARE_DEV_INTERN_LINE = "Basic knowledge of programming, databases and web-development concepts"


def names(text, method):
    return {s["skill_name"] for s in extract_skills(text, method=method)}


# ── 1. Generic words matched to specific skills (semantic step) ──
# A generic word alone names a field, not one skill. Each line is from the
# JD named on the right; the skill on the left was the wrong semantic hit.
GENERIC_WORD_CASES = [
    ("Assist in designing, developing, testing, and maintaining software applications",
     "A/B Testing"),                                                        # JD-SD-0001, 14 JDs
    ("develop in-demand capabilities in AI, Generative AI (GenAI), data, and analytics.",
     "Google Analytics"),                                                   # JD-SD-0004, 5 JDs
    ("Work with the Supabase backend, including the database, authentication and access control",
     "MySQL"),                                                              # JD-WD-0004, 4 JDs
    ("Basic knowledge in programming languages such as Java and JavaScript",
     "R"),                                                                  # JD-WD-0001, 7 JDs
    # Same pattern, found by scanning method_disagreements.csv:
    ("Support simple automation tasks using PowerShell or scripts to improve reporting",
     "Bash"),                                                               # JD-DA-0010
    ("inventory tracking and administration of hardware, software and infrastructure components",
     "Windows Server"),                                                     # JD-CE-0002
    ("System Administration: Provide support in managing the company's technology",
     "Windows Server"),                                                     # JD-CE-0009
    ("Requirements & Qualifications\n* Currently pursuing a degree",
     "Requirements Analysis"),                                              # JD-DA-0002 (a heading)
    ("and sell our own brands on Shopee, Lazada and TikTok Shop.",
     "Brand Management"),                                                   # JD-DA-0001
    ("Review and analyze telecommunication data from various markets to identify trends",
     "Market Research"),                                                    # JD-DA-0008
]


@model
@pytest.mark.parametrize("text, wrong", GENERIC_WORD_CASES, ids=[w for _, w in GENERIC_WORD_CASES])
def test_generic_word_is_not_a_specific_skill(text, wrong):
    assert wrong not in names(text, "semantic")
    assert wrong not in names(text, "hybrid")


@model
def test_generic_word_filter_keeps_real_skills():
    """The filter drops generic words alone, not phrases with a real term."""
    found = names("Basic knowledge in programming languages such as Java and JavaScript", "hybrid")
    assert {"Java", "JavaScript"} <= found
    assert "Log Analysis" in names("Analyse logs, endpoint telemetry, network data, and malware artifacts",
                                   "semantic")                              # JD-CY-0004
    assert "Data Visualisation" in names("Develop dashboards to track relevant metrics.", "semantic")


@model
def test_software_dev_intern_line():
    found = names(SOFTWARE_DEV_INTERN_LINE, "hybrid")
    assert not found & {"A/B Testing", "Log Analysis", "R", "MySQL"}
    # "web-development" must not pretend to be one framework or language
    assert not found & {"React", "JavaScript", "HTML", "CSS"}


# ── 2. Missing aliases (keyword) ──────────────────────────────
def test_ui_ux_alias():
    # JD-SD-0007
    text = "Turn business requirements and UI/UX flows into clean, secure, production-ready features"
    assert "UI/UX Design" in names(text, "keyword")


@pytest.mark.parametrize("text", [
    "Basic understanding of networking concepts (TCP/IP, DNS, firewalls, etc.).",   # JD-CY-0007
    "Configure and maintain the firewall.",
])
def test_firewall_alias(text):
    assert "Firewall Management" in names(text, "keyword")


def test_web_development_is_not_a_framework():
    text = "Knowledge of web development and web-development concepts"
    assert not names(text, "keyword") & {"React", "JavaScript", "HTML", "CSS"}


# ── 3. Aliases that are too broad (keyword) ───────────────────
@pytest.mark.parametrize("text", [
    "Support Data Science, Cloud Technologies, and Digital Transformation initiatives.",  # JD-DS-0007
    "Contribute to company-wide sustainability initiatives",
    "The initiative will roll out a new HR system across all branches.",
])
def test_initiative_as_a_project_is_not_self_motivation(text):
    assert "Self-Motivation" not in names(text, "keyword")


@pytest.mark.parametrize("text", [
    "Willingness to learn, take initiative and work collaboratively with the technical team",  # JD-CE-0001
    "Leadership potential: Demonstrates initiative and leadership qualities",            # JD-DS-0007
    "Takes initiative and delivers clear, practical solutions",                          # JD-WD-0002
    "Proactive, responsible and willing to take initiative.",                            # JD-SD-0013
])
def test_initiative_as_a_quality_is_self_motivation(text):
    assert "Self-Motivation" in names(text, "keyword")


@pytest.mark.parametrize("text", [
    "Continuous monitoring of security events across enterprise infrastructure using SIEM platforms",  # JD-CY-0006
    "General SIEM monitoring, analysis, content development, and maintenance.",          # JD-CY-0002
    "Assist in Security Event Monitoring - Work alongside SOC Analysts to track alerts",  # JD-CY-0010
    "Build monitoring tools: dashboards and alerts that catch problems early",          # JD-DA-0001
    "collect data, provide analytics, and enable intelligent monitoring and control.",  # JD-SD-0008
])
def test_monitoring_outside_it_operations_is_not_observability(text):
    assert "Monitoring & Observability" not in names(text, "keyword")


@pytest.mark.parametrize("text", [
    "Maintain monitoring and alerting and respond to alerts within agreed service targets",  # JD-CE-0003
    "Assist in monitoring infrastructure performance, reviewing alerts",                    # JD-CE-0001
    "Perform site performance monitoring to determine system performance bottlenecks.",     # JD-CE-0007
    "Proactive monitoring of supported cloud instances",                                    # JD-CE-0008
    "Practical exposure to AWS/cloud infrastructure, Docker, CI/CD and system monitoring.",  # JD-SD-0013
    "Monitoring - Prometheus, Grafana",                                                     # JD-CE-0008
])
def test_monitoring_in_it_operations_is_observability(text):
    assert "Monitoring & Observability" in names(text, "keyword")


def test_experimentation_needs_ab_testing_context():
    # JD-SD-0012; found by scanning method_disagreements.csv
    assert "A/B Testing" not in names(
        "Assist the engineering team with AI-related product development and experimentation.", "keyword")
    assert "A/B Testing" in names("Run online experimentation to improve conversion rates", "keyword")


def test_broad_aliases_are_context_dependent():
    cat = load_catalogue()
    assert cat.is_ambiguous("Initiative")
    assert cat.is_ambiguous("Monitoring")
    assert cat.is_ambiguous("Experimentation")


# ── 4. Word forms ─────────────────────────────────────────────
@pytest.mark.parametrize("text", [
    "Strong organizational skills and ability to work independently to meet deadlines",  # JD-DA-0005
    "Meets deadlines consistently.",
    "Experience meeting deadlines in a team.",
])
def test_meet_deadlines_keyword(text):
    assert "Time Management" in names(text, "keyword")


@model
def test_meeting_tight_deadlines_hybrid():
    assert "Time Management" in names("Able to work under pressure and meeting tight deadlines", "hybrid")


# ── 5. "change logs" (semantic) ───────────────────────────────
@model
def test_change_logs_is_not_log_analysis():
    # spaCy reads "change" as a verb, which leaves the bare noun "logs".
    found = names("Write documentation and change logs", "hybrid")
    assert "Documentation" in found
    assert "Log Analysis" not in found
