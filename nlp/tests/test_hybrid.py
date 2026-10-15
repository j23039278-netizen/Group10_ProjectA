"""Checks for hybrid extraction (S2-02): keyword first, then coordinated skill
lists and semantic hits for what keyword missed.

Run all:          python -m pytest nlp/tests -q
Skip model tests: python -m pytest nlp/tests -q -m "not model"
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from nlp import config, extract_skills, extractor, load_catalogue  # noqa: E402
from nlp.tests.test_keyword import BRIEF_EXPECTED, sample_jds  # noqa: E402

model = pytest.mark.model
BRIEF = ROOT / "nlp" / "tests" / "fixtures" / "brief_example_jd.txt"


def hybrid(text, **kw):
    return extract_skills(text, method="hybrid", **kw)


def keyword(text, **kw):
    return extract_skills(text, method="keyword", **kw)


def hit(text, phrase, skill, score, nth=0):
    """A fake semantic hit on the nth occurrence of `phrase` in `text`."""
    start = -1
    for _ in range(nth + 1):
        start = text.index(phrase, start + 1)
    return extractor._Hit(start, start + len(phrase), skill, "semantic", score)


@pytest.fixture
def semantic_hits(monkeypatch):
    """Replace the Level 2 step with fixed hits (no model needed)."""
    hits = []
    monkeypatch.setattr(extractor, "_semantic_hits", lambda text, catalogue: list(hits))
    return hits


# ── Merge rules (no model) ────────────────────────────────────
def test_semantic_adds_only_new_skills_outside_keyword_spans(semantic_hits):
    text = "Python and SQL required. You will build interactive dashboards for managers."
    semantic_hits += [
        hit(text, "Python", "Python", 0.90),                                 # keyword found it
        hit(text, "SQL required", "Data Analysis", 0.70),                    # overlaps "SQL"
        hit(text, "interactive dashboards", "Data Visualisation", 0.75),     # new skill
    ]
    found = hybrid(text)
    assert [(s["skill_name"], s["method"]) for s in found] == [
        ("Python", "keyword"), ("SQL", "keyword"), ("Data Visualisation", "semantic")]
    viz = found[-1]
    assert viz["raw_skill_text"] == "interactive dashboards"
    assert viz["confidence_score"] == 0.75


def test_semantic_skill_keeps_first_span_and_best_score(semantic_hits):
    text = "Build dashboards. Present charts to the team. Build dashboards weekly."
    semantic_hits += [hit(text, "Build dashboards", "Data Visualisation", 0.65),
                      hit(text, "Build dashboards", "Data Visualisation", 0.80, nth=1)]
    [viz] = hybrid(text)
    assert (viz["start_char"], viz["confidence_score"]) == (0, 0.80)


def test_keyword_results_are_unchanged(semantic_hits):
    text = ("Strong interpersonal and communication skills. Interpersonal Skills matter, "
            "and so do SQL and PowerBI.")
    semantic_hits.append(hit(text, "SQL", "SQL", 0.99))
    by_kw = {s["skill_name"]: s for s in keyword(text)}
    by_hy = {s["skill_name"]: s for s in hybrid(text)}
    # The list item "interpersonal" names a skill keyword already found later on:
    # the keyword result (span, confidence) wins.
    for name, s in by_kw.items():
        assert by_hy[name] == s


def test_results_are_ordered_and_unique(semantic_hits):
    text = "Communicate clearly. Python, R and SQL. Tell stories with data."
    semantic_hits += [hit(text, "Tell stories with data", "Data Visualisation", 0.7),
                      hit(text, "Communicate clearly", "Communication", 0.8)]
    found = hybrid(text)
    starts = [s["start_char"] for s in found]
    assert starts == sorted(starts)
    assert len({s["skill_name"] for s in found}) == len(found)
    assert [s["skill_name"] for s in found] == ["Communication", "Python", "R", "SQL", "Data Visualisation"]


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_blank_text_returns_empty_list(text):
    assert hybrid(text) == []


# ── Coordinated skill lists (no model) ────────────────────────
def list_items(text):
    cat = load_catalogue()
    return [(text[s:e], phrase) for s, e, phrase in
            extractor._list_items(text, extractor._keyword_hits(text, cat), cat)]


@pytest.mark.parametrize("text, expected", [
    ("Candidates should have good analytical, communication and problem-solving skills.",
     [("analytical", "analytical skills")]),
    ("* Strong analytical and troubleshooting skills", [("analytical", "analytical skills")]),
    ("Strong analytical and technical problem-solving abilities",
     [("analytical", "analytical abilities")]),
    ("Analytical and problem-solving mindset", [("Analytical", "Analytical mindset")]),
    ("Must have strong analytical, problem-solving, good communication and stakeholder management skills",
     [("analytical", "analytical skills")]),
    ("Strong organizational and time management skills",
     [("organizational", "organizational skills")]),
])
def test_list_items_found(text, expected):
    assert list_items(text) == expected


@pytest.mark.parametrize("text", [
    "Good communication skills.",                          # one item, no list
    "Python, R and SQL skills",                            # every item is a keyword hit
    "Creative and curious thinkers with good people sense",  # no head noun after the list
    "Strong technical and communication skills",           # "technical" asks for no skill
    "Bring curiosity and passion skills",                  # no item is a keyword hit
    "Tools: SQL; analytical and creative skills",          # a list never crosses ";" (or ".")
])
def test_no_list_items(text):
    assert list_items(text) == []


def test_list_item_that_is_a_catalogue_term_needs_no_model(semantic_hits):
    found = {s["skill_name"]: s for s in hybrid("Good interpersonal and communication skills")}
    assert found["Interpersonal Skills"]["method"] == "keyword"
    assert found["Interpersonal Skills"]["raw_skill_text"] == "interpersonal"
    assert found["Interpersonal Skills"]["confidence_score"] == 1.0


def test_list_item_settings():
    assert config.LIST_ITEM_TEXT_MODE in ("name_aliases", "name_aliases_max", "name_description")
    assert config.MATCH_THRESHOLD <= config.LIST_ITEM_THRESHOLD < 1.0


# ── Model ─────────────────────────────────────────────────────
@model
def test_brief_example_hybrid_finds_all_seven(capsys):
    """POC004 brief, section 6: L1 finds 6/7 (test_keyword, xfail), hybrid 7/7."""
    text = BRIEF.read_text(encoding="utf-8")
    cat = load_catalogue()
    expected = [cat.lookup(n) for n in BRIEF_EXPECTED]
    found = {s["skill_name"]: s for s in hybrid(text)}
    l1 = {s["skill_name"] for s in keyword(text)}
    with capsys.disabled():
        print(f"\nbrief example: keyword {sum(n in l1 for n in expected)}/{len(expected)}, "
              f"hybrid {sum(n in found for n in expected)}/{len(expected)}; "
              + ", ".join(f"{n} ({found[n]['method']}, {found[n]['raw_skill_text']!r})"
                          for n in expected if n in found))
    assert set(expected) <= set(found)
    assert found["Critical Thinking"]["raw_skill_text"] == "analytical"


def all_jds():
    return [("brief", BRIEF.read_text(encoding="utf-8"))] + sample_jds()


@model
@pytest.mark.parametrize("ref, text", all_jds(), ids=[ref for ref, _ in all_jds()])
def test_hybrid_contract_on_sample_jds(ref, text):
    cat = load_catalogue()
    found = hybrid(text)
    by_kw = {s["skill_name"]: s for s in keyword(text)}
    by_hy = {s["skill_name"]: s for s in found}
    # finds at least what keyword finds, with the same keyword result
    assert set(by_kw) <= set(by_hy), f"{ref}: lost {set(by_kw) - set(by_hy)}"
    assert all(by_hy[n] == s for n, s in by_kw.items())
    # one row per skill, ordered, offsets match, method fits jd_extracted_skills
    assert [s["start_char"] for s in found] == sorted(s["start_char"] for s in found)
    assert len(by_hy) == len(found)
    keyword_spans = [(h.start, h.end) for h in extractor._keyword_hits(text, cat)]
    keyword_spans += [(s["start_char"], s["end_char"]) for s in found if s["method"] == "keyword"]
    for s in found:
        assert s["method"] in ("keyword", "semantic")
        assert text[s["start_char"]:s["end_char"]] == s["raw_skill_text"]
        assert 0.0 < s["confidence_score"] <= 1.0
        if s["method"] == "semantic":
            assert all(s["end_char"] <= a or s["start_char"] >= b for a, b in keyword_spans), \
                f"{ref}: semantic {s['skill_name']} overlaps a keyword span"


@model
@pytest.mark.parametrize("text, skill, expected", [
    ("Good analytical and problem-solving skills", "Critical Thinking", True),
    ("Strong analytical and technical problem-solving abilities", "Critical Thinking", True),
    ("Strong interpersonal and communication abilities", "Interpersonal Skills", True),
    # 0.676 with name_aliases_max: below LIST_ITEM_THRESHOLD, see THRESHOLDS.md
    ("Strong organizational and time management skills", "Interpersonal Skills", False),
])
def test_list_items_with_the_model(text, skill, expected):
    found = {s["skill_name"]: s for s in hybrid(text)}
    assert (skill in found) is expected
    if expected:
        assert found[skill]["method"] in ("keyword", "semantic")
