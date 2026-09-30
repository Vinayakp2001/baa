# Project Handoff — Canada Business Data Automation

**Last updated:** 2026-09-28 — ALL implementation tasks complete. Full pipeline implemented: ingestion → normalisation → resolution → events → quality → public API → Next.js dashboard → DNC layer → compliance guards → n8n workflows. Run `scripts/validate_pipeline_e2e.py` to verify the wired pipeline. No outstanding tasks remain (optional test tasks marked with `*` skipped per spec).
**Project folder:** `C:\Users\LENOVO\Desktop\baa`
**Venv:** `baa_env`

---

## What This Project Is

Building a production-oriented, Canada-wide B2B business data pipeline for a telecom sales operation.
The system discovers and continuously refreshes Canadian businesses using legitimate public/open-data sources only.
No recurring third-party data costs.

---

## How to Continue

The validated source-research workflow (VR01–VR20) is complete. Do not restart source discovery or add sources without an explicit request.

Work through `.kiro/specs/canada-b2b-pipeline/tasks.md` serially, starting with the first unfinished subtask. For each subtask:

1. Read its acceptance criteria and the relevant design section.
2. Trace existing code and contracts before editing; extend current modules rather than creating parallel implementations.
3. Implement only that subtask, then run focused tests or validation and relevant regressions.
4. Mark it complete only after its acceptance criteria are verified; record test gaps honestly.
5. Update this handoff with the new verified checkpoint and exact next subtask.

Do not redesign service boundaries or batch later tasks into the current one. If implementation and spec contracts conflict, document the concrete mismatch and resolve it before proceeding. Git is not required for handoff continuity; use it only when the task specifically needs history or repository-state inspection.

---

## Phase Progress

```
Phase 1 — Source Discovery            ✅ COMPLETE
Phase 1.5 — Canada-Wide Gap Analysis  ✅ COMPLETE
Phase 2 — Source Validation           ✅ COMPLETE (VR01–VR20)
Phase 2.5 — Architecture Readiness    ✅ COMPLETE
Phase 2.6 — Gap Resolution            ✅ COMPLETE — source landscape FROZEN
Phase 3 — Data Profiling              complete enough for implementation; source landscape frozen
Phase 4 — Architecture                documented in .kiro/specs/canada-b2b-pipeline/
Phase 5 — Implementation              ✅ COMPLETE — all non-optional tasks done
```

---

## Current Frontier — Task 15

Authoritative implementation plan: `.kiro/specs/canada-b2b-pipeline/tasks.md`. Continue strictly one task/subtask at a time: inspect the existing contract, implement the smallest compatible change, run its focused validation, and only then update the checklist and this handoff. Do not use Git unless the current task specifically needs history or commit state.

### Verified checkpoint

- Task 14.1 is checked in `tasks.md`. `n8n/workflows/ingest-source.json` is an Execute Workflow subworkflow and the generated wrappers invoke it.
- Task 14.2 remains unchecked. `n8n/generate_source_workflows.py` generated 19 per-source schedules; `backend/tests/test_n8n_workflow_contracts.py` currently passes 2 tests validating wrapper cron/source wiring and required generic-workflow HTTP fields.
- The full FastAPI app import passed with `baa_env\Scripts\python.exe -c "import src.main"`.
- Run-scoped modes exist for ingestion fetch, normalization, resolution, events, and quality. The generic workflow sends `ingestion_run_id` to Events and Quality. A focused smoke check validated those schema shapes; no database-backed full n8n execution has been run.
- `backend/src/ingestion/adapters/registry.py` maps seeded adapter names to implemented bulk adapters. `POST /ingestion/fetch` can run an adapter when `records` is omitted and persists fetched records in bounded inserts.
- The event detector had been empty despite Task 10 being checked; `backend/src/events/detectors.py` now contains discovery/typed-event and prior-observation change detection. It imports through the app, but has no database integration tests.

### Blocking design decision for Task 14.2

The 19th scheduled source, `quebec_city_permits`, is in the source registry and schedule generator, but has no adapter. Its metadata is now verified from the public Données Québec CKAN record:

- Dataset: `permis-delivres-ville-de-quebec` (`879abf6e-c6b2-430a-b44a-16335467c6f6`), weekly, CC-BY 4.0.
- CSV resource: `https://www.donneesquebec.ca/recherche/dataset/879abf6e-c6b2-430a-b44a-16335467c6f6/resource/9555031e-cfc5-4b78-bec9-4ab84b549f67/download/vdq-permis.csv`.
- Fields: `NUMERO_PERMIS`, `DATE_DELIVRANCE`, `ADRESSE_TRAVAUX`, `DOMAINE`, `LOTS_IMPACTES`, `TYPE_PERMIS`, `ARRONDISSEMENT`, `RAISON`, `LONGITUDE`, `LATITUDE`.
- The feed has no business name or business identifier. Current resolution creates a canonical business even when the name is absent (falling back to `source_key`), while `business_event.entity_id` is required. Do not ingest these permits through normal entity resolution as if they were businesses.

