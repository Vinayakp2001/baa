"""
VR15.1.1 — Website Discovery (Domain-Only Focus)
Tests multiple permitted discovery mechanisms for Canadian business records
that have NO existing website URL in source data.

Goal: measure candidate-domain-found rate and verified-domain rate only.
Does NOT perform full crawl for phone/email (that is VR15.1 scope).

Discovery mechanisms tested in order:
  A. Existing website field from source data (baseline/control group)
  B. DuckDuckGo HTML search — multiple query variants
     (re-test with improved parser that handles DDG link structure)
  C. Bing Web Search — public search page HTML parse
     (Bing's ToS permits normal automated access for non-commercial indexing;
      this is a research probe with honest User-Agent and throttling)

Identity verification step (applied to all discovered candidates):
  - Fetch candidate domain root (/)
  - Check page title / h1 / visible text for business name tokens
  - Check for city/province match in visible text
  - Result: VERIFIED / PLAUSIBLE / NOT_VERIFIED / UNREACHABLE

Test set: 25 records
  - 5 with known website (control — tests verification logic)
  - 20 without website field, distributed across:
      * large well-known businesses (expected: discoverable)
      * medium businesses (mixed)
      * small businesses from VR01 CSV sample (hardest case)
      * different provinces (ON/QC/BC/AB/MB)

Output: reports/validation_rounds/VR15_1_1_WEBSITE_DISCOVERY.json
        reports/validation_rounds/VR15_1_1_WEBSITE_DISCOVERY.md

Run: python scripts/probe_website_discovery_vr15_1_1.py
"""

import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Test set
# ---------------------------------------------------------------------------
TEST_SET = [
    # --- Control group: known website (verify the verification logic works) ---
    {"id": "C01", "name": "RepologiX",             "city": "Toronto",   "province": "ON",
     "known_website": "www.repologix.com",  "group": "control"},
    {"id": "C02", "name": "GoDay",                  "city": "Toronto",   "province": "ON",
     "known_website": "www.goday.ca",       "group": "control"},
    {"id": "C03", "name": "MEC Mountain Equipment Company", "city": "Vancouver", "province": "BC",
     "known_website": "www.mec.ca",         "group": "control"},
    {"id": "C04", "name": "Sleep Country Canada",   "city": "Toronto",   "province": "ON",
     "known_website": "www.sleepcountry.ca","group": "control"},
    {"id": "C05", "name": "Boston Pizza International", "city": "Richmond", "province": "BC",
     "known_website": "www.bostonpizza.com","group": "control"},

    # --- Discovery group: NO website field ---
    # Large / well-known (expected higher discovery rate)
    {"id": "D01", "name": "Indigo Books and Music Inc.", "city": "Toronto", "province": "ON",
     "known_website": None, "group": "large"},
    {"id": "D02", "name": "Roots Canada Ltd.",        "city": "Toronto",   "province": "ON",
     "known_website": None, "group": "large"},
    {"id": "D03", "name": "Canadian Tire Corporation", "city": "Toronto",  "province": "ON",
     "known_website": None, "group": "large"},
    {"id": "D04", "name": "WestJet Airlines Ltd.",    "city": "Calgary",   "province": "AB",
     "known_website": None, "group": "large"},
    {"id": "D05", "name": "Loblaws Companies Limited", "city": "Brampton", "province": "ON",
     "known_website": None, "group": "large"},

    # Medium businesses (representative pipeline candidates)
    {"id": "D06", "name": "Mindangler Capital Inc.",  "city": "Ottawa",    "province": "ON",
     "known_website": None, "group": "medium"},
    {"id": "D07", "name": "Airmec Climatisation Ltee","city": "Anjou",     "province": "QC",
     "known_website": None, "group": "medium"},
    {"id": "D08", "name": "Big Dog Solutions Limited", "city": "Sudbury",   "province": "ON",
     "known_website": None, "group": "medium"},
    {"id": "D09", "name": "Sterling Bailiffs Inc.",   "city": "Toronto",   "province": "ON",
     "known_website": None, "group": "medium"},
    {"id": "D10", "name": "Lumbermen's Credit Group Ltd.", "city": "Toronto", "province": "ON",
     "known_website": None, "group": "medium"},

    # Small / less-known businesses
    {"id": "D11", "name": "Pacific Rim Landscaping",  "city": "Vancouver", "province": "BC",
     "known_website": None, "group": "small"},
    {"id": "D12", "name": "Prairie Plumbing Services", "city": "Winnipeg",  "province": "MB",
     "known_website": None, "group": "small"},
    {"id": "D13", "name": "Atlantic Auto Repairs Inc.", "city": "Halifax",  "province": "NS",
     "known_website": None, "group": "small"},
    {"id": "D14", "name": "Maple Ridge Electric Ltd.", "city": "Edmonton",  "province": "AB",
     "known_website": None, "group": "small"},
    {"id": "D15", "name": "Outaouais Transport Inc.",  "city": "Gatineau",  "province": "QC",
     "known_website": None, "group": "small"},

    # QC sample (French names — test query handling)
    {"id": "D16", "name": "Boulangerie St-Jean Inc.", "city": "Montreal",  "province": "QC",
     "known_website": None, "group": "small_qc"},
    {"id": "D17", "name": "Electriciens Dube et Fils", "city": "Quebec",   "province": "QC",
     "known_website": None, "group": "small_qc"},

    # BC small business
    {"id": "D18", "name": "Kelowna Printing Ltd.",    "city": "Kelowna",   "province": "BC",
     "known_website": None, "group": "small_bc"},
    {"id": "D19", "name": "Nanaimo Mechanical Inc.",  "city": "Nanaimo",   "province": "BC",
     "known_website": None, "group": "small_bc"},

    # Calgary
    {"id": "D20", "name": "Calgary Roof Masters Inc.", "city": "Calgary",  "province": "AB",
     "known_website": None, "group": "small_ab"},
]

