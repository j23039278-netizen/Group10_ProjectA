"""
Draw the gold annotation sample for the Sprint 4 L1 vs L2 evaluation.

Outputs (in --out-dir, default data/jd_dataset/gold/):
  gold_sample.csv        10 JDs per role (fixed seed) = 60 JDs
  gold_labels.csv        EMPTY template to be filled in by a human annotator
                         (jd_ref, skill_name, importance, evidence_text)
  gold_labels_draft.csv  keyword-baseline pre-fill to speed annotation up.
                         It is only a draft: every row must be checked and
                         corrected by hand, and missing skills added, before
                         the result is copied into gold_labels.csv.
                         See ANNOTATION_GUIDE.md.

gold_labels.csv is never overwritten once it has labels in it.

Usage (from repo root):
    python data/jd_dataset/make_gold_sample.py
"""

import argparse
import random
import re
from pathlib import Path

from jd_common import DATASET_FIELDS, DATASET_PATH, JD_DIR, SkillMatcher, read_dataset, write_csv

PER_ROLE = 10
SEED = 42
LABEL_FIELDS = ["jd_ref", "skill_name", "importance", "evidence_text"]

BONUS_CUES = re.compile(r"nice[- ]to[- ]have|a plus|an advantage|advantageous|bonus|added advantage", re.I)
PREFERRED_CUES = re.compile(r"prefer|desirable|ideally|good to have|familiarity with|exposure to", re.I)


def sentence_at(text, start, end):
    left = max(text.rfind(c, 0, start) for c in ".\n;") + 1
    rights = [i for i in (text.find(c, end) for c in ".\n;") if i != -1]
    right = min(rights) if rights else len(text)
    return text[left:right].strip()


def guess_importance(sentence, section):
    if BONUS_CUES.search(sentence) or BONUS_CUES.search(section):
        return "bonus"
    if PREFERRED_CUES.search(sentence) or PREFERRED_CUES.search(section):
        return "preferred"
    return "required"


def section_heading(text, pos):
    """Closest preceding short line ending in ':' (e.g. 'Nice to have:')."""
    head = ""
    for m in re.finditer(r"(?m)^[^\n]{0,60}:\s*$", text[:pos]):
        head = m.group()
    return head


def main():
    ap = argparse.ArgumentParser(description="Create the gold annotation sample")
    ap.add_argument("--dataset", default=str(DATASET_PATH))
    ap.add_argument("--out-dir", default=str(JD_DIR / "gold"))
    ap.add_argument("--per-role", type=int, default=PER_ROLE)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    out = Path(args.out_dir)

    jds = read_dataset(args.dataset)
    rng = random.Random(args.seed)
    sample = []
    for role in sorted({j["role_code"] for j in jds}):
        pool = sorted((j for j in jds if j["role_code"] == role), key=lambda j: j["jd_ref"])
        k = min(args.per_role, len(pool))
        if k < args.per_role:
            print(f"NOTE: {role} has only {len(pool)} JDs (< {args.per_role})")
        sample += sorted(rng.sample(pool, k), key=lambda j: j["jd_ref"])
    write_csv(out / "gold_sample.csv", sample, DATASET_FIELDS)

    labels_path = out / "gold_labels.csv"
    if not labels_path.exists() or len(labels_path.read_text(encoding="utf-8").strip().splitlines()) <= 1:
        write_csv(labels_path, [], LABEL_FIELDS)
    else:
        print(f"{labels_path} already has labels - left untouched")

    matcher = SkillMatcher()
    draft = []
    for j in sample:
        text = j["raw_text"]
        best = {}
        for s, e, _, skill in matcher.find(text):
            if skill in best:
                continue
            sent = sentence_at(text, s, e)
            best[skill] = {"jd_ref": j["jd_ref"], "skill_name": skill,
                           "importance": guess_importance(sent, section_heading(text, s)),
                           "evidence_text": sent[:300]}
        draft += best.values()
    write_csv(out / "gold_labels_draft.csv", draft, LABEL_FIELDS)
    print(f"gold_sample.csv: {len(sample)} JDs; gold_labels_draft.csv: {len(draft)} draft labels "
          f"(MUST be reviewed by hand before use)")


if __name__ == "__main__":
    main()
