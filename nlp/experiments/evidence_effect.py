"""
Effect of evidence derived from projects and certifications (nlp/evidence.py).

    python nlp/experiments/evidence_effect.py                  # hybrid, as the website
    python nlp/experiments/evidence_effect.py --method keyword # no model needed

Every synthetic student in data/output/ is assessed against their own target
role (database/seed_job_role_skills.sql), as data/run_assessments.py does, with
and without nlp.derive_evidence(). Readiness is the weighted score of
backend/assessment_service.py (required 3, preferred 2, bonus 1; strong 1.0,
developing 0.5, gap 0).

Two scenarios:
  website  stored evidence_type emptied. This is what real users have: the
           website has no evidence input for a skill, so only derived evidence
           can make a beginner skill Strong (rule C).
  stored   evidence_type as generated. The generator already derives it from
           the same projects and certifications, so little should change.

The generated evidence also serves as a reference for derive_evidence(): the
generator knows which skills each project and certification stands for, so
derived project / certification evidence is compared with it (precision,
recall).

Writes to nlp/experiments/results/:
  evidence_effect.csv           one row per scenario x group (all, archetype, role,
                                projects + certifications): students, rows,
                                Developing -> Strong, mean readiness without / with
  evidence_effect_students.csv  one row per student x scenario: both readiness scores
  evidence_effect.md            summary
"""

import argparse
import csv
import re
import statistics
import sys
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from nlp import config, derive_evidence, match_skills  # noqa: E402
from nlp.evidence import DERIVED_TYPES  # noqa: E402
from nlp.matcher import _evidence  # noqa: E402

DATA = REPO / "data" / "output"
ROLE_SEED = REPO / "database" / "seed_job_role_skills.sql"
RESULTS = Path(__file__).resolve().parent / "results"
ROLE_NAMES = {"DATA_ANALYST": "Data Analyst", "DATA_SCIENTIST": "Data Scientist",
              "SOFTWARE_DEV": "Software Developer", "CYBER_ANALYST": "Cybersecurity Analyst",
              "CLOUD_ENGINEER": "Cloud Engineer", "WEB_DEV": "Web Developer",
              "BUSINESS_ANALYST": "Business Analyst", "MARKETING_EXEC": "Marketing Executive",
              "FINANCIAL_ANALYST": "Financial Analyst", "HR_EXEC": "HR Executive"}
ARCHETYPES = ("strong", "average", "weak")
SCENARIOS = ("website", "stored")

# Weighted score as in backend/assessment_service.py.
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


def read_csv(name):
    with open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def by_profile(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["profile_id"]].append(row)
    return grouped


def load_students():
    meta = sorted(read_csv("students_meta.csv"), key=lambda m: m["email"])
    skills = defaultdict(list)
    for row in read_csv("student_skills.csv"):
        skills[row["profile_id"]].append({
            "skill_id": skill_id(row["skill_name"]), "skill_name": row["skill_name"],
            "proficiency_level": row["proficiency_level"],
            "evidence_type": list(_evidence(row["evidence_type"]))})
    return meta, skills, by_profile(read_csv("student_projects.csv")), \
        by_profile(read_csv("student_certifications.csv"))


# ── Report ────────────────────────────────────────────────────
def pct(part, whole):
    return f"{100 * part / whole:.1f}%" if whole else "-"


def summarise(rows, key):
    """Group rows of per-student results by key(row) -> summary dicts."""
    groups = defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    out = []
    for group, rs in groups.items():
        out.append({"group": group, "students": len(rs),
                    "rows": sum(r["rows"] for r in rs),
                    "developing_to_strong": sum(r["developing_to_strong"] for r in rs),
                    "students_changed": sum(r["developing_to_strong"] > 0 for r in rs),
                    "mean_without": round(statistics.mean(r["without"] for r in rs), 2),
                    "mean_with": round(statistics.mean(r["with"] for r in rs), 2),
                    "mean_delta": round(statistics.mean(r["with"] - r["without"] for r in rs), 2)})
    return out


def records_band(n):
    return "3+" if n >= 3 else str(n)


GROUPINGS = (("all", lambda r: "all"),
             ("archetype", lambda r: r["archetype"]),
             ("role", lambda r: r["role"]),
             ("projects + certifications", lambda r: records_band(r["records"])))
ORDER = {"archetype": ARCHETYPES, "projects + certifications": ("0", "1", "2", "3+")}


def ordered(summary, by):
    order = ORDER.get(by)
    return sorted(summary, key=lambda s: order.index(s["group"]) if order else s["group"])


