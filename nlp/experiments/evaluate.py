"""
Deliverable 11: evaluation of skill extraction (keyword, TF-IDF, semantic,
hybrid) against the hand-made gold labels.

    python nlp/experiments/evaluate.py [--repeats N]

Data
  data/jd_dataset/gold/gold_sample.csv   the 60 gold JDs (10 per role)
  data/jd_dataset/gold/gold_labels.csv   annotator A, frozen after the A/B resolution
  data/jd_dataset/gold/gold_labels_B.csv annotator B, 12 JDs (human ceiling)
  data/jd_dataset/gold/AGREEMENT.md      A vs B before the resolution
  The gold files are read only. JD-CE-0005 has no gold rows: annotator A
  rejected its only draft row (gold_workbook.xlsx, keep = N), so its gold set
  is empty and every skill a method finds there is a false positive.

Split
  Stratified by role, seed 42: per role, the two double-labelled JDs go to
  test and DEV_PER_ROLE of the other eight are drawn for dev (18 dev / 42
  test, about 1:2). No threshold is tuned in this script: every threshold in
  nlp/config.py was set before (nlp/experiments/THRESHOLDS.md). Dev is used
  for one decision only, which method is "best" (highest micro F1), so that
  the error analysis and the recommendation do not pick the winner on the
  numbers they report. Every result table is on test.

Matching
  Skills are compared by canonical name. NEW: rows (skills the catalogue does
  not have) stay in the gold set and count as misses for every method;
  scores are also given on catalogue skills only, so catalogue gaps and
  method errors can be told apart. Six skills joined the library in v4
  (2026-11-01, after the gold freeze). The guide says only NEW: rows are
  re-mapped when the library grows, so a NEW: term that the v4 library
  resolves and the library at the freeze (6171192) did not is re-mapped
  (V4_REMAP, 24 rows of A, 5 of B). NEW: terms that already had a catalogue
  alias at the freeze ("NEW: Tailwind CSS", "NEW: BigQuery", ...) are left
  as they are: the annotator chose NEW over that alias on purpose.

Metrics (test split)
  micro  precision / recall / F1 from the TP / FP / FN summed over the JDs
  macro  the mean over JDs of the per-JD precision / recall / F1. 0/0 cases:
         precision with no predicted skill is 1 if the JD has no gold skill,
         else 0; recall with no gold skill is 1; F1 = 2TP / (2TP + FP + FN),
         1 when both sets are empty.
  95% CI percentile bootstrap, BOOTSTRAP resamples of the test JDs (seed 42),
         the same resamples for every method.
  Scopes: all gold skills; catalogue skills only; required skills only
  (predictions that match a preferred / bonus gold skill are ignored, the
  extractors do not output importance); per role; per category (the four
  library categories Technical / AI_Digital / Analytical / Soft, plus
  "Business", the v3 business subcategories across categories; a method's
  prediction belongs to its skill's category, NEW: gold rows to none).

Significance
  Hybrid against each other method: approximate randomisation on the mean
  per-JD F1 (PERMUTATIONS random sign flips of the paired differences,
  two-sided, p = (extreme + 1) / (PERMUTATIONS + 1)), Holm-corrected over the
  three comparisons, plus the paired-bootstrap 95% CI of the micro-F1
  difference.

Human ceiling
  Annotator B against A before the resolution (counts parsed from
  AGREEMENT.md) and against the frozen gold, next to every method on the
  same 12 JDs.

Error analysis
  The best method on dev, on test: ERROR_SAMPLE false positives and
  ERROR_SAMPLE false negatives drawn with seed 42 (false negatives from
  catalogue skills only, because every NEW: miss is a catalogue gap and is
  counted in full). Each one is classified in REVIEWED_ERRORS; the script
  stops if a drawn example has no class, so the table cannot drift.

Runtime
  compare_methods.warm_up() and run_all(): median of --repeats runs per JD
  after a warm-up, on the test JDs.

Writes to nlp/experiments/results/:
  evaluation_split.csv          jd_ref, role, split, double-labelled
  evaluation_scores.csv         every split x scope x method: counts, micro / macro P R F1, 95% CI
  evaluation_per_jd.csv         test JDs x method: TP / FP / FN, P / R / F1 (all gold skills)
  evaluation_significance.csv   hybrid vs each method
  evaluation_ceiling.csv        annotator B and the methods on the 12 double-labelled JDs
  evaluation_errors.csv         every test FP / FN of the best method, with context
  evaluation_errors_reviewed.csv the classified sample
  evaluation_runtime.csv        test JDs x method: median seconds
  evaluation_summary.md         all tables
  evaluation_f1_ci.png, evaluation_role_heatmap.png, evaluation_precision_recall.png
"""

import argparse
import csv
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compare_methods as cm  # noqa: E402  (also puts the repo root on sys.path)

from nlp import config, load_catalogue  # noqa: E402

REPO = cm.REPO
GOLD_DIR = REPO / "data" / "jd_dataset" / "gold"
SAMPLE_PATH = GOLD_DIR / "gold_sample.csv"
GOLD_A_PATH = GOLD_DIR / "gold_labels.csv"
GOLD_B_PATH = GOLD_DIR / "gold_labels_B.csv"
AGREEMENT_PATH = GOLD_DIR / "AGREEMENT.md"
RESULTS = cm.RESULTS

# Report order: the baseline, the two L2 representations, then the combination.
METHODS = ("keyword", "tfidf", "semantic", "hybrid")
LABELS = cm.LABELS
ROLES = cm.ROLES
SEED = 42
DEV_PER_ROLE = 3
B_PER_ROLE = 2
BOOTSTRAP = 1000
PERMUTATIONS = 10000
ERROR_SAMPLE = 20
NEW_PREFIX = "NEW:"
CATEGORIES = ("Technical", "AI_Digital", "Analytical", "Soft", "Business")
CATEGORY_LABELS = {"Technical": "Technical", "AI_Digital": "AI & Digital", "Analytical": "Analytical",
                   "Soft": "Soft", "Business": "Business (v3 subcategories)"}
