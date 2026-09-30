"""
VR15.1 — Company Website Discovery & Crawl Probe
Probes a test set of Canadian businesses to measure:
  - Website discovery rate (given business name + city/province)
  - Phone extraction rate from official website
  - Email extraction rate from official website
  - Leadership/contact page detection rate

Strategy:
  1. For records that already have a website field (Ontario Select Licence), validate/crawl directly.
  2. For records without a website, attempt DuckDuckGo Lite HTML search to find candidate domain.
  3. Crawl discovered domain: /, /contact, /contact-us, /about, /about-us, /team, /leadership
  4. Extract: phone, email, mailto links, tel links, JSON-LD schema.org fields
  5. Respect robots.txt. Throttle. Identify crawler honestly.

Output: reports/validation_rounds/VR15_WEBSITE_ENRICHMENT.json (raw results)
        reports/validation_rounds/VR15_WEBSITE_ENRICHMENT.md  (summary report)

Run: python scripts/probe_company_websites_vr15_1.py
"""

import json
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Test set — mix of sources, sizes, sectors, provinces
# Records with known_website come from VR06 Ontario Select Licence (has website field)
# Records without known_website require discovery
# ---------------------------------------------------------------------------
TEST_SET = [
    # --- From VR06 Ontario Select Licence (website field present) ---
    {"id": "T01", "name": "Sterling Bailiffs Inc.", "city": "Toronto", "province": "ON",
     "known_website": "www.sterlingbailiffs.com", "source": "VR06"},
    {"id": "T02", "name": "Lumbermen's Credit Group Ltd.", "city": "Toronto", "province": "ON",
     "known_website": "www.lcg.ca", "source": "VR06"},
    {"id": "T03", "name": "GoDay", "city": "Toronto", "province": "ON",
     "known_website": "www.goday.ca", "source": "VR06"},
    {"id": "T04", "name": "RepologiX", "city": "Toronto", "province": "ON",
     "known_website": "www.repologix.com", "source": "VR06"},

    # --- Well-known Canadian businesses (no prior website in our data) ---
    {"id": "T05", "name": "MEC Mountain Equipment Company", "city": "Vancouver", "province": "BC",
     "known_website": None, "source": "manual"},
    {"id": "T06", "name": "Sleep Country Canada", "city": "Toronto", "province": "ON",
     "known_website": None, "source": "manual"},
    {"id": "T07", "name": "Boston Pizza International", "city": "Richmond", "province": "BC",
     "known_website": None, "source": "manual"},

    # --- Small businesses (harder, representative of pipeline reality) ---
    {"id": "T08", "name": "Mindangler Capital Inc.", "city": "Ottawa", "province": "ON",
     "known_website": None, "source": "VR01"},
    {"id": "T09", "name": "Airmec Climatisation Ltee", "city": "Anjou", "province": "QC",
     "known_website": None, "source": "VR01"},
    {"id": "T10", "name": "Big Dog Solutions Limited", "city": "Sudbury", "province": "ON",
     "known_website": None, "source": "VR06"},
]

HEADERS = {
    "User-Agent": "CanadianBusinessDataPipeline/1.0 (research probe; contact: research@pipeline.local)",
    "Accept-Language": "en-CA,en;q=0.9",
}

CRAWL_PATHS = ["/", "/contact", "/contact-us", "/about", "/about-us",
               "/team", "/leadership", "/management", "/locations"]

PHONE_RE = re.compile(
    r'(?<!\d)(\+?1[\s\-.]?)?'
    r'\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}'
    r'(?!\d)'
)
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

LEADERSHIP_TITLES = re.compile(
    r'\b(owner|founder|co-founder|president|vice president|vp|'
    r'general manager|gm|operations manager|office manager|'
    r'it manager|it director|director of it|technology manager|'
    r'procurement manager|purchasing manager|facilities manager|'
    r'controller|coo|cto|cio|chief operating|chief technology|chief information)\b',
    re.IGNORECASE
)

