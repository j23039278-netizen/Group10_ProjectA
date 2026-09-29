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

Pipeline: map title -> one of the 6 role_codes (skip unknown and senior roles)
-> clean (strip HTML, remove emails / phone numbers / URLs / company name,
collapse whitespace) -> drop texts < 300 chars -> de-duplicate by text hash
-> assign stable jd_refs (JD-DA-0001 ...) -> write CSV. Company is always
written as "Anonymised".

Usage (from repo root):
    python data/jd_dataset/ingest_jds.py
    python data/jd_dataset/ingest_jds.py --raw-dir data/jd_dataset/samples --out data/jd_dataset/samples/jd_dataset_sample.csv
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from jd_common import (DATASET_FIELDS, DATASET_PATH, REPO_ROOT, ROLE_ABBR, classify_role,
                       classify_seniority, clean_text, text_hash, write_csv)

MIN_CHARS = 300
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

TITLE_COLS = ["title", "job_title", "jobtitle", "position", "job title", "job_position"]
TEXT_COLS = ["description", "job_description", "jobdescription", "job description", "desc", "text"]
LOC_COLS = ["location", "job_location", "city", "job location"]
COMPANY_COLS = ["company", "company_name", "employer", "company name"]
URL_COLS = ["source_url", "job_posting_url", "absolute_url", "url", "link", "job_link", "application_url"]


def pick(row, candidates):
    lower = {k.lower().strip(): k for k in row}
    for c in candidates:
        if c in lower and row[lower[c]]:
            return row[lower[c]]
    return ""


def read_kaggle(raw_dir):
    kdir = raw_dir / "kaggle"
    if not kdir.is_dir():
        return []
    licenses = {}
    lic_path = kdir / "LICENSES.csv"
    if lic_path.exists():
        with open(lic_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                licenses[r["file"].strip()] = r
    out = []
    for path in sorted(kdir.glob("*.csv")):
        if path.name == "LICENSES.csv":
            continue
        lic = licenses.get(path.name)
        if not lic:
            print(f"WARNING: {path.name} has no row in kaggle/LICENSES.csv - "
                  f"record the dataset licence before using it.", file=sys.stderr)
        dataset = (lic or {}).get("dataset", path.stem)
        collected = (lic or {}).get("downloaded") or date.fromtimestamp(path.stat().st_mtime).isoformat()
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                out.append({
                    "title": pick(row, TITLE_COLS).strip(),
                    "text": pick(row, TEXT_COLS),
                    "location": pick(row, LOC_COLS).strip(),
                    "company": pick(row, COMPANY_COLS).strip(),
                    "source": f"kaggle:{dataset}",
                    "source_url": pick(row, URL_COLS).strip(),
                    "source_license": (lic or {}).get("license", "UNKNOWN"),
                    "collected_date": collected,
                    "role_hint": None,
                    "seniority_hint": None,
                })
    return out


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
            out.append({
                "title": (job.get("title") or "").strip(),
                "text": job.get("content") or job.get("description") or "",
                "location": str(loc).strip(),
                "company": (job.get("company") or job.get("company_name") or meta.get("company") or "").strip(),
                "source": job.get("source") or meta.get("source") or f"api:{source_name}",
                "source_url": job.get("absolute_url") or job.get("url") or job.get("source_url") or "",
                "source_license": (job.get("source_license") or meta.get("source_license")
                                   or meta.get("terms") or "See source API terms"),
                "collected_date": job.get("collected_date") or collected,
                "role_hint": None,
                "seniority_hint": None,
            })
    return out


def main():
    ap = argparse.ArgumentParser(description="Ingest raw JDs into jd_dataset.csv")
    ap.add_argument("--raw-dir", default=str(REPO_ROOT / "data" / "raw"))
    ap.add_argument("--out", default=str(DATASET_PATH))
    args = ap.parse_args()
    raw_dir = Path(args.raw_dir)

    raw = read_kaggle(raw_dir) + read_manual(raw_dir) + read_api(raw_dir)
    companies = {r["company"] for r in raw if r["company"]}
    stats = Counter()
    kept, seen = [], set()
    for r in raw:
        stats["read"] += 1
        role = r["role_hint"] or classify_role(r["title"])
        if not role:
            stats["skipped: title not one of the 6 roles"] += 1
            continue
        seniority = r["seniority_hint"] or classify_seniority(r["title"], r["text"])
        if seniority == "senior":
            stats["skipped: senior / management title"] += 1
            continue
        text = clean_text(r["text"], companies)
        if len(text) < MIN_CHARS:
            stats[f"skipped: shorter than {MIN_CHARS} chars"] += 1
            continue
        h = text_hash(text)
        if h in seen:
            stats["skipped: duplicate text"] += 1
            continue
        seen.add(h)
        kept.append({
            "role_code": role, "title": r["title"] or "(untitled)", "company": "Anonymised",
            "location": r["location"], "seniority": seniority, "source": r["source"],
            "source_url": r["source_url"],
            "source_license": r["source_license"], "collected_date": r["collected_date"],
            "raw_text": text, "_hash": h,
        })

    # stable jd_refs: sort by role, source, hash
    kept.sort(key=lambda x: (x["role_code"], x["source"], x["_hash"]))
    per_role = Counter()
    for k in kept:
        per_role[k["role_code"]] += 1
        k["jd_ref"] = f"JD-{ROLE_ABBR[k['role_code']]}-{per_role[k['role_code']]:04d}"
        del k["_hash"]

    write_csv(args.out, kept, DATASET_FIELDS)
    print(f"{datetime.now():%Y-%m-%d %H:%M}  wrote {len(kept)} JDs -> {args.out}")
    for k, v in stats.items():
        print(f"  {k:<40} {v}")
    for code in ROLE_ABBR:
        flag = "" if per_role[code] >= 30 else "   (< 30, target not met)"
        print(f"  {code:<16} {per_role[code]:>5}{flag}")


if __name__ == "__main__":
    main()
