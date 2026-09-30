# VR20 — Final Province Gap Feasibility Round
# Ontario / Quebec / Nova Scotia / New Brunswick

**Date:** 2026-09-27
**Research by:** GPT (browser investigation)
**Logged by:** Kiro
**Status:** ✅ COMPLETE — SOURCE FREEZE TRIGGERED

---

## Purpose

One targeted feasibility check on 4 provinces with unresolved source gaps.
Scope: does at least one free, legally reusable, machine-readable, automatable
individual-business dataset exist that can materially contribute to the discovery
or enrichment layer?

PEI and NL were permanently closed before this round (auth required / reuse prohibited).
This is the final research round. No further source discovery after this.

---

## Province 1 — Ontario

### New sources identified

| Source | Classification | Role |
|---|---|---|
| Community Small Business Investment Funds | PARTIALLY USABLE | ON specialized enrichment — registrant name, address, contact info, registration date, registration number/status |
| Tobacco Tax Registrant List | PARTIALLY USABLE | ON regulated sector — registrant name, address, modification date |
| Fuel and Gasoline Tax Registrant List | PARTIALLY USABLE | ON regulated sector — registrant name, address, authorization info |
| Dairy Distributors (non-shopkeepers) | PARTIALLY USABLE | ON regulated sector — business name, address, city, postal code, telephone, licence number |
| Provincially Licensed Dairy Plants | PARTIALLY USABLE | ON regulated sector — business name, address, city, postal code, telephone, licence number |
| Provincially Licensed Meat Plants | PARTIALLY USABLE | ON regulated sector — plant name, address, city, postal code, telephone, coordinates, animal-class info |

**Access:** Direct CSV + CKAN Data API. OGL-Ontario (commercial use permitted).
**Freshness:** Current — dairy plants Jul 16 2026, dairy distributors Jan 5 2026, tobacco Apr 21 2026, meat plants Aug 6 2026.
**Rate limits:** No material restriction on direct CSV/CKAN access.
**Record counts:** Small specialized datasets — not stated in catalogue metadata. These are regulated-sector populations, not Ontario business universe.

### Ontario conclusion

**PARTIAL — improved, not solved.**

These sources are valuable because several include phone/postal/contact information that
the existing general ON sources lack. However they represent specific regulated industries.
They do NOT provide a general Ontario business master.

Ontario general discovery gap: REMAINS UNRESOLVED.
Ontario enrichment layer: IMPROVED with 6 additional regulated-sector sources.

---

## Province 2 — Quebec

### Source A — Montréal Commercial Premises

| Attribute | Value |
|---|---|
| Source name | Locaux commerciaux et statuts d'occupation (Commercial Premises and Occupancy Status) |
| URL | donnees.montreal.ca |
| Geography | Montréal agglomeration / commercial areas across Montréal territory |
| Grain | Commercial establishment / local |
| Key fields | Establishment name, complete address, commercial usage/category, SCIAN (NAICS-equivalent), occupancy status/vacancy, arrondissement, neighbourhood, SDC, coordinates, multi-occupant/multi-use indicators |
| Record count | ~10.7 MB CSV (2025 dataset) — record count not stated in metadata |
| Access | Direct CSV, GeoJSON, GPKG, SHP — bulk openly published, no auth |
| Freshness | Annual collection — dataset updated December 15 2025; catalogue modified September 2026 |
| Licence | Creative Commons Attribution 4.0 / CC-BY Québec — commercial use permitted |
| Rate limits | None identified |
| Classification | IMPLEMENTABLE |
| Role | Major Montréal establishment discovery + NAICS enrichment source |

**Important limitation:** This is an establishment/local survey, not a legal-business registry.
The municipality explicitly notes some commercial premises may be missed and observed status
can change after collection. Do not treat as a live registry — treat as a discovery layer
snapshot with annual refresh.

**Why this matters:** First QC source with SCIAN (NAICS-equivalent) codes. Establishment names
+ addresses + commercial category + SCIAN. Fills a meaningful portion of the Montréal gap.

### Source B — Ville de Québec Permits

