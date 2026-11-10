"""
Check the learning-resource links in the seed files.

Collects every URL in database/seed_recommendations_library_final.sql and
database/seed_business_skills.sql, requests each one once and sorts the answers:

    dead            404 or 410: the page is gone, students reach a dead page
    check_by_hand   the site answers 200 but the page says it was not found, or a
                    deep link was redirected to the site's home page
    blocked         401, 403, 429, 5xx or another unexpected status: the site refuses
                    automated clients or had a problem, so the link is not confirmed
    no_response     a network error (timeout, DNS, TLS, connection refused)
    ok              2xx

Run it before each demo (standard library only, writes nothing by default):

    python data/check_resource_links.py
    python data/check_resource_links.py --csv data/output/resource_links.csv
    python data/check_resource_links.py --show-blocked

Exits with 1 if any link is dead, otherwise 0.

To be polite to the sites, each URL is requested once, with a timeout, an honest
User-Agent and a few workers; the URLs of one host are requested one after the other.
Nothing tries to get around a block or a login.
"""

import argparse
import csv
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SEED_FILES = [ROOT / "database" / "seed_recommendations_library_final.sql",
              ROOT / "database" / "seed_business_skills.sql"]

USER_AGENT = "SEAGAS-resource-link-check/1.0 (COS40005 student project; checks course links once before a demo)"
TIMEOUT = 20          # seconds per request
WORKERS = 6           # hosts checked at the same time
BODY_BYTES = 200_000  # enough of a page to read its <title> and first <h1>

CLASSES = ["dead", "check_by_hand", "blocked", "no_response", "ok"]

# One seed row: ('Skill', 'Title', 'type', 'provider', 'https://...', hours, 'cost', 'level', 'description'),
SQL_STRING = re.compile(r"'((?:[^']|'')*)'")
NOT_FOUND = re.compile(
    r"\b404\b|page not found|not found|page (?:does not|doesn't|no longer) exist|"
    r"no longer available|cannot be found|can't be found|could not be found|couldn't find|can't find",
    re.IGNORECASE)


# ── Collecting the URLs ──────────────────────────────────────

def parse_seed_rows(text, file_label=""):
    """The resource rows of a seed file: skill, title and url of each VALUES tuple with a URL"""
    rows = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("('"):
            continue
        values = [v.replace("''", "'") for v in SQL_STRING.findall(line)]
        url = next((v for v in values if v.startswith(("http://", "https://"))), None)
        if url is None or len(values) < 2:
            continue
        rows.append({"file": file_label, "line": line_no, "skill": values[0], "title": values[1], "url": url})
    return rows


def collect_rows(paths=SEED_FILES):
    rows = []
    for p in paths:
        rows += parse_seed_rows(Path(p).read_text(encoding="utf-8"), Path(p).name)
    return rows


# ── Classifying an answer (no network) ───────────────────────

def _page_heading(body):
    """The <title> and first <h1> of an HTML page, as plain text"""
    found = []
    for tag in ("title", "h1"):
        m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", body or "", re.IGNORECASE | re.DOTALL)
        if m:
            found.append(re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip())
    return " | ".join(found)


def _redirected_home(url, final_url):
    """A deep link that ended on the site's home page usually means the page was removed"""
    if not url or not final_url or url == final_url:
        return False
    return urlsplit(url).path.strip("/") != "" and urlsplit(final_url).path.strip("/") == ""


def classify(status=None, body="", error=None, url=None, final_url=None):
    """(class, reason) for one answer. status: the HTTP status, or None with error set
    when no answer came back. body: the start of the page for a 2xx answer."""
    if status is None:
        return "no_response", str(error or "no response")
    if status in (404, 410):
        return "dead", f"HTTP {status}"
    if 200 <= status < 300:
        heading = _page_heading(body)
        if heading and NOT_FOUND.search(heading):
            return "check_by_hand", f"HTTP {status} but the page says: {heading[:80]}"
        if _redirected_home(url, final_url):
            return "check_by_hand", f"HTTP {status} after a redirect to the home page {final_url}"
        return "ok", f"HTTP {status}"
    if status in (401, 403, 429) or status >= 500:
        return "blocked", f"HTTP {status}"
    return "blocked", f"HTTP {status} (unexpected)"


