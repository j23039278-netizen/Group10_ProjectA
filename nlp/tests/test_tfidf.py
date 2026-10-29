"""Checks for TF-IDF extraction (method="tfidf", for the method comparison).

TF-IDF needs spaCy (candidate phrases) and scikit-learn, but not the Sentence
Transformers model, so these tests are not marked `model` and also run with

    python -m pytest nlp/tests -q -m "not model"

Every test that extracts replaces nlp.model.get_model() with a function that
fails, so a model load (or download) would fail the test.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
pytest.importorskip("spacy")
pytest.importorskip("en_core_web_sm")
pytest.importorskip("sklearn")

import nlp  # noqa: E402
from nlp import config, extract_skills, load_catalogue, match_skills  # noqa: E402
from nlp import model as nlp_model  # noqa: E402
from nlp.extractor import TFIDF_METHOD, _semantic_candidates  # noqa: E402
from nlp.tests.test_keyword import BRIEF_EXPECTED  # noqa: E402

BRIEF = ROOT / "nlp" / "tests" / "fixtures" / "brief_example_jd.txt"
JD = ("Junior Data Analyst. Must know SQL and PowerBI; experience with data "
      "visualization tools is a plus. Good analytical and communication skills.\n"
      "- Build dashboards in Power BI and Tableau\n"
      "- Clean and analyse data with Python (pandas)\n"
      "- Work with stakeholders; communicate results clearly")


@pytest.fixture(autouse=True)
def no_model(monkeypatch):
    def fail():
        raise AssertionError("TF-IDF extraction must not load the Sentence Transformers model")
    monkeypatch.setattr(nlp_model, "get_model", fail)


def extract(text, **kw):
    return extract_skills(text, method="tfidf", **kw)


# ── Settings and interface ────────────────────────────────────
def test_settings():
    assert config.TFIDF_ANALYZER in nlp_model.TFIDF_ANALYZERS
    assert 0.0 < config.TFIDF_MATCH_THRESHOLD < 1.0


def test_tfidf_is_an_extraction_method_only():
    assert "tfidf" in nlp.EXTRACTION_METHODS
    assert "tfidf" not in nlp.VALID_METHODS            # the backend's list stays as it was
    student = [{"skill_id": None, "skill_name": "SQL", "proficiency_level": "advanced",
                "evidence_type": []}]
    required = [{"skill_id": None, "skill_name": "SQL", "importance": "required"}]
    with pytest.raises(ValueError, match="extract_skills"):
        match_skills(student, required, method="tfidf")


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_blank_text_returns_empty_list(text):
    assert extract(text) == []


def test_results_fill_every_field():
    found = extract(JD)
    assert found
    for s in found:
        assert set(s) == {"skill_id", "skill_name", "raw_skill_text", "method",
                          "confidence_score", "start_char", "end_char"}
        assert s["skill_id"] is None                     # default taxonomy has no UUIDs
        assert load_catalogue().get(s["skill_name"]) is not None
        assert s["raw_skill_text"] == JD[s["start_char"]:s["end_char"]]
        assert s["raw_skill_text"].strip()
        assert s["method"] == TFIDF_METHOD == "tfidf"
        assert config.TFIDF_MATCH_THRESHOLD <= s["confidence_score"] <= 1.0


def test_ordered_by_start_char_without_duplicates():
    found = extract(JD)
    starts = [s["start_char"] for s in found]
    assert starts == sorted(starts)
    names = [s["skill_name"] for s in found]
    assert len(names) == len(set(names))


def test_uses_the_semantic_candidate_phrases():
    spans = {(s, e) for s, e, _ in _semantic_candidates(JD, load_catalogue())}
    for s in extract(JD):
        assert (s["start_char"], s["end_char"]) in spans


def test_skill_ids_come_from_the_rows():
    rows = [{"skill_id": "11111111-1111-1111-1111-111111111111", "skill_name": "Python",
             "aliases": ["Python 3"]},
            {"skill_id": "22222222-2222-2222-2222-222222222222", "skill_name": "SQL",
             "aliases": ["T-SQL"]}]
    found = {s["skill_name"]: s["skill_id"]
             for s in extract("Requirements:\n- Python\n- SQL", skills=rows)}
    assert found == {"Python": rows[0]["skill_id"], "SQL": rows[1]["skill_id"]}


# ── Vectorizer ────────────────────────────────────────────────
def test_vectorizer_is_cached_per_analyzer():
    cat = load_catalogue()
    assert nlp_model.skill_tfidf(cat) is nlp_model.skill_tfidf(cat)
    word = nlp_model.skill_tfidf(cat, analyzer="word")
    assert word is not nlp_model.skill_tfidf(cat, analyzer="char_wb")
    assert word.names == tuple(e["skill_name"] for e in cat)
    with pytest.raises(ValueError):
        nlp_model.skill_tfidf(cat, analyzer="nope")


def test_exact_skill_name_is_its_own_best_match():
    cat = load_catalogue()
    for analyzer in nlp_model.TFIDF_ANALYZERS:
        vectors = nlp_model.skill_tfidf(cat, analyzer=analyzer)
        sims = vectors.similarity(["Power BI", "data visualization"])
        assert vectors.names[sims[0].argmax()] == "Power BI"
        assert vectors.names[sims[1].argmax()] == "Data Visualisation"   # US -> UK spelling


def test_word_tokens_keep_skill_symbols():
    vectors = nlp_model.skill_tfidf(load_catalogue(), analyzer="word")
    assert {"c++", "c#"} <= set(vectors.vectorizer.vocabulary_)


# ── POC004 brief, section 6 ───────────────────────────────────
def test_brief_example_tfidf(capsys):
    """Reports how many of the 7 brief skills TF-IDF finds (not asserted to be 7)."""
    text = BRIEF.read_text(encoding="utf-8")
    cat = load_catalogue()
    expected = [cat.lookup(n) for n in BRIEF_EXPECTED]
    names = {s["skill_name"] for s in extract(text)}
    with capsys.disabled():
        print(f"\nbrief example: tfidf {sum(n in names for n in expected)}/{len(expected)}, "
              f"missing {[n for n in expected if n not in names]}, "
              f"extra {sorted(names - set(expected))}")
    assert "Python" in names
