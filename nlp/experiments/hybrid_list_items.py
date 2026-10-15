"""
Evidence for LIST_ITEM_TEXT_MODE / LIST_ITEM_THRESHOLD in nlp/config.py
(hybrid extraction, S2-02).

    python nlp/experiments/hybrid_list_items.py

Runs the coordinated-list step of hybrid extraction ("good analytical,
communication and problem-solving skills" -> "analytical skills") over the 65
JDs in data/jd_dataset/jd_dataset.csv and the POC004 brief example, and writes
results/hybrid_list_items.csv: every list item keyword extraction did not
resolve, the phrase read with the head noun, its two most similar skills under
LIST_ITEM_TEXT_MODE and under SKILL_TEXT_MODE, and whether hybrid extraction
adds it at 0.65 and at 0.70. Whether each added skill is right was judged by
reading the JD line; see THRESHOLDS.md, "List items in hybrid extraction".
"""

import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from nlp import config, load_catalogue  # noqa: E402
from nlp.extractor import _index_for, _keyword_hits, _list_items, _term_key  # noqa: E402
from nlp.model import encode, skill_embeddings  # noqa: E402

JD_PATH = REPO / "data" / "jd_dataset" / "jd_dataset.csv"
BRIEF_PATH = REPO / "nlp" / "tests" / "fixtures" / "brief_example_jd.txt"
OUT_PATH = Path(__file__).resolve().parent / "results" / "hybrid_list_items.csv"
THRESHOLDS = (0.65, 0.70)


def top_two(vectors, phrase):
    sims = vectors.similarity(encode([phrase.lower()]))[0]
    order = sims.argsort()[::-1]
    return [(vectors.names[k], round(float(sims[k]), 3)) for k in order[:2]]


def main():
    catalogue = load_catalogue()
    index = _index_for(catalogue)
    item_mode = skill_embeddings(catalogue, config.LIST_ITEM_TEXT_MODE,
                                 use_disk=config.LIST_ITEM_TEXT_MODE == config.SKILL_TEXT_MODE)
    main_mode = skill_embeddings(catalogue)

    with open(JD_PATH, encoding="utf-8", newline="") as f:
        jds = [(r["jd_ref"], r["raw_text"]) for r in csv.DictReader(f)]
    jds.append(("BRIEF", BRIEF_PATH.read_text(encoding="utf-8")))

    rows = []
    for ref, text in jds:
        hits = _keyword_hits(text, catalogue)
        found = {h.skill_name for h in hits}
        for start, end, phrase in _list_items(text, hits, catalogue):
            line_start = text.rfind("\n", 0, start) + 1
            line_end = text.find("\n", end)
            row = {"jd_ref": ref,
                   "line": " ".join(text[line_start:line_end if line_end >= 0 else None].split())[:160],
                   "item": text[start:end], "phrase": phrase}
            term = index.terms.get(_term_key(phrase))
            if term is not None and not term.ambiguous:
                row.update(resolved_by="catalogue term", skill=term.skill_name, score=1.0,
                           second_skill="", second_score="")
            else:
                (best, score), (second, second_score) = top_two(item_mode, phrase)
                row.update(resolved_by="similarity", skill=best, score=score,
                           second_skill=second, second_score=second_score)
            (main_best, main_score), _ = top_two(main_mode, phrase)
            row.update(main_mode_skill=main_best, main_mode_score=main_score,
                       found_by_keyword=row["skill"] in found)
            for t in THRESHOLDS:
                row[f"added_at_{t:.2f}"] = (not row["found_by_keyword"]) and row["score"] >= t
            rows.append(row)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(jds)} texts, {len(rows)} unresolved list items -> {OUT_PATH.relative_to(REPO)}")
    for t in THRESHOLDS:
        added = Counter((r["phrase"].lower(), r["skill"]) for r in rows if r[f"added_at_{t:.2f}"])
        print(f"added at {t:.2f}: {sum(added.values())} items in "
              f"{len({r['jd_ref'] for r in rows if r[f'added_at_{t:.2f}']})} texts")
        for (phrase, skill), n in added.most_common():
            print(f"  {n:2} x {phrase!r} -> {skill}")


if __name__ == "__main__":
    main()
