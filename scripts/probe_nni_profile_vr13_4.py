"""
VR13.1 (v4) — NNI Business Profile Page + Regulations/Terms scrape
Goals:
1. Fetch /business/profile/2367 (237 TOV Construction) — confirm all public fields
2. Fetch a second profile to confirm field consistency
3. Fetch the NNI Regulations PDF URL and attempt to retrieve it for reuse terms review
4. Fetch /regmain (Register Your Business) — may contain terms on data use

Run: python scripts/probe_nni_profile_vr13_4.py
Output: reports/validation_rounds/VR13_1_NNI_PROFILE_2367.html
        reports/validation_rounds/VR13_1_NNI_V4.json
"""

import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

BASE = "https://nni.gov.nu.ca"
OUTPUT_JSON  = "reports/validation_rounds/VR13_1_NNI_V4.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
    "Referer": "https://nni.gov.nu.ca/business/list",
}

RESULTS = {}


def fetch(path, label=""):
    url = BASE + path if not path.startswith("http") else path
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", errors="replace")
            print(f"  {label or path} → {r.status} ({len(body)}b)")
            return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  {label or path} → {e.code} ({len(body)}b)")
        return e.code, body
    except Exception as ex:
        print(f"  {label or path} → ERROR: {ex}")
        return 0, str(ex)


