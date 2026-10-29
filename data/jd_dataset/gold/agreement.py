"""
Inter-annotator agreement between annotator A (gold_labels.csv) and annotator B
(gold_labels_B.csv) on the JDs both labelled (JDs with at least one row in each
file).

Skill presence (Cohen's kappa + raw percent agreement)
  The unit is one (JD, skill) pair, labelled present / absent by each annotator.
  Which skills to score per JD is a choice, because "absent" is open-ended:

  * Union only: the skills either annotator used in that JD. Every unit is
    present for at least one annotator, so the absent/absent cell is always 0.
    Kappa then ignores all the easy agreement on skills the JD clearly lacks;
    it is a strict, pessimistic figure, and percent agreement equals the
    overlap |A and B| / |A or B|.
  * Union + negatives: the union plus a per-JD random sample of catalogue
    skills neither annotator used (by default as many as the union, so the
    two classes are about the same size; --neg-ratio changes this). This gives
    the absent class real members, as kappa assumes. Random catalogue skills
    are mostly easy negatives, so this figure is optimistic.
  Scoring the whole catalogue (~166 skills per JD) is not used: absent/absent
  would swamp the table and percent agreement would sit near 100%
  whatever the annotators did. Both figures are reported; the true agreement
  lies between them. The sample is fixed by --seed and the jd_ref, so the
  numbers are reproducible.

Importance (weighted kappa)
  On the skills both marked present, importance is ordinal
  (bonus < preferred < required), so a linear-weighted kappa is used:
  required vs bonus counts as a bigger disagreement than required vs
  preferred. Exact agreement is reported too.

NEW: terms are compared case- and whitespace-insensitively ("NEW: DevOps" ==
"new: devops").

Outputs (in --out-dir, default the gold folder):
  agreement_disagreements.csv  jd_ref, skill, A, B, evidence (A/B = importance or "absent")
  AGREEMENT.md                 short report for the Sprint 4 write-up

Usage (from repo root):
    python data/jd_dataset/gold/agreement.py
"""

import argparse
import random
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from gold_common import (GOLD_DIR, IMPORTANCE, LABELS_PATH, SKILLS_PATH, Catalogue, load_skills,
                         read_csv, skill_key, write_csv)

ABSENT, PRESENT = "absent", "present"
ORDINAL = list(reversed(IMPORTANCE))  # bonus < preferred < required
DISAGREEMENT_FIELDS = ["jd_ref", "skill", "A", "B", "evidence"]


def load_labels(path):
    """{jd_ref: {skill key: {"skill", "importance", "evidence"}}}"""
    out = {}
    for r in read_csv(path):
        out.setdefault(r["jd_ref"], {})[skill_key(r["skill_name"])] = {
            "skill": r["skill_name"], "importance": r["importance"], "evidence": r["evidence_text"]}
    return out


def cohen_kappa(x, y):
    """Cohen's kappa for two equal-length label lists (nan if undefined)."""
    n = len(x)
    if n == 0:
        return float("nan")
    p_o = sum(a == b for a, b in zip(x, y)) / n
    cx, cy = Counter(x), Counter(y)
    p_e = sum(cx[c] * cy[c] for c in cx) / (n * n)
    return float("nan") if p_e == 1 else (p_o - p_e) / (1 - p_e)


def weighted_kappa(x, y, categories):
    """Linear-weighted Cohen's kappa for ordinal labels (`categories` in order):
    1 - observed / expected disagreement, with weight |i - j| per pair."""
    n = len(x)
    if n == 0:
        return float("nan")
    idx = {c: i for i, c in enumerate(categories)}
    cx, cy = Counter(x), Counter(y)
    observed = sum(abs(idx[a] - idx[b]) for a, b in zip(x, y)) / n
    expected = sum(cx[a] * cy[b] * abs(idx[a] - idx[b])
                   for a in categories for b in categories) / (n * n)
    return float("nan") if expected == 0 else 1 - observed / expected


def percent(x, y):
    return 100 * sum(a == b for a, b in zip(x, y)) / len(x) if x else float("nan")


def build_units(a, b, refs, catalogue_names, neg_ratio=1.0, seed=42):
    """One dict per (JD, skill): jd_ref, key, skill, a, b (importance or None), negative."""
    units = []
    for ref in refs:
        la, lb = a.get(ref, {}), b.get(ref, {})
        union = sorted(set(la) | set(lb))
        for key in union:
            info = la.get(key) or lb.get(key)
            units.append({"jd_ref": ref, "key": key, "skill": info["skill"],
                          "a": la.get(key, {}).get("importance"),
                          "b": lb.get(key, {}).get("importance"), "negative": False})
        candidates = [n for n in catalogue_names if skill_key(n) not in set(union)]
        k = min(len(candidates), round(neg_ratio * len(union)))
        for name in random.Random(f"{seed}:{ref}").sample(candidates, k):
            units.append({"jd_ref": ref, "key": skill_key(name), "skill": name,
                          "a": None, "b": None, "negative": True})
    return units


def presence_stats(units):
    x = [PRESENT if u["a"] else ABSENT for u in units]
    y = [PRESENT if u["b"] else ABSENT for u in units]
    pairs = Counter(zip(x, y))
    return {"units": len(units), "kappa": cohen_kappa(x, y), "percent": percent(x, y),
            "both": pairs[(PRESENT, PRESENT)], "a_only": pairs[(PRESENT, ABSENT)],
            "b_only": pairs[(ABSENT, PRESENT)], "neither": pairs[(ABSENT, ABSENT)]}


