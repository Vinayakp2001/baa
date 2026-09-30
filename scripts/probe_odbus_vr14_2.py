"""
VR14.2 — ODBus Endpoint Triage
HEAD (then GET fallback) each of 69 ODBus source URLs.
Captures: http_status, final_url, content_type, response_size, redirect_chain,
page_title, bot/WAF indicators, current-date evidence, licence link.
Classifies each as: CURRENT / MOVED / DEAD / RESTRICTED / UNKNOWN
Output: reports/validation_rounds/VR14_2_ODBUS_ENDPOINT_TRIAGE.json
        reports/validation_rounds/VR14_2_ODBUS_ENDPOINT_TRIAGE.md
"""

import zipfile
import csv
import json
import io
import urllib.request
import urllib.error
import urllib.parse
import ssl
import re
import time

ZIP_PATH = "data/raw/ODBus_2023.zip"
SOURCES_FILE = "ODBus_v1/ODBus_Sources.csv"
OUTPUT_JSON = "reports/validation_rounds/VR14_2_ODBUS_ENDPOINT_TRIAGE.json"
OUTPUT_MD   = "reports/validation_rounds/VR14_2_ODBUS_ENDPOINT_TRIAGE.md"

# Priority order from GPT brief — checked first, printed first
PRIORITY_SOURCE_IDS = [19, 32, 30, 31, 66, 2, 4, 33, 28, 29]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
}

# SSL context that tolerates self-signed / legacy certs
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

BOT_WAF_SIGNALS = [
    "just a moment", "cloudflare", "checking your browser", "ddos-guard",
    "attention required", "enable javascript", "access denied", "403 forbidden",
    "bot protection", "security check"
]

LOGIN_SIGNALS = [
    "sign in", "log in", "login", "please login", "authentication required",
    "you must be logged", "register to", "create an account"
]

STALE_SIGNALS = [
    "page not found", "404", "this page does not exist", "no longer available",
    "has been archived", "has moved", "this dataset has been removed",
    "this resource is no longer"
]

CURRENT_DATE_SIGNALS = ["2024", "2025", "2026"]


def load_sources():
    with zipfile.ZipFile(ZIP_PATH) as z:
        with z.open(SOURCES_FILE) as f:
            raw = f.read().decode("cp1252")
    reader = csv.DictReader(io.StringIO(raw))
    rows = []
    for i, row in enumerate(reader, 1):
        cleaned = {k.strip(): v.strip() for k, v in row.items() if k.strip()}
        cleaned["_source_id"] = i
        rows.append(cleaned)
    return rows


