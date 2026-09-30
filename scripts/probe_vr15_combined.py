"""
VR15 Combined Probe — Parts A, B, C
====================================
Part A: Corporations Canada API (VR15.2.2)
  - Correct base: https://apigateway-passerelledapi.ised-isde.canada.ca/corporations/api
  - Corporation lookup: /v1/corporations/{id}.json?lang=eng
  - Directors:          /v2/corporations/{number}/directors
  - Auth:               user-key header

Part B: Website/Business Directory Discovery (VR15.3)
  - YellowPages.ca HTML probe (unauthenticated, check access + ToS signal)
  - Canada411.ca HTML probe (unauthenticated, check access + ToS signal)
  - OpenStreetMap Overpass API (no auth, open licence)

Part C: Website Enrichment (VR15.4)
  - Known-domain businesses from VR06 + VR15.1 sample
  - Extract: phone, email, JSON-LD, mailto:, tel:, decision-maker name+title
  - robots.txt compliance check on each domain

Output:
  reports/validation_rounds/VR15_COMBINED.json
  reports/validation_rounds/VR15_COMBINED.md  (written after run — paste output to Kiro)

Usage:
  python scripts/probe_vr15_combined.py
"""

import json
import re
import time
import urllib.request
import urllib.error
import urllib.robotparser
import urllib.parse
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("ISED_API_KEY", "490fff09becefbe9245841cb84073be8")

CORPS_API_BASE = "https://apigateway-passerelledapi.ised-isde.canada.ca/corporations/api"

# Corp numbers from CBCA CSV (VR01) — not manually assembled
CORP_NUMBERS = [
    "8660115",   # MINDANGLER CAPITAL INC. (ON)
    "821080",    # AIRMEC CLIMATISATION LTEE (QC)
    "4396626",   # AIR CANADA (QC)
    "158072",    # CANADIAN TIRE CORPORATION LIMITED (ON)
    "271517",    # ROGERS COMMUNICATIONS INC. (ON)
]

# Part B — directory sources to probe
DIRECTORY_SOURCES = [
    {
        "name": "YellowPages.ca",
        "test_url": "https://www.yellowpages.ca/search/si/1/Plumber/Toronto+ON",
        "robots_url": "https://www.yellowpages.ca/robots.txt",
        "notes": "HTML search results page — check status, content type, link count, ToS signal",
    },
    {
        "name": "Canada411.ca",
        "test_url": "https://www.canada411.ca/search/reverse/1/4162481229/",
        "robots_url": "https://www.canada411.ca/robots.txt",
        "notes": "Reverse phone lookup — check status, content type, data presence",
    },
    {
        "name": "OpenStreetMap Overpass API",
        "test_url": (
            "https://overpass-api.de/api/interpreter"
            "?data=[out:json];node[%22shop%22](43.6,-79.5,43.7,-79.3);out+10;"
        ),
        "robots_url": None,
        "notes": "OSM business nodes in Toronto bbox — open licence (ODbL), no auth",
    },
]

# Part C — known-domain businesses (from VR06 + VR15.1 confirmed live)
ENRICHMENT_BUSINESSES = [
    {"id": "T04", "name": "RepologiX",              "domain": "https://www.repologix.com"},
    {"id": "C01", "name": "Mindangler Capital Inc.", "domain": "https://www.mindangler.com"},
    {"id": "C02", "name": "Sleep Country Canada",    "domain": "https://www.sleepcountry.ca"},
    {"id": "C03", "name": "Boston Pizza",            "domain": "https://www.bostonpizza.com"},
    {"id": "C04", "name": "MEC",                     "domain": "https://www.mec.ca"},
]

CRAWL_PATHS = ["/", "/contact", "/contact-us", "/about", "/about-us", "/team", "/leadership"]

THROTTLE = 1.2   # seconds between requests
OUTPUT_JSON = "reports/validation_rounds/VR15_COMBINED.json"

# ---------------------------------------------------------------------------
# Shared HTTP helper
# ---------------------------------------------------------------------------

def fetch(url, extra_headers=None, timeout=15):
    """GET url, return (status, content_type, body_text, error)."""
    headers = {
        "User-Agent": "Canada-Biz-Pipeline-Research/1.0 (VR15-combined; non-commercial)",
        "Accept": "text/html,application/json,*/*",
    }
    if extra_headers:
        headers.update(extra_headers)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            ct = r.headers.get("Content-Type", "")
            text = raw.decode("utf-8", errors="replace")
            return r.status, ct, text, None
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:800]
        except Exception:
            pass
        return e.code, "", body, f"HTTPError {e.code}: {e.reason}"
    except Exception as e:
        return None, "", "", str(e)