def fetch_binary(url, label=""):
    """Fetch binary (PDF). Return (status, bytes_len, first_200_chars_decoded)."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
            sample = body[:200].decode("latin-1", errors="replace")
            print(f"  {label} → {r.status} ({len(body)}b)")
            return r.status, len(body), sample
    except urllib.error.HTTPError as e:
        print(f"  {label} → {e.code}")
        return e.code, 0, ""
    except Exception as ex:
        print(f"  {label} → ERROR: {ex}")
        return 0, 0, str(ex)


def extract_profile_fields(html):
    """
    Parse a business profile page. NNI uses Drupal field--name-* classes.
    Returns dict of field_name -> value.
    """
    fields = {}

    # Strategy 1: field--name-* divs (Drupal standard)
    for m in re.finditer(
            r'<div[^>]+class="[^"]*field--name-([\w-]+)[^"]*"[^>]*>'
            r'.*?<div[^>]+class="[^"]*field__item[^"]*"[^>]*>(.*?)</div>',
            html, re.I | re.DOTALL):
        fname = m.group(1).replace("-", "_")
        val = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if val:
            fields[fname] = val

    # Strategy 2: label/value pairs in a definition list or table
    for m in re.finditer(
            r'<(?:dt|th)[^>]*>\s*([^<]{2,50}?)\s*</(?:dt|th)>\s*'
            r'<(?:dd|td)[^>]*>(.*?)</(?:dd|td)>',
            html, re.I | re.DOTALL):
        label = re.sub(r'<[^>]+>', '', m.group(1)).strip().rstrip(':')
        val   = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if label and val:
            fields[f"label__{label}"] = val

    # Strategy 3: scan for specific known NNI field keywords in surrounding text
    keywords = {
        "phone": r'(?:phone|telephone)[^\n<]{0,10}[:\s]+([+\d\s\(\)\-\.]{7,20})',
        "email": r'(?:e-?mail)[^\n<]{0,10}[:\s]+([\w._%+\-]+@[\w.\-]+\.[a-z]{2,})',
        "employees": r'(?:employee|# of employee)[^\n<]{0,20}[:\s]+(\d+)',
        "status": r'(?:business status|status)[^\n<]{0,10}[:\s]+([A-Za-z ]{3,20})',
        "effective_date": r'(?:effective date)[^\n<]{0,10}[:\s]+(\d{4}-\d{2}-\d{2})',
        "postal_code": r'([A-Z]\d[A-Z]\s?\d[A-Z]\d)',
        "nti_cert": r'(?:NTI|certificate)[^\n<]{0,20}[:\s]+([A-Z0-9\-]{4,20})',
    }
    for key, pattern in keywords.items():
        m = re.search(pattern, html, re.I)
        if m and f"kw__{key}" not in fields:
            fields[f"kw__{key}"] = m.group(1).strip()

    return fields


def extract_main_content(html):
    """Extract the main content area of a Drupal page."""
    m = re.search(r'<main[^>]*>(.*?)</main>', html, re.I | re.DOTALL)
    if m:
        return re.sub(r'<[^>]+>', ' ', m.group(1))
    return re.sub(r'<[^>]+>', ' ', html)


# ---------------------------------------------------------------------------
# 1. Profile page — /business/profile/2367
# ---------------------------------------------------------------------------
print("\n[1] Fetching /business/profile/2367 (237 TOV Construction & Supply Ltd.) ...")
s, body = fetch("/business/profile/2367", "profile/2367")
RESULTS["profile_2367"] = {
    "status": s,
    "bytes": len(body),
    "fields": extract_profile_fields(body),
    "main_text": extract_main_content(body)[:3000],
}
with open("reports/validation_rounds/VR13_1_NNI_PROFILE_2367.html", "w", encoding="utf-8") as f:
    f.write(body)
print(f"  Fields extracted: {list(RESULTS['profile_2367']['fields'].keys())}")
print(f"  Main text snippet:\n{RESULTS['profile_2367']['main_text'][:600]}")
time.sleep(1)

# ---------------------------------------------------------------------------
# 2. Second profile — /business/profile/2210 (Beland, Patrick — 2026-09-21 date)
# ---------------------------------------------------------------------------
print("\n[2] Fetching /business/profile/2210 (second profile for consistency check) ...")
s, body2 = fetch("/business/profile/2210", "profile/2210")
RESULTS["profile_2210"] = {
    "status": s,
    "bytes": len(body2),
    "fields": extract_profile_fields(body2),
    "main_text": extract_main_content(body2)[:3000],
}
with open("reports/validation_rounds/VR13_1_NNI_PROFILE_2210.html", "w", encoding="utf-8") as f:
    f.write(body2)
print(f"  Fields extracted: {list(RESULTS['profile_2210']['fields'].keys())}")
print(f"  Main text snippet:\n{RESULTS['profile_2210']['main_text'][:600]}")
time.sleep(1)

# ---------------------------------------------------------------------------
# 3. Register Your Business page — may contain data use terms
# ---------------------------------------------------------------------------
print("\n[3] Fetching /regmain (Register Your Business) ...")
s, body3 = fetch("/regmain", "regmain")
RESULTS["regmain"] = {
    "status": s,
    "bytes": len(body3),
    "main_text": extract_main_content(body3)[:4000],
}
print(f"  Main text:\n{RESULTS['regmain']['main_text'][:800]}")
time.sleep(0.5)

# ---------------------------------------------------------------------------
# 4. NNI Regulations PDF — check if retrievable and check first bytes for text
# ---------------------------------------------------------------------------
print("\n[4] Attempting to fetch NNI Regulations PDF ...")
pdf_url = "https://nni.gov.nu.ca/sites/nni.gov.nu.ca/files/NNI-Regs-amendment_2.pdf"
ps, plen, psample = fetch_binary(pdf_url, "NNI-Regs-amendment_2.pdf")
RESULTS["regulations_pdf"] = {
    "url": pdf_url,
    "status": ps,
    "bytes": plen,
    "is_pdf": psample.startswith("%PDF"),
    "sample": psample[:200],
}
print(f"  is_pdf={RESULTS['regulations_pdf']['is_pdf']} size={plen}b")

# Also try the older policy PDF
pdf_url2 = "https://nni.gov.nu.ca/files/01nniPolicyEng.pdf"
ps2, plen2, psample2 = fetch_binary(pdf_url2, "01nniPolicyEng.pdf")
RESULTS["policy_pdf"] = {
    "url": pdf_url2,
    "status": ps2,
    "bytes": plen2,
    "is_pdf": psample2.startswith("%PDF"),
}
print(f"  older policy: status={ps2} is_pdf={RESULTS['policy_pdf']['is_pdf']} size={plen2}b")
time.sleep(0.5)

# ---------------------------------------------------------------------------
# 5. Contact page — may show official contact for reuse inquiries
# ---------------------------------------------------------------------------
print("\n[5] Fetching /contact ...")
s, body5 = fetch("/contact", "contact")
RESULTS["contact"] = {
    "status": s,
    "bytes": len(body5),
    "main_text": extract_main_content(body5)[:2000],
}
print(f"  Contact info:\n{RESULTS['contact']['main_text'][:500]}")

# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------
RESULTS["generated"] = datetime.now(timezone.utc).isoformat()
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, indent=2, ensure_ascii=False)
print(f"\nJSON saved → {OUTPUT_JSON}")
print("\n=== PROFILE FIELD COMPARISON ===")
print("Profile 2367 fields:", sorted(RESULTS["profile_2367"]["fields"].keys()))
print("Profile 2210 fields:", sorted(RESULTS["profile_2210"]["fields"].keys()))
print("\nDone.")
