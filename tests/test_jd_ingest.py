"""Checks for the JD title rules, region and Kaggle sampling (run: python -m pytest tests -q).

All postings below are fictional.
"""

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data" / "jd_dataset"))
import ingest_jds  # noqa: E402
from jd_common import (DATASET_FIELDS, brand_words, classify_role, classify_seniority,  # noqa: E402
                       clean_text, combine_seniority, mask_words, read_dataset, region_of, write_csv)


@pytest.mark.parametrize("title, role", [
    # Business roles, including US title variants
    ("Junior Business Analyst", "BUSINESS_ANALYST"),
    ("IT Business Analyst", "BUSINESS_ANALYST"),
    ("Business Systems Analyst - Site Reliability Center", "BUSINESS_ANALYST"),
    ("Business Intelligence Analyst", "DATA_ANALYST"),
    ("Business Data Analyst", "DATA_ANALYST"),
    ("Financial Analyst", "FINANCIAL_ANALYST"),
    ("FP&A Analyst", "FINANCIAL_ANALYST"),
    ("Financial Reporting Analyst", "FINANCIAL_ANALYST"),
    ("Financial Data Analyst", "DATA_ANALYST"),
    ("HR Executive", "HR_EXEC"),
    ("Human Resources Generalist", "HR_EXEC"),
    ("HR Coordinator", "HR_EXEC"),
    ("Recruiter", "HR_EXEC"),
    ("Technical Recruiter - Cloud", "HR_EXEC"),
    ("Talent Acquisition Specialist", "HR_EXEC"),
    ("HR Data Analyst", "DATA_ANALYST"),
    ("Marketing Executive", "MARKETING_EXEC"),
    ("Marketing Coordinator", "MARKETING_EXEC"),
    ("Digital Marketing Specialist", "MARKETING_EXEC"),
    ("Social Media Marketing Intern", "MARKETING_EXEC"),
    ("Marketing Data Analyst", "DATA_ANALYST"),
    ("Retail Sales Print & Marketing Associate", None),
    ("Salesforce Marketing Cloud Specialist", None),
    # Physical security is not cyber security
    ("Security Officer", None),
    ("Armed Security Officer", None),
    ("Security Guard - Mobile Patrol", None),
    ("Security Supervisor's: $26.00/hour", None),
    ("Information System Security Officer", "CYBER_ANALYST"),
    ("Information Systems Security Officer (ISSO)", "CYBER_ANALYST"),
    ("IT Security Specialist", "CYBER_ANALYST"),
    ("Security Analyst", "CYBER_ANALYST"),
    ("Security Engineer", "CYBER_ANALYST"),
    ("Junior SOC Analyst", "CYBER_ANALYST"),
    ("Associate Client Advisor - Cyber", None),
    ("FedRAMP Cloud Cybersecurity Analyst", "CYBER_ANALYST"),
    ("Jr. Python Developer for Cyber Program", "SOFTWARE_DEV"),
    ("Enterprise Cloud Sales Representative", None),
    ("Apprentice Terminal Operator 12-hr", None),
    ("Computer Numerical Control Programmer", None),
    # Clearance wording and pay rates do not decide the role
    ("Data Analyst Supporting the FBI with Security Clearance", "DATA_ANALYST"),
    ("Program Analyst with Security Clearance", None),
    ("Social Security Specialist", None),
    ("Housekeeper $15hr", None),
    # Retail "front end", towns and products named "cloud"
    ("Front End Developer", "WEB_DEV"),
    ("Retail Front End Supervisor", None),
    ("Front End Entry Level", None),
    ("Part Time Teller St Cloud South", None),
    ("Oracle Cloud SCM Consultant", None),
    ("HVAC Programmer", None),
    ("Online Data Analyst", None),
    ("Volunteer: Marketing Coordinator needed for Cyber Defense Center", None),
])
def test_tricky_titles(title, role):
    assert classify_role(title) == role


def test_seniority_level_column_refines_plain_titles_only():
    assert combine_seniority(classify_seniority("Financial Analyst"), "Entry level") == "entry"
    assert combine_seniority(classify_seniority("Business Analyst"), "Associate") == "junior"
    assert combine_seniority(classify_seniority("Business Analyst"), "Mid-Senior level") == "mid"
    assert combine_seniority(classify_seniority("Recruiter"), "Director") == "senior"
    assert combine_seniority(classify_seniority("Senior Recruiter"), "Entry level") == "senior"
    assert combine_seniority(classify_seniority("Marketing Intern"), "Mid-Senior level") == "entry"
    assert classify_seniority("Chief Information Security Officer") == "senior"


@pytest.mark.parametrize("location, region", [
    ("Petaling Jaya, Selangor", "Malaysia"),
    ("Remote (Malaysia)", "Malaysia"),
    ("Singapore", "other APAC"),
    ("Bengaluru, Karnataka, India", "other APAC"),
    ("Greater Palm Bay-Melbourne-Titusville Area", "other"),
    ("Sydney, NS", "other"),
    ("Remote", "remote"),
    ("New York, NY", "other"),
    ("", "other"),
])
def test_region_of(location, region):
    assert region_of(location) == region


def test_brand_words_mask_short_employer_names_only():
    assert brand_words("Apex Systems") == {"Apex"}
    assert brand_words("Example Health Consortium (EHC)") == {"Example", "Consortium", "EHC"}
    t = mask_words("Join Apex. Apex builds cloud data systems; apex of the market.", brand_words("Apex Systems"))
    assert t == "Join [COMPANY]. [COMPANY] builds cloud data systems; apex of the market."