# ── Requesting ───────────────────────────────────────────────

def fetch(url, timeout=TIMEOUT):
    """One GET request: (status, body_start, error, final_url)"""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(BODY_BYTES)
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.status, raw.decode(charset, errors="replace"), None, resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, "", None, url
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, ConnectionError, OSError) as e:
        return None, "", getattr(e, "reason", e), url


def check_urls(urls, workers=WORKERS, fetcher=fetch):
    """{url: (class, reason)}. URLs of one host are fetched one after the other."""
    by_host = defaultdict(list)
    for u in urls:
        by_host[urlsplit(u).hostname or ""].append(u)

    def run_host(host_urls):
        out = {}
        for u in host_urls:
            status, body, error, final_url = fetcher(u)
            out[u] = classify(status, body, error, u, final_url)
        return out

    results = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(run_host, by_host.values()):
            results.update(part)
    return results


# ── Report ───────────────────────────────────────────────────

def host_of(url):
    host = urlsplit(url).hostname or ""
    return host[4:] if host.startswith("www.") else host


def print_report(rows, results, show_blocked=False):
    rows_by_url = defaultdict(list)
    for r in rows:
        rows_by_url[r["url"]].append(r)
    count = Counter(cls for cls, _ in results.values())

    print(f"Checked {len(results)} distinct URLs used by {len(rows)} resource rows.\n")
    print("By class:")
    for cls in CLASSES:
        n_rows = sum(len(rows_by_url[u]) for u, (c, _) in results.items() if c == cls)
        print(f"  {cls:<14} {count.get(cls, 0):>4} URLs  ({n_rows} rows)")

    per_host = defaultdict(Counter)
    for u, (cls, _) in results.items():
        per_host[host_of(u)][cls] += 1
    print("\nBy host (hosts with anything other than ok):")
    print(f"  {'host':<34}" + "".join(f"{c:>15}" for c in CLASSES))
    for host in sorted(per_host, key=lambda h: (-sum(per_host[h].values()), h)):
        if set(per_host[host]) <= {"ok"}:
            continue
        print(f"  {host:<34}" + "".join(f"{per_host[host].get(c, 0):>15}" for c in CLASSES))

    def listing(cls, title):
        urls = sorted(u for u, (c, _) in results.items() if c == cls)
        if not urls:
            return
        print(f"\n{title} ({len(urls)}):")
        for u in urls:
            print(f"  {u}  [{results[u][1]}]")
            for r in rows_by_url[u]:
                print(f"      {r['skill']} -- {r['title']}  ({r['file']}:{r['line']})")

    listing("dead", "Dead links")
    listing("check_by_hand", "Check by hand")
    listing("no_response", "No response")
    if show_blocked:
        print("\nBlocked or unknown, by host:")
        blocked = defaultdict(list)
        for u, (c, reason) in results.items():
            if c == "blocked":
                blocked[host_of(u)].append((u, reason))
        for host in sorted(blocked):
            print(f"  {host} ({len(blocked[host])})")
            for u, reason in sorted(blocked[host]):
                print(f"      {u}  [{reason}]")


def write_csv(path, rows, results):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class", "reason", "host", "url", "skill", "title", "file", "line"])
        for r in sorted(rows, key=lambda r: (CLASSES.index(results[r["url"]][0]), r["url"], r["skill"])):
            cls, reason = results[r["url"]]
            w.writerow([cls, reason, host_of(r["url"]), r["url"], r["skill"], r["title"], r["file"], r["line"]])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check the learning-resource links in the seed files.")
    ap.add_argument("--csv", help="also write every row and its result to this CSV file")
    ap.add_argument("--show-blocked", action="store_true", help="list the blocked URLs by host")
    ap.add_argument("--workers", type=int, default=WORKERS, help=f"hosts checked at once (default {WORKERS})")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    rows = collect_rows()
    urls = sorted({r["url"] for r in rows})
    results = check_urls(urls, workers=max(1, min(args.workers, 10)))
    print_report(rows, results, args.show_blocked)
    if args.csv:
        write_csv(args.csv, rows, results)
        print(f"\nWrote {args.csv}")
    return 1 if any(c == "dead" for c, _ in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