def json_keys(text):
    try:
        p = json.loads(text)
        if isinstance(p, dict):
            return list(p.keys())
        if isinstance(p, list):
            info = [f"array len={len(p)}"]
            if p and isinstance(p[0], dict):
                info.append(f"item_keys={list(p[0].keys())}")
            return info
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Part A — Corporations Canada API
# ---------------------------------------------------------------------------

def part_a():
    print("\n=== PART A: Corporations Canada API ===")
    results = []
    req_count = 0

    endpoints = [
        ("corporation_lookup", "/v1/corporations/{n}.json?lang=eng"),
        ("directors",          "/v2/corporations/{n}/directors"),
    ]

    for corp_num in CORP_NUMBERS:
        print(f"\n  Corp {corp_num}")
        corp_result = {"corp_num": corp_num, "endpoints": []}

        for label, path_tpl in endpoints:
            path = path_tpl.replace("{n}", corp_num)
            url = CORPS_API_BASE.rstrip("/") + path
            print(f"    [{label}] {url}")

            if req_count > 0:
                time.sleep(THROTTLE)

            status, ct, body, err = fetch(url, extra_headers={"user-key": API_KEY})
            req_count += 1

            keys = json_keys(body) if not err else None
            sample = body[:500] if body else ""
            print(f"      → {status}  ct={ct[:40]}  keys={keys}  err={err}")
            if sample:
                print(f"      sample: {sample[:200]}")

            corp_result["endpoints"].append({
                "endpoint": label, "url": url,
                "status": status, "content_type": ct,
                "json_keys": keys, "body_sample": sample,
                "error": err,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        results.append(corp_result)

    return results


# ---------------------------------------------------------------------------
# Part B — Directory / open-data source discovery
# ---------------------------------------------------------------------------

def part_b():
    print("\n=== PART B: Website/Business Directory Discovery ===")
    results = []

    for src in DIRECTORY_SOURCES:
        print(f"\n  {src['name']}")
        result = {"source": src["name"], "notes": src["notes"]}

        # robots.txt
        robots_allowed = None
        if src["robots_url"]:
            time.sleep(THROTTLE)
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(src["robots_url"])
            try:
                rp.read()
                robots_allowed = rp.can_fetch(
                    "Canada-Biz-Pipeline-Research", src["test_url"]
                )
                print(f"    robots.txt: crawl allowed = {robots_allowed}")
            except Exception as e:
                print(f"    robots.txt: error — {e}")
                robots_allowed = None
        result["robots_allowed"] = robots_allowed

        # test request
        time.sleep(THROTTLE)
        status, ct, body, err = fetch(src["test_url"])
        print(f"    test GET → {status}  ct={ct[:50]}  err={err}")

        # rough signal counts
        link_count = len(re.findall(r'href=["\']https?://', body))
        phone_count = len(re.findall(
            r'(\+?1[\s\-.]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4})', body
        ))
        email_count = len(re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', body))
        tos_signal = any(w in body.lower() for w in [
            "terms of use", "terms of service", "prohibited", "scraping",
            "automated", "commercial use", "redistribution"
        ])
        print(f"    links={link_count}  phones={phone_count}  emails={email_count}  ToS-signal={tos_signal}")

        # sample of body for ToS text
        tos_excerpt = ""
        for phrase in ["terms of use", "terms of service", "prohibited", "automated"]:
            idx = body.lower().find(phrase)
            if idx >= 0:
                tos_excerpt = body[max(0, idx-30):idx+120].strip()
                break

        result.update({
            "test_url": src["test_url"],
            "status": status, "content_type": ct,
            "body_bytes": len(body),
            "link_count": link_count,
            "phone_count": phone_count,
            "email_count": email_count,
            "tos_signal_present": tos_signal,
            "tos_excerpt": tos_excerpt[:300],
            "error": err,
            "body_sample": body[:800],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Part C — Website enrichment on known domains
# ---------------------------------------------------------------------------

PHONE_RE = re.compile(
    r'(?:tel:|(\+?1[\s\-.]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}))'
)
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
# JSON-LD telephone/email
JSONLD_RE = re.compile(r'"(?:telephone|email)"\s*:\s*"([^"]+)"')
# tel: href
TEL_HREF_RE = re.compile(r'tel:([\d\s\+\-\(\)\.]+)')
# mailto:
MAILTO_RE = re.compile(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})')
# Simple name+title heuristic: "FirstName LastName, Title" or "Title: FirstName LastName"
PERSON_RE = re.compile(
    r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)'
    r'[\s,\|–\-]+(?:CEO|President|Director|VP|Owner|Founder|Manager|Partner)',
    re.MULTILINE
)


def extract_signals(body, url):
    phones = list({m for m in TEL_HREF_RE.findall(body)})
    phones += [m for m in PHONE_RE.findall(body) if m and m not in phones]
    emails = list({m for m in MAILTO_RE.findall(body)})
    emails += [m for m in EMAIL_RE.findall(body)
               if m not in emails and "example" not in m and len(m) < 60]
    jsonld_vals = JSONLD_RE.findall(body)
    persons = PERSON_RE.findall(body)
    return {
        "phones": phones[:5],
        "emails": emails[:5],
        "jsonld_contact_fields": jsonld_vals[:5],
        "persons_detected": persons[:5],
        "source_url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


def check_robots(domain, path):
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(domain.rstrip("/") + "/robots.txt")
    try:
        rp.read()
        return rp.can_fetch("Canada-Biz-Pipeline-Research", domain + path)
    except Exception:
        return True  # assume allowed if robots.txt unreachable


def part_c():
    print("\n=== PART C: Website Enrichment ===")
    results = []

    for biz in ENRICHMENT_BUSINESSES:
        print(f"\n  {biz['id']} — {biz['name']} ({biz['domain']})")
        biz_result = {
            "id": biz["id"], "name": biz["name"],
            "domain": biz["domain"], "pages": [],
        }
        all_phones, all_emails, all_jsonld, all_persons = [], [], [], []

        for path in CRAWL_PATHS:
            url = biz["domain"].rstrip("/") + path
            time.sleep(THROTTLE)

            allowed = check_robots(biz["domain"], path)
            if not allowed:
                print(f"    {path} — robots.txt disallowed, skipping")
                biz_result["pages"].append({"path": path, "skipped": "robots_disallowed"})
                continue

            status, ct, body, err = fetch(url)
            print(f"    {path} → {status}  err={err}")

            if status == 200 and body:
                sig = extract_signals(body, url)
                all_phones  += sig["phones"]
                all_emails  += sig["emails"]
                all_jsonld  += sig["jsonld_contact_fields"]
                all_persons += sig["persons_detected"]
                biz_result["pages"].append({
                    "path": path, "status": status,
                    "phones": sig["phones"], "emails": sig["emails"],
                    "jsonld": sig["jsonld_contact_fields"],
                    "persons": sig["persons_detected"],
                    "source_url": url,
                    "retrieved_at": sig["retrieved_at"],
                })
                if sig["phones"] or sig["emails"] or sig["persons_detected"]:
                    print(f"      phones={sig['phones']}  emails={sig['emails']}  persons={sig['persons_detected']}")
            else:
                biz_result["pages"].append({"path": path, "status": status, "error": err})

        # deduplicate
        biz_result["summary"] = {
            "phones_unique":  list(dict.fromkeys(all_phones))[:5],
            "emails_unique":  list(dict.fromkeys(all_emails))[:5],
            "jsonld_unique":  list(dict.fromkeys(all_jsonld))[:5],
            "persons_unique": list(dict.fromkeys(all_persons))[:5],
        }
        print(f"  Summary: phones={biz_result['summary']['phones_unique']} "
              f"emails={biz_result['summary']['emails_unique']} "
              f"persons={biz_result['summary']['persons_unique']}")
        results.append(biz_result)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    print("VR15 Combined Probe — Parts A, B, C")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")

    part_a_results = part_a()
    part_b_results = part_b()
    part_c_results = part_c()

    # Status summary
    print("\n=== STATUS SUMMARY ===")

    a_statuses = {}
    for c in part_a_results:
        for ep in c["endpoints"]:
            s = str(ep["status"]) if ep["status"] else "ERR"
            a_statuses[s] = a_statuses.get(s, 0) + 1
    print(f"Part A (API): {a_statuses}")

    b_statuses = {s["source"]: s["status"] for s in part_b_results}
    print(f"Part B (directories): {b_statuses}")

    c_summary = {
        b["name"]: {
            "phones": len(b["summary"]["phones_unique"]),
            "emails": len(b["summary"]["emails_unique"]),
            "persons": len(b["summary"]["persons_unique"]),
        }
        for b in part_c_results
    }
    print(f"Part C (enrichment): {json.dumps(c_summary, indent=2)}")

    output = {
        "vr": "VR15_COMBINED",
        "generated": datetime.now(timezone.utc).isoformat(),
        "part_a_corps_api": part_a_results,
        "part_b_directory_discovery": part_b_results,
        "part_c_website_enrichment": part_c_results,
        "status_summary": {
            "part_a": a_statuses,
            "part_b": b_statuses,
            "part_c": c_summary,
        },
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nOutput written: {OUTPUT_JSON}")
    print("Paste terminal output to Kiro.")


if __name__ == "__main__":
    run()