BUSINESS_SUBCATEGORIES = {"Marketing", "Finance & Accounting", "Human Resources", "Business Process",
                          "Business Software"}

# NEW: terms that the v4 library resolves and the library at the gold freeze
# (6171192) did not; see the module docstring.
V4_REMAP = {
    "NEW: DevOps": "DevOps",
    "NEW: Manual Testing": "Software Testing",
    "NEW: Microsoft 365": "Microsoft Office",
    "NEW: Microsoft Office": "Microsoft Office",
    "NEW: Organisational Skills": "Organisational Skills",
    "NEW: Relational Databases": "SQL",
    "NEW: Software Testing": "Software Testing",
}

# ── Error classes ─────────────────────────────────────────────
CATALOGUE_GAP = "Catalogue gap"
AMBIGUOUS = "Ambiguous term"
GENERIC = "Generic word"
PARAPHRASE = "Paraphrase miss"
ANNOTATION = "Annotation disagreement"
ERROR_CLASSES = (CATALOGUE_GAP, AMBIGUOUS, GENERIC, PARAPHRASE, ANNOTATION)

# (jd_ref, skill_name, "FP" | "FN") -> (class, note). Classified by reading the
# JD text around each example (evaluation_errors_reviewed.csv has the context)
# and the gold rows of the same and other JDs. The classes, for both directions:
#   Catalogue gap      the catalogue lacks the skill or a standard term for it
#                      (FN: a missing alias or word form; FP: the specific skill
#                      is missing, so the term maps to a broader one)
#   Ambiguous term     a skill word used in another sense (a role, a degree
#                      subject, the company's activity, an everyday adjective)
#   Generic word       a heading or a generic field word matched a skill
#   Paraphrase miss    the JD words the skill freely (FN: not found; FP: matched
#                      to a neighbouring skill instead)
#   Annotation disagreement  the output is defensible and the gold decision is
#                      a judgement call or differs from the gold of other JDs
REVIEWED_ERRORS = {
    ("JD-CY-0010", "Log Analysis", "FP"): (
        ANNOTATION, "'track alerts, logs, and security incidents'; the gold labels the same duty in "
                    "JD-CY-0005 ('Monitor security alerts and logs') as Log Analysis."),
    ("JD-CE-0002", "UI/UX Design", "FP"): (
        AMBIGUOUS, "'ensuring prompt resolution and positive user experience' (IT support outcome, not design)."),
    ("JD-SD-0008", "Google Analytics", "FP"): (
        GENERIC, "'collect data, provide analytics'; the generic-word filter covers bare 'analytics' only."),
    ("JD-DA-0004", "Business Process Improvement", "FP"): (
        ANNOTATION, "Duty 'strategies to improve business processes'; a duty can count as a skill (guide), "
                    "the annotator did not label it."),
    ("JD-CY-0010", "SIEM", "FP"): (
        PARAPHRASE, "'Assist in Security Event Monitoring' names the SOC practice (in the gold), not the SIEM tool."),
    ("JD-WD-0011", "Project Management", "FP"): (
        ANNOTATION, "'Manage multiple projects simultaneously and deliver projects within deadlines'; the gold "
                    "reads it as Time Management only."),
    ("JD-CY-0001", "Critical Thinking", "FP"): (
        ANNOTATION, "'Good analytical and communication skill' (list-item rule). The gold maps 'analytical' to "
                    "Problem Solving in 13 rows and to Critical Thinking in 1; here to neither."),
    ("JD-WD-0010", "Project Management", "FP"): (
        AMBIGUOUS, "'Meet customer with Project Manager' names a person."),
    ("JD-CE-0008", "SQL", "FP"): (
        CATALOGUE_GAP, "'Microsoft SQL' (Server); the gold has NEW: Microsoft SQL Server, the catalogue only SQL."),
    ("JD-DS-0010", "AI Literacy", "FP"): (
        AMBIGUOUS, "'Degree (Artificial Intelligence / Computer Science ...)' is a degree subject, never evidence."),
    ("JD-SD-0012", "UI/UX Design", "FP"): (
        AMBIGUOUS, "'improve product performance and user experience' (product outcome, not design)."),
    ("JD-DS-0001", "Leadership", "FP"): (
        AMBIGUOUS, "'communicated to the team and leadership' means the managers."),
    ("JD-CE-0008", "Requirements Analysis", "FP"): (
        GENERIC, "'Technical requirements' is a section heading."),
    ("JD-DS-0002", "Data Cleaning", "FP"): (
        ANNOTATION, "'Exposure to ... Data manipulation tasks'; close to the alias 'Data wrangling', not labelled."),
    ("JD-DA-0007", "Decision Making", "FP"): (
        AMBIGUOUS, "'strengthen our operations and decision making with the power of data' describes the company."),
    ("JD-CE-0004", "Agile / Scrum", "FP"): (
        AMBIGUOUS, "'multitask and be agile' means adaptable, not the method."),
    ("JD-WD-0011", "Communication", "FP"): (
        AMBIGUOUS, "'communicate in Mandarin for effective team communication' is a language requirement, "
                   "which the guide excludes (borderline)."),
    ("JD-SD-0009", "Project Management", "FP"): (
        AMBIGUOUS, "'cross-functional teams (PM, QA, DevOps)': PM is a role."),
    ("JD-CY-0008", "Teamwork", "FP"): (
        AMBIGUOUS, "'experience how the security team work': noun 'team' + verb 'work'."),
    ("JD-WD-0004", "Data Visualisation", "FP"): (
        AMBIGUOUS, "'features on the web dashboard (Next.js)' is an app screen; v4 alias 'Dashboards'."),
    ("JD-DS-0007", "Time Management", "FN"): (
        PARAPHRASE, "'the ability to prioritize tasks in a fast-paced environment'."),
    ("JD-SD-0008", "Generative AI", "FN"): (
        CATALOGUE_GAP, "'use of A.I. tools'; no alias such as 'AI tools' (guide rule R4)."),
    ("JD-CE-0002", "Teamwork", "FN"): (
        PARAPHRASE, "'Enjoy collaborating with individuals from diverse backgrounds'."),
    ("JD-SD-0007", "Documentation", "FN"): (
        PARAPHRASE, "'Write clear specs'."),
    ("JD-CY-0008", "Networking", "FN"): (
        PARAPHRASE, "'good understanding in Security and Network related concept'; 'network' alone is too "
                    "generic for an alias."),
    ("JD-WD-0004", "Generative AI", "FN"): (
        CATALOGUE_GAP, "'Use AI coding tools'; no alias such as 'AI tools' (guide rule R4)."),
    ("JD-SD-0011", "Time Management", "FN"): (
        PARAPHRASE, "'meet project timelines' (the alias form is 'meet deadlines')."),
    ("JD-WD-0002", "Cloud Computing", "FN"): (
        CATALOGUE_GAP, "'cloud hosting'; aliases are cloud platforms / infrastructure / services."),
    ("JD-SD-0003", "Problem Solving", "FN"): (
        CATALOGUE_GAP, "'enthusiastic problem-solver'; the agent noun is not an alias form."),
    ("JD-DS-0001", "Adaptability", "FN"): (
        PARAPHRASE, "'Comfortable with ambiguity'."),
    ("JD-CY-0009", "Communication", "FN"): (
        PARAPHRASE, "'communicate effectively' (verb form; below the semantic threshold)."),
    ("JD-DS-0002", "AI Literacy", "FN"): (
        PARAPHRASE, "'develop and deploy AI use cases' (guide rule R4)."),
    ("JD-SD-0007", "Requirements Analysis", "FN"): (
        PARAPHRASE, "'Turn business requirements and UI/UX flows into ... features'."),
    ("JD-DA-0003", "ETL", "FN"): (
        PARAPHRASE, "'extract, validate, and transform multi-source business data'."),
    ("JD-CE-0001", "Cybersecurity", "FN"): (
        CATALOGUE_GAP, "'IT security practices'; aliases are Information security / InfoSec / Cyber defence."),
    ("JD-WD-0011", "Time Management", "FN"): (
        PARAPHRASE, "'deliver projects within deadlines'; hybrid read the sentence as Project Management."),
    ("JD-CY-0005", "Log Analysis", "FN"): (
        PARAPHRASE, "'Monitor security alerts and logs'."),
    ("JD-DS-0001", "Communication", "FN"): (
        PARAPHRASE, "'explain your reasoning and your results to people who are not technical'."),
    ("JD-DA-0005", "Teamwork", "FN"): (
        PARAPHRASE, "'Work closely with project and software team'."),
    ("JD-CY-0004", "Self-Motivation", "FN"): (
        PARAPHRASE, "'Take ownership of your own development'."),
}


