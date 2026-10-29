"""
S2-02-01: choose the semantic similarity thresholds with evidence.

Run from the repo root:

    python nlp/experiments/threshold_sweep.py

Input: nlp/experiments/threshold_pairs.csv, labelled by hand
(columns phrase, skill_name, label; 1 = same skill, 0 = not; extra columns are
ignored). See nlp/experiments/README.md for the labelling rules.

If that file does not exist yet, the script writes
threshold_pairs_candidates.csv (about 60 phrase / skill pairs from the JD
dataset, label column empty) and stops. Label it, save it as
threshold_pairs.csv and run again. The model only chooses which pairs to show;
the labels must come from a person.

With labels, for each skill text mode in nlp.model.SKILL_TEXT_MODES (name +
aliases as one text, name and each alias separately, name + description) it
sweeps thresholds 0.40-0.90 in 0.05 steps and writes to results/:
  threshold_sweep.csv   precision / recall / F1 per mode and threshold
  pair_scores.csv       cosine similarity of every pair under each mode
  threshold_sweep.png   precision / recall / F1 curves
and prints the proposed MATCH / RELATED thresholds. The chosen values go in
nlp/config.py by hand, with the reasoning in THRESHOLDS.md.

    python nlp/experiments/threshold_sweep.py --method tfidf

does the same for TF-IDF extraction on the same pairs: for each analyzer in
nlp.model.TFIDF_ANALYZERS (word 1-2-grams, char_wb 3-5-grams), with the skill
texts of config.SKILL_TEXT_MODE, it sweeps thresholds 0.05-0.90 (TF-IDF
cosines run lower than embedding cosines) and writes threshold_sweep_tfidf.csv,
pair_scores_tfidf.csv and threshold_sweep_tfidf.png. It proposes
TFIDF_ANALYZER and TFIDF_MATCH_THRESHOLD (no RELATED: matching has no TF-IDF
method).
"""

import argparse
import csv
import random
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from nlp import config, load_catalogue  # noqa: E402
from nlp.extractor import _semantic_candidates  # noqa: E402
from nlp.model import SKILL_TEXT_MODES, TFIDF_ANALYZERS, encode, skill_embeddings, skill_tfidf  # noqa: E402
from nlp.normalise import skill_key  # noqa: E402

EXP_DIR = Path(__file__).resolve().parent
PAIRS_PATH = EXP_DIR / "threshold_pairs.csv"
CANDIDATES_PATH = EXP_DIR / "threshold_pairs_candidates.csv"
RESULTS_DIR = EXP_DIR / "results"
JD_PATH = REPO / "data" / "jd_dataset" / "jd_dataset.csv"

THRESHOLDS = [round(0.40 + 0.05 * i, 2) for i in range(11)]   # 0.40 ... 0.90
TFIDF_THRESHOLDS = [round(0.05 * i, 2) for i in range(1, 19)]  # 0.05 ... 0.90
RELATED_MIN_RECALL = 0.95
MODE_TITLES = {"name_aliases": "name + aliases (one text)",
               "name_aliases_max": "name + aliases (best term)",
               "name_description": "name + description"}   # RELATED must still catch nearly every true match
TFIDF_TITLES = {"word": "word 1-2-grams", "char_wb": "char_wb 3-5-grams"}

# Candidate pairs per similarity bin (mean over both modes); 6 bins x 10 = 60.
SIM_BINS = [(0.0, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 1.01)]
PAIRS_PER_BIN = 10
SEED = 40005


