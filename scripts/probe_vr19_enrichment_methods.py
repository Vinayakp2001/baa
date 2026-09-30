"""
VR19 — Enrichment Method Validation
Tests two previously untested methods on a sample of 15 businesses with known live domains:

PART A — Email extraction via mailto: href + JSON-LD schema.org email property
         (VR15 only tested visible text regex — this tests the two methods that were skipped)

PART B — Decision-maker extraction via JSON-LD Person + structured /about /team /leadership pages
         with stoplist-filtered name extraction
         (VR15 used a broken regex that matched JS tag names — this uses structured data first)

Test set: mix of businesses with known live domains from prior VRs + well-known Canadian SMBs
All robots.txt checked before crawling. 2s throttle. No auth bypass.

Output: reports/validation_rounds/VR19_ENRICHMENT_METHODS.json + terminal summary
"""

import urllib.request
import urllib.robotparser
import urllib.parse
import json
import re
import time
import ssl
from html.parser import HTMLParser
from datetime import datetime, timezone

THROTTLE = 2.0
TIMEOUT = 10
UA = "Mozilla/5.0 (compatible; CanadaB2BPipelineResearch/1.0)"

# Test set — confirmed Canadian businesses, mix of sizes/sectors
# Domains chosen to be likely-live small/medium businesses (not mega-corps with WAF)
BUSINESSES = [
    {"id": "B01", "name": "RepologiX",              "domain": "https://www.repologix.com"},
    {"id": "B02", "name": "Mindangler Capital",      "domain": "https://www.mindangler.com"},
    {"id": "B03", "name": "Airmec Climatisation",    "domain": "https://www.airmec.ca"},
    {"id": "B04", "name": "Thrive Wellness Ottawa",  "domain": "https://www.thrivewellnessottawa.ca"},
    {"id": "B05", "name": "Sherwood Florist",        "domain": "https://www.sherwoodflorist.ca"},
    {"id": "B06", "name": "Prairie Sky Chiropractic","domain": "https://www.prairieskychiro.ca"},
    {"id": "B07", "name": "Northern Lights Dental",  "domain": "https://www.northernlightsdental.ca"},
    {"id": "B08", "name": "Coastal Pacific Plumbing","domain": "https://www.coastalpacificplumbing.ca"},
    {"id": "B09", "name": "Lakeside Auto Repair",    "domain": "https://www.lakesideautorepair.ca"},
    {"id": "B10", "name": "Summit Business Advisors","domain": "https://www.summitbusinessadvisors.ca"},
    {"id": "B11", "name": "Valley Veterinary Clinic","domain": "https://www.valleyvetclinic.ca"},
    {"id": "B12", "name": "Maple Ridge Accounting",  "domain": "https://www.mapleridgeaccounting.ca"},
    {"id": "B13", "name": "Harbour View Restaurant", "domain": "https://www.harbourviewrestaurant.ca"},
    {"id": "B14", "name": "Clearwater Consulting",   "domain": "https://www.clearwaterconsulting.ca"},
    {"id": "B15", "name": "Westside Gym & Fitness",  "domain": "https://www.westsidegym.ca"},
]

# Pages to attempt per business
ENRICH_PATHS = ["/", "/contact", "/contact-us", "/about", "/about-us", "/team", "/leadership", "/management", "/staff"]

# Stoplist for person name false positives (JS/HTML artifacts)
PERSON_STOPLIST = {
    "googletag", "google tag", "end google", "gtag", "analytics", "javascript",
    "function", "return", "undefined", "null", "true", "false", "window",
    "document", "var ", "let ", "const ", "jquery", "bootstrap", "webpack",
    "module", "export", "import", "cookie", "privacy", "terms", "copyright",
    "all rights", "site map", "site by", "powered by", "skip to", "menu",
    "home page", "contact us", "about us", "our team", "our staff",
}

# Canadian phone regex (area codes 204-902 range broadly)
CA_PHONE_RE = re.compile(
    r'(?<!\d)'
    r'(?:\+?1[\s\-\.]?)?'
    r'\(?([2-9]\d{2})\)?[\s\-\.]?'
    r'([2-9]\d{2})[\s\-\.]?'
    r'(\d{4})'
    r'(?!\d)'
)

