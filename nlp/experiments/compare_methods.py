"""
S2-02-02: compare Level 1 (keyword), Level 2 (semantic) and hybrid extraction
on the real JDs, to find inconsistent behaviour before integration.

    python nlp/experiments/compare_methods.py

Input: data/jd_dataset/jd_dataset.csv. Every JD is run through
nlp.extract_skills() with each method (after a warm-up; REPEATS timed runs,
the median counts). Writes to nlp/experiments/results/:

  method_comparison.csv              one row per JD x method x skill found
  method_counts.csv                  skills per JD per method (mean / median / min / max), overall and per role
  method_overlap.csv                 per JD: keyword vs semantic skill sets and their Jaccard index
  method_skill_agreement.csv         per skill: JDs where only keyword / both / only semantic found it
  method_runtime.csv                 per JD and method: median seconds of REPEATS runs
  method_disagreements.csv           every skill that keyword or semantic found and the other did not, with context
  method_disagreements_reviewed.csv  the examples classified by hand (REVIEWED below)
  method_comparison_summary.md       all tables
  method_skills_per_jd.png, method_agreement.png, method_runtime.png

This is a preliminary comparison, not an evaluation. Precision / recall / F1
are only computed if data/jd_dataset/gold/gold_labels.csv has hand-made rows,
and then only on the JDs those rows cover. gold_labels_draft.csv is a keyword
pre-fill and is never used as ground truth.
"""

import csv
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from nlp import config, extract_skills, load_catalogue  # noqa: E402
from nlp.model import encode, get_model, get_spacy, skill_embeddings  # noqa: E402

JD_PATH = REPO / "data" / "jd_dataset" / "jd_dataset.csv"
GOLD_PATH = REPO / "data" / "jd_dataset" / "gold" / "gold_labels.csv"
RESULTS = Path(__file__).resolve().parent / "results"
METHODS = ("keyword", "semantic", "hybrid")
REPEATS = 5
CONTEXT = 70           # characters of JD text shown on each side of a disagreement
TOP = 15
ROLES = {"DATA_ANALYST": "Data Analyst", "DATA_SCIENTIST": "Data Scientist",
         "SOFTWARE_DEV": "Software Developer", "CYBER_ANALYST": "Cybersecurity Analyst",
         "CLOUD_ENGINEER": "Cloud Engineer", "WEB_DEV": "Web Developer"}

# ── Disagreements classified by hand ──────────────────────────
# Chosen from method_disagreements.csv by reading the JD context. found_by is
# the method that found the skill (the other one did not). The script checks
# that each example still occurs, so the table cannot drift from the outputs.
# The examples fixed on 2026-10-29 (A/B Testing, Google Analytics, R, MySQL,
# UI/UX Design, Firewall Management, Time Management, Self-Motivation, Monitoring
# & Observability) no longer occur: see results/fixes_2026-10_before_after.md.
KEYWORD_MISS = "Likely keyword miss (synonym / paraphrase)"
SEMANTIC_FP = "Likely semantic false positive"
AMBIGUOUS = "Ambiguous-term issue"
CATALOGUE_GAP = "Catalogue gap"
REVIEWED = [
    {"jd_ref": "JD-DS-0005", "skill_name": "Data Visualisation", "found_by": "semantic", "category": KEYWORD_MISS,
     "note": "Paraphrase; no alias covers 'develop dashboards' (8 JDs have such a semantic-only hit)."},
    {"jd_ref": "JD-DA-0004", "skill_name": "Teamwork", "found_by": "semantic", "category": KEYWORD_MISS,
     "note": "Paraphrase; aliases are 'Collaboration', 'Team player', 'Cooperative work' (11 JDs)."},
    {"jd_ref": "JD-CY-0005", "skill_name": "Vulnerability Assessment", "found_by": "semantic", "category": KEYWORD_MISS,
     "note": "Paraphrase; 0.868 is the highest semantic-only score."},
    {"jd_ref": "JD-DS-0002", "skill_name": "Business Analysis", "found_by": "semantic", "category": SEMANTIC_FP,
     "note": "Hiring boilerplate ('subject to business needs and available headcount')."},
    {"jd_ref": "JD-WD-0010", "skill_name": "Project Management", "found_by": "semantic", "category": SEMANTIC_FP,
     "note": "'Meet customer with Project Manager' names a person, not a requirement."},
    {"jd_ref": "JD-CE-0002", "skill_name": "Prompt Engineering", "found_by": "semantic", "category": AMBIGUOUS,
     "note": "'prompt resolution' means quick. Keyword reads 'user experience' in the same phrase as "
             "UI/UX Design; hybrid keeps that and drops this overlapping semantic hit."},
]