REQUEST_DELAY = 2.0  # seconds between requests
REQUEST_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Minimal HTML parser — extracts text, links, mailto, tel
# ---------------------------------------------------------------------------
class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.mailto_links = []
        self.tel_links = []
        self.all_links = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a":
            href = attrs_dict.get("href", "")
            if href.startswith("mailto:"):
                email = href[7:].split("?")[0].strip()
                if email:
                    self.mailto_links.append(email)
            elif href.startswith("tel:"):
                phone = href[4:].strip()
                if phone:
                    self.tel_links.append(phone)
            elif href:
                self.all_links.append(href)

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)

    def get_text(self):
        return " ".join(self.text_parts)


# ---------------------------------------------------------------------------
# robots.txt cache
# ---------------------------------------------------------------------------
_robots_cache = {}

def can_fetch(url):
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    if robots_url not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception:
            # If robots.txt unreachable, allow by default
            rp = None
        _robots_cache[robots_url] = rp
        time.sleep(0.5)
    rp = _robots_cache[robots_url]
    if rp is None:
        return True
    return rp.can_fetch(HEADERS["User-Agent"], url)


# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------
def fetch_url(url, timeout=REQUEST_TIMEOUT):
    result = {
        "url": url, "status": None, "content_type": None,
        "body": "", "error": None
    }
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["status"] = resp.status
            result["content_type"] = resp.headers.get("Content-Type", "")
            raw = resp.read(200_000)  # cap at 200KB per page
            charset = "utf-8"
            ct = result["content_type"]
            if ct and "charset=" in ct:
                charset = ct.split("charset=")[-1].split(";")[0].strip()
            try:
                result["body"] = raw.decode(charset, errors="replace")
            except Exception:
                result["body"] = raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# Normalise a candidate domain → https://domain
# ---------------------------------------------------------------------------
def normalise_domain(raw):
    raw = raw.strip().rstrip("/")
    if not raw:
        return None
    if not raw.startswith("http"):
        raw = "https://" + raw
    parsed = urllib.parse.urlparse(raw)
    return f"{parsed.scheme}://{parsed.netloc}"


# ---------------------------------------------------------------------------
# DuckDuckGo Lite search — returns first ~5 result URLs (HTML parse, no API)
# ---------------------------------------------------------------------------
def ddg_search(query, max_results=5):
    """
    Queries DuckDuckGo Lite HTML interface.
    Returns list of result URLs (strings).
    NOTE: DuckDuckGo's ToS does not explicitly prohibit non-commercial
    automated access to the lite HTML interface, but throttling and
    honest User-Agent identification are required. This is used here
    solely for research probe purposes.
    """
    encoded = urllib.parse.urlencode({"q": query, "kl": "ca-en"})
    url = f"https://lite.duckduckgo.com/lite/?{encoded}"
    time.sleep(REQUEST_DELAY)
    resp = fetch_url(url)
    if not resp["body"]:
        return []
    parser = SimpleHTMLParser()
    parser.feed(resp["body"])
    results = []
    for link in parser.all_links:
        if link.startswith("http") and "duckduckgo.com" not in link:
            results.append(link)
            if len(results) >= max_results:
                break
    return results


# ---------------------------------------------------------------------------
# Extract structured data from a crawled page
# ---------------------------------------------------------------------------
def extract_from_page(url, body):
    parser = SimpleHTMLParser()
    parser.feed(body)
    text = parser.get_text()

    phones = list(set(PHONE_RE.findall(text)))
    # PHONE_RE returns tuples due to group; flatten
    phones_flat = []
    for p in PHONE_RE.finditer(text):
        phones_flat.append(p.group(0).strip())
    phones_flat = list(set(phones_flat))

    tel_phones = list(set(parser.tel_links))
    all_phones = list(set(phones_flat + tel_phones))

    emails_text = list(set(EMAIL_RE.findall(text)))
    emails_mailto = list(set(parser.mailto_links))
    all_emails = list(set(emails_text + emails_mailto))
    # Filter junk
    all_emails = [e for e in all_emails if not e.endswith((".png", ".jpg", ".gif", ".css"))]

    # JSON-LD extraction
    jsonld_phones = []
    jsonld_emails = []
    jsonld_name = None
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                          body, re.DOTALL | re.IGNORECASE):
        try:
            data = json.loads(m.group(1))
            if isinstance(data, dict):
                if data.get("telephone"):
                    jsonld_phones.append(str(data["telephone"]))
                if data.get("email"):
                    jsonld_emails.append(str(data["email"]))
                if data.get("name"):
                    jsonld_name = str(data["name"])
        except Exception:
            pass

    all_phones = list(set(all_phones + jsonld_phones))
    all_emails = list(set(all_emails + jsonld_emails))

    # Leadership signal
    leadership_signals = []
    for line in text.split("."):
        if LEADERSHIP_TITLES.search(line):
            leadership_signals.append(line.strip()[:200])

    has_leadership_page = any(kw in url.lower() for kw in
                               ["/team", "/leadership", "/management", "/about", "/people"])

    return {
        "url": url,
        "phones": all_phones[:10],
        "emails": all_emails[:10],
        "jsonld_name": jsonld_name,
        "leadership_signals": leadership_signals[:5],
        "has_leadership_page": has_leadership_page,
    }