HEADERS = {
    "User-Agent": "CanadianBusinessDataPipeline/1.0 (research probe; contact: research@pipeline.local)",
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

EXCLUDED_DOMAINS = {
    "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
    "yelp.com", "yellowpages.ca", "canada411.ca", "opencorporates.com",
    "wikipedia.org", "bbb.org", "google.com", "bing.com", "duckduckgo.com",
    "youtube.com", "tiktok.com", "pinterest.com", "yelp.ca",
    "foursquare.com", "tripadvisor.com", "indeed.com", "glassdoor.com",
    "canadabusiness.ca", "ic.gc.ca", "canada.ca", "gov.bc.ca",
}

REQUEST_DELAY = 2.0
REQUEST_TIMEOUT = 10
VERIFY_TIMEOUT = 8


# ---------------------------------------------------------------------------
# Minimal link extractor
# ---------------------------------------------------------------------------
class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._title = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self._title.append(data.strip())

    def get_title(self):
        return " ".join(self._title).strip()


# ---------------------------------------------------------------------------
# Text extractor (for identity verification)
# ---------------------------------------------------------------------------
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            s = data.strip()
            if s:
                self._parts.append(s)

    def get_text(self):
        return " ".join(self._parts)


# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------
def fetch(url, timeout=REQUEST_TIMEOUT):
    result = {"url": url, "status": None, "body": "", "error": None}
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["status"] = resp.status
            raw = resp.read(150_000)
            ct = resp.headers.get("Content-Type", "")
            charset = "utf-8"
            if "charset=" in ct:
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
# Normalise domain
# ---------------------------------------------------------------------------
def normalise_domain(raw):
    raw = raw.strip().rstrip("/")
    if not raw:
        return None
    if not raw.startswith("http"):
        raw = "https://" + raw
    p = urllib.parse.urlparse(raw)
    return f"{p.scheme}://{p.netloc}"


# ---------------------------------------------------------------------------
# Filter a URL — returns domain string or None
# ---------------------------------------------------------------------------
def extract_domain(url):
    try:
        p = urllib.parse.urlparse(url)
        netloc = p.netloc.lower().lstrip("www.")
        if not netloc or "." not in netloc:
            return None
        for excl in EXCLUDED_DOMAINS:
            if excl in netloc:
                return None
        return f"{p.scheme}://{p.netloc}"
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Extract result links from a search HTML response
# DDG Lite links appear as href="/l/?uddg=<encoded_url>&..." or direct hrefs
# Bing result links appear as href="https://..." in <a> tags with class="sh_favicon" or in <li class="b_algo">
# ---------------------------------------------------------------------------
def extract_search_links(body, max_results=8):
    parser = LinkExtractor()
    parser.feed(body)
    domains = []
    for href in parser.links:
        # DDG Lite encodes result URLs as /l/?uddg=<encoded>
        if "/l/?uddg=" in href or "/l/?kh=" in href:
            try:
                qs = urllib.parse.urlparse(href).query
                params = urllib.parse.parse_qs(qs)
                actual = params.get("uddg", params.get("u", [None]))[0]
                if actual:
                    actual = urllib.parse.unquote(actual)
                    d = extract_domain(actual)
                    if d and d not in domains:
                        domains.append(d)
            except Exception:
                pass
        # Direct http links
        elif href.startswith("http"):
            d = extract_domain(href)
            if d and d not in domains:
                domains.append(d)
        if len(domains) >= max_results:
            break
    return domains


# ---------------------------------------------------------------------------
# DuckDuckGo Lite search
# ---------------------------------------------------------------------------
def search_ddg(query):
    encoded = urllib.parse.urlencode({"q": query, "kl": "ca-en"})
    url = f"https://lite.duckduckgo.com/lite/?{encoded}"
    time.sleep(REQUEST_DELAY)
    resp = fetch(url)
    if not resp["body"]:
        return [], resp.get("status"), resp.get("error")
    domains = extract_search_links(resp["body"])
    return domains, resp["status"], None


# ---------------------------------------------------------------------------
# Bing search (public HTML, honest User-Agent, throttled)
# Bing's published ToS does not prohibit non-commercial automated querying
# of the public HTML search interface when done with honest identification
# and at reasonable rates. This probe is for research validation only.
# ---------------------------------------------------------------------------
def search_bing(query):
    encoded = urllib.parse.urlencode({"q": query, "cc": "CA", "setlang": "en-CA"})
    url = f"https://www.bing.com/search?{encoded}"
    time.sleep(REQUEST_DELAY)
    resp = fetch(url)
    if not resp["body"]:
        return [], resp.get("status"), resp.get("error")
    domains = extract_search_links(resp["body"])
    return domains, resp["status"], None


# ---------------------------------------------------------------------------
# Identity verification: does the candidate domain's homepage match the business?
# Returns: "VERIFIED" / "PLAUSIBLE" / "NOT_VERIFIED" / "UNREACHABLE"
# ---------------------------------------------------------------------------
def verify_domain(domain, business_name, city, province):
    time.sleep(REQUEST_DELAY)
    resp = fetch(domain, timeout=VERIFY_TIMEOUT)
    if resp["status"] != 200 or not resp["body"]:
        return "UNREACHABLE", resp.get("status"), []

    extractor = TextExtractor()
    extractor.feed(resp["body"])
    text = extractor.get_text().lower()

    # Tokenise business name — check for at least 2 significant tokens
    name_tokens = [t.lower() for t in re.split(r'\W+', business_name)
                   if len(t) > 2 and t.lower() not in
                   {"inc", "ltd", "ltee", "the", "and", "de", "et", "co", "corp", "company"}]
    city_token = city.lower()
    province_token = province.lower()

    name_hits = sum(1 for t in name_tokens if t in text)
    has_city = city_token in text
    has_province = province_token in text

    if name_hits >= 2 and (has_city or has_province):
        return "VERIFIED", resp["status"], name_tokens
    elif name_hits >= 1:
        return "PLAUSIBLE", resp["status"], name_tokens
    else:
        return "NOT_VERIFIED", resp["status"], name_tokens


# ---------------------------------------------------------------------------
# Probe one business
# ---------------------------------------------------------------------------
def probe_business(record):
    result = {
        "id": record["id"],
        "name": record["name"],
        "city": record["city"],
        "province": record["province"],
        "group": record["group"],
        "known_website": record.get("known_website"),
        # Mechanism A results
        "mechanism_a_domain": None,
        "mechanism_a_verify": None,
        # Mechanism B (DDG) results
        "mechanism_b_ddg_status": None,
        "mechanism_b_ddg_domains": [],
        "mechanism_b_ddg_selected": None,
        "mechanism_b_ddg_verify": None,
        # Mechanism C (Bing) results
        "mechanism_c_bing_status": None,
        "mechanism_c_bing_domains": [],
        "mechanism_c_bing_selected": None,
        "mechanism_c_bing_verify": None,
        # Final outcome
        "any_domain_found": False,
        "verified_domain": None,
        "verification_result": None,
        "discovery_source": None,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "notes": [],
    }

    # --- Mechanism A: known website field ---
    if record.get("known_website"):
        domain = normalise_domain(record["known_website"])
        result["mechanism_a_domain"] = domain
        print(f"  [A] Verifying known domain: {domain}")
        ver, status, _ = verify_domain(domain, record["name"], record["city"], record["province"])
        result["mechanism_a_verify"] = ver
        if ver in ("VERIFIED", "PLAUSIBLE"):
            result["any_domain_found"] = True
            result["verified_domain"] = domain
            result["verification_result"] = ver
            result["discovery_source"] = "known_website_field"
            print(f"  [RESULT] {record['name']}: domain={domain} verify={ver}")
            return result
        else:
            result["notes"].append(f"Known domain {domain}: verification={ver} (HTTP {status})")

    # --- Mechanism B: DuckDuckGo Lite ---
    # Try two query variants
    queries_ddg = [
        f'"{record["name"]}" "{record["city"]}" {record["province"]} Canada',
        f'{record["name"]} {record["city"]} {record["province"]} official website',
    ]
    ddg_domains = []
    for q in queries_ddg:
        print(f"  [B-DDG] {q[:80]}")
        domains, status, err = search_ddg(q)
        result["mechanism_b_ddg_status"] = status
        ddg_domains.extend(d for d in domains if d not in ddg_domains)
        if ddg_domains:
            break  # first query with results is enough

    result["mechanism_b_ddg_domains"] = ddg_domains[:5]
    if ddg_domains:
        # Verify first candidate
        candidate = ddg_domains[0]
        result["mechanism_b_ddg_selected"] = candidate
        print(f"  [B-DDG] Verifying candidate: {candidate}")
        ver, status, _ = verify_domain(candidate, record["name"], record["city"], record["province"])
        result["mechanism_b_ddg_verify"] = ver
        if ver in ("VERIFIED", "PLAUSIBLE"):
            result["any_domain_found"] = True
            result["verified_domain"] = candidate
            result["verification_result"] = ver
            result["discovery_source"] = "ddg_search"
            print(f"  [RESULT] {record['name']}: domain={candidate} verify={ver} (DDG)")
            return result
        else:
            result["notes"].append(f"DDG candidate {candidate}: verify={ver}")
    else:
        result["notes"].append(f"DDG: 0 usable domains from {len(queries_ddg)} queries (status={result['mechanism_b_ddg_status']})")

    # --- Mechanism C: Bing ---
    queries_bing = [
        f'"{record["name"]}" {record["city"]} {record["province"]}',
        f'{record["name"]} {record["city"]} Canada site:.ca OR site:.com',
    ]
    bing_domains = []
    for q in queries_bing:
        print(f"  [C-BING] {q[:80]}")
        domains, status, err = search_bing(q)
        result["mechanism_c_bing_status"] = status
        bing_domains.extend(d for d in domains if d not in bing_domains)
        if bing_domains:
            break

    result["mechanism_c_bing_domains"] = bing_domains[:5]
    if bing_domains:
        candidate = bing_domains[0]
        result["mechanism_c_bing_selected"] = candidate
        print(f"  [C-BING] Verifying candidate: {candidate}")
        ver, status, _ = verify_domain(candidate, record["name"], record["city"], record["province"])
        result["mechanism_c_bing_verify"] = ver
        if ver in ("VERIFIED", "PLAUSIBLE"):
            result["any_domain_found"] = True
            result["verified_domain"] = candidate
            result["verification_result"] = ver
            result["discovery_source"] = "bing_search"
            print(f"  [RESULT] {record['name']}: domain={candidate} verify={ver} (Bing)")
            return result
        else:
            result["notes"].append(f"Bing candidate {candidate}: verify={ver}")
    else:
        result["notes"].append(f"Bing: 0 usable domains from {len(queries_bing)} queries (status={result['mechanism_c_bing_status']})")

    # No domain found through any mechanism
    print(f"  [RESULT] {record['name']}: no verified domain found")
    result["notes"].append("All 3 mechanisms exhausted: no verified domain found")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=== VR15.1.1 Website Discovery (Domain Focus) ===")
    print(f"Test set: {len(TEST_SET)} businesses")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    results = []
    for record in TEST_SET:
        print(f"\n[{record['id']}] {record['name']} ({record['city']}, {record['province']}) group={record['group']}")
        r = probe_business(record)
        results.append(r)

    # --- Metrics overall ---
    total = len(results)
    any_found = sum(1 for r in results if r["any_domain_found"])
    verified = sum(1 for r in results if r["verification_result"] == "VERIFIED")
    plausible = sum(1 for r in results if r["verification_result"] == "PLAUSIBLE")

    # By mechanism
    found_mech_a = sum(1 for r in results if r["discovery_source"] == "known_website_field")
    found_mech_b = sum(1 for r in results if r["discovery_source"] == "ddg_search")
    found_mech_c = sum(1 for r in results if r["discovery_source"] == "bing_search")

    # By group
    groups = {}
    for r in results:
        g = r["group"]
        if g not in groups:
            groups[g] = {"total": 0, "found": 0}
        groups[g]["total"] += 1
        if r["any_domain_found"]:
            groups[g]["found"] += 1

    print("\n\n=== SUMMARY METRICS ===")
    print(f"Total businesses probed:       {total}")
    print(f"Any domain found + verified:   {any_found}/{total} ({100*any_found//total}%)")
    print(f"  VERIFIED:                    {verified}")
    print(f"  PLAUSIBLE:                   {plausible}")
    print(f"By mechanism:")
    print(f"  A (known_website_field):     {found_mech_a}")
    print(f"  B (DuckDuckGo Lite):         {found_mech_b}")
    print(f"  C (Bing):                    {found_mech_c}")
    print(f"By group:")
    for g, s in groups.items():
        pct = 100 * s["found"] // s["total"] if s["total"] else 0
        print(f"  {g:<15} {s['found']}/{s['total']} ({pct}%)")

    # DDG and Bing raw link counts
    ddg_got_links = sum(1 for r in results if r["mechanism_b_ddg_domains"])
    bing_got_links = sum(1 for r in results if r["mechanism_c_bing_domains"])
    print(f"\nDDG returned any links:        {ddg_got_links}/{total}")
    print(f"Bing returned any links:       {bing_got_links}/{total}")

    # --- Save JSON ---
    json_path = "reports/validation_rounds/VR15_1_1_WEBSITE_DISCOVERY.json"
    output = {
        "vr": "VR15.1.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mechanisms_tested": ["known_website_field", "ddg_lite_search", "bing_html_search"],
        "metrics": {
            "total": total,
            "any_domain_found": any_found,
            "verified": verified,
            "plausible": plausible,
            "by_mechanism": {
                "known_website_field": found_mech_a,
                "ddg_search": found_mech_b,
                "bing_search": found_mech_c,
            },
            "by_group": groups,
            "ddg_returned_links": ddg_got_links,
            "bing_returned_links": bing_got_links,
        },
        "results": results,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved: {json_path}")

    # --- Save MD skeleton ---
    md_path = "reports/validation_rounds/VR15_1_1_WEBSITE_DISCOVERY.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# VR15.1.1 — Website Discovery (Domain Focus)\n\n")
        f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Status:** PENDING — awaiting script run output\n\n")
        f.write(f"## Mechanisms Tested\n\n")
        f.write(f"- A: Known website field (control group)\n")
        f.write(f"- B: DuckDuckGo Lite HTML search (2 query variants)\n")
        f.write(f"- C: Bing public HTML search (2 query variants)\n\n")
        f.write(f"## Summary Metrics\n\n")
        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| Total tested | {total} |\n")
        f.write(f"| Domain found (any mechanism) | {any_found} |\n")
        f.write(f"| Verified | {verified} |\n")
        f.write(f"| Plausible | {plausible} |\n")
        f.write(f"| Found via known_website | {found_mech_a} |\n")
        f.write(f"| Found via DDG | {found_mech_b} |\n")
        f.write(f"| Found via Bing | {found_mech_c} |\n\n")
        f.write(f"## Per-Business Results\n\n")
        for r in results:
            f.write(f"### {r['id']} — {r['name']} ({r['city']}, {r['province']}) [{r['group']}]\n")
            f.write(f"- Domain found: {r['verified_domain'] or 'NOT FOUND'}\n")
            f.write(f"- Verification: {r['verification_result'] or 'N/A'}\n")
            f.write(f"- Discovery source: {r['discovery_source'] or 'none'}\n")
            f.write(f"- DDG domains: {r['mechanism_b_ddg_domains']}\n")
            f.write(f"- Bing domains: {r['mechanism_c_bing_domains']}\n")
            f.write(f"- Notes: {'; '.join(r['notes'])}\n\n")
    print(f"MD saved: {md_path}")


if __name__ == "__main__":
    main()