# ── Candidate generation (no labels) ──────────────────────────
def generate_candidates():
    catalogue = load_catalogue()
    term_keys = {skill_key(t) for e in catalogue
                 for t in [e["skill_name"]] + e["aliases"] + e["ambiguous_aliases"]}

    with open(JD_PATH, encoding="utf-8", newline="") as f:
        jds = list(csv.DictReader(f))

    phrase_jd = {}   # lower-case phrase -> (phrase as written, jd_ref)
    for jd in jds:
        for _, _, phrase in _semantic_candidates(jd["raw_text"], catalogue):
            low = phrase.lower()
            # exact names / aliases are the keyword extractor's job, not a threshold question
            if low not in phrase_jd and skill_key(phrase) not in term_keys:
                phrase_jd[low] = (phrase, jd["jd_ref"])
    phrases = sorted(phrase_jd)

    phrase_vecs = encode(phrases)
    sims = np.zeros((len(phrases), len(catalogue)), dtype=np.float32)
    for mode in SKILL_TEXT_MODES:
        skills = skill_embeddings(catalogue, mode, use_disk=False)
        sims += skills.similarity(phrase_vecs)
    sims /= len(SKILL_TEXT_MODES)
    names = skills.names

    # pool: each phrase with its best and second-best skill
    pool = []
    for i, low in enumerate(phrases):
        for j in np.argsort(-sims[i])[:2]:
            pool.append((float(sims[i, j]), phrase_jd[low][0], names[j], phrase_jd[low][1]))

    rng = random.Random(SEED)
    chosen, used_phrases = [], set()
    for lo, hi in SIM_BINS:
        in_bin = [p for p in pool if lo <= p[0] < hi]
        rng.shuffle(in_bin)
        taken = 0
        for _, phrase, skill, jd_ref in in_bin:
            if taken == PAIRS_PER_BIN:
                break
            if phrase.lower() in used_phrases:
                continue
            used_phrases.add(phrase.lower())
            chosen.append((phrase, skill, jd_ref))
            taken += 1
    rng.shuffle(chosen)   # the order must not give the bin away

    with open(CANDIDATES_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["phrase", "skill_name", "label", "jd_ref"])
        for phrase, skill, jd_ref in chosen:
            w.writerow([phrase, skill, "", jd_ref])
    return len(chosen), len(phrases)


# ── Sweep ─────────────────────────────────────────────────────
def load_pairs(catalogue):
    with open(PAIRS_PATH, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    pairs = []
    for n, row in enumerate(rows, start=2):
        label = (row.get("label") or "").strip()
        if label not in ("0", "1"):
            raise SystemExit(f"{PAIRS_PATH.name} line {n}: label must be 0 or 1, got {label!r}")
        skill = catalogue.get(row["skill_name"])
        if skill is None:
            raise SystemExit(f"{PAIRS_PATH.name} line {n}: unknown skill {row['skill_name']!r}")
        pairs.append((row["phrase"].strip(), skill["skill_name"], int(label)))
    return pairs


def metrics(scores, labels, t):
    pred = scores >= t
    tp = int(np.sum(pred & (labels == 1)))
    fp = int(np.sum(pred & (labels == 0)))
    fn = int(np.sum(~pred & (labels == 1)))
    tn = int(np.sum(~pred & (labels == 0)))
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}


def propose(rows):
    """MATCH = best F1 (ties: higher threshold, i.e. more precise).
    RELATED = highest threshold below MATCH that keeps recall >= RELATED_MIN_RECALL."""
    match = max(rows, key=lambda r: (r["f1"], r["threshold"]))
    below = [r for r in rows if r["threshold"] < match["threshold"]
             and r["recall"] >= RELATED_MIN_RECALL]
    related = max(below, key=lambda r: r["threshold"]) if below else min(rows, key=lambda r: r["threshold"])
    return match, related