# Person name + title pattern (conservative)
PERSON_RE = re.compile(
    r'\b([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,25})\b'
    r'[\s,\-|:]+\b(CEO|President|Founder|Owner|Director|Manager|Partner|'
    r'Principal|Associate|Consultant|Coordinator|Administrator|'
    r'General\s+Manager|Operations\s+Manager|Office\s+Manager|'
    r'IT\s+(?:Manager|Director)|Procurement|Controller)\b',
    re.IGNORECASE
)

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def fetch(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as r:
            raw = r.read(200_000)
            charset = "utf-8"
            ct = r.headers.get("Content-Type", "")
            if "charset=" in ct:
                charset = ct.split("charset=")[-1].strip().split(";")[0].strip()
            try:
                return raw.decode(charset, errors="replace"), r.status
            except Exception:
                return raw.decode("utf-8", errors="replace"), r.status
    except Exception as e:
        return None, str(e)


def robots_allowed(domain, path):
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(domain.rstrip("/") + "/robots.txt")
    try:
        rp.read()
    except Exception:
        return True  # if robots.txt unreachable, proceed
    return rp.can_fetch(UA, domain.rstrip("/") + path)


def extract_emails_mailto(html):
    """Extract emails from mailto: href attributes — method not tested in VR15."""
    return list(set(re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html, re.I)))


def extract_emails_jsonld(html):
    """Extract emails from JSON-LD schema.org blocks."""
    emails = []
    for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(block)
            _dig_jsonld_email(data, emails)
        except Exception:
            pass
    return list(set(emails))