| Attribute | Value |
|---|---|
| Source name | Permis délivrés à la Ville de Québec |
| URL | donnees.quebec.ca |
| Geography | City of Québec |
| Grain | Municipal permit / event |
| Key fields | Permit number, issue date, permit-related spatial/property information |
| Record count | ~11 MB CSV |
| Access | Direct CSV, GeoJSON, SHP — public download |
| Freshness | Weekly update — coverage Jan 2020 to present; last updated Sep 20 2026 |
| Licence | CC-BY 4.0 — commercial use permitted |
| Rate limits | Données Québec web interface has bot protection but downloadable resource is public |
| Classification | PARTIALLY USABLE |
| Role | Québec City municipal event/change signal — not a general business master |

### Quebec conclusion

**PARTIAL — materially improved at municipal/establishment level.**

Montréal dataset is IMPLEMENTABLE and meaningful: establishment names, addresses, SCIAN,
occupancy status. This is the first validated QC source worth ingesting.

Québec City permits = event/change signal layer, not a business master.

Province-wide QC discovery gap: REMAINS UNRESOLVED (REQ blocked, no provincial master found).
Montréal + Québec City municipal coverage: IMPROVED.

---

## Province 3 — Nova Scotia

No qualifying individual-business discovery dataset found.

**Investigation scope:** Nova Scotia Open Data portal (data.novascotia.ca), Business and Economy category.
**What was found:** Aggregate/sector datasets — e.g. Tourism NS accommodation data reports room nights and
occupancy by region, not individual establishments.
**RJSC:** WAF not bypassed as instructed — remains deferred, not prohibited.

**Classification: NOT SUITABLE** for core discovery layer.
**NS gap: REMAINS. No change.**

---

## Province 4 — New Brunswick

No qualifying individual-business dataset found across Fredericton, Moncton, and Saint John.

**Investigation scope:** City of Fredericton open data, City of Moncton open data, City of Saint John open data.
**What was found:**
- Saint John: surfaced "Business Improvement Area" dataset — geographic boundary, not business records
- Moncton: portal active and machine-readable, no qualifying business dataset surfaced
- Fredericton: portal alive, no qualifying business licence/establishment dataset identified
- NB corporate registry bulk copying restriction: untouched as instructed

**Classification: NOT SUITABLE** for core discovery layer.
**NB gap: REMAINS. No change.**

---

## Final Province Status

| Province | Previous status | Post-VR20 status | Change |
|---|---|---|---|
| ON | ❌ MAJOR GAP | ⚠️ PARTIAL — enriched with 6 regulated-sector sources | Improved |
| QC | ❌ LARGEST GAP | ⚠️ PARTIAL — Montréal (IMPLEMENTABLE) + QC City (PARTIALLY USABLE) | Materially improved |
| NS | ❌ UNRESOLVED | ❌ GAP CONFIRMED — no open-data alternative found | No change |
| NB | ❌ UNRESOLVED | ❌ GAP CONFIRMED — no municipal open-data source found | No change |
| PE | ❌ NOT SUITABLE | ❌ CLOSED | Permanently closed |
| NL | ❌ NOT SUITABLE | ❌ CLOSED | Permanently closed |

---

## Architecture Impact

GPT conclusion: **SOURCE FREEZE IS NOW JUSTIFIED.**

The architecture should not create a fake Canada-wide uniform source. Instead:

```
Federal       → strong national identity backbone
Provincial    → specialized sources where available
Municipal     → business / establishment / licence / event signals
Enrichment    → phone / email / employees / contacts / NAICS
Entity Res.   → ONE canonical business entity
              + source-specific observations
              + provenance + events
```

Final province classifications for architecture:
- ON → PARTIAL (specialized regulated-sector enrichment only; no general master)
- QC → PARTIAL (Montréal establishment discovery + QC City event signal; no provincial master)
- NS → GAP (confirmed)
- NB → GAP (confirmed)

---

## Status: VR20 CLOSED — PHASE 2.6 COMPLETE — SOURCE LANDSCAPE FROZEN