# ---------------------------------------------------------------------------
# Probe one business
# ---------------------------------------------------------------------------
def probe_business(record):
    result = {
        "id": record["id"],
        "name": record["name"],
        "city": record["city"],
        "province": record["province"],
        "source": record["source"],
        "known_website": record.get("known_website"),
        "discovered_domain": None,
        "discovery_method": None,
        "domain_reachable": False,
        "pages_crawled": [],
        "phones": [],
        "emails": [],
        "leadership_signals": [],
        "has_leadership_page": False,
        "error": None,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }

    # Step 1 — determine candidate domain
    if record.get("known_website"):
        domain = normalise_domain(record["known_website"])
        result["discovery_method"] = "known_website_field"
    else:
        # Try DuckDuckGo search
        query = f'{record["name"]} {record["city"]} {record["province"]} Canada official website'
        print(f"  [DDG] Searching: {query[:80]}")
        candidates = ddg_search(query)
        domain = None
        for url in candidates:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            # Exclude social/directory sites
            excluded = ["linkedin", "facebook", "twitter", "instagram", "yelp",
                        "yellowpages", "canada411", "opencorporates", "wikipedia",
                        "bbb.org", "google.com"]
            if not any(ex in netloc for ex in excluded):
                domain = f"{parsed.scheme}://{parsed.netloc}"
                result["discovery_method"] = "ddg_search"
                break
        if not domain:
            result["error"] = "no_candidate_domain_found"
            print(f"  [RESULT] {record['name']}: no domain found")
            return result

    result["discovered_domain"] = domain

    # Step 2 — verify domain is reachable
    print(f"  [VERIFY] {domain}")
    time.sleep(REQUEST_DELAY)
    root_resp = fetch_url(domain)
    if not root_resp["status"] or root_resp["status"] >= 400:
        result["error"] = f"domain_unreachable:{root_resp['status'] or root_resp['error']}"
        print(f"  [RESULT] {record['name']}: domain unreachable ({result['error']})")
        return result

    result["domain_reachable"] = True

    # Step 3 — crawl candidate paths
    all_phones = []
    all_emails = []
    all_leadership = []

    for path in CRAWL_PATHS:
        url = domain + path
        if not can_fetch(url):
            print(f"    [ROBOTS] blocked: {url}")
            continue
        time.sleep(REQUEST_DELAY)
        print(f"    [CRAWL] {url}")
        resp = fetch_url(url)
        if resp["status"] == 200 and resp["body"]:
            ct = resp.get("content_type", "")
            if "html" not in (ct or "").lower():
                continue
            extracted = extract_from_page(url, resp["body"])
            page_summary = {
                "path": path,
                "status": resp["status"],
                "phones_found": len(extracted["phones"]),
                "emails_found": len(extracted["emails"]),
                "leadership_signals": len(extracted["leadership_signals"]),
            }
            result["pages_crawled"].append(page_summary)
            all_phones.extend(extracted["phones"])
            all_emails.extend(extracted["emails"])
            all_leadership.extend(extracted["leadership_signals"])
            if extracted["has_leadership_page"]:
                result["has_leadership_page"] = True
        elif resp["status"] and resp["status"] != 404:
            result["pages_crawled"].append({"path": path, "status": resp["status"]})

    result["phones"] = list(set(all_phones))[:10]
    result["emails"] = list(set(all_emails))[:10]
    result["leadership_signals"] = list(set(all_leadership))[:10]

    print(f"  [RESULT] {record['name']}: domain={domain} phones={len(result['phones'])} "
          f"emails={len(result['emails'])} leadership={len(result['leadership_signals'])}")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=== VR15.1 Company Website Enrichment Probe ===")
    print(f"Test set: {len(TEST_SET)} businesses")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    results = []
    for record in TEST_SET:
        print(f"\n[{record['id']}] {record['name']} ({record['city']}, {record['province']})")
        r = probe_business(record)
        results.append(r)

    # --- Metrics ---
    total = len(results)
    domain_found = sum(1 for r in results if r["discovered_domain"])
    domain_reachable = sum(1 for r in results if r["domain_reachable"])
    phone_found = sum(1 for r in results if r["phones"])
    email_found = sum(1 for r in results if r["emails"])
    leadership_found = sum(1 for r in results if r["leadership_signals"])
    has_leadership_page = sum(1 for r in results if r["has_leadership_page"])

    print("\n\n=== SUMMARY METRICS ===")
    print(f"Total businesses probed:     {total}")
    print(f"Domain found:                {domain_found}/{total} ({100*domain_found//total}%)")
    print(f"Domain reachable:            {domain_reachable}/{total} ({100*domain_reachable//total}%)")
    print(f"Phone extracted:             {phone_found}/{total} ({100*phone_found//total}%)")
    print(f"Email extracted:             {email_found}/{total} ({100*email_found//total}%)")
    print(f"Leadership signal found:     {leadership_found}/{total} ({100*leadership_found//total}%)")
    print(f"Leadership page detected:    {has_leadership_page}/{total}")

    # --- Save JSON ---
    json_path = "reports/validation_rounds/VR15_WEBSITE_ENRICHMENT.json"
    output = {
        "vr": "VR15.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "total": total,
            "domain_found": domain_found,
            "domain_reachable": domain_reachable,
            "phone_found": phone_found,
            "email_found": email_found,
            "leadership_found": leadership_found,
            "has_leadership_page": has_leadership_page,
        },
        "results": results,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved: {json_path}")

    # --- Save MD skeleton (to be filled by Kiro after run) ---
    md_path = "reports/validation_rounds/VR15_WEBSITE_ENRICHMENT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# VR15.1 — Company Website Discovery & Enrichment\n\n")
        f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Status:** PENDING — awaiting script run output\n\n")
        f.write(f"## Metrics\n\n")
        f.write(f"| Metric | Count | % |\n|---|---|---|\n")
        f.write(f"| Domain found | {domain_found} | {100*domain_found//total}% |\n")
        f.write(f"| Domain reachable | {domain_reachable} | {100*domain_reachable//total}% |\n")
        f.write(f"| Phone extracted | {phone_found} | {100*phone_found//total}% |\n")
        f.write(f"| Email extracted | {email_found} | {100*email_found//total}% |\n")
        f.write(f"| Leadership signal | {leadership_found} | {100*leadership_found//total}% |\n\n")
        f.write(f"## Per-Business Results\n\n")
        for r in results:
            f.write(f"### {r['id']} — {r['name']} ({r['city']}, {r['province']})\n")
            f.write(f"- Source: {r['source']}\n")
            f.write(f"- Domain: {r['discovered_domain'] or 'NOT FOUND'}\n")
            f.write(f"- Discovery method: {r['discovery_method'] or 'N/A'}\n")
            f.write(f"- Reachable: {r['domain_reachable']}\n")
            f.write(f"- Phones: {r['phones']}\n")
            f.write(f"- Emails: {r['emails']}\n")
            f.write(f"- Leadership signals: {len(r['leadership_signals'])}\n")
            f.write(f"- Error: {r['error'] or 'none'}\n\n")
    print(f"MD saved: {md_path}")


if __name__ == "__main__":
    main()