# ── Running the methods ───────────────────────────────────────
def load_jds():
    with open(JD_PATH, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if (r.get("raw_text") or "").strip()]


def warm_up(text):
    """Load the model, spaCy and both embedding sets once; return the cold-start times."""
    times = {}
    t0 = time.perf_counter()
    get_model()
    times["model"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    get_spacy()
    times["spaCy"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    catalogue = load_catalogue()
    skill_embeddings(catalogue)
    item_mode = config.LIST_ITEM_TEXT_MODE
    skill_embeddings(catalogue, item_mode, use_disk=item_mode == config.SKILL_TEXT_MODE)
    times["skill embeddings"] = time.perf_counter() - t0
    for method in METHODS:
        extract_skills(text, method=method)
    return times


def run_all(jds):
    """{jd_ref: {method: [ExtractedSkill]}} and {jd_ref: {method: median seconds}}.

    The methods take turns within each repeat, so a burst of background load
    slows all three alike instead of one method's runs.
    """
    found, seconds = defaultdict(dict), defaultdict(dict)
    for jd in jds:
        runs = defaultdict(list)
        for _ in range(REPEATS):
            for method in METHODS:
                start = time.perf_counter()
                found[jd["jd_ref"]][method] = extract_skills(jd["raw_text"], method=method)
                runs[method].append(time.perf_counter() - start)
        for method in METHODS:
            seconds[jd["jd_ref"]][method] = statistics.median(runs[method])
    return found, seconds


# ── Tables ────────────────────────────────────────────────────
def describe(values):
    return {"n_jds": len(values), "mean": round(statistics.mean(values), 2),
            "median": statistics.median(values), "min": min(values), "max": max(values)}


def count_rows(jds, found):
    groups = [("All", jds)] + [(code, [j for j in jds if j["role_code"] == code]) for code in ROLES]
    rows = []
    for scope, group in groups:
        for method in METHODS:
            rows.append({"scope": scope, "method": method,
                         **describe([len(found[j["jd_ref"]][method]) for j in group])})
    return rows


def overlap_rows(jds, found):
    rows = []
    for jd in jds:
        k = {s["skill_name"] for s in found[jd["jd_ref"]]["keyword"]}
        s = {s["skill_name"] for s in found[jd["jd_ref"]]["semantic"]}
        rows.append({"jd_ref": jd["jd_ref"], "role_code": jd["role_code"],
                     "n_keyword": len(k), "n_semantic": len(s), "n_both": len(k & s),
                     "n_only_keyword": len(k - s), "n_only_semantic": len(s - k),
                     "jaccard": round(len(k & s) / len(k | s), 3) if k | s else 1.0,
                     "only_keyword": "; ".join(sorted(k - s)), "only_semantic": "; ".join(sorted(s - k))})
    return rows


def agreement_rows(overlap, found):
    counts = defaultdict(Counter)
    for row in overlap:
        k = {s["skill_name"] for s in found[row["jd_ref"]]["keyword"]}
        s = {s["skill_name"] for s in found[row["jd_ref"]]["semantic"]}
        for name in k - s:
            counts[name]["only_keyword"] += 1
        for name in k & s:
            counts[name]["both"] += 1
        for name in s - k:
            counts[name]["only_semantic"] += 1
    return [{"skill_name": name, "only_keyword": c["only_keyword"], "both": c["both"],
             "only_semantic": c["only_semantic"]} for name, c in sorted(counts.items())]


def context(text, start, end):
    left = " ".join(text[max(0, start - CONTEXT):start].split())
    right = " ".join(text[end:end + CONTEXT].split())
    return f"...{left} [{' '.join(text[start:end].split())}] {right}..."


def disagreement_rows(jds, found):
    """Skills found by exactly one of keyword / semantic. For keyword-only skills,
    semantic_span_score is the similarity of the keyword's span to that skill
    (why semantic missed it: near the threshold, or far below)."""
    catalogue = load_catalogue()
    vectors = skill_embeddings(catalogue)
    index = {name: k for k, name in enumerate(vectors.names)}
    rows = []
    for jd in jds:
        by_method = {m: {s["skill_name"]: s for s in found[jd["jd_ref"]][m]} for m in METHODS}
        k, s = by_method["keyword"], by_method["semantic"]
        for found_by, mine, other in (("keyword", k, s), ("semantic", s, k)):
            for name in sorted(set(mine) - set(other), key=lambda n: mine[n]["start_char"]):
                hit = mine[name]
                rows.append({"jd_ref": jd["jd_ref"], "role_code": jd["role_code"], "skill_name": name,
                             "found_by": found_by, "raw_skill_text": hit["raw_skill_text"],
                             "confidence": round(hit["confidence_score"], 3),
                             "in_hybrid": name in by_method["hybrid"],
                             "semantic_span_score": "",
                             "context": context(jd["raw_text"], hit["start_char"], hit["end_char"])})
    keyword_only = [r for r in rows if r["found_by"] == "keyword"]
    if keyword_only:
        sims = vectors.similarity(encode([r["raw_skill_text"].lower() for r in keyword_only]))
        for row, sim in zip(keyword_only, sims):
            row["semantic_span_score"] = round(float(sim[index[row["skill_name"]]]), 3)
    return rows


def reviewed_rows(disagreements):
    by_key = {(r["jd_ref"], r["skill_name"], r["found_by"]): r for r in disagreements}
    rows = []
    for item in REVIEWED:
        key = (item["jd_ref"], item["skill_name"], item["found_by"])
        if key not in by_key:
            raise SystemExit(f"reviewed example no longer occurs: {key}")
        source = by_key[key]
        rows.append({**item, "raw_skill_text": source["raw_skill_text"],
                     "confidence": source["confidence"], "in_hybrid": source["in_hybrid"],
                     "context": source["context"]})
    return rows


def gold_scores(jds, found):
    """Micro precision / recall / F1 per method on the JDs with hand-made gold rows, or None."""
    if not GOLD_PATH.exists():
        return None
    with open(GOLD_PATH, encoding="utf-8", newline="") as f:
        gold_rows = [r for r in csv.DictReader(f) if (r.get("skill_name") or "").strip()]
    if not gold_rows:
        return None
    catalogue = load_catalogue()
    gold = defaultdict(set)
    for r in gold_rows:
        gold[r["jd_ref"]].add(catalogue.lookup(r["skill_name"]) or r["skill_name"].strip())
    refs = [j["jd_ref"] for j in jds if j["jd_ref"] in gold]
    scores = []
    for method in METHODS:
        tp = sum(len(gold[ref] & {s["skill_name"] for s in found[ref][method]}) for ref in refs)
        predicted = sum(len(found[ref][method]) for ref in refs)
        actual = sum(len(gold[ref]) for ref in refs)
        p = tp / predicted if predicted else 0.0
        r = tp / actual if actual else 0.0
        scores.append({"method": method, "jds": len(refs), "precision": round(p, 3), "recall": round(r, 3),
                       "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0})
    return scores


def write_csv(name, rows):
    with open(RESULTS / name, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


# ── Figures (half page width in a Word report) ────────────────
# Colours: the dataviz reference palette, categorical slots 1-3 by method (the
# same in every figure) and its muted grey for "both"; checked with the
# palette validator on a white page.
COLORS = {"keyword": "#2a78d6", "semantic": "#eb6834", "hybrid": "#1baf7a"}
BOTH = "#898781"
INK, INK_2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
FIG_WIDTH = 3.25       # inches, half the text width of an A4 page
GAP_PT = 1.2           # white gap between touching marks
ROUND_PT = 2.0         # rounded data end of a bar


def setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    names = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        "font.family": "Segoe UI" if "Segoe UI" in names else "DejaVu Sans",
        "font.size": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5, "text.color": INK, "axes.labelcolor": INK_2,
        "xtick.color": MUTED, "ytick.color": INK_2, "axes.edgecolor": BASE,
        "savefig.dpi": 300, "savefig.facecolor": "white", "figure.facecolor": "white",
    })
    return plt


def style_axes(ax):
    ax.set_facecolor("white")
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(BASE)
    ax.spines["left"].set_linewidth(0.8)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.tick_params(axis="x", length=0, pad=2)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def units_per_point(ax):
    """Data units per typographic point along x and y (axes position and limits must be final)."""
    fig = ax.figure
    pos = ax.get_position()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    return (abs(x1 - x0) / (pos.width * fig.get_figwidth() * 72),
            abs(y1 - y0) / (pos.height * fig.get_figheight() * 72))


def hbar(ax, y, x0, x1, height, color, rounded=True):
    """Horizontal bar, square at x0 and with a rounded data end at x1."""
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath
    if x1 <= x0:
        return
    ux, uy = units_per_point(ax)
    r_pt = min(ROUND_PT, height / uy / 2) if rounded else 0.0
    rx, ry = min(r_pt * ux, x1 - x0), r_pt * uy
    yb, yt = y - height / 2, y + height / 2
    if rx > 0 and ry > 0:
        verts = [(x0, yb), (x1 - rx, yb), (x1, yb), (x1, yb + ry), (x1, yt - ry),
                 (x1, yt), (x1 - rx, yt), (x0, yt), (x0, yb)]
        codes = [MPath.MOVETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.LINETO,
                 MPath.CURVE3, MPath.CURVE3, MPath.LINETO, MPath.CLOSEPOLY]
    else:
        verts = [(x0, yb), (x1, yb), (x1, yt), (x0, yt), (x0, yb)]
        codes = [MPath.MOVETO] + [MPath.LINETO] * 3 + [MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color, edgecolor="none", linewidth=0))


def legend_handles(items):
    from matplotlib.patches import Patch
    return [Patch(facecolor=color, edgecolor="none", label=label) for label, color in items]


def group_labels(jds):
    counts = Counter(j["role_code"] for j in jds)
    return [f"All JDs ({len(jds)})"] + [f"{name} ({counts[code]})" for code, name in ROLES.items()]


def figure_skills_per_jd(plt, jds, counts, path):
    """(a) Mean skills per JD by method, for all JDs and per role."""
    from matplotlib.ticker import MultipleLocator
    means = {(r["scope"], r["method"]): r["mean"] for r in counts}
    scopes = ["All"] + list(ROLES)
    labels = group_labels(jds)
    bar, step = 0.24, 0.27                       # bar thickness and pitch, in group units
    centres = [0.0] + [1.35 + i for i in range(len(ROLES))]   # extra space after "All JDs"

    fig = plt.figure(figsize=(FIG_WIDTH, 3.15))
    ax = fig.add_axes([0.40, 0.11, 0.53, 0.78])
    style_axes(ax)
    xmax = max(means.values()) * 1.18
    ax.set_xlim(0, xmax)
    ax.set_ylim(centres[-1] + 0.55, -0.55)
    ax.set_yticks(centres, labels)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.set_xlabel("Skills found per JD (mean)")
    for centre, scope in zip(centres, scopes):
        for k, method in enumerate(METHODS):
            y = centre + (k - 1) * step
            value = means[(scope, method)]
            hbar(ax, y, 0, value, bar, COLORS[method])
            if scope == "All":                    # direct labels on the headline group only
                ax.text(value + xmax * 0.015, y, f"{value:.1f}", va="center", ha="left",
                        fontsize=7, color=INK_2)
    fig.legend(handles=legend_handles([(m.capitalize(), COLORS[m]) for m in METHODS]),
               loc="upper center", bbox_to_anchor=(0.62, 1.0), ncol=3, frameon=False,
               handlelength=0.9, handleheight=0.9, columnspacing=1.0, handletextpad=0.4)
    fig.savefig(path)
    plt.close(fig)


def figure_agreement(plt, jds, overlap, path):
    """(b) Keyword vs semantic per JD: only keyword | both | only semantic (stacked, mean per JD)."""
    from matplotlib.ticker import MultipleLocator
    scopes = ["All"] + list(ROLES)
    parts = (("n_only_keyword", "Only keyword", COLORS["keyword"]),
             ("n_both", "Both", BOTH),
             ("n_only_semantic", "Only semantic", COLORS["semantic"]))
    means = {}
    for scope in scopes:
        rows = overlap if scope == "All" else [r for r in overlap if r["role_code"] == scope]
        means[scope] = [statistics.mean(r[key] for r in rows) for key, _, _ in parts]
    labels = group_labels(jds)
    centres = [0.0] + [1.3 + i for i in range(len(ROLES))]

    fig = plt.figure(figsize=(FIG_WIDTH, 2.6))
    ax = fig.add_axes([0.40, 0.14, 0.55, 0.74])
    style_axes(ax)
    xmax = max(sum(v) for v in means.values()) * 1.08
    ax.set_xlim(0, xmax)
    ax.set_ylim(centres[-1] + 0.6, -0.6)
    ax.set_yticks(centres, labels)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.set_xlabel("Skills per JD (mean), found by either method")
    ux, _ = units_per_point(ax)
    gap = GAP_PT * ux
    renderer = fig.canvas.get_renderer()
    for centre, scope in zip(centres, scopes):
        values = means[scope]
        last = max(i for i, v in enumerate(values) if v > 0)
        left = 0.0
        for i, ((_, _, color), value) in enumerate(zip(parts, values)):
            x0 = left + (gap / 2 if i > 0 else 0)
            x1 = left + value - (gap / 2 if i < last else 0)
            hbar(ax, centre, x0, x1, 0.62, color, rounded=i == last)
            if scope == "All":                   # inside when it fits, else past the bar end, else none
                text = ax.text((x0 + x1) / 2, centre, f"{value:.1f}", ha="center", va="center",
                               fontsize=7, color="white" if color == COLORS["keyword"] else INK)
                width = text.get_window_extent(renderer).width / fig.dpi * 72 * ux
                if width + 8 * ux > x1 - x0:      # 4 pt of padding on each side
                    if i == last:
                        text.set(x=x1 + 3 * ux, ha="left", color=INK_2)
                    else:
                        text.remove()
            left += value
    fig.legend(handles=legend_handles([(label, color) for _, label, color in parts]),
               loc="upper center", bbox_to_anchor=(0.62, 1.0), ncol=3, frameon=False,
               handlelength=0.9, handleheight=0.9, columnspacing=1.0, handletextpad=0.4)
    fig.savefig(path)
    plt.close(fig)


def figure_runtime(plt, seconds, path):
    """(c) Time per JD by method: median (dot) and range over the JDs (line), log scale."""
    fig = plt.figure(figsize=(FIG_WIDTH, 1.55))
    ax = fig.add_axes([0.20, 0.27, 0.70, 0.66])
    style_axes(ax)
    ax.set_xscale("log")
    ax.set_xlim(0.05, 2000)
    ax.set_ylim(len(METHODS) - 0.4, -0.6)
    ax.set_yticks(range(len(METHODS)), [m.capitalize() for m in METHODS])
    ticks = [0.1, 1, 10, 100, 1000]
    ax.set_xticks(ticks, ["0.1", "1", "10", "100", "1,000"])
    ax.minorticks_off()
    ax.set_xlabel("Time per JD (ms, log scale)")
    for y, method in enumerate(METHODS):
        ms = [seconds[ref][method] * 1000 for ref in seconds]
        median = statistics.median(ms)
        ax.plot([min(ms), max(ms)], [y, y], color=COLORS[method], linewidth=1.5,
                solid_capstyle="round", zorder=2)
        ax.plot([median], [y], marker="o", markersize=6, color=COLORS[method],
                markeredgecolor="white", markeredgewidth=1.2, zorder=3)
        label = f"{median:.1f} ms" if median < 10 else f"{median:.0f} ms"
        ax.text(max(ms) * 1.35, y, label, va="center", ha="left", fontsize=7, color=INK_2)
    fig.savefig(path)
    plt.close(fig)


# ── Summary ───────────────────────────────────────────────────
def md_table(header, rows, text_columns=1):
    """Markdown table; the first text_columns columns are left-aligned, the rest right-aligned."""
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join("---" if i < text_columns else "---:" for i in range(len(header))) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return lines


def write_summary(jds, counts, overlap, agreement, seconds, cold, found, disagreements, reviewed, gold):
    roles = Counter(j["role_code"] for j in jds)
    lines = [
        "# Keyword vs semantic vs hybrid extraction (S2-02-02)",
        "",
        f"Generated by `nlp/experiments/compare_methods.py` on {time.strftime('%Y-%m-%d')}: "
        f"{len(jds)} JDs from `data/jd_dataset/jd_dataset.csv` ("
        + ", ".join(f"{ROLES[c]} {roles[c]}" for c in ROLES) + "). Settings: MATCH "
        f"{config.MATCH_THRESHOLD:.2f}, SKILL_TEXT_MODE {config.SKILL_TEXT_MODE}, list items "
        f"{config.LIST_ITEM_TEXT_MODE} at {config.LIST_ITEM_THRESHOLD:.2f}. Skills are compared by "
        "canonical name.",
        "",
        "## Skills found per JD",
        "",
    ]
    lines += md_table(["Scope", "Method", "Mean", "Median", "Min", "Max"],
                      [[ROLES.get(r["scope"], "All JDs"), r["method"], f"{r['mean']:.1f}", r["median"],
                        r["min"], r["max"]] for r in counts], text_columns=2)
    hybrid_semantic = [sum(s["method"] == "semantic" for s in found[j["jd_ref"]]["hybrid"]) for j in jds]
    lines += ["", f"Hybrid rows found by its semantic steps: mean {statistics.mean(hybrid_semantic):.1f} per JD "
              f"({sum(hybrid_semantic)} in total); the rest are the keyword results.", ""]

    jac = [r["jaccard"] for r in overlap]
    totals = {key: sum(r[key] for r in overlap) for key in ("n_only_keyword", "n_both", "n_only_semantic")}
    union = sum(totals.values())
    lines += ["## Keyword vs semantic overlap", "",
              f"Jaccard index per JD (shared skills / all skills found by either): mean "
              f"{statistics.mean(jac):.2f}, median {statistics.median(jac):.2f}, min {min(jac):.2f}, "
              f"max {max(jac):.2f}. Of {union} JD-skill pairs found by either method, "
              f"{totals['n_both']} ({100 * totals['n_both'] / union:.0f}%) were found by both, "
              f"{totals['n_only_keyword']} ({100 * totals['n_only_keyword'] / union:.0f}%) only by keyword and "
              f"{totals['n_only_semantic']} ({100 * totals['n_only_semantic'] / union:.0f}%) only by semantic.", ""]
    rows = []
    for code in ROLES:
        mine = [r for r in overlap if r["role_code"] == code]
        rows.append([ROLES[code], len(mine), f"{statistics.mean(r['jaccard'] for r in mine):.2f}",
                     f"{statistics.mean(r['n_only_keyword'] for r in mine):.1f}",
                     f"{statistics.mean(r['n_both'] for r in mine):.1f}",
                     f"{statistics.mean(r['n_only_semantic'] for r in mine):.1f}"])
    lines += md_table(["Role", "JDs", "Mean Jaccard", "Only keyword / JD", "Both / JD", "Only semantic / JD"], rows)
    for key, title in (("only_keyword", "only by keyword"), ("both", "by both"), ("only_semantic", "only by semantic")):
        top = sorted((r for r in agreement if r[key]), key=lambda r: (-r[key], r["skill_name"]))[:TOP]
        lines += ["", f"Top {TOP} skills found {title} (number of JDs):", "",
                  ", ".join(f"{r['skill_name']} {r[key]}" for r in top)]

    lines += ["", "## Runtime per JD", "",
              f"Median of {REPEATS} runs per JD after a warm-up, CPU. Cold start before the first JD: "
              + ", ".join(f"{k} {v:.1f} s" for k, v in cold.items()) + ".", ""]
    rows = []
    for method in METHODS:
        ms = [seconds[ref][method] * 1000 for ref in seconds]
        rows.append([method, f"{statistics.mean(ms):.1f}", f"{statistics.median(ms):.1f}",
                     f"{min(ms):.1f}", f"{max(ms):.1f}"])
    lines += md_table(["Method", "Mean ms", "Median ms", "Min ms", "Max ms"], rows)

    near = [r for r in disagreements if r["found_by"] == "keyword" and r["semantic_span_score"] != ""
            and config.MATCH_THRESHOLD - 0.05 <= r["semantic_span_score"] < config.MATCH_THRESHOLD]
    lines += ["", "## Disagreements", "",
              f"{len(disagreements)} disagreements ({sum(r['found_by'] == 'keyword' for r in disagreements)} "
              f"keyword-only, {sum(r['found_by'] == 'semantic' for r in disagreements)} semantic-only); all are in "
              "`method_disagreements.csv` with their context. Of the keyword-only spans, "
              f"{len(near)} score within 0.05 below MATCH as a phrase (near misses of the semantic threshold).", ""]
    if reviewed:
        lines += md_table(["#", "JD", "Skill", "Found by", "JD text", "Class"],
                          [[i, r["jd_ref"], r["skill_name"], f"{r['found_by']} ({r['confidence']:.2f})",
                            f"\"{r['raw_skill_text']}\"", r["category"]] for i, r in enumerate(reviewed, 1)],
                          text_columns=6)
        lines += ["", "Counts by class: " + ", ".join(f"{c} {n}" for c, n in Counter(r["category"] for r in reviewed).most_common())]

    lines += ["", "## Gold labels", ""]
    if gold:
        lines += [f"Hand-made gold rows cover {gold[0]['jds']} JDs; scores on those JDs only:", ""]
        lines += md_table(["Method", "JDs", "Precision", "Recall", "F1"],
                          [[g["method"], g["jds"], g["precision"], g["recall"], g["f1"]] for g in gold])
    else:
        lines += ["`data/jd_dataset/gold/gold_labels.csv` has no hand-made rows yet, so no precision, recall or F1 "
                  "is reported. `gold_labels_draft.csv` is a keyword pre-fill and is not ground truth."]
    (RESULTS / "method_comparison_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    jds = load_jds()
    print(f"{len(jds)} JDs; warming up ...")
    cold = warm_up(jds[0]["raw_text"])
    found, seconds = run_all(jds)

    RESULTS.mkdir(parents=True, exist_ok=True)
    roles = {j["jd_ref"]: j["role_code"] for j in jds}
    write_csv("method_comparison.csv", [
        {"jd_ref": ref, "role_code": roles[ref], "method": method, "skill_name": s["skill_name"],
         "raw_skill_text": s["raw_skill_text"], "confidence": round(s["confidence_score"], 3),
         "found_by": s["method"]}
        for ref in found for method in METHODS for s in found[ref][method]])
    counts = count_rows(jds, found)
    overlap = overlap_rows(jds, found)
    agreement = agreement_rows(overlap, found)
    disagreements = disagreement_rows(jds, found)
    reviewed = reviewed_rows(disagreements)
    gold = gold_scores(jds, found)
    write_csv("method_counts.csv", counts)
    write_csv("method_overlap.csv", overlap)
    write_csv("method_skill_agreement.csv", agreement)
    write_csv("method_runtime.csv", [{"jd_ref": j["jd_ref"], "role_code": j["role_code"], "chars": len(j["raw_text"]),
                                      **{f"{m}_s": round(seconds[j["jd_ref"]][m], 5) for m in METHODS}}
                                     for j in jds])
    write_csv("method_disagreements.csv", disagreements)
    if reviewed:
        write_csv("method_disagreements_reviewed.csv", reviewed)

    plt = setup_matplotlib()
    figure_skills_per_jd(plt, jds, counts, RESULTS / "method_skills_per_jd.png")
    figure_agreement(plt, jds, overlap, RESULTS / "method_agreement.png")
    figure_runtime(plt, seconds, RESULTS / "method_runtime.png")
    write_summary(jds, counts, overlap, agreement, seconds, cold, found, disagreements, reviewed, gold)
    print((RESULTS / "method_comparison_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
