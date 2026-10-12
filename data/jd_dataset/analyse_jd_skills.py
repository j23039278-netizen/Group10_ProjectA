"""
Skill frequency analysis over jd_dataset.csv (keyword baseline).

Outputs (in --out-dir, default data/jd_dataset/):
  jd_skill_frequency.csv  share of each role's JDs that mention each skill,
                          with a suggested importance
                          (>= 50% required, 20-50% preferred, 10-20% bonus)
  unmatched_terms.csv     frequent terms / phrases NOT covered by the skills
                          library -> candidates for new skills
                          (spaCy noun chunks if spaCy is installed, otherwise n-grams)
  role_skill_diff.csv     suggested vs current importance in
                          database/seed_job_role_skills.sql (differences only)

It never edits the seed files — Yong Hin decides what to change.

Usage (from repo root):
    python data/jd_dataset/analyse_jd_skills.py
    python data/jd_dataset/analyse_jd_skills.py --dataset data/jd_dataset/samples/jd_dataset_sample.csv --out-dir data/jd_dataset/samples
"""

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

from jd_common import DATASET_PATH, JD_DIR, SkillMatcher, load_role_skills, load_skills, read_dataset, write_csv

STOPWORDS = set("""
a about above across after again against all also am an and any are as at be because been before being
below between both but by can could did do does doing down during each etc few for from further had has
have having he her here hers him his how i if in into is it its itself just least less may me might more
most must my no nor not now of off on once only or other our ours out over own per plus please same shall
she should so some such than that the their theirs them then there these they this those through to too
under until up upon us very via was we well were what when where which while who whom why will with
within without would you your yours
ability able apply applicant applicants candidate candidates company role position job work working
team teams year years experience experienced strong good excellent knowledge understanding skills skill
including include includes related relevant required requirements requirement preferred responsibilities
responsible using use used new join opportunity opportunities based across support ensure within day
key make great looking seeking environment degree bachelor bachelors diploma field e.g i.e plus
benefits salary office hybrid remote malaysia kuala lumpur selangor petaling jaya [email] [url] [phone]
[company] minimum least one two three etc.
write build run help nice clean hiring junior senior graduate fresh engineer engineers developer analyst
computer science information technology looking join build building develop developing design designing
maintain manage managing provide create perform take keep turn share set up want like get hands-on
email phone url familiarity
""".split())


def suggest(pct):
    if pct >= 50:
        return "required"
    if pct >= 20:
        return "preferred"
    if pct >= 10:
        return "bonus"
    return ""


def matched_mask(text, hits):
    """Blank out matched skill spans so they don't show up as unmatched terms."""
    chars = list(text)
    for s, e, _, _ in hits:
        for i in range(s, e):
            chars[i] = " "
    return "".join(chars)


def load_spacy():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:  # spaCy or the model not installed -> n-gram fallback
        return None


def candidate_terms(text, nlp=None):
    """spaCy noun chunks when available, else 1-3 word n-grams without stopwords."""
    if nlp is not None:
        terms = set()
        for chunk in nlp(text).noun_chunks:
            words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9+#.\-/]*", chunk.text)
                     if w.lower() not in STOPWORDS]
            if words and len(words) <= 3:
                terms.add(" ".join(words))
        return terms
    terms = set()
    for sentence in re.split(r"[\n.;:,()!?•*]+", text):
        words = [w.lower().strip(".-/") for w in re.findall(r"[A-Za-z][A-Za-z0-9+#.\-/]*", sentence)]
        for n in (1, 2, 3):
            for i in range(len(words) - n + 1):
                gram = words[i:i + n]
                if gram[0] in STOPWORDS or gram[-1] in STOPWORDS or len(gram[0]) < 2:
                    continue
                if any(w in STOPWORDS for w in gram) and n == 2:
                    continue
                terms.add(" ".join(gram))
    return terms


