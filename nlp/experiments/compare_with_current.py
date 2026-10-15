"""
Before / after evidence for the matcher (S2-12-01, S2-11-02).

    python nlp/experiments/compare_with_current.py

Compares the matching that backend/routers/assessments.py runs today
(reimplemented here; the router is not imported):

    same skill_id                               -> strong      (similarity 1.0)
    one skill name is a substring of the other  -> developing  (similarity 0.6)
    anything else                               -> gap

with nlp.match_skills(method="hybrid"), for 200 synthetic students drawn with
seed 42 from data/output/ and every one of the 6 roles in
database/seed_job_role_skills.sql (1,200 assessments). Both sides get the
weighted readiness score of assessments.py (required 3, preferred 2, bonus 1;
strong 1.0, developing 0.5, gap 0). Every skill gets a UUID derived from its
name, so "same skill_id" means "same skills_library row", as in the database.

Writes to nlp/experiments/results/:
  compare_with_current_scores.csv   one row per student x role: both readiness scores
  compare_with_current_changes.csv  one row per required skill whose status changed
  compare_with_current.md           summary: transitions, score changes, 10 examples
"""

import csv
import random
import re
import statistics
import sys
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from nlp import config, match_skills  # noqa: E402

DATA = REPO / "data" / "output"
ROLE_SEED = REPO / "database" / "seed_job_role_skills.sql"
RESULTS = Path(__file__).resolve().parent / "results"
N_STUDENTS = 200
SEED = 42
BIG_CHANGE = 10          # readiness points
STATUSES = ("strong", "developing", "gap")
# Substring matches of the current logic that reflect a real relation (judged
# by hand from the full list of pairs): every other substring pair is a word
# trap such as "R" in "Docker" or "Java" in "JavaScript".
REAL_RELATIONS = {frozenset(p) for p in [("SQL", "PostgreSQL"), ("SQL", "MySQL"), ("SQL", "SQLite"),
                                         ("Communication", "Stakeholder Communication"),
                                         ("Linux", "Kali Linux")]}
ROLE_NAMES = {"DATA_ANALYST": "Data Analyst", "DATA_SCIENTIST": "Data Scientist",
              "SOFTWARE_DEV": "Software Developer", "CYBER_ANALYST": "Cybersecurity Analyst",
              "CLOUD_ENGINEER": "Cloud Engineer", "WEB_DEV": "Web Developer"}

# Weighted score as in backend/routers/assessments.py.
WEIGHTS = {"required": 3, "preferred": 2, "bonus": 1}
CREDIT = {"strong": 1.0, "developing": 0.5, "gap": 0.0}


def skill_id(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"seagas/skills_library/{name}"))


def readiness(results):
    earned = sum(WEIGHTS.get(r["importance"], 1) * CREDIT[r["match_status"]] for r in results)
    total = sum(WEIGHTS.get(r["importance"], 1) for r in results)
    return round(earned / total * 100, 2) if total else 0


# ── Data ──────────────────────────────────────────────────────
def load_roles():
    sql = ROLE_SEED.read_text(encoding="utf-8")
    rows = re.findall(r"^\s*\('([A-Z_]+)',\s*'((?:[^']|'')+)',\s*'(required|preferred|bonus)'\)",
                      sql, flags=re.M)
    roles = defaultdict(list)
    for code, name, importance in rows:
        name = name.replace("''", "'")
        roles[ROLE_NAMES[code]].append({"skill_id": skill_id(name), "skill_name": name,
                                        "importance": importance})
    for skills in roles.values():       # the API orders required -> preferred -> bonus
        skills.sort(key=lambda r: list(WEIGHTS).index(r["importance"]))
    return dict(roles)


