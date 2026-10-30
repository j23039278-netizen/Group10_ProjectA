"""
Build data/jd_dataset/jd_dataset.csv from raw job descriptions.

Input (default --raw-dir data/raw, which is git-ignored):
  kaggle/*.csv          public datasets downloaded by hand from Kaggle.
  kaggle/LICENSES.csv   one row per CSV: file,dataset,license,downloaded
                        (e.g. postings.csv,arshkon/linkedin-job-postings,CC BY-SA 4.0,2026-10-01)
  manual/<ROLE_CODE>/<n>.txt   one JD per file, copied by hand:
        line 1: <source URL> <YYYY-MM-DD>
        optional header lines: "Title: ...", "Location: ...", "Company: ...", "Seniority: ..."
        blank line, then the JD body
  api/<source>/**/*.json   reserved for the Phase 6 API collector (not built yet).
        Each file is a JSON list of jobs, or an object with a "jobs" list
        (Greenhouse / Remotive style). Recognised job fields: title, content /
        description, location (string or {"name": ...}), company / company_name,
        absolute_url / url / source_url. Optional top-level (or per-job) keys:
        "source" (e.g. "api:greenhouse:<board>", default "api:<source>"),
        "source_license" / "terms", "collected_date".
  company_aliases.txt   optional: other names of the employers (short forms,
        brands, parent groups), one per line, "#" for comments. They are
        masked as [COMPANY] like the company field.

Pipeline: map title -> one of the 10 role_codes (skip unknown and senior roles)
-> clean (strip HTML, drop the "About the company" blurb, remove emails /
phone numbers / URLs / company names and aliases, collapse whitespace) -> drop texts < 300 chars -> de-duplicate by text hash
-> draw a capped sample from each Kaggle file -> assign stable jd_refs -> write CSV.
Company is always written as "Anonymised".

Kaggle sampling: a large file must not swamp the dataset. Per role and Kaggle
file, at most --cap JDs are taken (default: what the role still needs to reach
30 JDs from the other sources, plus a margin of 5; 0 if it already has 30).
The draw happens after the seniority, length and duplicate filters, with seed
42, and prefers entry / junior postings, then Malaysia, then other APAC, then
the rest. At most --employer-cap postings (default 5) per employer per role are
taken (employer = website domain, else company name, else company id, read
before anonymisation). Manual and API JDs are never capped.

Stable jd_refs: the existing --out file is read first. Its rows are kept as
they are (also when their raw file is no longer in --raw-dir) and keep their
jd_ref; a raw JD with the same text hash (or the same source and URL) is
recognised as already present. New JDs get the next number per role, ordered by
source and text hash. Running ingest again on the same input gives the same
file, and adding a file never renumbers old JDs. --rebuild ignores the existing file.

Usage (from repo root):
    python data/jd_dataset/ingest_jds.py
    python data/jd_dataset/ingest_jds.py --profile        # describe each Kaggle CSV and stop
    python data/jd_dataset/ingest_jds.py --cap 20 --employer-cap 3
    python data/jd_dataset/ingest_jds.py --raw-dir data/jd_dataset/samples --out data/jd_dataset/samples/jd_dataset_sample.csv
"""

import argparse
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from itertools import chain
from pathlib import Path

from jd_common import (DATASET_FIELDS, DATASET_PATH, REGIONS, REPO_ROOT, ROLE_ABBR, brand_words,
                       classify_role, classify_seniority, clean_text, combine_seniority, company_variants,
                       mask_companies, mask_words, read_dataset, region_of, text_hash, write_csv)

MIN_CHARS = 300
TARGET_PER_ROLE = 30
CAP_MARGIN = 5
EMPLOYER_CAP = 5
SEED = 42
# Draw order inside a role: entry / junior first, then Malaysia, other APAC, the rest.
SENIORITY_RANK = {"entry": 0, "junior": 0, "mid": 1}
REGION_RANK = {"Malaysia": 0, "other APAC": 1, "remote": 2, "other": 2}
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

