import sys, traceback, json, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser

HTML_BASE = "https://ised-isde.canada.ca/cc/lgcy/fdrlCrpDtls.html"
HEADERS = {"User-Agent": "CanadianBusinessDataPipeline/1.0"}
TEST_CORPS = [
    ("8660115", "MINDANGLER CAPITAL INC.", "ON"),
    ("821080",  "AIRMEC CLIMATISATION LTEE", "QC"),
    ("4396626", "AIR CANADA corrected", "QC"),
]
DIRECTOR_RE = re.compile(r'\bdirectors?\b', re.IGNORECASE)
ISC_RE = re.compile(r'\bindividuals?\s+with\s+significant\s+control\b', re.IGNORECASE)
NAME_RE = re.compile(r'^[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)+$')
BOILERPLATE = {"minimum","maximum","information","director","directors","elected",
               "shareholders","corporation","referred","management","supervised",
               "individual","individuals","significant","control","annual","filing"}

class SP(HTMLParser):
    H = {"h1","h2","h3","h4","h5","th","caption","dt"}
    S = {"script","style","nav","footer","header"}
    def __init__(self):
        super().__init__()
        self.sections = {}
        self._cur = "preamble"
        self._skip = 0
        self._inh = False
        self._hbuf = []
        self._tbuf = []
    def handle_starttag(self, tag, attrs):
        if tag in self.S: self._skip += 1; return
        if tag in self.H: self._inh = True; self._hbuf = []
    def handle_endtag(self, tag):
        if tag in self.S: self._skip = max(0, self._skip-1); return
        if tag in self.H and self._inh:
            ht = " ".join(self._hbuf).strip()
            if ht: self._flush(); self._cur = ht
            self._inh = False; self._hbuf = []
    def handle_data(self, data):
        if self._skip: return
        s = data.strip()
        if not s: return
        (self._hbuf if self._inh else self._tbuf).append(s)
    def _flush(self):
        if self._tbuf:
            self.sections.setdefault(self._cur, []).extend(self._tbuf)
            self._tbuf = []
    def close(self): self._flush(); super().close()
    def get(self): self._flush(); return self.sections

def find_sec(sections, pat):
    for h, t in sections.items():
        if pat.search(h): return h, t
    return None, []

def extract_names(frags):
    out = []
    for f in frags:
        for p in re.split(r'[,;\n]', f):
            p = p.strip()
            if not p or len(p) < 4 or len(p) > 80: continue
            if any(w in BOILERPLATE for w in p.lower().split()): continue
            if NAME_RE.match(p): out.append(p)
    return list(dict.fromkeys(out))

def fetch(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read(800000).decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e: return e.code, "", str(e)
    except Exception as e: return None, "", str(e)

print("START", flush=True)
results = []

for corp_num, name, prov in TEST_CORPS:
    url = f"{HTML_BASE}?corpId={corp_num}"
    print(f"\n[{corp_num}] {name}", flush=True)
    time.sleep(2.5)
    status, body, err = fetch(url)
    print(f"  HTTP {status}  len={len(body)}  err={err}", flush=True)

    rec = {"corp_num": corp_num, "name": name, "province": prov,
           "http_status": status, "page_accessible": status == 200 and bool(body),
           "directors_section_present": False, "directors_section_heading": None,
           "director_extraction_succeeded": False, "directors": [],
           "isc_section_present": False, "isc_section_heading": None,
           "isc_extraction_succeeded": False, "isc_persons": [],
           "all_section_headings": [], "notes": [],
           "source_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat()}

    if status != 200 or not body:
        rec["notes"].append(f"Not accessible: {status} {err}")
        results.append(rec)
        continue

    sp = SP(); sp.feed(body); sp.close()
    secs = sp.get()
    rec["all_section_headings"] = list(secs.keys())
    print(f"  Sections: {list(secs.keys())[:15]}", flush=True)

    dh, dt = find_sec(secs, DIRECTOR_RE)
    if dh:
        rec["directors_section_present"] = True
        rec["directors_section_heading"] = dh
        names = extract_names(dt)
        print(f"  Dir section '{dh}': frags={len(dt)} names={names}", flush=True)
        if names:
            rec["director_extraction_succeeded"] = True
            rec["directors"] = names
    else:
        print(f"  No director section", flush=True)

    ih, it = find_sec(secs, ISC_RE)
    if ih:
        rec["isc_section_present"] = True
        rec["isc_section_heading"] = ih
        names = extract_names(it)
        print(f"  ISC section '{ih}': frags={len(it)} names={names}", flush=True)
        if names:
            rec["isc_extraction_succeeded"] = True
            rec["isc_persons"] = names
    else:
        print(f"  No ISC section", flush=True)

    results.append(rec)

print("\n=== SUMMARY ===", flush=True)
for r in results:
    print(f"  {r['corp_num']}  dir={r['directors']}  isc={r['isc_persons']}", flush=True)

out = {"vr": "VR15.2.1", "generated_at": datetime.now(timezone.utc).isoformat(), "results": results}
with open("reports/validation_rounds/VR15_2_1_CORPS_DOM.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("JSON saved.", flush=True)
print("DONE", flush=True)