# ── Data ──────────────────────────────────────────────────────
def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows):
    with open(RESULTS / name, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def is_new(name):
    return name.startswith(NEW_PREFIX)


def load_gold(path, catalogue):
    """{jd_ref: {skill: {"importance", "evidence"}}}, canonical names, V4_REMAP applied,
    the strongest importance kept when two rows name the same skill; and the number
    of re-mapped rows."""
    rank = {"required": 0, "preferred": 1, "bonus": 2}
    gold, remapped = defaultdict(dict), 0
    for r in read_csv(path):
        name = " ".join(r["skill_name"].split())
        if not name:
            continue
        if name in V4_REMAP:
            name, remapped = V4_REMAP[name], remapped + 1
        elif not is_new(name):
            name = catalogue.lookup(name) or name
        old = gold[r["jd_ref"]].get(name)
        if old is None or rank[r["importance"]] < rank[old["importance"]]:
            gold[r["jd_ref"]][name] = {"importance": r["importance"], "evidence": r["evidence_text"]}
    return gold, remapped


def split_jds(sample, b_refs):
    """{jd_ref: "dev" | "test"}: per role, B's JDs to test, DEV_PER_ROLE others to dev."""
    rng = random.Random(SEED)
    split = {}
    for role in ROLES:
        refs = sorted(r["jd_ref"] for r in sample if r["role_code"] == role)
        pool = [ref for ref in refs if ref not in b_refs]
        dev = set(rng.sample(pool, DEV_PER_ROLE))
        split.update({ref: "dev" if ref in dev else "test" for ref in refs})
    return split


def ceiling_from_agreement():
    """(both, A skills, B skills) of the pre-resolution A vs B comparison in AGREEMENT.md."""
    text = AGREEMENT_PATH.read_text(encoding="utf-8")
    m = re.search(r"= 2 x (\d+) / \((\d+) A \+ (\d+) B skills\)", text)
    if not m:
        raise SystemExit("AGREEMENT.md: positive specific agreement line not found")
    return tuple(int(g) for g in m.groups())


# ── Counting ──────────────────────────────────────────────────
def category_of(name, catalogue):
    entry = catalogue.get(name)
    if entry is None:
        return set()
    cats = {entry["category"]}
    if entry.get("subcategory") in BUSINESS_SUBCATEGORIES:
        cats.add("Business")
    return cats


def scope_sets(scope, gold, predicted, catalogue):
    """(gold set, predicted set) of one JD in a scope."""
    if scope == "all":
        return set(gold), predicted
    if scope == "catalogue":
        return {s for s in gold if not is_new(s)}, predicted
    if scope == "required":
        required = {s for s, g in gold.items() if g["importance"] == "required"}
        ignored = set(gold) - required
        return required, predicted - ignored
    if scope.startswith("category:"):
        cat = scope.split(":", 1)[1]
        return ({s for s in gold if cat in category_of(s, catalogue)},
                {s for s in predicted if cat in category_of(s, catalogue)})
    raise ValueError(scope)


def counts(refs, gold, found, method, scope, catalogue):
    """Array (len(refs), 3) of TP, FP, FN per JD."""
    out = np.zeros((len(refs), 3), dtype=int)
    for i, ref in enumerate(refs):
        g, p = scope_sets(scope, gold.get(ref, {}), found[ref][method], catalogue)
        out[i] = (len(g & p), len(p - g), len(g - p))
    return out


def micro(c):
    """Micro P, R, F1 from summed counts; c is (..., n_jds, 3)."""
    tp, fp, fn = (c[..., k].sum(axis=-1).astype(float) for k in range(3))
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(tp + fp > 0, tp / (tp + fp), 0.0)
        r = np.where(tp + fn > 0, tp / (tp + fn), 0.0)
        f = np.where(p + r > 0, 2 * p * r / (p + r), 0.0)
    return p, r, f


def per_jd(c):
    """Per-JD P, R, F1 with the 0/0 conventions of the docstring; c is (n_jds, 3)."""
    tp, fp, fn = (c[:, k].astype(float) for k in range(3))
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(tp + fp > 0, tp / (tp + fp), np.where(tp + fn > 0, 0.0, 1.0))
        r = np.where(tp + fn > 0, tp / (tp + fn), 1.0)
        f = np.where(2 * tp + fp + fn > 0, 2 * tp / (2 * tp + fp + fn), 1.0)
    return p, r, f


def score_row(c, resamples, macro=True):
    """Point values and 95% CIs for one count array."""
    row = {"jds": len(c), "gold": int(c[:, 0].sum() + c[:, 2].sum()),
           "predicted": int(c[:, 0].sum() + c[:, 1].sum()),
           "tp": int(c[:, 0].sum()), "fp": int(c[:, 1].sum()), "fn": int(c[:, 2].sum())}
    boot = c[resamples]                                   # (BOOTSTRAP, n_jds, 3)
    for name, point, dist in zip(("micro_p", "micro_r", "micro_f1"), micro(c), micro(boot)):
        row[name] = round(float(point), 3)
        row[name + "_lo"], row[name + "_hi"] = (round(float(v), 3) for v in np.percentile(dist, [2.5, 97.5]))
    if macro:
        for name, values in zip(("macro_p", "macro_r", "macro_f1"), per_jd(c)):
            dist = values[resamples].mean(axis=1)
            row[name] = round(float(values.mean()), 3)
            row[name + "_lo"], row[name + "_hi"] = (round(float(v), 3) for v in np.percentile(dist, [2.5, 97.5]))
    return row


# ── Significance ──────────────────────────────────────────────
def randomisation_p(a, b, rng):
    """Two-sided approximate randomisation test on the mean of paired differences."""
    d = a - b
    observed = abs(d.mean())
    signs = rng.choice([-1.0, 1.0], size=(PERMUTATIONS, len(d)))
    extreme = int((np.abs((signs * d).mean(axis=1)) >= observed - 1e-12).sum())
    return (extreme + 1) / (PERMUTATIONS + 1)


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


# ── Error analysis ────────────────────────────────────────────
def error_rows(refs, gold, hits, method, text_of):
    """Every FP and FN of one method on refs, with context."""
    rows = []
    for ref in refs:
        g = gold.get(ref, {})
        by_name = {s["skill_name"]: s for s in hits[ref][method]}
        for name in sorted(set(by_name) - set(g)):
            s = by_name[name]
            rows.append({"jd_ref": ref, "skill_name": name, "error": "FP", "found_by": s["method"],
                         "confidence": round(s["confidence_score"], 3), "jd_text": s["raw_skill_text"],
                         "importance": "", "is_new": False,
                         "context": cm.context(text_of[ref], s["start_char"], s["end_char"])})
        for name in sorted(set(g) - set(by_name)):
            rows.append({"jd_ref": ref, "skill_name": name, "error": "FN", "found_by": "",
                         "confidence": "", "jd_text": "", "importance": g[name]["importance"],
                         "is_new": is_new(name), "context": g[name]["evidence"]})
    return rows


def draw_sample(errors):
    rng = random.Random(SEED)
    fps = [r for r in errors if r["error"] == "FP"]
    fns = [r for r in errors if r["error"] == "FN" and not r["is_new"]]
    return rng.sample(fps, min(ERROR_SAMPLE, len(fps))) + rng.sample(fns, min(ERROR_SAMPLE, len(fns)))


def reviewed_rows(sample):
    rows, missing = [], []
    for r in sample:
        key = (r["jd_ref"], r["skill_name"], r["error"])
        if key not in REVIEWED_ERRORS:
            missing.append(key)
            continue
        cls, note = REVIEWED_ERRORS[key]
        if cls not in ERROR_CLASSES:
            raise SystemExit(f"unknown error class {cls!r} for {key}")
        rows.append({**r, "class": cls, "note": note})
    unused = set(REVIEWED_ERRORS) - {(r["jd_ref"], r["skill_name"], r["error"]) for r in sample}
    return rows, missing, unused


# ── Figures (half page width in a Word report) ────────────────
# Same palette, fonts and helpers as compare_methods.py: one colour per method
# in every figure. The heat map uses the reference palette's blue sequential
# ramp; annotator B is the muted grey, which no method uses.
HUMAN = cm.BOTH
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
        "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]


def figure_f1_ci(plt, scores, ceiling_f1, path):
    """Micro F1 with 95% CI per method: all gold skills and catalogue skills only."""
    fig = plt.figure(figsize=(cm.FIG_WIDTH, 2.35))
    ax = fig.add_axes([0.20, 0.19, 0.74, 0.62])
    cm.style_axes(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(len(METHODS) - 0.45, -0.55)
    ax.set_yticks(range(len(METHODS)), [LABELS[m] for m in METHODS])
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0], ["0", "0.2", "0.4", "0.6", "0.8", "1.0"])
    ax.set_xlabel("Micro F1 on the test JDs (95% bootstrap CI)")
    ax.axvline(ceiling_f1, color=HUMAN, linewidth=1, linestyle=(0, (3, 2)), zorder=1)
    ax.text(ceiling_f1, -0.62, f"A vs B {ceiling_f1:.2f}", ha="center", va="bottom", fontsize=6.5,
            color=cm.INK_2)
    for y, method in enumerate(METHODS):
        for dy, scope, filled in ((-0.13, "all", True), (0.13, "catalogue", False)):
            s = scores[("test", scope, method)]
            ax.plot([s["micro_f1_lo"], s["micro_f1_hi"]], [y + dy, y + dy], color=cm.COLORS[method],
                    linewidth=1.5, solid_capstyle="round", zorder=2)
            ax.plot([s["micro_f1"]], [y + dy], marker="o", markersize=5.5, zorder=3,
                    color=cm.COLORS[method] if filled else "white", markeredgecolor=cm.COLORS[method],
                    markeredgewidth=1.3)
            ax.text(s["micro_f1_lo"] - 0.02, y + dy, f"{s['micro_f1']:.2f}", va="center", ha="right",
                    fontsize=6.5, color=cm.INK_2)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", linestyle="none", markersize=5.5, color=cm.INK_2,
                      label="All gold skills"),
               Line2D([], [], marker="o", linestyle="none", markersize=5.5, color="white",
                      markeredgecolor=cm.INK_2, markeredgewidth=1.3, label="Catalogue skills only")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.57, 1.0), ncol=2, frameon=False,
               handletextpad=0.3, columnspacing=1.2)
    fig.savefig(path)
    plt.close(fig)