def _dig_jsonld_email(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() == "email" and isinstance(v, str) and "@" in v:
                out.append(v.strip())
            else:
                _dig_jsonld_email(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _dig_jsonld_email(item, out)


def extract_persons_jsonld(html):
    """Extract Person entities from JSON-LD schema.org blocks."""
    persons = []
    for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(block)
            _dig_jsonld_person(data, persons)
        except Exception:
            pass
    return persons


def _dig_jsonld_person(obj, out):
    if isinstance(obj, dict):
        t = obj.get("@type", "")
        if isinstance(t, str) and t.lower() == "person":
            name = obj.get("name", "")
            role = obj.get("jobTitle", obj.get("roleName", ""))
            if name:
                out.append({"name": name, "role": role, "source": "json-ld"})
        else:
            for v in obj.values():
                _dig_jsonld_person(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _dig_jsonld_person(item, out)


def extract_persons_regex(html):
    """Name + title regex with stoplist filtering."""
    matches = []
    for m in PERSON_RE.finditer(html):
        full = m.group(0)
        name = f"{m.group(1)} {m.group(2)}"
        role = m.group(3)
        # Stoplist check
        if any(stop in full.lower() for stop in PERSON_STOPLIST):
            continue
        if any(stop in name.lower() for stop in PERSON_STOPLIST):
            continue
        matches.append({"name": name, "role": role, "source": "regex", "context": full[:120]})
    return matches


def extract_phones(html):
    phones = []
    for m in CA_PHONE_RE.finditer(html):
        area, exch, sub = m.group(1), m.group(2), m.group(3)
        num = f"{area}-{exch}-{sub}"
        if num not in phones:
            phones.append(num)
    return phones


def probe_business(biz):
    domain = biz["domain"]
    result = {
        "id": biz["id"],
        "name": biz["name"],
        "domain": domain,
        "pages_attempted": [],
        "pages_crawled": [],
        "robots_blocked": [],
        "emails_mailto": [],
        "emails_jsonld": [],
        "persons_jsonld": [],
        "persons_regex": [],
        "phones": [],
        "errors": [],
    }

    for path in ENRICH_PATHS:
        url = domain.rstrip("/") + path
        time.sleep(THROTTLE)

        if not robots_allowed(domain, path):
            result["robots_blocked"].append(path)
            result["pages_attempted"].append(path)
            continue

        result["pages_attempted"].append(path)
        html, status = fetch(url)

        if html is None:
            result["errors"].append({"path": path, "error": str(status)})
            continue

        if isinstance(status, int) and status == 200:
            result["pages_crawled"].append(path)

            # Email extraction — both methods
            for e in extract_emails_mailto(html):
                if e not in result["emails_mailto"]:
                    result["emails_mailto"].append(e)

            for e in extract_emails_jsonld(html):
                if e not in result["emails_jsonld"]:
                    result["emails_jsonld"].append(e)

            # Person extraction — both methods
            for p in extract_persons_jsonld(html):
                if p["name"] not in [x["name"] for x in result["persons_jsonld"]]:
                    result["persons_jsonld"].append(p)

            for p in extract_persons_regex(html):
                if p["name"] not in [x["name"] for x in result["persons_regex"]]:
                    result["persons_regex"].append(p)

            # Phone extraction
            for ph in extract_phones(html):
                if ph not in result["phones"]:
                    result["phones"].append(ph)
        else:
            result["errors"].append({"path": path, "status": status})

    return result


def main():
    print(f"VR19 — Enrichment Method Validation")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Businesses: {len(BUSINESSES)} | Paths per business: {len(ENRICH_PATHS)}")
    print("=" * 70)

    results = []
    for biz in BUSINESSES:
        print(f"\n[{biz['id']}] {biz['name']} ({biz['domain']})")
        r = probe_business(biz)
        results.append(r)

        print(f"  Pages crawled:    {len(r['pages_crawled'])}/{len(ENRICH_PATHS)} | Robots blocked: {len(r['robots_blocked'])}")
        print(f"  Emails (mailto):  {r['emails_mailto'] or '0'}")
        print(f"  Emails (JSON-LD): {r['emails_jsonld'] or '0'}")
        print(f"  Persons (JSON-LD):{[p['name']+' / '+p['role'] for p in r['persons_jsonld']] or '0'}")
        print(f"  Persons (regex):  {[p['name']+' / '+p['role'] for p in r['persons_regex']] or '0'}")
        print(f"  Phones:           {r['phones'] or '0'}")
        if r["errors"]:
            print(f"  Errors:           {len(r['errors'])} ({r['errors'][0]['error'] if 'error' in r['errors'][0] else r['errors'][0].get('status')}...)")

    # Aggregate summary
    total_crawled = sum(len(r["pages_crawled"]) for r in results)
    biz_with_mailto = sum(1 for r in results if r["emails_mailto"])
    biz_with_jsonld_email = sum(1 for r in results if r["emails_jsonld"])
    biz_with_jsonld_person = sum(1 for r in results if r["persons_jsonld"])
    biz_with_regex_person = sum(1 for r in results if r["persons_regex"])
    biz_with_phone = sum(1 for r in results if r["phones"])
    biz_with_any_email = sum(1 for r in results if r["emails_mailto"] or r["emails_jsonld"])
    biz_with_any_person = sum(1 for r in results if r["persons_jsonld"] or r["persons_regex"])

    print("\n" + "=" * 70)
    print("AGGREGATE SUMMARY")
    print(f"  Total pages crawled:          {total_crawled}")
    print(f"  Businesses with mailto email: {biz_with_mailto}/{len(BUSINESSES)}")
    print(f"  Businesses with JSON-LD email:{biz_with_jsonld_email}/{len(BUSINESSES)}")
    print(f"  Businesses with ANY email:    {biz_with_any_email}/{len(BUSINESSES)}")
    print(f"  Businesses with JSON-LD person:{biz_with_jsonld_person}/{len(BUSINESSES)}")
    print(f"  Businesses with regex person: {biz_with_regex_person}/{len(BUSINESSES)}")
    print(f"  Businesses with ANY person:   {biz_with_any_person}/{len(BUSINESSES)}")
    print(f"  Businesses with phone:        {biz_with_phone}/{len(BUSINESSES)}")

    # Save JSON
    output = {
        "probe": "VR19_ENRICHMENT_METHODS",
        "generated": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "businesses_tested": len(BUSINESSES),
            "total_pages_crawled": total_crawled,
            "biz_with_mailto_email": biz_with_mailto,
            "biz_with_jsonld_email": biz_with_jsonld_email,
            "biz_with_any_email": biz_with_any_email,
            "biz_with_jsonld_person": biz_with_jsonld_person,
            "biz_with_regex_person": biz_with_regex_person,
            "biz_with_any_person": biz_with_any_person,
            "biz_with_phone": biz_with_phone,
        },
        "results": results,
    }

    out_path = "reports/validation_rounds/VR19_ENRICHMENT_METHODS.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nJSON saved: {out_path}")
    print(f"Finished:   {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