def probe_url(url, source_id):
    """Try HEAD first, fall back to GET if HEAD fails or returns ambiguous result."""
    result = {
        "source_id": source_id,
        "original_url": url,
        "http_status": None,
        "final_url": url,
        "content_type": None,
        "response_size_bytes": None,
        "redirect_chain": [],
        "page_title": None,
        "bot_waf_detected": False,
        "login_required": False,
        "current_date_evidence": False,
        "licence_link_present": False,
        "cert_ok": True,
        "error": None,
        "method_used": None,
        "body_snippet": None,
    }

    if not url or url == "?":
        result["error"] = "no url"
        result["http_status"] = 0
        return result

    # --- HEAD attempt ---
    head_status = None
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            head_status = resp.status
            result["http_status"] = resp.status
            result["final_url"] = resp.url
            result["content_type"] = resp.headers.get("Content-Type", "")
            cl = resp.headers.get("Content-Length")
            result["response_size_bytes"] = int(cl) if cl else None
            result["method_used"] = "HEAD"
    except urllib.error.HTTPError as e:
        head_status = e.code
        result["http_status"] = e.code
        result["method_used"] = "HEAD"
    except ssl.SSLError:
        result["cert_ok"] = False
        head_status = None
    except Exception as e:
        head_status = None
        result["error"] = str(e)[:120]

    # Fall back to GET if HEAD gave 405 / 0 / SSL error / connection error
    needs_get = (
        head_status is None or
        head_status == 405 or
        head_status == 0 or
        not result["cert_ok"]
    )

    if needs_get:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
                result["http_status"] = resp.status
                result["final_url"] = resp.url
                result["content_type"] = resp.headers.get("Content-Type", "")
                body_bytes = resp.read(8192)  # first 8KB only
                result["response_size_bytes"] = len(body_bytes)
                result["method_used"] = "GET"
                result["error"] = None
                result["cert_ok"] = True

                # Decode body for signal detection
                try:
                    body = body_bytes.decode("utf-8", errors="replace")
                except Exception:
                    body = ""
                result["body_snippet"] = body[:300].replace("\n", " ")

                body_lower = body.lower()
                # Page title
                m = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
                if m:
                    result["page_title"] = m.group(1).strip()[:120]

                # Signals
                result["bot_waf_detected"] = any(s in body_lower for s in BOT_WAF_SIGNALS)
                result["login_required"] = any(s in body_lower for s in LOGIN_SIGNALS)
                result["current_date_evidence"] = any(s in body for s in CURRENT_DATE_SIGNALS)
                result["licence_link_present"] = (
                    "licence" in body_lower or "license" in body_lower or "ogl" in body_lower
                )

        except urllib.error.HTTPError as e:
            result["http_status"] = e.code
            result["method_used"] = "GET"
            # Read error body for WAF/login signals
            try:
                body = e.read(4096).decode("utf-8", errors="replace")
                body_lower = body.lower()
                result["bot_waf_detected"] = any(s in body_lower for s in BOT_WAF_SIGNALS)
                result["login_required"] = any(s in body_lower for s in LOGIN_SIGNALS)
                result["body_snippet"] = body[:200].replace("\n", " ")
            except Exception:
                pass
        except Exception as e:
            result["error"] = str(e)[:120]
            result["method_used"] = "GET"

    # If HEAD was 200 and we didn't do GET, do a small GET to check page content
    elif head_status == 200 and result["method_used"] == "HEAD":
        try:
            req = urllib.request.Request(result["final_url"], headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
                body_bytes = resp.read(8192)
                body = body_bytes.decode("utf-8", errors="replace")
                body_lower = body.lower()
                result["body_snippet"] = body[:300].replace("\n", " ")
                m = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
                if m:
                    result["page_title"] = m.group(1).strip()[:120]
                result["bot_waf_detected"] = any(s in body_lower for s in BOT_WAF_SIGNALS)
                result["login_required"] = any(s in body_lower for s in LOGIN_SIGNALS)
                result["current_date_evidence"] = any(s in body for s in CURRENT_DATE_SIGNALS)
                result["licence_link_present"] = (
                    "licence" in body_lower or "license" in body_lower or "ogl" in body_lower
                )
                result["method_used"] = "HEAD+GET"
        except Exception:
            pass  # HEAD result stands

    return result


def classify(probe):
    status = probe.get("http_status") or 0
    final = probe.get("final_url", "") or ""
    original = probe.get("original_url", "") or ""
    error = probe.get("error") or ""
    ct = probe.get("content_type") or ""

    if status == 0 or ("connection" in error.lower() if error else False):
        return "DEAD"
    if status in (403, 429) or probe.get("bot_waf_detected"):
        return "RESTRICTED"
    if probe.get("login_required") and status not in (200,):
        return "RESTRICTED"
    if status == 404:
        return "DEAD"
    if status in (301, 302, 307, 308):
        return "MOVED"
    if status == 200:
        # Check if final URL domain differs from original (portal migration)
        try:
            orig_host = urllib.parse.urlparse(original).netloc
            final_host = urllib.parse.urlparse(final).netloc
            if orig_host and final_host and orig_host != final_host:
                return "MOVED"
        except Exception:
            pass
        if probe.get("bot_waf_detected"):
            return "RESTRICTED"
        return "CURRENT"
    if status >= 500:
        return "UNKNOWN"
    return "UNKNOWN"


def main():
    sources = load_sources()
    print(f"Loaded {len(sources)} sources from ODBus_Sources.csv")
    print()

    # Re-order: priorities first, then remainder in original order
    priority_set = set(PRIORITY_SOURCE_IDS)
    ordered = (
        [s for s in sources if s["_source_id"] in priority_set] +
        [s for s in sources if s["_source_id"] not in priority_set]
    )

    results = []
    classification_counts = {}

    for src in ordered:
        sid = src["_source_id"]
        url = src.get("Link to Dataset", "")
        name = src.get("Dataset Name", "")
        city = src.get("City", "")
        prov = src.get("Province/ Territory", "")
        licence_url = src.get("Link to Dataset License", "")
        odbus_date = src.get("Date last updated as of date of download", "")

        print(f"[{sid:02d}] [{prov}] {city} — {name}")
        print(f"       {url[:80]}")

        probe = probe_url(url, sid)
        classification = classify(probe)

        record = {
            "source_id": sid,
            "province": prov,
            "city": city,
            "source_name": name,
            "original_url": url,
            "odbus_update_date": odbus_date,
            "odbus_licence_url": licence_url,
            "http_status": probe["http_status"],
            "final_url": probe["final_url"],
            "content_type": probe["content_type"],
            "response_size_bytes": probe["response_size_bytes"],
            "method_used": probe["method_used"],
            "page_title": probe["page_title"],
            "bot_waf_detected": probe["bot_waf_detected"],
            "login_required": probe["login_required"],
            "current_date_evidence": probe["current_date_evidence"],
            "licence_link_present": probe["licence_link_present"],
            "cert_ok": probe["cert_ok"],
            "error": probe["error"],
            "classification": classification,
            "production_candidate": False,  # requires data + licensing + automation checks
            "notes": ""
        }

        # Auto-notes
        notes = []
        if probe["bot_waf_detected"]:
            notes.append("Bot/WAF protection detected")
        if probe["login_required"]:
            notes.append("Login page detected in response")
        if probe["current_date_evidence"]:
            notes.append("2024/2025/2026 date found in page content")
        if probe["final_url"] and probe["final_url"] != url:
            notes.append(f"Redirected to: {probe['final_url'][:80]}")
        if probe["error"]:
            notes.append(f"Error: {probe['error'][:80]}")
        record["notes"] = "; ".join(notes)

        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        results.append(record)

        print(f"       → {classification} | HTTP {probe['http_status']} | {(probe.get('content_type') or '')[:40]}")
        if record["notes"]:
            print(f"       ℹ {record['notes'][:100]}")
        print()

        time.sleep(0.5)  # polite delay

    # --- Summary ---
    print("=== CLASSIFICATION SUMMARY ===")
    for cls, count in sorted(classification_counts.items(), key=lambda x: -x[1]):
        print(f"  {cls}: {count}")
    print()

    print("=== CURRENT SOURCES ===")
    for r in results:
        if r["classification"] == "CURRENT":
            print(f"  [{r['source_id']:02d}] [{r['province']}] {r['city']} — {r['source_name']}")
            print(f"        {r['final_url'][:80]}")
            if r["current_date_evidence"]:
                print(f"        ✅ Current date evidence")
    print()

    # --- Save JSON ---
    output = {
        "total_sources": len(results),
        "classification_summary": classification_counts,
        "sources": results
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved: {OUTPUT_JSON}")

    # --- Save MD ---
    write_md(results, classification_counts)
    print(f"Saved: {OUTPUT_MD}")


def write_md(results, counts):
    lines = [
        "# VR14.2 — ODBus Endpoint Triage",
        "",
        f"Generated: `2026-09-26`",
        f"Script: `scripts/probe_odbus_vr14_2.py`",
        f"JSON: `reports/validation_rounds/VR14_2_ODBUS_ENDPOINT_TRIAGE.json`",
        "",
        "---",
        "",
        "## Classification Summary",
        "",
        "| Classification | Count |",
        "|---|---|",
    ]
    for cls, count in sorted(counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {cls} | {count} |")

    lines += [
        "",
        "---",
        "",
        "## Full Triage Results",
        "",
        "| # | Prov | City | Dataset | Status | Classification | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        notes = r["notes"][:60] + "..." if len(r["notes"]) > 60 else r["notes"]
        lines.append(
            f"| {r['source_id']} | {r['province']} | {r['city']} | {r['source_name']} "
            f"| {r['http_status']} | {r['classification']} | {notes} |"
        )

    lines += ["", "---", "", "## Current Sources Detail", ""]
    for r in results:
        if r["classification"] == "CURRENT":
            lines += [
                f"### [{r['source_id']}] {r['city']} — {r['source_name']}",
                "",
                f"- Province: {r['province']}",
                f"- HTTP: {r['http_status']}",
                f"- Final URL: {r['final_url']}",
                f"- Content-Type: {r['content_type']}",
                f"- Size: {r['response_size_bytes']} bytes",
                f"- Current date evidence: {r['current_date_evidence']}",
                f"- Licence link present: {r['licence_link_present']}",
                f"- Production candidate: {r['production_candidate']}",
                f"- Notes: {r['notes']}",
                "",
            ]

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