def figure_role_heatmap(plt, scores, role_jds, path):
    """Micro F1 per role (rows) and method (columns), all gold skills, test split."""
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Rectangle
    cmap = ListedColormap(RAMP)
    fig = plt.figure(figsize=(cm.FIG_WIDTH, 2.55))
    ax = fig.add_axes([0.37, 0.06, 0.60, 0.84])
    ax.set_xlim(0, len(METHODS))
    ax.set_ylim(len(ROLES), 0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.tick_params(length=0)
    ax.xaxis.tick_top()
    ax.set_xticks([i + 0.5 for i in range(len(METHODS))], [LABELS[m] for m in METHODS], color=cm.INK_2)
    ax.set_yticks([i + 0.5 for i in range(len(ROLES))],
                  [f"{name} ({role_jds[code]})" for code, name in ROLES.items()])
    for i, code in enumerate(ROLES):
        for j, method in enumerate(METHODS):
            value = scores[("test", f"role:{code}", method)]["micro_f1"]
            color = cmap(min(int(value * len(RAMP)), len(RAMP) - 1))
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=color, edgecolor="white", linewidth=1.5))
            ax.text(j + 0.5, i + 0.5, f"{value:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if value >= 0.55 else cm.INK)
    fig.text(0.37, 0.005, "Micro F1, all gold skills, test JDs (n per role)", fontsize=6.5, color=cm.MUTED,
             va="bottom")
    fig.savefig(path)
    plt.close(fig)


def figure_precision_recall(plt, scores, ceiling, path):
    """Micro precision vs recall per method (95% CI crosses), iso-F1 curves, annotator B."""
    fig = plt.figure(figsize=(cm.FIG_WIDTH, 3.0))
    ax = fig.add_axes([0.15, 0.14, 0.80, 0.80])
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(cm.BASE)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(length=0, pad=3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    ax.set_xticks(ticks, [f"{t:g}" for t in ticks])
    ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
    ax.set_xlabel("Micro recall (all gold skills)")
    ax.set_ylabel("Micro precision")
    r = np.linspace(0.01, 1, 400)
    for f1 in (0.4, 0.6, 0.8):
        with np.errstate(divide="ignore", invalid="ignore"):
            p = f1 * r / (2 * r - f1)
        ok = (p > 0) & (p <= 1) & (2 * r > f1)
        ax.plot(r[ok], p[ok], color=cm.GRID, linewidth=0.8, zorder=1)
        ax.text(1.0, f1 / (2 - f1), f"F1 {f1:g}", fontsize=6, color=cm.MUTED, ha="right", va="bottom")
    offsets = {"keyword": (-0.04, 0.05), "tfidf": (0.03, -0.06), "semantic": (-0.03, -0.07),
               "hybrid": (0.03, -0.07)}
    for method in METHODS:
        s = scores[("test", "all", method)]
        color = cm.COLORS[method]
        ax.plot([s["micro_r_lo"], s["micro_r_hi"]], [s["micro_p"]] * 2, color=color, linewidth=1.2, zorder=2)
        ax.plot([s["micro_r"]] * 2, [s["micro_p_lo"], s["micro_p_hi"]], color=color, linewidth=1.2, zorder=2)
        ax.plot([s["micro_r"]], [s["micro_p"]], marker="o", markersize=6, color=color,
                markeredgecolor="white", markeredgewidth=1.2, zorder=3)
        dx, dy = offsets[method]
        ax.text(s["micro_r"] + dx, s["micro_p"] + dy, LABELS[method], fontsize=7, color=cm.INK,
                ha="left" if dx > 0 else "right", va="center")
    p_b, r_b = ceiling
    ax.plot([r_b], [p_b], marker="D", markersize=5.5, color=HUMAN, markeredgecolor="white",
            markeredgewidth=1.0, zorder=3)
    ax.text(r_b, p_b + 0.04, "Annotator B vs A\n(12 JDs)", fontsize=6.5, color=cm.INK_2,
            ha="center", va="bottom")
    fig.savefig(path)
    plt.close(fig)


# ── Summary ───────────────────────────────────────────────────
def ci(s, key):
    return f"{s[key]:.3f} [{s[key + '_lo']:.2f}, {s[key + '_hi']:.2f}]"


def write_summary(ctx):
    s, md = ctx["scores"], cm.md_table
    lines = [
        "# Skill extraction evaluation (Deliverable 11)",
        "",
        f"Generated by `nlp/experiments/evaluate.py` on {time.strftime('%Y-%m-%d')}. Gold: "
        f"`gold_labels.csv` (annotator A, frozen), {ctx['n_gold_rows']} skills in {len(ctx['sample'])} JDs "
        f"({ctx['n_new']} `NEW:` = not in the catalogue; {ctx['remapped']} `NEW:` rows re-mapped to v4 "
        "library skills, see the script docstring). Library "
        f"{len(ctx['catalogue'])} skills. Settings: MATCH {config.MATCH_THRESHOLD:.2f}, list items "
        f"{config.LIST_ITEM_THRESHOLD:.2f}, TF-IDF {config.TFIDF_ANALYZER} {config.TFIDF_MATCH_THRESHOLD:.2f} "
        "(all set before this evaluation; none tuned here).",
        "",
        f"Split (seed {SEED}, stratified by role): {ctx['n_dev']} dev / {ctx['n_test']} test JDs; the 12 "
        "double-labelled JDs are all in test. Dev is only used to pick the best method. "
        f"CIs: percentile bootstrap, {BOOTSTRAP} resamples of the test JDs.",
        "",
        "## Dev split: method selection",
        "",
    ]
    lines += md(["Method", "Micro P", "Micro R", "Micro F1"],
                [[LABELS[m], f"{s[('dev', 'all', m)]['micro_p']:.3f}", f"{s[('dev', 'all', m)]['micro_r']:.3f}",
                  f"{s[('dev', 'all', m)]['micro_f1']:.3f}"] for m in METHODS])
    lines += ["", f"Best on dev: **{LABELS[ctx['best']]}**.", "", "## Test split: main results", "",
              "All gold skills (`NEW:` rows count as misses for every method):", ""]
    lines += md(["Method", "Gold", "Found", "TP", "Micro P", "Micro R", "Micro F1", "Macro P", "Macro R",
                 "Macro F1"],
                [[LABELS[m], r["gold"], r["predicted"], r["tp"], ci(r, "micro_p"), ci(r, "micro_r"),
                  ci(r, "micro_f1"), ci(r, "macro_p"), ci(r, "macro_r"), ci(r, "macro_f1")]
                 for m in METHODS for r in [s[("test", "all", m)]]])
    lines += ["", "Catalogue skills only (`NEW:` rows removed from the gold set):", ""]
    lines += md(["Method", "Gold", "Micro P", "Micro R", "Micro F1", "Macro F1"],
                [[LABELS[m], r["gold"], ci(r, "micro_p"), ci(r, "micro_r"), ci(r, "micro_f1"), ci(r, "macro_f1")]
                 for m in METHODS for r in [s[("test", "catalogue", m)]]])
    n_new_test = s[("test", "all", "hybrid")]["gold"] - s[("test", "catalogue", "hybrid")]["gold"]
    lines += ["", f"`NEW:` misses on test: {n_new_test} of {s[('test', 'all', 'hybrid')]['gold']} gold skills "
              f"({100 * n_new_test / s[('test', 'all', 'hybrid')]['gold']:.0f}%), the same for every method. "
              "Most frequent: " + ", ".join(f"{n[5:]} {c}" for n, c in ctx["top_new"]) + ".", ""]
    lines += ["Without the v4 re-map (all gold skills, test): " + ", ".join(
        f"{LABELS[m]} F1 {ctx['no_remap'][m]:.3f}" for m in METHODS) + ".", ""]
    lines += ["Required skills only (predictions matching a preferred / bonus gold skill are ignored):", ""]
    lines += md(["Method", "Gold", "Micro P", "Micro R", "Micro F1"],
                [[LABELS[m], r["gold"], ci(r, "micro_p"), ci(r, "micro_r"), ci(r, "micro_f1")]
                 for m in METHODS for r in [s[("test", "required", m)]]])

    lines += ["", "## Per role (test, micro F1 [95% CI], all gold skills)", ""]
    lines += md(["Role", "JDs"] + [LABELS[m] for m in METHODS],
                [[name, ctx["role_jds"][code]] + [ci(s[("test", f"role:{code}", m)], "micro_f1") for m in METHODS]
                 for code, name in ROLES.items()], text_columns=1)
    lines += ["", "## Per category (test, micro P / R / F1)", "",
              "A prediction belongs to its skill's category; `NEW:` gold rows belong to no category, so these "
              "are catalogue-skill scores. Business = the v3 business subcategories (Marketing, Finance & "
              "Accounting, Human Resources, Business Process, Business Software), which sit inside Technical "
              "and Analytical.", ""]
    rows = []
    for cat in CATEGORIES:
        for m in METHODS:
            r = s[("test", f"category:{cat}", m)]
            rows.append([CATEGORY_LABELS[cat], LABELS[m], r["gold"], r["predicted"], f"{r['micro_p']:.3f}",
                         f"{r['micro_r']:.3f}", ci(r, "micro_f1")])
    lines += md(["Category", "Method", "Gold", "Found", "P", "R", "F1 [95% CI]"], rows, text_columns=2)

    lines += ["", "## Significance (test, hybrid vs each method)", "",
              f"Approximate randomisation on the mean per-JD F1 ({PERMUTATIONS} sign flips, two-sided), "
              "Holm-corrected; paired-bootstrap 95% CI of the micro-F1 difference (same resamples).", ""]
    lines += md(["Comparison", "Mean per-JD F1 diff", "p", "p (Holm)", "Micro F1 diff [95% CI]",
                 "JDs hybrid better / worse / tie"],
                [[f"Hybrid vs {LABELS[r['other']]}", f"{r['macro_f1_diff']:+.3f}", f"{r['p']:.4f}",
                  f"{r['p_holm']:.4f}", f"{r['micro_f1_diff']:+.3f} [{r['micro_f1_diff_lo']:+.3f}, "
                  f"{r['micro_f1_diff_hi']:+.3f}]", f"{r['better']} / {r['worse']} / {r['tie']}"]
                 for r in ctx["significance"]])

    both, a_n, b_n = ctx["agreement"]
    lines += ["", "## Human ceiling (the 12 double-labelled JDs)", "",
              f"Annotator B vs A before the resolution (`AGREEMENT.md`): {both} shared of {a_n} A and {b_n} B "
              "skills. B vs the frozen gold is optimistic as a ceiling, because the resolution adopted some of "
              "B's labels. The methods are scored on the same 12 JDs against the frozen gold.", ""]
    lines += md(["Labeller", "Reference", "P", "R", "F1 (all)", "F1 (catalogue)"],
                [[r["who"], r["reference"], f"{r['p']:.3f}", f"{r['r']:.3f}", f"{r['f1']:.3f}",
                  r["f1_catalogue"]] for r in ctx["ceiling"]], text_columns=2)

    lines += ["", f"## Error analysis ({LABELS[ctx['best']]}, test)", "",
              f"{ctx['n_fp']} false positives and {ctx['n_fn']} false negatives ({ctx['n_fn_new']} of them `NEW:`). "
              f"Sample of {ERROR_SAMPLE} FP and {ERROR_SAMPLE} catalogue-skill FN (seed {SEED}), classified by "
              "reading the JD text (`evaluation_errors_reviewed.csv`).", ""]
    for kind, title in (("FP", "false positives"), ("FN", "catalogue-skill false negatives")):
        top = Counter(r["skill_name"] for r in ctx["errors"] if r["error"] == kind and not r["is_new"])
        lines += [f"Most frequent {title}: " + ", ".join(f"{n} {c}" for n, c in top.most_common(8)) + "."]
    lines += [""]
    if ctx["reviewed"]:
        table = Counter((r["error"], r["class"]) for r in ctx["reviewed"])
        lines += md(["Class", "FP", "FN"], [[c, table[("FP", c)], table[("FN", c)]] for c in ERROR_CLASSES])
        lines += [""]
        lines += md(["#", "Error", "JD", "Skill", "Class", "Note"],
                    [[i, r["error"], r["jd_ref"], r["skill_name"], r["class"], r["note"]]
                     for i, r in enumerate(ctx["reviewed"], 1)], text_columns=6)
    if ctx["missing"]:
        lines += ["", f"**{len(ctx['missing'])} sampled examples are not classified yet.**"]

    lines += ["", "## Runtime per JD (test JDs)", "",
              f"Median of {ctx['repeats']} runs per JD after a warm-up, CPU. Cold start: "
              + ", ".join(f"{k} {v:.1f} s" for k, v in ctx["cold"].items()) + ".", ""]
    lines += md(["Method", "Mean ms", "Median ms", "Max ms"],
                [[LABELS[m], f"{r['mean']:.1f}", f"{r['median']:.1f}", f"{r['max']:.1f}"]
                 for m in METHODS for r in [ctx["runtime"][m]]])
    (RESULTS / "evaluation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repeats", type=int, default=cm.REPEATS, help="timed runs per JD and method")
    args = parser.parse_args()
    cm.REPEATS = args.repeats

    catalogue = load_catalogue()
    sample = read_csv(SAMPLE_PATH)
    text_of = {r["jd_ref"]: r["raw_text"] for r in sample}
    role_of = {r["jd_ref"]: r["role_code"] for r in sample}
    gold, remapped = load_gold(GOLD_A_PATH, catalogue)
    gold_b, _ = load_gold(GOLD_B_PATH, catalogue)
    b_refs = set(gold_b)
    if len(b_refs) != B_PER_ROLE * len(ROLES):
        raise SystemExit(f"expected {B_PER_ROLE * len(ROLES)} double-labelled JDs, found {len(b_refs)}")
    split = split_jds(sample, b_refs)
    refs = {name: [r["jd_ref"] for r in sample if split[r["jd_ref"]] == name] for name in ("dev", "test")}

    print(f"{len(sample)} gold JDs ({len(refs['dev'])} dev / {len(refs['test'])} test); warming up ...")
    cold = cm.warm_up(sample[0]["raw_text"])
    hits, seconds = cm.run_all(sample)
    found = {ref: {m: {s["skill_name"] for s in hits[ref][m]} for m in METHODS} for ref in hits}

    # Scores
    rng = np.random.default_rng(SEED)
    resamples = {name: rng.integers(0, len(r), size=(BOOTSTRAP, len(r))) for name, r in refs.items()}
    scopes = ["all", "catalogue", "required"] + [f"category:{c}" for c in CATEGORIES]
    scores, per_jd_counts = {}, {}
    for name in ("dev", "test"):
        for scope in scopes:
            for m in METHODS:
                c = counts(refs[name], gold, found, m, scope, catalogue)
                per_jd_counts[(name, scope, m)] = c
                scores[(name, scope, m)] = score_row(c, resamples[name], macro=scope in ("all", "catalogue",
                                                                                          "required"))
    role_jds = Counter(role_of[ref] for ref in refs["test"])
    for code in ROLES:
        mine = [ref for ref in refs["test"] if role_of[ref] == code]
        role_resamples = np.random.default_rng(SEED).integers(0, len(mine), size=(BOOTSTRAP, len(mine)))
        for m in METHODS:
            scores[("test", f"role:{code}", m)] = score_row(counts(mine, gold, found, m, "all", catalogue),
                                                            role_resamples, macro=False)
    best = max(METHODS, key=lambda m: scores[("dev", "all", m)]["micro_f1"])

    # Sensitivity: the same scores without V4_REMAP
    gold_raw = defaultdict(dict)
    for r in read_csv(GOLD_A_PATH):
        name = " ".join(r["skill_name"].split())
        gold_raw[r["jd_ref"]][name if is_new(name) else catalogue.lookup(name) or name] = {
            "importance": r["importance"], "evidence": r["evidence_text"]}
    no_remap = {m: float(micro(counts(refs["test"], gold_raw, found, m, "all", catalogue))[2]) for m in METHODS}

    # Significance
    sig_rng = np.random.default_rng(SEED)
    f1_of = {m: per_jd(per_jd_counts[("test", "all", m)])[2] for m in METHODS}
    boot_f1 = {m: micro(per_jd_counts[("test", "all", m)][resamples["test"]])[2] for m in METHODS}
    significance = []
    for other in [m for m in METHODS if m != "hybrid"]:
        d = f1_of["hybrid"] - f1_of[other]
        diff_dist = boot_f1["hybrid"] - boot_f1[other]
        lo, hi = np.percentile(diff_dist, [2.5, 97.5])
        significance.append({
            "other": other, "macro_f1_diff": round(float(d.mean()), 4),
            "p": randomisation_p(f1_of["hybrid"], f1_of[other], sig_rng),
            "micro_f1_diff": round(float(scores[("test", "all", "hybrid")]["micro_f1"]
                                         - scores[("test", "all", other)]["micro_f1"]), 3),
            "micro_f1_diff_lo": round(float(lo), 3), "micro_f1_diff_hi": round(float(hi), 3),
            "better": int((d > 1e-12).sum()), "worse": int((d < -1e-12).sum()), "tie": int((abs(d) <= 1e-12).sum())})
    for row, p in zip(significance, holm([r["p"] for r in significance])):
        row["p"], row["p_holm"] = round(row["p"], 4), round(p, 4)

    # Human ceiling on the double-labelled JDs
    both, a_n, b_n = ceiling_from_agreement()
    b_list = sorted(b_refs)
    ceiling = [{"who": "Annotator B", "reference": "A before resolution (AGREEMENT.md)",
                "p": both / b_n, "r": both / a_n, "f1": 2 * both / (a_n + b_n), "f1_catalogue": "-"}]
    b_found = {ref: {m: set(gold_b[ref]) for m in METHODS} for ref in b_list}
    cb = counts(b_list, gold, b_found, "hybrid", "all", catalogue)
    cb_cat = counts(b_list, gold, {ref: {"hybrid": {s for s in gold_b[ref] if not is_new(s)}} for ref in b_list},
                    "hybrid", "catalogue", catalogue)
    p, r, f = micro(cb)
    ceiling.append({"who": "Annotator B", "reference": "frozen gold", "p": float(p), "r": float(r), "f1": float(f),
                    "f1_catalogue": f"{float(micro(cb_cat)[2]):.3f}"})
    for m in METHODS:
        p, r, f = micro(counts(b_list, gold, found, m, "all", catalogue))
        ceiling.append({"who": LABELS[m], "reference": "frozen gold", "p": float(p), "r": float(r), "f1": float(f),
                        "f1_catalogue": f"{float(micro(counts(b_list, gold, found, m, 'catalogue', catalogue))[2]):.3f}"})

    # Error analysis
    errors = error_rows(refs["test"], gold, hits, best, text_of)
    sample_errors = draw_sample(errors)
    reviewed, missing, unused = reviewed_rows(sample_errors)
    if unused:
        raise SystemExit(f"REVIEWED_ERRORS has examples that are no longer drawn: {sorted(unused)}")

    # Runtime
    runtime = {}
    for m in METHODS:
        ms = [seconds[ref][m] * 1000 for ref in refs["test"]]
        runtime[m] = {"mean": statistics.mean(ms), "median": statistics.median(ms), "max": max(ms)}

    # Outputs
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_csv("evaluation_split.csv", [{"jd_ref": r["jd_ref"], "role_code": r["role_code"],
                                        "split": split[r["jd_ref"]], "double_labelled": r["jd_ref"] in b_refs,
                                        "gold_skills": len(gold.get(r["jd_ref"], {}))} for r in sample])
    write_csv("evaluation_scores.csv", [{"split": k[0], "scope": k[1], "method": k[2], **v}
                                        for k, v in scores.items()])
    rows = []
    for m in METHODS:
        c = per_jd_counts[("test", "all", m)]
        for ref, (tp, fp, fn), p, r, f in zip(refs["test"], c, *per_jd(c)):
            rows.append({"jd_ref": ref, "role_code": role_of[ref], "method": m, "tp": tp, "fp": fp, "fn": fn,
                         "precision": round(float(p), 3), "recall": round(float(r), 3), "f1": round(float(f), 3)})
    write_csv("evaluation_per_jd.csv", rows)
    write_csv("evaluation_significance.csv", significance)
    write_csv("evaluation_ceiling.csv", [{**r, "p": round(r["p"], 3), "r": round(r["r"], 3),
                                          "f1": round(r["f1"], 3)} for r in ceiling])
    write_csv("evaluation_errors.csv", errors)
    write_csv("evaluation_errors_reviewed.csv",
              reviewed or [{**r, "class": "", "note": ""} for r in sample_errors])
    write_csv("evaluation_runtime.csv", [{"jd_ref": ref, "role_code": role_of[ref], "chars": len(text_of[ref]),
                                          **{f"{m}_s": round(seconds[ref][m], 5) for m in METHODS}}
                                         for ref in refs["test"]])

    plt = cm.setup_matplotlib()
    figure_f1_ci(plt, scores, ceiling[0]["f1"], RESULTS / "evaluation_f1_ci.png")
    figure_role_heatmap(plt, scores, role_jds, RESULTS / "evaluation_role_heatmap.png")
    figure_precision_recall(plt, scores, (ceiling[0]["p"], ceiling[0]["r"]),
                            RESULTS / "evaluation_precision_recall.png")

    test_new = Counter(s for ref in refs["test"] for s in gold.get(ref, {}) if is_new(s))
    write_summary({
        "scores": scores, "sample": sample, "catalogue": catalogue, "remapped": remapped,
        "n_gold_rows": sum(len(v) for v in gold.values()),
        "n_new": sum(is_new(s) for v in gold.values() for s in v),
        "n_dev": len(refs["dev"]), "n_test": len(refs["test"]), "best": best, "role_jds": role_jds,
        "top_new": test_new.most_common(8), "no_remap": no_remap, "significance": significance,
        "agreement": (both, a_n, b_n), "ceiling": ceiling, "reviewed": reviewed, "missing": missing,
        "errors": errors,
        "n_fp": sum(r["error"] == "FP" for r in errors), "n_fn": sum(r["error"] == "FN" for r in errors),
        "n_fn_new": sum(r["error"] == "FN" and r["is_new"] for r in errors),
        "runtime": runtime, "cold": cold, "repeats": cm.REPEATS})
    print((RESULTS / "evaluation_summary.md").read_text(encoding="utf-8"))
    if missing:
        print(f"{len(missing)} sampled errors have no class in REVIEWED_ERRORS; "
              "see results/evaluation_errors_reviewed.csv")


if __name__ == "__main__":
    main()