def load_students():
    with open(DATA / "students_meta.csv", encoding="utf-8", newline="") as f:
        meta = list(csv.DictReader(f))
    picked = sorted(random.Random(SEED).sample(meta, N_STUDENTS), key=lambda m: m["email"])
    wanted = {m["profile_id"] for m in picked}
    skills = defaultdict(list)
    with open(DATA / "student_skills.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["profile_id"] in wanted:
                evidence = [e.strip().strip('"') for e in row["evidence_type"].strip("{}").split(",")]
                skills[row["profile_id"]].append({
                    "skill_id": skill_id(row["skill_name"]), "skill_name": row["skill_name"],
                    "proficiency_level": row["proficiency_level"],
                    "evidence_type": [e for e in evidence if e]})
    return picked, skills


# ── Current backend logic (assessments.py, lines 117-153) ─────
def current_match(student_skills, required_skills):
    """[{importance, match_status, similarity_score, trigger}] as assessments.py decides today.
    trigger is the student skill behind the decision (the first one in profile order)."""
    by_id = {s["skill_id"]: s["skill_name"] for s in student_skills}
    names = [s["skill_name"] for s in student_skills]
    out = []
    for r in required_skills:
        name = r["skill_name"].lower()
        if r["skill_id"] and r["skill_id"] in by_id:
            status, sim, trigger = "strong", 1.0, by_id[r["skill_id"]]
        else:
            trigger = next((n for n in names if name in n.lower() or n.lower() in name), None)
            status, sim = ("developing", 0.6) if trigger else ("gap", 0.0)
        out.append({"importance": r["importance"], "match_status": status,
                    "similarity_score": sim, "trigger": trigger})
    return out


# ── Report ────────────────────────────────────────────────────
def pct(part, whole):
    return f"{100 * part / whole:.1f}%" if whole else "-"


def is_trap(change):
    """Current says developing only because one name is inside the other, and hybrid says gap."""
    return (change["current_status"] == "developing" and change["hybrid_status"] == "gap"
            and frozenset((change["skill_name"], change["current_trigger"])) not in REAL_RELATIONS)


def pick_examples(changes, n=10):
    """Clearest cases: word traps the hybrid matcher rejects (short names such
    as R, Go, Java first), then the most frequent gains from similarity."""
    examples, seen = [], set()
    substring = Counter((c["skill_name"], c["current_trigger"]) for c in changes if is_trap(c))
    for (skill, trigger), _ in sorted(substring.items(), key=lambda kv: (len(kv[0][0]), -kv[1], kv[0])):
        if skill not in seen and len(examples) < n - 3:
            seen.add(skill)
            examples.append(next(c for c in changes if (c["skill_name"], c["current_trigger"]) == (skill, trigger)
                                 and c["hybrid_status"] == "gap") | {"count": substring[(skill, trigger)]})
    gains = Counter((c["skill_name"], c["matched_student_skill"], c["current_status"], c["hybrid_status"])
                    for c in changes if c["hybrid_status"] != "gap")
    for key, count in gains.most_common():
        if len(examples) >= n:
            break
        if key[0] not in seen:
            seen.add(key[0])
            examples.append(next(c for c in changes if (c["skill_name"], c["matched_student_skill"],
                                                        c["current_status"], c["hybrid_status"]) == key)
                            | {"count": count})
    return examples


def write_summary(path, students, roles, scores, rows_total, transitions, changes, examples, seconds):
    n_assess = len(scores)
    big = [s for s in scores if abs(s["delta"]) > BIG_CHANGE]
    target = [s for s in scores if s["role"] == s["target_role"]]
    big_target = [s for s in target if abs(s["delta"]) > BIG_CHANGE]
    any_role = {s["email"] for s in big}
    traps = Counter(frozenset((c["skill_name"], c["current_trigger"])) for c in changes if is_trap(c))
    lost = Counter((c["skill_name"], c["current_trigger"]) for c in changes
                   if c["current_status"] == "developing" and c["hybrid_status"] == "gap" and not is_trap(c))
    similar_strong = Counter((c["skill_name"], c["matched_student_skill"], c["hybrid_similarity"])
                             for c in changes if c["hybrid_status"] == "strong")
    beginners = sum(1 for ss in students.values() for s in ss
                    if s["proficiency_level"] == "beginner" and not s["evidence_type"])

    lines = [
        "# Current backend matching vs `match_skills(method=\"hybrid\")`",
        "",
        f"Generated by `nlp/experiments/compare_with_current.py` on {time.strftime('%Y-%m-%d')} "
        f"(run time {seconds:.1f} s; catalogue skills use the cached skill embeddings, so matching "
        "needs no model load once `nlp/resources/skill_embeddings.npy` exists).",
        "",
        f"**Setup.** {len(students)} synthetic students (random sample, seed {SEED}, from "
        f"`data/output/`) assessed against all {len(roles)} roles in `database/seed_job_role_skills.sql`: "
        f"{n_assess} assessments, {rows_total:,} required-skill rows. *Current* is the logic in "
        "`backend/routers/assessments.py` today (same `skill_id` -> strong; one name contains the "
        "other -> developing; else gap), reimplemented in the script. *Hybrid* is `nlp.match_skills` "
        f"with MATCH {config.MATCH_THRESHOLD:.2f}, RELATED {config.RELATED_THRESHOLD:.2f}. Both use "
        "the weighted readiness score of `assessments.py`.",
        "",
        "## Skill statuses",
        "",
        f"{sum(transitions[(a, b)] for a in STATUSES for b in STATUSES if a != b):,} of "
        f"{rows_total:,} rows ({pct(sum(transitions[(a, b)] for a in STATUSES for b in STATUSES if a != b), rows_total)}) "
        "change status. Rows: current status; columns: hybrid status.",
        "",
        "| current \\ hybrid | strong | developing | gap |",
        "|---|---:|---:|---:|",
    ]
    for a in STATUSES:
        lines.append(f"| **{a}** | " + " | ".join(f"{transitions[(a, b)]:,}" for b in STATUSES) + " |")
    lines += ["", "Changes by type:", ""]
    for (a, b), count in sorted(((k, v) for k, v in transitions.items() if k[0] != k[1]),
                                key=lambda kv: -kv[1]):
        lines.append(f"- {a} -> {b}: {count:,}")
    lines += [
        "",
        f"No strong -> developing changes can happen on this data: none of the {sum(len(v) for v in students.values()):,} "
        f"skill entries of these students is beginner without evidence ({beginners}), so every "
        "same-skill match stays strong.",
        "",
        "### Substring matches that hybrid rejects (developing -> gap)",
        "",
        f"**Word traps removed:** {sum(traps.values()):,} rows ({len(traps)} skill pairs, either "
        "direction) where one name only sits inside another word. The most frequent:",
        "",
        "| Shorter name | Inside | Rows |",
        "|---|---|---:|",
    ]
    for pair, count in traps.most_common(10):
        short, long_ = sorted(pair, key=len)
        lines.append(f"| {short} | {long_} | {count} |")
    lines += [
        "",
        f"**Related skills lost:** {sum(lost.values()):,} rows are real relations (judged by hand, "
        "`REAL_RELATIONS` in the script) that the current logic marks developing and hybrid marks a "
        f"gap, because their embeddings score below RELATED ({config.RELATED_THRESHOLD:.2f}). "
        "These are regressions to fix (see docs/NLP_CLASSIFICATION_RULES.md, section 7):",
        "",
        "| Required skill | Student skill | Rows |",
        "|---|---|---:|",
    ]
    for (skill, trigger), count in lost.most_common():
        lines.append(f"| {skill} | {trigger} | {count} |")
    lines += [
        "",
        "### Strong through similarity between two different skills",
        "",
        f"{sum(similar_strong.values())} rows ({pct(sum(similar_strong.values()), rows_total)} of all rows) "
        "become strong because a *different* student skill reaches MATCH:",
        "",
        "| Required skill | Student skill | Similarity | Rows |",
        "|---|---|---:|---:|",
    ]
    for (skill, have, sim), count in similar_strong.most_common():
        lines.append(f"| {skill} | {have} | {float(sim):.3f} | {count} |")

    def means(rows):
        return {a: (statistics.mean(s["current_score"] for s in rows if s["archetype"] == a),
                    statistics.mean(s["hybrid_score"] for s in rows if s["archetype"] == a))
                for a in ("strong", "average", "weak")}
    mean_all, mean_target = means(scores), means(target)
    up = sum(1 for s in big if s["delta"] > 0)
    lines += [
        "",
        "## Readiness scores",
        "",
        f"- **{pct(len(big), n_assess)}** of the {n_assess} assessments ({len(big)}) change by more than "
        f"{BIG_CHANGE} points ({up} up, {len(big) - up} down); mean change "
        f"{statistics.mean(s['delta'] for s in scores):+.2f}, largest {max(scores, key=lambda s: abs(s['delta']))['delta']:+.2f}.",
        f"- {pct(len(any_role), len(students))} of the students ({len(any_role)}) have at least one role "
        f"that changes by more than {BIG_CHANGE} points; on their own target role it is "
        f"{pct(len(big_target), len(target))} ({len(big_target)} of {len(target)}).",
        "",
        "| Archetype | Current, target role | Hybrid, target role | Current, all 6 roles | Hybrid, all 6 roles |",
        "|---|---:|---:|---:|---:|",
    ]
    for a in ("strong", "average", "weak"):
        lines.append(f"| {a} | {mean_target[a][0]:.1f} | {mean_target[a][1]:.1f} | "
                     f"{mean_all[a][0]:.1f} | {mean_all[a][1]:.1f} |")
    lines += [
        "",
        "## 10 clearest examples",
        "",
        "| # | Student | Role | Required skill | Current | Hybrid | Rows like this |",
        "|---:|---|---|---|---|---|---:|",
    ]
    for i, c in enumerate(examples, 1):
        current = f"{c['current_status']} ({c['current_trigger']})" if c["current_trigger"] else c["current_status"]
        hybrid = (f"{c['hybrid_status']} ({c['matched_student_skill']}, {c['hybrid_similarity']:.3f})"
                  if c["matched_student_skill"] else c["hybrid_status"])
        lines.append(f"| {i} | {c['email'].split('@')[0]} | {c['role']} | {c['skill_name']} | "
                     f"{current} | {hybrid} | {c['count']} |")
    lines += ["", "Hybrid reasons for these rows:", ""]
    for i, c in enumerate(examples, 1):
        lines.append(f"{i}. {c['reason']}")
    lines += ["", "Full rows: `compare_with_current_changes.csv`; scores: `compare_with_current_scores.csv`.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    t0 = time.perf_counter()
    roles = load_roles()
    picked, students = load_students()

    scores, changes = [], []
    transitions = Counter()
    rows_total = 0
    for m in picked:
        mine = students[m["profile_id"]]
        for role, required in roles.items():
            before = current_match(mine, required)
            after = match_skills(mine, required, method="hybrid")
            scores.append({"email": m["email"], "archetype": m["archetype"],
                           "target_role": m["target_role"], "role": role, "n_skills": len(mine),
                           "current_score": readiness(before), "hybrid_score": readiness(after)})
            scores[-1]["delta"] = round(scores[-1]["hybrid_score"] - scores[-1]["current_score"], 2)
            for req, b, a in zip(required, before, after):
                rows_total += 1
                transitions[(b["match_status"], a["match_status"])] += 1
                if b["match_status"] != a["match_status"]:
                    changes.append({
                        "email": m["email"], "archetype": m["archetype"], "role": role,
                        "skill_name": req["skill_name"], "importance": req["importance"],
                        "current_status": b["match_status"], "current_trigger": b["trigger"],
                        "hybrid_status": a["match_status"], "hybrid_similarity": a["similarity_score"],
                        "matched_student_skill": a["matched_student_skill"], "reason": a["reason"]})
    seconds = time.perf_counter() - t0

    RESULTS.mkdir(parents=True, exist_ok=True)
    for name, rows in (("compare_with_current_scores.csv", scores),
                       ("compare_with_current_changes.csv", changes)):
        with open(RESULTS / name, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    examples = pick_examples(changes)
    write_summary(RESULTS / "compare_with_current.md", students, roles, scores, rows_total,
                  transitions, changes, examples, seconds)
    print((RESULTS / "compare_with_current.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
