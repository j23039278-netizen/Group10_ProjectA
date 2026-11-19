"""
SEAGAS - Cross-market check of the Job Readiness Score (lecturer feedback F03)

Question: do the skills and the score that SEAGAS uses for a role hold in more than one
job market? The six IT roles have job descriptions from two markets in the dataset
(data/jd_dataset/jd_dataset.csv): Malaysia (JobStreet / Indeed, 10-13 per role) and
the US (LinkedIn via Kaggle, 22-25 per role). The four Business roles are US only and
cannot be compared yet (F06).

    python data/analysis/f03_cross_market.py          # from the repository root

Four checks, per IT role:
1. Skill demand: Spearman correlation between the share of Malaysian and of US JDs that
   ask for each skill, with a 95% bootstrap interval (JDs resampled within each market).
2. Template fit: how many of the role template's skills each market asks for, and the
   skills common in one market but rare in the other (>= 20 points apart).
3. Importance tiers: the tier each market alone would suggest for each template skill
   (same rule as data/jd_dataset/analyse_jd_skills.py: >= 50% required, >= 20% preferred,
   >= 10% bonus), and how often the two markets agree.
4. Student order: every student whose target role is the IT role, scored three ways from
   their current skills (keyword matching, rule C credit): readiness against the SEAGAS
   template, against a template built from Malaysian JDs only and from US JDs only; plus
   JD fit against Malaysian and US JDs. Spearman between them.

Writes docs/report_drafts/cross_market_validation.md and data/analysis/output/*.csv.
Read only: the database and the dataset are not changed.
"""

import csv
import random
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))
import os
os.chdir(ROOT / "backend")                    # backend/.env holds DATABASE_URL

from sqlalchemy import text                    # noqa: E402
from database import SessionLocal              # noqa: E402
import assessment_service                      # noqa: E402
import jd_fit                                  # noqa: E402
from readiness import tiered_readiness         # noqa: E402
import nlp                                     # noqa: E402

DATASET = ROOT / "data" / "jd_dataset"
OUT_DIR = ROOT / "data" / "analysis" / "output"
REPORT = ROOT / "docs" / "report_drafts" / "cross_market_validation.md"
IT_ROLES = ["DATA_ANALYST", "DATA_SCIENTIST", "SOFTWARE_DEV", "CYBER_ANALYST", "CLOUD_ENGINEER", "WEB_DEV"]
MARKETS = {"Malaysia": "MY", "other": "US"}    # every "other" JD is a US posting (DATASET_SUMMARY.md)
BOOT = 2000
GAP_POINTS = 20
random.seed(42)


def suggest(pct):
    """Same rule as data/jd_dataset/analyse_jd_skills.py"""
    if pct >= 50:
        return "required"
    if pct >= 20:
        return "preferred"
    if pct >= 10:
        return "bonus"
    return None


def load_jds():
    """{role: {"MY": [skill set per JD], "US": [...]}}"""
    region = {r["jd_ref"]: MARKETS.get(r["region"]) for r in csv.DictReader(open(DATASET / "jd_dataset.csv", encoding="utf-8"))}
    role_of = {r["jd_ref"]: r["role_code"] for r in csv.DictReader(open(DATASET / "jd_dataset.csv", encoding="utf-8"))}
    skills = defaultdict(set)
    for r in csv.DictReader(open(DATASET / "jd_skill_evidence.csv", encoding="utf-8")):
        if r["skill_name"]:
            skills[r["jd_ref"]].add(r["skill_name"])
    out = defaultdict(lambda: {"MY": [], "US": []})
    for ref, role in role_of.items():
        if role in IT_ROLES and region[ref]:
            out[role][region[ref]].append(skills.get(ref, set()))
    return out


def shares(jds, universe):
    n = len(jds)
    return {s: 100.0 * sum(s in j for j in jds) / n for s in universe}


def rho(a, b):
    r = spearmanr(a, b).statistic
    return None if r != r else float(r)        # NaN when one side is constant


def boot_ci(my, us, universe):
    vals = []
    for _ in range(BOOT):
        bm = [random.choice(my) for _ in my]
        bu = [random.choice(us) for _ in us]
        sm, su = shares(bm, universe), shares(bu, universe)
        r = rho([sm[s] for s in universe], [su[s] for s in universe])
        if r is not None:
            vals.append(r)
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def market_template(share):
    """{skill: importance} from one market's shares"""
    return {s: suggest(p) for s, p in share.items() if suggest(p)}