def table(summary, by):
    lines = [f"| {by.capitalize()} | Students | Rows | Developing → Strong | Students with a change "
             "| Mean readiness without | with | Δ |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for s in ordered(summary, by):
        lines.append(f"| {s['group']} | {s['students']} | {s['rows']} | {s['developing_to_strong']} "
                     f"({pct(s['developing_to_strong'], s['rows'])}) | {s['students_changed']} "
                     f"| {s['mean_without']:.2f} | {s['mean_with']:.2f} | {s['mean_delta']:+.2f} |")
    return lines


def examples_table(counter, n=8):
    lines = ["| Student skill | Evidence from | Rows |", "|---|---|---:|"]
    lines += [f"| {skill} | {source} | {count} |" for (skill, source), count in counter.most_common(n)]
    return lines


def write_summary(path, method, students, transitions, summaries, agreement, examples, seconds):
    web = {by: summaries[("website", by)] for by, _ in GROUPINGS}
    stored_all = summaries[("stored", "all")][0]
    web_all = web["all"][0]
    lines = [
        "# Evidence from projects and certifications: effect on readiness",
        "",
        f"`python nlp/experiments/evidence_effect.py --method {method}` · rules "
        f"`{config.MATCH_RULES_VERSION}` · {students} synthetic students (`data/output/`, "
        f"`{(DATA / 'DATA_VERSION').read_text(encoding='utf-8').strip()}`), each against their "
        f"own target role · {seconds:.0f} s",
        "",
        "`nlp.derive_evidence()` adds project, certification and internship evidence to the "
        "skills a student lists, from their projects (technologies, title, description) and "
        "certifications (name; issuer only when the name gives no skill). Only a **beginner** "
        "skill can change, from Developing to Strong (rule C); every other status is the same "
        "with and without it.",
        "",
        "## Website scenario (stored evidence empty, as for real users)",
        "",
        "The website has no evidence input when a student adds a skill, so `evidence_type` is "
        "empty for real users. Without derived evidence a beginner skill can never be Strong.",
        "",
        f"With derived evidence, **{web_all['developing_to_strong']} of {web_all['rows']} "
        f"required-skill rows ({pct(web_all['developing_to_strong'], web_all['rows'])}) move from "
        f"Developing to Strong**, for {web_all['students_changed']} of {students} students "
        f"({pct(web_all['students_changed'], students)}). Mean readiness rises from "
        f"{web_all['mean_without']:.2f} to {web_all['mean_with']:.2f} ({web_all['mean_delta']:+.2f} "
        "points).",
        "",
        *table(web["archetype"], "archetype"),
        "",
        *table(web["role"], "role"),
        "",
        "By the number of projects and certifications the student lists:",
        "",
        *table(web["projects + certifications"], "projects + certifications"),
        "",
        "## Stored scenario (synthetic evidence as generated)",
        "",
        "The generator writes `evidence_type` from the same projects and certifications, so "
        f"derived evidence adds little: {stored_all['developing_to_strong']} of "
        f"{stored_all['rows']} rows ({pct(stored_all['developing_to_strong'], stored_all['rows'])}) "
        f"move from Developing to Strong; mean readiness {stored_all['mean_without']:.2f} → "
        f"{stored_all['mean_with']:.2f} ({stored_all['mean_delta']:+.2f}). The rows that change:",
        "",
        *examples_table(examples["stored"]),
        "",
        "Status transitions, all scenarios (without → with):",
        "",
        "| Scenario | Transition | Rows |",
        "|---|---|---:|",
        *[f"| {sc} | {a} → {b} | {n} |" for (sc, a, b), n in sorted(transitions.items())],
        "",
        "## Derived evidence against the generator's evidence",
        "",
        "The generator knows which skills each project and certification stands for (the "
        "project template's skills, the certification's skill list). Per student skill:",
        "",
        "| Evidence | Both | Derived only | Generator only | Precision | Recall |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for kind, c in agreement.items():
        lines.append(f"| {kind} | {c['both']} | {c['derived']} | {c['generator']} "
                     f"| {pct(c['both'], c['both'] + c['derived'])} "
                     f"| {pct(c['both'], c['both'] + c['generator'])} |")
    lines += [
        "",
        "Project evidence (project or internship) is close to complete because synthetic "
        "projects list their skills in `technologies`. Certification recall is lower by design: "
        "keyword extraction reads only the certification's name, and the generator's lists "
        "include skills the name does not say (\"Google Data Analytics Professional "
        "Certificate\" stands for SQL, Tableau and R too). \"Derived only\" rows:",
        "",
        *examples_table(examples["derived only"]),
        "",
        "## Notes",
        "",
        "- Cloud Computing rows come from `IMPLIED_SKILLS` (an AWS / Azure / GCP project or "
        "certification is also Cloud Computing evidence), which the generator's project "
        "templates do not list. CRM Software rows come from \"HubSpot\" in a certification name, "
        "a catalogue alias of CRM Software: a HubSpot Academy marketing certification is not CRM "
        "evidence, a known false positive (`docs/NLP_CLASSIFICATION_RULES.md`, section 4a).",
        "- Only rule C depends on evidence, so the transitions and the Δ are the same for "
        "`keyword` and `hybrid` (checked); the absolute readiness differs (hybrid also gives "
        "Developing for related skills).",
        "- The effect is bounded by the beginner skills that a project or certification names. "
        "The generator makes a skill with project or certification evidence more likely "
        "intermediate or advanced, so few synthetic beginner skills have one, and students with "
        "no projects or certifications cannot gain. Per skill the gain is half its weight "
        "(Developing 0.5 → Strong 1.0).",
        "- `DERIVED_EVIDENCE_NEEDS_PROOF` (off) would count only projects / certifications with "
        "an evidence file or link. The synthetic data has no evidence files, so with it on the "
        "\"with\" columns would equal \"without\".",
        "",
        "Per student: `evidence_effect_students.csv`; groups: `evidence_effect.csv`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# ── Run ───────────────────────────────────────────────────────
def sources(skill, kind=None):
    """Titles behind a derived skill's evidence, e.g. "certification: AWS Certified ..."."""
    kinds = ("project", "internship") if kind == "project" else (kind,) if kind else DERIVED_TYPES
    return "; ".join(f"{k}: {', '.join(skill['evidence_sources'][k])}"
                     for k in kinds if k in skill["evidence_sources"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("--method", default="hybrid", choices=("keyword", "semantic", "hybrid"))
    args = ap.parse_args()

    t0 = time.perf_counter()
    roles = load_roles()
    meta, skills, projects, certs = load_students()

    per_student, transitions = [], Counter()
    agreement = {k: Counter() for k in ("project", "certification")}
    examples = {"stored": Counter(), "derived only": Counter()}   # (skill, titles) -> rows
    for m in meta:
        pid, role = m["profile_id"], m["target_role"]
        mine, required = skills[pid], roles[role]
        derived_only = derive_evidence([dict(s, evidence_type=[]) for s in mine], projects[pid], certs[pid])
        for s, d in zip(mine, derived_only):
            for kind, derived in (("project", {"project", "internship"} & set(d["evidence_type"])),
                                  ("certification", "certification" in d["evidence_type"])):
                generated = kind in s["evidence_type"]
                agreement[kind]["both" if derived and generated else "derived" if derived
                                else "generator" if generated else "neither"] += 1
                if derived and not generated:
                    examples["derived only"][(s["skill_name"], sources(d, kind))] += 1
        for scenario in SCENARIOS:
            base = [dict(s, evidence_type=[]) for s in mine] if scenario == "website" else mine
            without = match_skills(base, required, args.method)
            derived = derive_evidence(base, projects[pid], certs[pid])
            with_ = match_skills(derived, required, args.method)
            by_name = {d["skill_name"]: d for d in derived}
            moved = 0
            for a, b in zip(without, with_):
                if a["match_status"] != b["match_status"]:
                    transitions[(scenario, a["match_status"], b["match_status"])] += 1
                    moved += (a["match_status"], b["match_status"]) == ("developing", "strong")
                    if scenario == "stored":
                        skill = b["matched_student_skill"]
                        examples["stored"][(skill, sources(by_name[skill]))] += 1
            per_student.append({"scenario": scenario, "email": m["email"], "archetype": m["archetype"],
                                "role": role, "records": len(projects[pid]) + len(certs[pid]),
                                "rows": len(required), "developing_to_strong": moved,
                                "without": readiness(without), "with": readiness(with_)})
    seconds = time.perf_counter() - t0

    summaries, group_rows = {}, []
    for scenario in SCENARIOS:
        rows = [r for r in per_student if r["scenario"] == scenario]
        for by, key in GROUPINGS:
            summaries[(scenario, by)] = summarise(rows, key)
            group_rows += [{"scenario": scenario, "group_by": by, **s}
                           for s in ordered(summaries[(scenario, by)], by)]

    RESULTS.mkdir(parents=True, exist_ok=True)
    for name, rows in (("evidence_effect.csv", group_rows), ("evidence_effect_students.csv", per_student)):
        with open(RESULTS / name, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    write_summary(RESULTS / "evidence_effect.md", args.method, len(meta), transitions, summaries,
                  agreement, examples, seconds)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # "→" on a Windows console
    print((RESULTS / "evidence_effect.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
