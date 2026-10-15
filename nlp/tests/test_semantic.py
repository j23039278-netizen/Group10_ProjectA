"""Checks for Level 2 semantic extraction (S2-02).

Run all:          python -m pytest nlp/tests -q
Skip model tests: python -m pytest nlp/tests -q -m "not model"
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
np = pytest.importorskip("numpy")
from nlp import config, extract_skills, load_catalogue  # noqa: E402
from nlp import model as nlp_model  # noqa: E402

model = pytest.mark.model


def extract(text, **kw):
    return extract_skills(text, method="semantic", **kw)


def names(text):
    return {s["skill_name"] for s in extract(text)}


# ── No model needed ───────────────────────────────────────────
@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_blank_text_returns_empty_list(text):
    assert extract(text) == []


def test_thresholds_are_ordered():
    assert 0.0 < config.RELATED_THRESHOLD < config.MATCH_THRESHOLD < 1.0


def test_skill_text_modes():
    entry = load_catalogue().get("Power BI")
    assert nlp_model.skill_texts(entry, "name_aliases") == ["Power BI: PowerBI, Microsoft Power BI"]
    assert nlp_model.skill_texts(entry, "name_aliases_max") == ["Power BI", "PowerBI", "Microsoft Power BI"]
    [desc] = nlp_model.skill_texts(entry, "name_description")
    assert desc.startswith("Power BI: Business intelligence")
    assert nlp_model.skill_texts(load_catalogue().get("Go"), "name_aliases_max") == [
        "Go", "Golang", "Go language"]                     # ambiguous alias "Go" not repeated
    with pytest.raises(ValueError):
        nlp_model.skill_texts(entry, "nope")


def test_catalogue_hash_changes_with_catalogue():
    rows = [{"skill_name": "SQL", "aliases": ["T-SQL"], "description": "Query language"}]
    texts = [nlp_model.skill_texts(e, "name_aliases") for e in load_catalogue(rows)]
    changed = [nlp_model.skill_texts(e, "name_aliases")
               for e in load_catalogue([dict(rows[0], aliases=["T-SQL", "PL/SQL"])])]
    assert nlp_model.catalogue_hash(texts, "name_aliases") == nlp_model.catalogue_hash(texts, "name_aliases")
    assert nlp_model.catalogue_hash(texts, "name_aliases") != nlp_model.catalogue_hash(changed, "name_aliases")
    assert nlp_model.catalogue_hash(texts, "name_aliases") != nlp_model.catalogue_hash(texts, "name_description")


# ── Model ─────────────────────────────────────────────────────
@model
def test_model_loads_once():
    first = nlp_model.get_model()
    assert nlp_model.get_model() is first
    assert nlp_model.get_spacy() is nlp_model.get_spacy()


@model
def test_skill_embeddings_cached_and_normalised():
    cat = load_catalogue()
    skills = nlp_model.skill_embeddings(cat)
    assert nlp_model.skill_embeddings(cat) is skills
    assert len(skills.names) == len(cat) == len(skills.starts)
    assert np.allclose(np.linalg.norm(skills.matrix, axis=1), 1.0, atol=1e-4)


@model
def test_best_term_mode_scores_an_alias_like_its_name():
    skills = nlp_model.skill_embeddings(load_catalogue(), "name_aliases_max", use_disk=False)
    sims = skills.similarity(nlp_model.encode(["statistical modelling"]))[0]
    assert skills.names[int(sims.argmax())] == "Statistical Analysis"
    assert sims.max() > 0.99                                # exact alias


@model
def test_disk_cache_rebuilds_when_catalogue_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(nlp_model, "EMBEDDINGS_PATH", tmp_path / "emb.npy")
    monkeypatch.setattr(nlp_model, "EMBEDDINGS_META_PATH", tmp_path / "emb.json")
    monkeypatch.setattr(nlp_model, "_embedding_cache", {})
    rows = [{"skill_name": "SQL", "aliases": ["T-SQL"]}, {"skill_name": "Python", "aliases": []}]

    first = nlp_model.skill_embeddings(load_catalogue(rows), "name_aliases_max")
    assert (tmp_path / "emb.npy").exists()
    monkeypatch.setattr(nlp_model, "_embedding_cache", {})           # new process
    again = nlp_model.skill_embeddings(load_catalogue(rows), "name_aliases_max")   # from disk
    assert np.array_equal(first.matrix, again.matrix)
    assert list(again.starts) == [0, 2]                              # SQL, T-SQL | Python

    rows.append({"skill_name": "Docker", "aliases": []})
    rebuilt = nlp_model.skill_embeddings(load_catalogue(rows), "name_aliases_max")
    assert len(rebuilt.names) == 3
    assert np.load(tmp_path / "emb.npy").shape[0] == 4


# Below MATCH with the chosen settings (name_aliases, MATCH 0.60); the best
# phrase scores are noted. Strict xfail: if a later change finds them, update
# the test. "statistical modelling" and "team player" are catalogue aliases, so
# the keyword side of hybrid extraction is expected to cover the first case.
_BELOW_MATCH = pytest.mark.xfail(strict=True, reason=(
    "below MATCH with name_aliases: see nlp/experiments/THRESHOLDS.md (limitations)"))


@model
@pytest.mark.parametrize("text, expected", [
    ("You will build data visualisation dashboards for the sales team.", "Data Visualisation"),
    ("Build interactive dashboards and charts.", "Data Visualisation"),
    pytest.param("Experience with statistical modelling of customer behaviour.",
                 "Statistical Analysis", marks=_BELOW_MATCH),                # 0.56
    pytest.param("We want a team player who communicates well.",
                 "Communication", marks=_BELOW_MATCH),                       # 0.51
])
def test_synonyms_map_to_catalogue_skill(text, expected):
    assert expected in names(text)


@model
@pytest.mark.parametrize("text", [
    "Free parking and gym.",
    "Our office is a short walk from the LRT station.",
])
def test_unrelated_text_returns_nothing(text):
    assert extract(text) == []


@model
def test_result_fields_follow_contract():
    text = ("Junior Data Analyst\n"
            "* Clean and analyse data from several sources\n"
            "* Build data visualisation dashboards\n"
            "* Strong written and verbal communication skills\n")
    found = extract(text)
    assert found
    assert [s["start_char"] for s in found] == sorted(s["start_char"] for s in found)
    assert len({s["skill_name"] for s in found}) == len(found)
    for s in found:
        assert s["method"] == "semantic"
        assert s["skill_id"] is None
        assert s["raw_skill_text"] == text[s["start_char"]:s["end_char"]]
        assert config.MATCH_THRESHOLD <= s["confidence_score"] <= 1.0


@model
def test_db_rows_carry_skill_ids():
    rows = [{"skill_id": "uuid-viz", "skill_name": "Data Visualisation",
             "aliases": ["Data viz", "Dashboard creation"]},
            {"skill_id": "uuid-sql", "skill_name": "SQL", "aliases": []}]
    found = extract("Build interactive dashboards and charts.", skills=rows)
    assert [(s["skill_id"], s["skill_name"]) for s in found] == [("uuid-viz", "Data Visualisation")]


# ── POC004 brief, section 6 ───────────────────────────────────
@model
@pytest.mark.xfail(strict=True, reason=(
    "No candidate phrase contains 'analytical' ('good analytical, communication and "
    "problem-solving skills' is one 11-token sentence), and with name_aliases even "
    "'analytical skills' scores Critical Thinking 0.529 < Problem Solving 0.576; "
    "see nlp/experiments/THRESHOLDS.md"))
def test_brief_example_semantic_finds_critical_thinking(capsys):
    from nlp.tests.test_keyword import BRIEF_EXPECTED
    path = ROOT / "nlp" / "tests" / "fixtures" / "brief_example_jd.txt"
    if not path.exists():
        pytest.skip("missing fixture nlp/tests/fixtures/brief_example_jd.txt")
    cat = load_catalogue()
    expected = [cat.lookup(n) for n in BRIEF_EXPECTED]
    found = {s["skill_name"]: s for s in extract(path.read_text(encoding="utf-8"))}
    hits = [n for n in expected if n in found]
    with capsys.disabled():
        print(f"\nsemantic finds {len(hits)}/{len(expected)} brief skills: "
              + ", ".join(f"{n} ({found[n]['confidence_score']:.3f})" for n in hits)
              + f"; missed: {', '.join(n for n in expected if n not in found) or '-'}")
    assert "Critical Thinking" in found


@model
def test_junk_candidates_are_dropped():
    text = ("Bachelor's degree in Computer Science. 2 years of experience. "
            "Attractive salary and medical insurance. Send your CV to us.")
    assert "Computer Vision" not in names(text)
    for s in extract(text):
        raw = s["raw_skill_text"].lower()
        assert not any(w in raw for w in ("degree", "years", "salary", "insurance", "cv"))