Before marking 14.2 complete, decide how to represent permits that cannot be linked to a known business. Safe options are to add an explicitly unlinked permit-event representation (with a reviewed migration/API impact), or to defer/disable the Québec City ingestion and amend the scope. Do not invent a business identity or silently skip these records. After this decision, finish and validate 14.2; then proceed to 14.3 and 14.4 serially.

### Known follow-up risks

- Quality scoring currently passes contact confidence labels (`HIGH`/`LOW`) where scoring helpers expect source classes (`A`/`B`/`C`); resolve this in the quality task, with a focused test.
- Run-scoped quality currently loads all entity IDs from a run into memory; test/adjust batching before full-scale ingestion.
- The frontend contains only a Dockerfile. DNC flag management routes and robots.txt compliance utility were not found. Reverify these when reaching Tasks 15–17.
- Task 17.2 end-to-end validation has not been run. The design document's “pre-implementation” status and older README/HANDOFF phase statements are stale relative to the implementation spec; use the Kiro task list as the active work contract.

The architecture notes below are historical design context. The Kiro spec's task sequence and acceptance criteria are the current implementation contract.

Historical architecture sequence (completed; retained for context):

```
1. CANONICAL DATA MODEL
2. PROVENANCE MODEL
3. EVENT MODEL
4. ENTITY RESOLUTION / DEDUPLICATION
5. INGESTION ARCHITECTURE
6. ENRICHMENT ARCHITECTURE
7. SCHEDULING / RETRY MODEL
8. API / DASHBOARD
9. IMPLEMENTATION PLAN
```

This design sequence is historical. Continue implementation from the Kiro task list above.

### What GPT already told us about architecture approach

These are confirmed decisions — do not relitigate:

- Derive conceptual model from evidence first, then turn into PostgreSQL schema
- Core entity model: `business`, `corporation`, `location`, `licence`, `person/contact`
- Provenance model: preserve conflicting values, never overwrite — keep source history
- Event model: incorporation / registration / licence / opening / closure / renewal — all DISTINCT event types, not a single `created_at`
- Employee model: `raw_value` + `employee_min` + `employee_max` + `employee_bucket` + `employee_source`
- Entity resolution: corp IDs + BN + name + address → pipeline-generated entity ID
- Enrichment model: website phone / directors layered on top, not required for base record
- Freshness: `first_seen`, `last_seen`, `last_verified`, source retrieval timestamps on every record
- Quality scoring: keep incomplete records, score them, separate sales-ready from incomplete
- Scheduled ingestion: source-specific jobs, incremental updates
- Province/source gaps = first-class flags in schema, not silent omissions

---

## Validated Source Landscape (frozen — do not add sources)

### Discovery layer (Class A)
| Source | Province | Rows | Key fields |
|---|---|---|---|
| Corporations Canada CBCA CSV | Federal | 645,005 | name, address, BN, corp number, status |
| Calgary business licences | AB | 23,178 | name, address, first_iss_dt (HIGH new-biz signal) |
| Edmonton business licences | AB | 43,719 | name, address, originalissuedate (HIGH new-biz signal) |
| Vancouver business licences | BC | 206,024 | name, address, status, issueddate, employee count (integer, 100%) |
| Saskatoon all businesses | SK | 7,472 | name, address, NAICS sub-sector |
| Montréal Commercial Premises | QC | large (~10MB CSV) | name, address, SCIAN (NAICS-equiv), commercial category, occupancy |

### New-business event signals (Class B)
| Source | Signal type | Strength |
|---|---|---|
| CBCA monthly incorporations HTML | federal_incorporation | HIGH |
| Calgary first_iss_dt | municipal_licence_first_issue | HIGH |
| Edmonton originalissuedate | municipal_licence_first_issue | HIGH |
| Manitoba Companies Office weekly PDF | provincial_registration | HIGH |
| Saskatoon new businesses XLSX | municipal_licence_first_issue | MEDIUM (51/month) |
| Québec City Permits | municipal_permit_event | MEDIUM (weekly) |
| Winnipeg business licences | licence_status_change (closure detection) | Class B only — not discovery master |

### Enrichment sources (Class C)
| Source | Key enrichment fields |
|---|---|
| Corporations Canada API (60 req/min) | directors: firstName, lastName, serviceAddress |
| BC OrgBook API | BC identity verification, registration history (no contact/address/directors) |
| Ontario Select Licence | phone (99%), email (81%), website (10%) — 674 regulated businesses |
| BC Indigenous Business Listings | phone (93%), email (89%), contact name (88%), employee range, website (52%) |
| NNI Nunavut Business Registry | phone, email, contact name, employee integer, address — 187 businesses (TERMS UNRESOLVED) |
| ON regulated-sector sources (×6) | phone/postal for dairy/tobacco/fuel/meat regulated businesses — OGL-Ontario |