def plot(table, path, modes=SKILL_TEXT_MODES, titles=MODE_TITLES, thresholds=THRESHOLDS,
         what="Semantic skill matching", xlabel="cosine similarity threshold"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # validated categorical slots 1-3 (dataviz reference palette, light surface)
    series = [("precision", "#2a78d6", "-"), ("recall", "#eb6834", "--"), ("f1", "#1baf7a", "-.")]
    ink, muted, grid, surface = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"

    fig, axes = plt.subplots(1, len(modes), figsize=(max(11, 14 * len(modes) / 3), 4.2), sharey=True,
                             facecolor=surface)
    for ax, mode in zip(axes, modes):
        rows = [r for r in table if r["mode"] == mode]
        xs = [r["threshold"] for r in rows]
        ax.set_facecolor(surface)
        for key, colour, style in series:
            ys = [r[key] for r in rows]
            ax.plot(xs, ys, color=colour, linestyle=style, linewidth=2,
                    marker="o", markersize=4, label="F1" if key == "f1" else key.capitalize())
        ax.set_title(titles[mode], fontsize=10, color=ink, loc="left")
        ax.set_xlabel(xlabel, fontsize=9, color=muted)
        ax.set_xticks(thresholds[::2] if len(thresholds) > 12 else thresholds)
        ax.set_xlim(thresholds[0] - 0.02, thresholds[-1] + 0.02)
        ax.set_ylim(0, 1.02)
        ax.tick_params(colors=muted, labelsize=8)
        ax.grid(True, color=grid, linewidth=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(grid)
    axes[0].set_ylabel("score", fontsize=9, color=muted)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=3, fontsize=9, frameon=False)
    fig.suptitle(f"{what}: precision / recall / F1 by threshold "
                 f"(n = {table[0]['tp'] + table[0]['fp'] + table[0]['fn'] + table[0]['tn']} labelled pairs)",
                 fontsize=11, color=ink, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(path, dpi=150, facecolor=surface)
    plt.close(fig)


def sweep():
    catalogue = load_catalogue()
    pairs = load_pairs(catalogue)
    labels = np.array([p[2] for p in pairs])
    phrase_vecs = encode([p[0] for p in pairs])

    scores = {}
    for mode in SKILL_TEXT_MODES:
        skills = skill_embeddings(catalogue, mode, use_disk=False)
        col_of = {n: i for i, n in enumerate(skills.names)}
        full = skills.similarity(phrase_vecs)
        scores[mode] = full[np.arange(len(pairs)), [col_of[p[1]] for p in pairs]]

    table = [{"mode": mode, "threshold": t, **metrics(scores[mode], labels, t)}
             for mode in SKILL_TEXT_MODES for t in THRESHOLDS]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "threshold_sweep.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)
    with open(RESULTS_DIR / "pair_scores.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["phrase", "skill_name", "label"] + [f"sim_{m}" for m in SKILL_TEXT_MODES])
        for k, (phrase, skill, label) in enumerate(pairs):
            w.writerow([phrase, skill, label] + [f"{scores[m][k]:.3f}" for m in SKILL_TEXT_MODES])
    plot(table, RESULTS_DIR / "threshold_sweep.png")

    print(f"{len(pairs)} labelled pairs ({int(labels.sum())} positive)\n")
    print(f"{'mode':<17} {'thr':>5} {'P':>6} {'R':>6} {'F1':>6}  tp fp fn tn")
    for r in table:
        print(f"{r['mode']:<17} {r['threshold']:>5.2f} {r['precision']:>6.3f} {r['recall']:>6.3f} "
              f"{r['f1']:>6.3f}  {r['tp']:>2} {r['fp']:>2} {r['fn']:>2} {r['tn']:>2}")
    print()
    best = None
    for mode in SKILL_TEXT_MODES:
        match, related = propose([r for r in table if r["mode"] == mode])
        print(f"{mode}: MATCH {match['threshold']:.2f} (F1 {match['f1']:.3f}, P {match['precision']:.3f}, "
              f"R {match['recall']:.3f}); RELATED {related['threshold']:.2f} (R {related['recall']:.3f})")
        if best is None or match["f1"] > best[1]["f1"]:
            best = (mode, match, related)
    print(f"\nproposed: SKILL_TEXT_MODE = {best[0]!r}, MATCH_THRESHOLD = {best[1]['threshold']:.2f}, "
          f"RELATED_THRESHOLD = {best[2]['threshold']:.2f}")
    print(f"results in {RESULTS_DIR}")


def sweep_tfidf():
    """TF-IDF version of sweep(): one 'mode' per analyzer, skill texts of SKILL_TEXT_MODE."""
    catalogue = load_catalogue()
    pairs = load_pairs(catalogue)
    labels = np.array([p[2] for p in pairs])
    phrases = [p[0] for p in pairs]
    analyzers = tuple(TFIDF_ANALYZERS)

    scores = {}
    for analyzer in analyzers:
        skills = skill_tfidf(catalogue, config.SKILL_TEXT_MODE, analyzer)
        col_of = {n: i for i, n in enumerate(skills.names)}
        full = skills.similarity(phrases)
        scores[analyzer] = full[np.arange(len(pairs)), [col_of[p[1]] for p in pairs]]

    table = [{"analyzer": a, "threshold": t, **metrics(scores[a], labels, t)}
             for a in analyzers for t in TFIDF_THRESHOLDS]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "threshold_sweep_tfidf.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)
    with open(RESULTS_DIR / "pair_scores_tfidf.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["phrase", "skill_name", "label"] + [f"tfidf_{a}" for a in analyzers])
        for k, (phrase, skill, label) in enumerate(pairs):
            w.writerow([phrase, skill, label] + [f"{scores[a][k]:.3f}" for a in analyzers])
    plot([dict(r, mode=r["analyzer"]) for r in table], RESULTS_DIR / "threshold_sweep_tfidf.png",
         modes=analyzers, titles=TFIDF_TITLES, thresholds=TFIDF_THRESHOLDS,
         what=f"TF-IDF ({config.SKILL_TEXT_MODE})",
         xlabel="TF-IDF cosine similarity threshold")

    print(f"{len(pairs)} labelled pairs ({int(labels.sum())} positive), "
          f"skill texts {config.SKILL_TEXT_MODE}\n")
    print(f"{'analyzer':<9} {'thr':>5} {'P':>6} {'R':>6} {'F1':>6}  tp fp fn tn")
    for r in table:
        print(f"{r['analyzer']:<9} {r['threshold']:>5.2f} {r['precision']:>6.3f} {r['recall']:>6.3f} "
              f"{r['f1']:>6.3f}  {r['tp']:>2} {r['fp']:>2} {r['fn']:>2} {r['tn']:>2}")
    print()
    best = None
    for analyzer in analyzers:
        match, _ = propose([r for r in table if r["analyzer"] == analyzer])
        print(f"{analyzer}: MATCH {match['threshold']:.2f} (F1 {match['f1']:.3f}, "
              f"P {match['precision']:.3f}, R {match['recall']:.3f})")
        if best is None or match["f1"] > best[1]["f1"]:
            best = (analyzer, match)
    print(f"\nproposed: TFIDF_ANALYZER = {best[0]!r}, TFIDF_MATCH_THRESHOLD = {best[1]['threshold']:.2f}")
    print(f"results in {RESULTS_DIR}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--method", choices=("semantic", "tfidf"), default="semantic",
                        help="representation to sweep (default: semantic, the embeddings)")
    args = parser.parse_args()
    if not PAIRS_PATH.exists():
        n, pool = generate_candidates()
        print(f"{PAIRS_PATH.name} not found.")
        print(f"Wrote {n} unlabelled pairs (from {pool} distinct JD phrases) to "
              f"{CANDIDATES_PATH.relative_to(REPO)}.")
        print("Label each pair by hand (1 = same skill, 0 = not; see nlp/experiments/README.md), "
              f"save it as {PAIRS_PATH.relative_to(REPO)} and run this script again.")
        return 2
    if args.method == "tfidf":
        sweep_tfidf()
    else:
        sweep()
    return 0


if __name__ == "__main__":
    sys.exit(main())