TITLE_COLS = ["title", "job_title", "jobtitle", "position", "job title", "job_position"]
TEXT_COLS = ["description", "job_description", "jobdescription", "job description", "desc", "text"]
LOC_COLS = ["location", "job_location", "city", "job location"]
COMPANY_COLS = ["company", "company_name", "employer", "company name"]
URL_COLS = ["source_url", "job_posting_url", "absolute_url", "url", "link", "job_link", "application_url"]
LEVEL_COLS = ["formatted_experience_level", "experience_level", "seniority_level", "job_level", "career_level"]
# Employer key for --employer-cap: website domain first, then the company name, then an id.
DOMAIN_COLS = ["company_domain", "company_website", "website_domain", "company_url", "website", "domain"]
COMPANY_ID_COLS = ["company_id", "employer_id"]


def pick(row, candidates):
    lower = {k.lower().strip(): k for k in row if k}
    for c in candidates:
        if c in lower and row[lower[c]]:
            return row[lower[c]]
    return ""


def employer_key(domain, company, company_id=""):
    """Normalised employer for --employer-cap ("https://www.bosch.com/x" -> "bosch.com")."""
    d = re.sub(r"^(?:https?://)?(?:www\.)?", "", (domain or "").strip().lower()).split("/")[0]
    if d:
        return d
    variants = sorted(company_variants(company), key=len)
    if variants:
        return variants[0].lower()
    return f"id:{company_id}" if company_id else ""