def importance_stats(units):
    both = [u for u in units if u["a"] and u["b"]]
    x, y = [u["a"] for u in both], [u["b"] for u in both]
    return {"units": len(both), "weighted_kappa": weighted_kappa(x, y, ORDINAL),
            "percent": percent(x, y)}


def disagreements(units, a, b):
    rows = []
    for u in units:
        if u["a"] == u["b"]:
            continue
        ev = []
        for who, labels in (("A", a), ("B", b)):
            got = labels.get(u["jd_ref"], {}).get(u["key"])
            if got and got["evidence"]:
                ev.append(f"{who}: {got['evidence']}")
        rows.append({"jd_ref": u["jd_ref"], "skill": u["skill"], "A": u["a"] or ABSENT,
                     "B": u["b"] or ABSENT, "evidence": " | ".join(ev)})
    return rows


def fmt(v, digits=3):
    return "n/a" if v != v else f"{v:.{digits}f}"  # v != v: nan


def band(k):
    """Landis & Koch (1977) label."""
    if k != k:
        return "undefined"
    for limit, label in ((0, "poor"), (0.2, "slight"), (0.4, "fair"), (0.6, "moderate"),
                         (0.8, "substantial")):
        if k <= limit:
            return label
    return "almost perfect"


def report_md(refs, pres_union, pres_neg, imp, n_dis, args):
    lines = [
        "# Inter-annotator agreement (gold JD skills)",
        "",
        f"Generated by `agreement.py` on {date.today().isoformat()}. "
        f"A = `{Path(args.a).name}`, B = `{Path(args.b).name}`.",
        "",
        f"JDs labelled by both: **{len(refs)}** ({', '.join(refs)}).",
        "",
        "## Skill presence (Cohen's kappa)",
        "",
        "| Units scored | Units | Both | A only | B only | Neither | Agreement | kappa |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, s in (("Union of both annotators' skills", pres_union),
                    (f"Union + sampled negatives (ratio {args.neg_ratio}, seed {args.seed})", pres_neg)):
        lines.append(f"| {name} | {s['units']} | {s['both']} | {s['a_only']} | {s['b_only']} | "
                     f"{s['neither']} | {fmt(s['percent'], 1)}% | {fmt(s['kappa'])} ({band(s['kappa'])}) |")
    lines += [
        "",
        "Union only has no absent/absent cell, so it is the strict figure; the sampled "
        "negatives are mostly easy, so that figure is optimistic. The true agreement lies "
        "between them (see the `agreement.py` docstring).",
        "",
        "## Importance (skills both marked present)",
        "",
        f"- Units: {imp['units']}",
        f"- Exact agreement: {fmt(imp['percent'], 1)}%",
        f"- Linear-weighted kappa: {fmt(imp['weighted_kappa'])} ({band(imp['weighted_kappa'])})",
        "",
        "## Disagreements",
        "",
        f"{n_dis} (JD, skill) pairs differ in presence or importance; see "
        "`agreement_disagreements.csv`. Resolve them together, fix the workbook(s), "
        "re-run `collect_workbook.py`, then freeze `gold_labels.csv`.",
        "",
        "Kappa bands: Landis & Koch (1977).",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Agreement between annotators A and B")
    ap.add_argument("--a", default=str(LABELS_PATH["A"]))
    ap.add_argument("--b", default=str(LABELS_PATH["B"]))
    ap.add_argument("--skills", default=str(SKILLS_PATH))
    ap.add_argument("--neg-ratio", type=float, default=1.0,
                    help="sampled negatives per JD, as a multiple of the union size")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", default=str(GOLD_DIR))
    args = ap.parse_args(argv)

    a, b = load_labels(args.a), load_labels(args.b)
    refs = sorted(set(a) & set(b))
    if not refs:
        print(f"No JD is labelled in both {args.a} and {args.b}.")
        return 1
    names = Catalogue(load_skills(args.skills)).names
    units = build_units(a, b, refs, names, args.neg_ratio, args.seed)
    union_units = [u for u in units if not u["negative"]]
    pres_union, pres_neg = presence_stats(union_units), presence_stats(units)
    imp = importance_stats(union_units)
    dis = disagreements(union_units, a, b)

    out = Path(args.out_dir)
    write_csv(out / "agreement_disagreements.csv", dis, DISAGREEMENT_FIELDS)
    (out / "AGREEMENT.md").write_text(report_md(refs, pres_union, pres_neg, imp, len(dis), args),
                                      encoding="utf-8")

    print(f"JDs labelled by both: {len(refs)}")
    for name, s in (("union only", pres_union), ("union + negatives", pres_neg)):
        print(f"presence kappa ({name}): {fmt(s['kappa'])}  agreement {fmt(s['percent'], 1)}%  "
              f"units {s['units']}")
    print(f"importance weighted kappa: {fmt(imp['weighted_kappa'])}  exact {fmt(imp['percent'], 1)}%  "
          f"units {imp['units']}")
    print(f"{len(dis)} disagreements -> {out / 'agreement_disagreements.csv'}; report -> {out / 'AGREEMENT.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