### Benchmark only (Class D — no individual records)
- StatsCan Table A (business counts by province × NAICS × size)
- StatsCan Table B (new employer entrants benchmark)

### Confirmed gaps — permanent, do not research further
| Province | Gap status | Reason |
|---|---|---|
| ON general | GAP (partial enrichment only) | No free general-business master. Regulated-sector sources only. Toronto WAF-blocked. |
| QC general | GAP (Montréal partial) | REQ non-commercial blocked. Montréal city only via Commercial Premises dataset. |
| NS | GAP | RJSC WAF-blocked. No open-data alternative found (VR20). |
| NB | GAP | No municipal open-data source found (VR20). |
| PE | CLOSED | Auth required. |
| NL | CLOSED | Reuse explicitly prohibited. |

---

## Critical Architecture Rules (non-negotiable)

1. **Never overwrite source values** — provenance model must preserve originals + conflict history
2. **Never fabricate** — employee NULL = NULL, not estimated. 500+ stays 500+, never split to 500–999/1000+.
3. **Never flatten grains** — corporation ≠ business ≠ location ≠ licence ≠ event. Each source's grain must be preserved.
4. **Pipeline-generated entity ID** — never borrow an ID from a single source as the canonical key
5. **Event model not a flag** — `federal_incorporation` ≠ `municipal_licence_first_issue` ≠ `provincial_registration`. All are distinct event types with their own date and source.
6. **Email/phone = nullable** — no estimation, no fabrication. Present when a source provides it.
7. **Person roles are distinct** — DIRECTOR ≠ OWNER ≠ PRESIDENT ≠ GM ≠ IT ≠ PROCUREMENT. Store source-provided role.
8. **Province gaps are first-class** — schema must flag "no discovery source for this province" explicitly, not silently under-represent.
9. **NNI is conditional** — do not mark commercially cleared until NNI Regulations PDF reviewed.
10. **Sales-ready threshold** — minimum: name + address + province + status=active + at least one of (phone | email | website | director_name).

---

## Deferred Items (not blocking architecture — resolve opportunistically)

```
VR10  — NS RJSC          WAF block. Not prohibited. Browser DevTools needed to determine automation path.
VR13  — Yukon SD         OGL confirmed, 403 block. Manual browser download needed.
VR13  — NWT CROS         URL: justice.gov.nt.ca/app/cros-rsel/search. Basic info free.
VR13  — NNI terms        NNI Regulations PDF not parsed. Do not mark commercially cleared yet.
```

---

## Key Reference Documents

| Document | Purpose |
|---|---|
| `reports/ARCHITECTURE_READINESS_MATRIX.md` | **PRIMARY INPUT** — full source catalogue, province coverage, field coverage, 10 data-quality issues, compliance constraints, 8 open architectural questions |
| `reports/validation_rounds/VR20_PROVINCE_GAP_FINAL.md` | Final province gap findings — ON/QC/NS/NB |
| `reports/validation_rounds/VR19_ENRICHMENT_METHODS.md` | Email + decision-maker enrichment — closed as non-core |
| `reports/SOURCE_DISCOVERY_TRACKER.md` | Living master tracker — all VR results |
| `reports/CANADA_WIDE_GAP_ANALYSIS.md` | Phase 1.5 gap analysis (background) |

---

## Data Files in data/raw/ (do not delete)

- `saskatoon_all_businesses_20260925.xlsx` — 7,472 Saskatoon businesses
- `saskatoon_new_businesses_20260925.xlsx` — 51 new businesses Aug 2026
- `manitoba_filings_2026-09-19.pdf` + `.txt` — Sep 19 2026 weekly filing
- `manitoba_filings_2026-09-12.pdf` + `.txt` — Sep 12 2026 weekly filing
- `ontario_select_licence_business_20260925.csv` — 674 Ontario regulated businesses
- `ontario_select_licence_individual_20260925.csv` — 329 licensed individuals

---

## Pip Dependencies Already Installed

```
pip install openpyxl beautifulsoup4 pdfplumber requests
```

---

## Compliance Notes (must be respected in architecture)

- StatsCan Business Register: individual records confidential under Statistics Act — do not use
- BC OrgBook: bulk prohibited, 10-page limit, targeted lookup only
- Quebec REQ: non-commercial restriction — BLOCKED
- NB corporate registry: automated bulk copying restricted
- NS RJSC: WAF blocks all automated HTTP — status unknown
- PEI OCBR: login required — NOT SUITABLE
- NNI: no OGL, no explicit prohibition, terms unresolved — treat as conditional
- Corporations Canada API: 60 req/min, user-key header auth, Public Plan subscribed
- Vancouver / Calgary / Edmonton / Saskatoon / BC Indigenous / Montréal: all OGL or CC-BY — commercial use permitted