def test_clean_text_masks_email_domains_and_handles():
    t = clean_text("Mail only comes from @acme.example addresses. Follow @AcmeCorp. "
                   "Apply at https //acme.example/jobs or x@acme.example@acme.example")
    assert "acme" not in t.lower() and "Acme" not in t
    assert "[EMAIL]" in t and "[URL]" in t


# ── ingest: sampling and stable jd_refs ─────────────────────────────────────
BODY = ("Responsibilities: build weekly SQL reports and Power BI dashboards for the operations team, "
        "clean data in Excel, explain trends to managers and document every data source. "
        "Requirements: degree in statistics or IT, good communication and teamwork. "
        "Nice to have: Python, Tableau and some experience with cloud data warehouses. ")


def kaggle_rows(n, title="Data Analyst", employer="Employer {i}", location="Austin, TX", tag="a"):
    return [{"title": title, "company_name": employer.format(i=i), "location": location,
             "description": f"{BODY} Posting {tag}-{i}.", "job_posting_url": f"https://jobs.example/{tag}/{i}"}
            for i in range(n)]


def write_kaggle(raw, name, rows):
    kdir = raw / "kaggle"
    kdir.mkdir(parents=True, exist_ok=True)
    with open(kdir / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    lic = kdir / "LICENSES.csv"
    new = not lic.exists()
    with open(lic, "a", newline="", encoding="utf-8") as f:
        if new:
            f.write("file,dataset,license,downloaded\n")
        f.write(f"{name},example/{Path(name).stem},CC BY-SA 4.0,2026-10-30\n")


def write_manual(raw, role, n):
    d = raw / "manual" / role
    d.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (d / f"{i}.txt").write_text(f"https://my.jobstreet.example/{role}/{i} 2026-10-12\nTitle: Junior Analyst\n"
                                    f"Location: Kuala Lumpur\n\n{BODY} Manual posting {i}.", encoding="utf-8")


def run(raw, out, **kw):
    rows, stats = ingest_jds.build(raw, out, **kw)
    write_csv(out, rows, DATASET_FIELDS)
    return rows, stats


def test_default_cap_tops_role_up_to_target_plus_margin(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "jd.csv"
    write_manual(raw, "DATA_ANALYST", 2)
    write_kaggle(raw, "big.csv", kaggle_rows(60))
    rows, _ = run(raw, out)
    da = [r for r in rows if r["role_code"] == "DATA_ANALYST"]
    assert sum(r["source"] == "manual" for r in da) == 2
    assert sum(r["source"].startswith("kaggle:") for r in da) == 30 - 2 + ingest_jds.CAP_MARGIN
    assert all(r["source_license"] == "CC BY-SA 4.0" for r in da if r["source"].startswith("kaggle:"))
    assert {r["company"] for r in rows} == {"Anonymised"}


def test_cap_employer_cap_and_draw_order(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "jd.csv"
    rows_in = (kaggle_rows(10, employer="Bigco Sdn Bhd", tag="big")
               + kaggle_rows(4, title="Junior Data Analyst", tag="jr")
               + kaggle_rows(3, title="Data Analyst", location="Kuala Lumpur, Malaysia", tag="my")
               + kaggle_rows(20, tag="us"))
    write_kaggle(raw, "big.csv", rows_in)
    rows, stats = run(raw, out, cap=8, employer_cap=2)
    assert len(rows) == 8
    titles = [r["title"] for r in rows]
    assert titles.count("Junior Data Analyst") == 4              # entry / junior first
    assert sum(r["region"] == "Malaysia" for r in rows) == 3     # then Malaysia
    assert sum("Posting big-" in r["raw_text"] for r in rows) <= 2
    assert all("Bigco" not in r["raw_text"] for r in rows)


def test_rerun_is_identical_and_new_file_does_not_renumber(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "jd.csv"
    write_manual(raw, "DATA_ANALYST", 3)
    write_manual(raw, "WEB_DEV", 2)
    write_kaggle(raw, "a.csv", kaggle_rows(15, tag="a") + kaggle_rows(5, title="Web Developer", tag="aw"))
    run(raw, out, cap=6)
    first = out.read_bytes()
    run(raw, out, cap=6)
    assert out.read_bytes() == first

    old = {r["jd_ref"]: r for r in read_dataset(out)}
    write_kaggle(raw, "b.csv", kaggle_rows(15, tag="b") + kaggle_rows(4, title="Recruiter", tag="bh"))
    rows, _ = run(raw, out, cap=6)
    new = {r["jd_ref"]: r for r in rows}
    assert all(new[ref] == row for ref, row in old.items())
    added = set(new) - set(old)
    assert added and all(new[ref]["source"] == "kaggle:example/b" for ref in added)
    for role in ("DATA_ANALYST", "HR_EXEC"):
        old_max = max((int(k[-4:]) for k, r in old.items() if r["role_code"] == role), default=0)
        assert all(int(k[-4:]) > old_max for k in added if new[k]["role_code"] == role)

    # Old JDs stay even when their raw files are gone.
    for p in (raw / "manual" / "WEB_DEV").glob("*.txt"):
        p.unlink()
    rows, _ = run(raw, out, cap=6)
    assert {r["jd_ref"] for r in rows} == set(new)
