"""VR11.1 PEI OCBR probe - confirmed URLs."""
import json, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

THROTTLE = 2.0
PEI_GOV = "https://www.princeedwardisland.ca"
OCBR = "https://ocbr.princeedwardisland.ca"
HDRS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-script/1.0)",
    "Accept": "application/json, text/html, */*",
}
RPT = {"generated": datetime.now(timezone.utc).isoformat(), "results": [], "terms": [], "summary": {}}


def get(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HDRS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", errors="replace")
            return r.status, dict(r.headers), body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")
    except Exception as ex:
        return 0, {}, str(ex)


def is_json(b):
    try:
        json.loads(b)
        return True
    except Exception:
        return False


def keys(obj, pre="", d=0):
    out = []
    if d > 5:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{pre}.{k}" if pre else k
            out.append(p)
            out.extend(keys(v, p, d+1))
    elif isinstance(obj, list) and obj:
        out.extend(keys(obj[0], pre+"[]", d+1))
    return out


def hit(url, label, params=None):
    status, hdrs, body = get(url, params)
    time.sleep(THROTTLE)
    ct = hdrs.get("Content-Type", hdrs.get("content-type", ""))
    jj = is_json(body)
    html = "<html" in body.lower() or "<!doctype" in body.lower()
    print(f"  {label}: {status} json={jj} html={html} len={len(body)} ct={ct[:50]}")
    rec = {"url": url, "label": label, "status": status, "ct": ct, "is_json": jj, "is_html": html, "len": len(body)}
    if jj and status == 200:
        parsed = json.loads(body)
        kk = keys(parsed)
        rec["keys"] = kk
        rec["sample"] = json.dumps(parsed, indent=2)[:1500]
        print(f"    JSON KEYS: {kk[:20]}")
    if html and status == 200:
        lower = body.lower()
        for kw in ["fetch(", "/api/", "ocbr.princeton", "iframe", "action="]:
            if kw in lower:
                i = lower.find(kw)
                print(f"    hint[{kw}]: {body[max(0,i-10):i+80].strip()[:100]}")
        thits = [w for w in ["automated","scraping","robot","copyright","eula","prohibit"] if w in lower]
        if thits:
            RPT["terms"].extend(thits)
            print(f"    terms: {thits}")
    RPT["results"].append(rec)
    return status, body


print("\n=== Step 1: PEI gov registry pages ===")
hit(PEI_GOV + "/en/feature/pei-business-corporate-registry", "NEW_PAGE")
hit(PEI_GOV + "/en/feature/pei-business-corporate-registry-original", "ORIG_PAGE")

print("\n=== Step 2: OCBR host paths ===")
for p in ["/", "/ocbr/", "/ocbr/login", "/ocbr/search", "/ocbr/api/search",
          "/api/search", "/api/v1/search", "/search", "/public/search"]:
    hit(OCBR + p, p)

print("\n=== Step 3: OCBR search queries ===")
for p in ["/ocbr/api/search", "/ocbr/search", "/api/search"]:
    for pm in [{"q": "Sobeys"}, {"name": "Sobeys"}, {"businessName": "Sobeys"}]:
        s, b = hit(OCBR + p, f"{p}?{urllib.parse.urlencode(pm)}", params=pm)

print("\n=== Step 4: PEI gov API paths ===")
for p in ["/api/registry/search", "/api/businesses/search", "/api/corporate/search"]:
    hit(PEI_GOV + p, p, params={"q": "Sobeys"})

print("\n=== Step 5: robots.txt / terms ===")
for host, hl in [(PEI_GOV, "PEI"), (OCBR, "OCBR")]:
    for p in ["/robots.txt", "/en/about/terms-conditions", "/privacy"]:
        s, b = hit(host + p, f"{hl}{p}")
        if s == 200:
            lower = b.lower()
            thits = [w for w in ["disallow","automated","scraping","copyright","prohibit"] if w in lower]
            if thits:
                RPT["terms"].extend(thits)
                print(f"    terms in {hl}{p}: {thits}")

# summary
ok = [r for r in RPT["results"] if r["status"] == 200]
json_ok = [r for r in ok if r["is_json"]]
RPT["summary"] = {
    "pages_200": [r["url"] for r in ok],
    "json_200": [r["url"] for r in json_ok],
    "terms": list(set(RPT["terms"])),
}
out = "reports/validation_rounds/VR11_PEI_OCBR.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(RPT, f, indent=2, ensure_ascii=False)
print(f"\n=== written: {out} ===")
print(json.dumps(RPT["summary"], indent=2))