def main():
    ap = argparse.ArgumentParser(description="JD skill frequency analysis")
    ap.add_argument("--dataset", default=str(DATASET_PATH))
    ap.add_argument("--out-dir", default=str(JD_DIR))
    ap.add_argument("--min-docs", type=int, default=2,
                    help="minimum number of JDs an unmatched term must appear in (default 2)")
    ap.add_argument("--top", type=int, default=300, help="max unmatched terms to write")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)

    jds = read_dataset(args.dataset)
    if not jds:
        raise SystemExit(f"No JDs in {args.dataset}")
    skills = {s["skill_name"]: s for s in load_skills()}
    matcher = SkillMatcher(list(skills.values()))
    nlp = load_spacy()
    print("Unmatched terms via:", "spaCy noun chunks" if nlp else "n-grams (spaCy not installed)")

    n_by_role = Counter(j["role_code"] for j in jds)
    skill_docs = defaultdict(Counter)       # role -> skill -> n JDs
    term_docs = Counter()
    term_roles = defaultdict(Counter)
    for j in jds:
        hits = matcher.find(j["raw_text"])
        for sk in {h[3] for h in hits}:
            skill_docs[j["role_code"]][sk] += 1
        for t in candidate_terms(matched_mask(j["raw_text"], hits), nlp):
            term_docs[t] += 1
            term_roles[t][j["role_code"]] += 1

    # 1. frequency table
    current = load_role_skills()
    freq_rows = []
    for role in sorted(n_by_role):
        n = n_by_role[role]
        for sk, c in skill_docs[role].most_common():
            pct = round(c / n * 100, 1)
            freq_rows.append({
                "role_code": role, "skill_name": sk, "category": skills[sk]["category"],
                "subcategory": skills[sk]["subcategory"], "jd_count": c, "role_jd_total": n,
                "pct_of_jds": pct, "suggested_importance": suggest(pct),
                "current_importance": current.get(role, {}).get(sk, ""),
            })
    write_csv(out_dir / "jd_skill_frequency.csv", freq_rows, list(freq_rows[0].keys()) if freq_rows else
              ["role_code", "skill_name", "category", "subcategory", "jd_count", "role_jd_total",
               "pct_of_jds", "suggested_importance", "current_importance"])

    # 2. unmatched terms
    unmatched = [
        {"term": t, "jd_count": c, "pct_of_all_jds": round(c / len(jds) * 100, 1),
         "roles": "|".join(f"{r}:{k}" for r, k in term_roles[t].most_common())}
        for t, c in term_docs.most_common() if c >= args.min_docs
    ][:args.top]
    write_csv(out_dir / "unmatched_terms.csv", unmatched, ["term", "jd_count", "pct_of_all_jds", "roles"])

    # 3. suggested vs current role mapping
    diff = []
    for role in sorted(set(n_by_role) | set(current)):
        n = n_by_role.get(role, 0)
        role_skills = set(skill_docs[role]) | set(current.get(role, {}))
        for sk in sorted(role_skills):
            c = skill_docs[role][sk]
            pct = round(c / n * 100, 1) if n else 0.0
            sug = suggest(pct) if n else ""
            cur = current.get(role, {}).get(sk, "")
            if sug != cur:
                diff.append({"role_code": role, "skill_name": sk, "role_jd_total": n, "pct_of_jds": pct,
                             "current_importance": cur or "(not mapped)",
                             "suggested_importance": sug or "(drop / below 10%)"})
    write_csv(out_dir / "role_skill_diff.csv", diff,
              ["role_code", "skill_name", "role_jd_total", "pct_of_jds", "current_importance",
               "suggested_importance"])

    print(f"Analysed {len(jds)} JDs ({dict(n_by_role)})")
    print(f"  jd_skill_frequency.csv  {len(freq_rows)} rows")
    print(f"  unmatched_terms.csv     {len(unmatched)} rows")
    print(f"  role_skill_diff.csv     {len(diff)} rows")
    if min(n_by_role.values()) < 30:
        print("  NOTE: fewer than 30 JDs for some roles - percentages are not reliable yet.")


if __name__ == "__main__":
    main()