def score(student, template):
    required = [{"skill_id": None, "skill_name": s, "importance": imp} for s, imp in template.items()]
    if not required:
        return None
    return tiered_readiness(nlp.match_skills(student, required, method="keyword"))


def main():
    db = SessionLocal()
    jds = load_jds()
    roles = {r.role_code: r for r in db.execute(text(
        "SELECT role_id, role_code, role_name FROM job_roles WHERE role_code = ANY(:c)"), {"c": IT_ROLES})}
    rows_skill, rows_role, rows_student_summary = [], [], []
    for code in IT_ROLES:
        role = roles[code]
        my, us = jds[code]["MY"], jds[code]["US"]
        template = dict(db.execute(text(
            "SELECT sl.skill_name, j.importance FROM job_role_skills j JOIN skills_library sl USING (skill_id) "
            "WHERE j.role_id = :r"), {"r": str(role.role_id)}).fetchall())
        universe = sorted(set().union(*my, *us) | set(template))
        sm, su = shares(my, universe), shares(us, universe)

        # 1. skill demand
        r_all = rho([sm[s] for s in universe], [su[s] for s in universe])
        lo, hi = boot_ci(my, us, universe)
        r_tpl = rho([sm[s] for s in template], [su[s] for s in template])

        # 2. template fit
        asked_my = sum(sm[s] > 0 for s in template)
        asked_us = sum(su[s] > 0 for s in template)
        mean_my = statistics.mean(len(j) for j in my)
        mean_us = statistics.mean(len(j) for j in us)
        for s in universe:
            if s in template or max(sm[s], su[s]) >= 20:
                rows_skill.append({"role_code": code, "skill_name": s, "in_template": template.get(s, ""),
                                   "pct_my": round(sm[s], 1), "pct_us": round(su[s], 1),
                                   "diff_points": round(sm[s] - su[s], 1),
                                   "tier_my": suggest(sm[s]) or "", "tier_us": suggest(su[s]) or ""})
        more_my = sorted((s for s in universe if sm[s] - su[s] >= GAP_POINTS), key=lambda s: su[s] - sm[s])
        more_us = sorted((s for s in universe if su[s] - sm[s] >= GAP_POINTS), key=lambda s: sm[s] - su[s])

        # 3. tiers
        agree = sum((suggest(sm[s]) or "below") == (suggest(su[s]) or "below") for s in template)
        within_one = sum(abs(_rank(suggest(sm[s])) - _rank(suggest(su[s]))) <= 1 for s in template)

        # 4. students
        profiles = db.execute(text("""
            SELECT sp.profile_id FROM student_profiles sp JOIN users u ON u.user_id = sp.user_id
            WHERE u.role = 'student' AND u.is_active AND sp.target_role = :n"""), {"n": role.role_name}).fetchall()
        t_my, t_us = market_template(sm), market_template(su)
        res = defaultdict(list)
        for p in profiles:
            student = assessment_service.load_student_skills(db, p.profile_id)
            if not student:
                continue
            res["seagas"].append(score(student, template))
            res["my_tpl"].append(score(student, t_my))
            res["us_tpl"].append(score(student, t_us))
            res["fit_my"].append(jd_fit.jd_fit(student, my)["covered"] / len(my))
            res["fit_us"].append(jd_fit.jd_fit(student, us)["covered"] / len(us))
        n_students = len(res["seagas"])
        summary = {
            "role_code": code, "role_name": role.role_name, "students": n_students,
            "rho_seagas_my_tpl": rho(res["seagas"], res["my_tpl"]),
            "rho_seagas_us_tpl": rho(res["seagas"], res["us_tpl"]),
            "rho_my_tpl_us_tpl": rho(res["my_tpl"], res["us_tpl"]),
            "rho_seagas_fit_my": rho(res["seagas"], res["fit_my"]),
            "rho_seagas_fit_us": rho(res["seagas"], res["fit_us"]),
            "mean_seagas": statistics.mean(res["seagas"]), "mean_my_tpl": statistics.mean(res["my_tpl"]),
            "mean_us_tpl": statistics.mean(res["us_tpl"]),
            "covers_my": 100 * statistics.mean(res["fit_my"]), "covers_us": 100 * statistics.mean(res["fit_us"]),
        }
        rows_student_summary.append(summary)
        rows_role.append({"role_code": code, "role_name": role.role_name, "jds_my": len(my), "jds_us": len(us),
                          "skills_per_jd_my": mean_my, "skills_per_jd_us": mean_us,
                          "rho_all": r_all, "ci_low": lo, "ci_high": hi, "rho_template": r_tpl,
                          "template_size": len(template), "asked_my": asked_my, "asked_us": asked_us,
                          "tier_agree": agree, "tier_within_one": within_one,
                          "more_my": [(s, sm[s], su[s]) for s in more_my[:5]],
                          "more_us": [(s, sm[s], su[s]) for s in more_us[:5]]})
        print(f"{code}: rho {r_all:.2f} [{lo:.2f}, {hi:.2f}], students {n_students}, "
              f"seagas~MY-fit {summary['rho_seagas_fit_my']:.2f}, seagas~US-fit {summary['rho_seagas_fit_us']:.2f}", flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "cross_market_skills.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_skill[0]))
        w.writeheader()
        w.writerows(rows_skill)
    with open(OUT_DIR / "cross_market_students.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_student_summary[0]))
        w.writeheader()
        w.writerows({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in rows_student_summary)
    write_report(rows_role, rows_student_summary)
    print("Written:", REPORT)


def _rank(tier):
    return {"required": 3, "preferred": 2, "bonus": 1}.get(tier, 0)


def f2(v):
    return "n/a" if v is None else f"{v:.2f}"


def summary_lines(roles, students):
    rng = lambda xs: f"{min(xs):.2f} to {max(xs):.2f}"
    pct = lambda r, k: 100 * r[k] / r["template_size"]
    asked = [min(r["asked_my"], r["asked_us"]) / r["template_size"] * 100 for r in roles]
    both = [min(s["rho_seagas_my_tpl"], s["rho_seagas_us_tpl"]) for s in students]
    weak = [f"{s['role_name']} ({'Malaysia' if s['rho_seagas_my_tpl'] < s['rho_seagas_us_tpl'] else 'US'} "
            f"{min(s['rho_seagas_my_tpl'], s['rho_seagas_us_tpl']):.2f})" for s in students
            if min(s["rho_seagas_my_tpl"], s["rho_seagas_us_tpl"]) < 0.7]
    return [
        f"- **Skill demand differs between the markets.** The order of skills by demand agrees only moderately "
        f"(Spearman ρ {rng([r['rho_all'] for r in roles])} across the six IT roles). Malaysian JDs ask more often for "
        "BI and visualisation tools, testing and monitoring, and self-motivation; US JDs more often for cloud and "
        "DevOps tools, Java, Agile and identity management (section 2).",
        f"- **The role templates cover both markets.** Each market's JDs name at least {min(asked):.0f}% of the "
        "template skills of every role (section 1), so the skill lists themselves are not market-specific.",
        f"- **The importance tiers are market-specific.** Each market alone would give the same tier to "
        f"{min(pct(r, 'tier_agree') for r in roles):.0f}-{max(pct(r, 'tier_agree') for r in roles):.0f}% of the "
        f"template skills, but a tier within one step to {min(pct(r, 'tier_within_one') for r in roles):.0f}-"
        f"{max(pct(r, 'tier_within_one') for r in roles):.0f}% (section 3).",
        f"- **The score orders students much the same under either market's demands** for most roles: the lower of "
        f"the two correlations (SEAGAS against the Malaysian-only and the US-only template) ranges "
        f"{rng(both)}" + (f"; it is weaker for {', '.join(weak)}." if weak else ".") + " (section 4)",
        "",
        "**What it means for SEAGAS.** The scoring method (tiered coverage, 70 / 25 / 5, rule C) does not depend on "
        "the country, and the skill catalogue and role skill lists transfer. What does not transfer as it is, is "
        "which skills are required, preferred or bonus: that is a property of the local job market. For use outside "
        "Malaysia, a role template should keep its skills but take its tiers from local job descriptions (a "
        "per-market template), and the result should be checked again with more Malaysian JDs (F06) and with Business "
        "roles once Malaysian Business JDs exist.",
    ]


def write_report(roles, students):
    L = [
        "# Cross-market check of the Job Readiness Score (F03)",
        "",
        f"Produced {date.today().isoformat()} by `data/analysis/f03_cross_market.py` from `data/jd_dataset/` and the "
        "local database. Lecturer feedback F03 (Sprint 3 review, 12 November 2026): the readiness score should be "
        "usable internationally.",
        "",
        "**Scope.** Only the six IT roles have job descriptions from two markets: Malaysia (JobStreet and Indeed, "
        "copied by hand) and the US (LinkedIn, via Kaggle). The four Business roles have US postings only and are "
        "not compared here; adding Malaysian Business JDs is part of F06.",
        "",
        "## Summary",
        "",
        *summary_lines(roles, students),
        "",
        "## 1. Do the two markets ask for the same skills?",
        "",
        "Share of JDs that name each skill, Malaysia against US; Spearman ρ over every skill seen in the role "
        f"(95% bootstrap interval, {BOOT} resamples of the JDs within each market) and over the template skills only.",
        "",
        "| Role | JDs MY / US | Skills per JD MY / US | ρ all skills [95% CI] | ρ template skills | Template skills asked in MY / US |",
        "|---|---|---|---|---|---|",
    ]
    for r in roles:
        L.append(f"| {r['role_name']} | {r['jds_my']} / {r['jds_us']} | {r['skills_per_jd_my']:.1f} / {r['skills_per_jd_us']:.1f} | "
                 f"{f2(r['rho_all'])} [{f2(r['ci_low'])}, {f2(r['ci_high'])}] | {f2(r['rho_template'])} | "
                 f"{r['asked_my']} / {r['asked_us']} of {r['template_size']} |")
    L += ["", "## 2. Skills common in one market only", "",
          f"Skills whose share differs by at least {GAP_POINTS} percentage points (up to five per side; MY % / US %).", "",
          "| Role | More often in Malaysian JDs | More often in US JDs |", "|---|---|---|"]
    for r in roles:
        fmt = lambda xs: "; ".join(f"{s} ({m:.0f} / {u:.0f})" for s, m, u in xs) or "none"
        L.append(f"| {r['role_name']} | {fmt(r['more_my'])} | {fmt(r['more_us'])} |")
    L += ["", "## 3. Would each market give a template skill the same importance?", "",
          "Tier each market alone would suggest (≥ 50% required, ≥ 20% preferred, ≥ 10% bonus, else below), "
          "for the skills of the SEAGAS template.", "",
          "| Role | Same tier | Within one tier |", "|---|---|---|"]
    for r in roles:
        n = r["template_size"]
        L.append(f"| {r['role_name']} | {r['tier_agree']} of {n} ({100 * r['tier_agree'] / n:.0f}%) | "
                 f"{r['tier_within_one']} of {n} ({100 * r['tier_within_one'] / n:.0f}%) |")
    L += ["", "## 4. Would students be ranked the same in either market?", "",
          "Every student whose target role is the IT role (synthetic students), from their current skills with "
          "keyword matching. *SEAGAS*: readiness against the role template. *MY / US template*: readiness against a "
          "template built from that market's JDs only (rule of section 3). *JD fit*: share of that market's JDs the "
          "student covers (60% rule, `backend/jd_fit.py`).", "",
          "| Role | Students | ρ SEAGAS vs MY template | ρ SEAGAS vs US template | ρ MY vs US template | "
          "ρ SEAGAS vs JD fit MY | ρ SEAGAS vs JD fit US | Mean readiness SEAGAS / MY / US |",
          "|---|---:|---|---|---|---|---|---|"]
    for s in students:
        L.append(f"| {s['role_name']} | {s['students']:,} | {f2(s['rho_seagas_my_tpl'])} | {f2(s['rho_seagas_us_tpl'])} | "
                 f"{f2(s['rho_my_tpl_us_tpl'])} | {f2(s['rho_seagas_fit_my'])} | {f2(s['rho_seagas_fit_us'])} | "
                 f"{s['mean_seagas']:.1f} / {s['mean_my_tpl']:.1f} / {s['mean_us_tpl']:.1f} |")
    L += ["", "## Limits", "",
          "- Few Malaysian JDs per role (10-13), so the intervals are wide; one JD moves a share by 8-10 points.",
          "- The bootstrap intervals sit mostly below the estimate: resampling repeats JDs, which adds noise to the "
          "shares and pulls a rank correlation down. Read them as a rough range, not an exact 95% interval.",
          "- Some differences are extraction noise rather than demand, e.g. Recruitment in US Software Developer "
          "JDs comes from LinkedIn hiring boilerplate.",
          "- US postings are longer and, for five of the six roles, name slightly more skills per JD (section 1), "
          "which raises US shares a little across the board. Spearman compares orders, not levels, so it is less "
          "affected than raw shares.",
          "- Students are synthetic, generated from the same skill catalogue: section 4 shows whether the score "
          "orders the same profiles alike under both markets' demands, not how real students would fare.",
          "- Business roles are not covered (US only).",
          "- The skill sets come from SEAGAS's own extraction (`jd_skill_evidence.csv`), so extraction errors "
          "affect both markets the same way.", ""]
    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