def kaggle_files(raw_dir):
    kdir = raw_dir / "kaggle"
    if not kdir.is_dir():
        return [], {}
    licenses = {}
    lic_path = kdir / "LICENSES.csv"
    if lic_path.exists():
        with open(lic_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                licenses[r["file"].strip()] = r
    return [p for p in sorted(kdir.glob("*.csv")) if p.name != "LICENSES.csv"], licenses


def read_kaggle(raw_dir):
    """Yield one record per Kaggle row. Files are streamed, never loaded whole."""
    paths, licenses = kaggle_files(raw_dir)
    for path in paths:
        lic = licenses.get(path.name)
        if not lic:
            print(f"WARNING: {path.name} has no row in kaggle/LICENSES.csv - "
                  f"record the dataset licence before using it.", file=sys.stderr)
        dataset = (lic or {}).get("dataset", path.stem)
        collected = (lic or {}).get("downloaded") or date.fromtimestamp(path.stat().st_mtime).isoformat()
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                company = pick(row, COMPANY_COLS).strip()
                yield {
                    "title": pick(row, TITLE_COLS).strip(),
                    "text": pick(row, TEXT_COLS),
                    "location": pick(row, LOC_COLS).strip(),
                    "company": company,
                    "source": f"kaggle:{dataset}",
                    "source_url": pick(row, URL_COLS).strip(),
                    "source_license": (lic or {}).get("license", "UNKNOWN"),
                    "collected_date": collected,
                    "role_hint": None,
                    "seniority_hint": None,
                    "level": pick(row, LEVEL_COLS).strip(),
                    "employer": employer_key(pick(row, DOMAIN_COLS), company, pick(row, COMPANY_ID_COLS)),
                }


def parse_date(value):
    v = (value or "").strip()
    if re.fullmatch(r"\d{9,13}(?:\.\d+)?", v):  # epoch seconds or milliseconds
        t = float(v)
        return datetime.fromtimestamp(t / 1000 if t > 1e11 else t, timezone.utc).date()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", v)
    if m:
        try:
            return date(*map(int, m.groups()))
        except ValueError:
            return None
    return None


ENGLISH_RE = re.compile(r"\b(?:the|and|to|of|with|you|for)\b", re.I)


def profile_kaggle(raw_dir):
    """Print a short profile of each Kaggle CSV (streamed; no posting text is printed)."""
    paths, licenses = kaggle_files(raw_dir)
    if not paths:
        print(f"No Kaggle CSVs in {raw_dir / 'kaggle'}")
    for path in paths:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames or []
            lower = {c.lower().strip(): c for c in cols}
            used = {name: next((lower[c] for c in cand if c in lower), "-") for name, cand in
                    [("title", TITLE_COLS), ("text", TEXT_COLS), ("location", LOC_COLS),
                     ("company", COMPANY_COLS), ("url", URL_COLS), ("level", LEVEL_COLS),
                     ("domain", DOMAIN_COLS)]}
            date_cols = [c for c in cols if re.search(r"date|time|posted|listed", c, re.I)]
            n, english, roles, regions, dates = 0, 0, Counter(), Counter(), []
            for row in reader:
                n += 1
                if len(ENGLISH_RE.findall(pick(row, TEXT_COLS)[:1000])) >= 5:
                    english += 1
                roles[classify_role(pick(row, TITLE_COLS)) or "(none)"] += 1
                regions[region_of(pick(row, LOC_COLS))] += 1
                d = next((d for d in (parse_date(row[c]) for c in date_cols) if d), None)
                if d:
                    dates.append(d)
        lic = licenses.get(path.name, {})
        print(f"\n{path.name}  ({path.stat().st_size / 1e6:,.0f} MB, {n:,} rows)")
        print(f"  dataset / licence : {lic.get('dataset', '(not in LICENSES.csv)')} / {lic.get('license', 'UNKNOWN')}")
        print(f"  columns ({len(cols)})      : {', '.join(cols)}")
        print("  columns used      : " + ", ".join(f"{k}={v}" for k, v in used.items()))
        print(f"  language          : {english / max(n, 1):.0%} of descriptions look English")
        print(f"  date range        : {min(dates)} to {max(dates)}" if dates else "  date range        : unknown")
        print("  region            : " + ", ".join(f"{r} {regions[r]:,}" for r in REGIONS))
        print("  title -> role     : " + ", ".join(f"{r} {c:,}" for r, c in roles.most_common()))


def read_manual(raw_dir):
    mdir = raw_dir / "manual"
    if not mdir.is_dir():
        return []
    out = []
    for path in sorted(mdir.glob("*/*.txt")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines:
            continue
        first = lines[0].split()
        url = first[0] if first else ""
        collected = next((w for w in first[1:] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", w)), "")
        headers, i = {}, 1
        while i < len(lines) and lines[i].strip():
            m = re.match(r"^(Title|Location|Company|Seniority)\s*:\s*(.*)$", lines[i].strip(), re.I)
            if not m:
                break
            headers[m.group(1).lower()] = m.group(2).strip()
            i += 1
        role_hint = path.parent.name.upper()
        out.append({
            "title": headers.get("title", ""),
            "text": "\n".join(lines[i:]),
            "location": headers.get("location", ""),
            "company": headers.get("company", ""),
            "source": "manual" if not url.startswith("sample:") else "sample",
            "source_url": url,
            "source_license": "Copied manually for non-commercial academic research",
            "collected_date": collected,
            "role_hint": role_hint if role_hint in ROLE_ABBR else None,
            "seniority_hint": headers.get("seniority", "").lower() or None,
            "level": "",
            "employer": employer_key("", headers.get("company", "")),
            "file": str(path),
        })
    return out


def read_api(raw_dir):
    """Phase 6 hook: JSON files saved by the (future) API collector."""
    adir = raw_dir / "api"
    if not adir.is_dir():
        return []
    out = []
    for path in sorted(adir.glob("*/**/*.json")):
        source_name = path.relative_to(adir).parts[0]
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data if isinstance(data, dict) else {}
        jobs = data.get("jobs", []) if isinstance(data, dict) else data
        collected = meta.get("collected_date") or date.fromtimestamp(path.stat().st_mtime).isoformat()
        for job in jobs:
            loc = job.get("location") or job.get("candidate_required_location") or ""
            if isinstance(loc, dict):
                loc = loc.get("name", "")
            company = (job.get("company") or job.get("company_name") or meta.get("company") or "").strip()
            out.append({
                "title": (job.get("title") or "").strip(),
                "text": job.get("content") or job.get("description") or "",
                "location": str(loc).strip(),
                "company": company,
                "source": job.get("source") or meta.get("source") or f"api:{source_name}",
                "source_url": job.get("absolute_url") or job.get("url") or job.get("source_url") or "",
                "source_license": (job.get("source_license") or meta.get("source_license")
                                   or meta.get("terms") or "See source API terms"),
                "collected_date": job.get("collected_date") or collected,
                "role_hint": None,
                "seniority_hint": None,
                "level": "",
                "employer": employer_key("", company),
            })
    return out


def read_aliases(raw_dir):
    path = raw_dir / "company_aliases.txt"
    if not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {ln.split("#", 1)[0].strip() for ln in lines} - {""}


def draw(pool, room, employer_count, employer_cap, rng):
    """Pick up to `room` rows: seeded shuffle, then entry / junior first and
    Malaysia, other APAC, the rest; skip employers that already have
    `employer_cap` rows in this role. Returns (drawn, skipped_by_employer_cap)."""
    pool = sorted(pool, key=lambda c: c["_hash"])
    rng.shuffle(pool)
    pool.sort(key=lambda c: (SENIORITY_RANK.get(c["seniority"], 1), REGION_RANK[c["region"]]))
    drawn, skipped = [], 0
    for c in pool:
        if len(drawn) >= room:
            break
        key = (c["role_code"], c["_employer"])
        if employer_count[key] >= employer_cap:
            skipped += 1
            continue
        employer_count[key] += 1
        drawn.append(c)
    return drawn, skipped


def build(raw_dir, previous=None, cap=None, employer_cap=EMPLOYER_CAP, seed=SEED):
    """Return (rows, stats). `previous` is the existing dataset CSV, or None to start fresh."""
    prev_rows = read_dataset(previous) if previous and Path(previous).exists() else []
    prev_by_hash = {text_hash(r["raw_text"]): r for r in prev_rows}
    prev_by_url = {(r["source"], r["source_url"]): r for r in prev_rows if r["source_url"]}

    manual, api = read_manual(raw_dir), read_api(raw_dir)
    # Company names from manual and API files are masked in every JD (re-posts often
    # lack the company field). A Kaggle row only adds its own company: a Kaggle file
    # has thousands of employers, some named after common words.
    companies = {v for r in manual + api if r["company"] for v in company_variants(r["company"])}
    companies |= read_aliases(raw_dir)
    stats = defaultdict(Counter)
    candidates, seen = [], set()
    for r in chain(manual, api, read_kaggle(raw_dir)):
        st = stats[r["source"]]
        st["read"] += 1
        role = r["role_hint"] or classify_role(r["title"])
        if not role:
            st[f"skipped: title not one of the {len(ROLE_ABBR)} roles"] += 1
            continue
        seniority = r["seniority_hint"] or combine_seniority(classify_seniority(r["title"], r["text"]), r["level"])
        if seniority == "senior":
            st["skipped: senior / management title"] += 1
            continue
        is_kaggle = r["source"].startswith("kaggle:")
        own = company_variants(r["company"]) if is_kaggle else set()
        brands = brand_words(r["company"]) if is_kaggle else set()
        text = mask_words(clean_text(r["text"], companies | own), brands)
        if len(text) < MIN_CHARS:
            st[f"skipped: shorter than {MIN_CHARS} chars"] += 1
            continue
        h = text_hash(text)
        if h in seen:
            st["skipped: duplicate text"] += 1
            continue
        seen.add(h)
        prev = prev_by_hash.get(h) or prev_by_url.get((r["source"], r["source_url"]))
        if prev:
            st["already in dataset"] += 1
        candidates.append({
            "role_code": role, "title": mask_words(mask_companies(r["title"], companies | own), brands) or "(untitled)",
            "company": "Anonymised", "location": r["location"], "region": region_of(r["location"]),
            "seniority": seniority, "source": r["source"], "source_url": r["source_url"],
            "source_license": r["source_license"], "collected_date": r["collected_date"],
            "raw_text": text, "_hash": h, "_employer": r["employer"], "_prev": prev,
        })

    # Old rows are kept as they are, with their jd_ref (region is derived, so it is filled in).
    rows = [dict(p, region=p.get("region") or region_of(p["location"])) for p in prev_rows]
    if prev_rows:
        stats["(existing dataset)"]["kept with their jd_ref"] = len(prev_rows)
        stats["(existing dataset)"]["raw file not in --raw-dir"] = len(
            {p["jd_ref"] for p in prev_rows} - {c["_prev"]["jd_ref"] for c in candidates if c["_prev"]})
    new = [c for c in candidates if not c["_prev"]]
    rows += [c for c in new if not c["source"].startswith("kaggle:")]
    employer_count = Counter((c["role_code"], c["_employer"]) for c in candidates
                             if c["_prev"] and c["source"].startswith("kaggle:"))
    for source in sorted({c["source"] for c in new if c["source"].startswith("kaggle:")}):
        st = stats[source]
        for role in ROLE_ABBR:
            pool = [c for c in new if c["source"] == source and c["role_code"] == role]
            if not pool:
                continue
            have = sum(1 for r in rows if r["role_code"] == role and r["source"] == source)
            others = sum(1 for r in rows if r["role_code"] == role and r["source"] != source)
            limit = cap if cap is not None else (
                TARGET_PER_ROLE - others + CAP_MARGIN if others < TARGET_PER_ROLE else 0)
            rng = random.Random(f"{seed}|{source}|{role}")
            drawn, skipped = draw(pool, max(0, limit - have), employer_count, employer_cap, rng)
            rows += drawn
            st["skipped: per-employer cap"] += skipped
            st["not drawn: per-role cap"] += len(pool) - len(drawn) - skipped

    # New rows get the next number per role, ordered by source and text hash.
    last = Counter()
    for r in rows:
        if r.get("jd_ref"):
            last[r["role_code"]] = max(last[r["role_code"]], int(r["jd_ref"].rsplit("-", 1)[1]))
    for r in sorted((r for r in rows if not r.get("jd_ref")),
                    key=lambda x: (x["role_code"], x["source"], x["_hash"])):
        last[r["role_code"]] += 1
        r["jd_ref"] = f"JD-{ROLE_ABBR[r['role_code']]}-{last[r['role_code']]:04d}"
        stats[r["source"]]["added"] += 1
    rows.sort(key=lambda r: (r["role_code"], r["jd_ref"]))
    return [{k: r.get(k, "") for k in DATASET_FIELDS} for r in rows], stats


def print_report(rows, stats):
    for source in sorted(stats):
        print(f"  {source}")
        for k, v in stats[source].items():
            print(f"    {k:<40} {v:>7,}")
    sources = sorted({r["source"] for r in rows})
    print(f"\n  {'role':<18} {'total':>5}  " + "  ".join(f"{s[:32]:>32}" for s in sources)
          + "  " + "  ".join(f"{g:>10}" for g in REGIONS))
    for code in ROLE_ABBR:
        rr = [r for r in rows if r["role_code"] == code]
        by_src, by_reg = Counter(r["source"] for r in rr), Counter(r["region"] for r in rr)
        flag = "" if len(rr) >= TARGET_PER_ROLE else f"   (< {TARGET_PER_ROLE}: needs {TARGET_PER_ROLE - len(rr)} more)"
        print(f"  {code:<18} {len(rr):>5}  " + "  ".join(f"{by_src[s]:>32}" for s in sources)
              + "  " + "  ".join(f"{by_reg[g]:>10}" for g in REGIONS) + flag)


def main():
    ap = argparse.ArgumentParser(description="Ingest raw JDs into jd_dataset.csv")
    ap.add_argument("--raw-dir", default=str(REPO_ROOT / "data" / "raw"))
    ap.add_argument("--out", default=str(DATASET_PATH))
    ap.add_argument("--cap", type=int, default=None,
                    help=f"max JDs per role from each Kaggle file (default: what the role needs to reach "
                         f"{TARGET_PER_ROLE}, plus {CAP_MARGIN})")
    ap.add_argument("--employer-cap", type=int, default=EMPLOYER_CAP,
                    help=f"max Kaggle JDs per employer per role (default {EMPLOYER_CAP})")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--rebuild", action="store_true",
                    help="ignore the existing --out file (renumbers jd_refs; never use it once gold labels exist)")
    ap.add_argument("--profile", action="store_true", help="print a profile of each Kaggle CSV and stop")
    args = ap.parse_args()
    raw_dir = Path(args.raw_dir)
    if args.profile:
        profile_kaggle(raw_dir)
        return

    rows, stats = build(raw_dir, None if args.rebuild else args.out, args.cap, args.employer_cap, args.seed)
    write_csv(args.out, rows, DATASET_FIELDS)
    print(f"{datetime.now():%Y-%m-%d %H:%M}  wrote {len(rows)} JDs -> {args.out}")
    print_report(rows, stats)


if __name__ == "__main__":
    main()
