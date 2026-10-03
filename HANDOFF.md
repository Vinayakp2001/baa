# Project Handoff — Canada Business Data Automation

**Last updated:** 2026-10-03 — Edmonton COMPLETED. Vancouver resolution complete; events detection retry is running, and quality scoring/completion remain unverified.
**Project folder:** `C:\Users\LENOVO\Desktop\baa`
**Venv:** `baa_env`
**Repository:** `https://github.com/Vinayakp2001/baa` (private, branch `main`)

---

## What This Project Is

A production-oriented, Canada-wide B2B business data pipeline for a telecom sales operation.
Discovers and continuously refreshes Canadian businesses from legitimate public/open-data sources only.
No recurring third-party data costs.

---

## Current State (2026-10-03 checkpoint)

### Running stack

| Service | Status | Notes |
|---|---|---|
| PostgreSQL | healthy | host port 5433 (5432 owned by separate `cpilot` project) |
| API (FastAPI) | running | `/healthz`, `/api/docs`, `/api/businesses` → 200 |
| Frontend (Next.js 15.5.24) | running | `http://localhost` → dashboard |
| n8n 1.45.1 | running | `http://localhost/n8n/` → 200 |
| nginx 1.27-alpine | running | 900s proxy timeout; `/healthz` proxied directly to FastAPI |

- Migrations: `007 (head)` — indexes 006 and 007 applied (postal prefix + raw address indexes for matcher performance)
- `.env` is local, Git-ignored — never commit it
- `cpilot` project left untouched

### Source import progress

| Source | Status | Records | Entities | Notes |
|---|---|---|---|---|
| Calgary | ✅ COMPLETED | 23,141 | ~23k | province=NULL known gap |
| Edmonton | ✅ COMPLETED | 43,722 | ~40k | run `01b96158` |
| Vancouver | ⏳ IN PROGRESS | 206,242 | 192,656 linked | run `6da6634d` — events retry running; quality unverified |
| Saskatoon | ❌ Not started | - | - | |
| Corps Canada CSV | ❌ Not started | - | - | |

### Vancouver run details (run `6da6634d-8c99-4284-821f-56b894d29537`)

- Fetch: ✅ 206,242 records
- Normalise: ✅ 206,242 (192,656 got a name after Vancouver field mapping fix)
- Resolve: ✅ complete — 122,177 NEW, 70,474 CANDIDATE, 5 MATCHED, 13,586 UNRESOLVED, 0 PENDING. The 13,586 unresolved payloads have no supported business name or identifier.
- Events detect: ⏳ latest retry started 2026-10-03T08:11Z; prior completed pass created 47,252 events across 192,651 entities. The latest retry had no completion log at 2026-10-03 14:18 UTC+5:30 and still had an open transaction.
- Quality score: ⏳ unverified — a separate long-lived transaction (about 17 hours at the last check) was active on business identifiers; no quality completion log was found. Do not start another scoring request until this session is understood.
- Complete: ❌ pending

**To resume after events and quality finish:**
```powershell
# Check if events done:
docker compose logs --follow --no-log-prefix api 2>$null | Select-String -Pattern "complete|start|error"

# Once the quality scoring request has completed and its results are verified:
python scripts/resume_run.py --run-id 6da6634d-8c99-4284-821f-56b894d29537 --source-key vancouver --from-stage complete
```

**If PC slept mid-process and events/quality need to be re-run:**
```powershell
# Check logs for where it stopped, then resume from that stage:
python scripts/resume_run.py --run-id 6da6634d-8c99-4284-821f-56b894d29537 --source-key vancouver --from-stage events
# or --from-stage quality, or --from-stage complete
```

### Key fixes made this session

- Vancouver normaliser fix: `businessname` + `businesstradename` field aliases added to `normaliser.py`
- Resolver fix: `scalar_one_or_none()` → `scalars().first()` in `routes.py` (Vancouver has duplicate source_record_ids)
- Address safeguards: province/postal truncation added to `address.py`
- Resolver performance: commits every 1,000 rows, skips observation rewrites for new entities
- `scripts/resume_run.py` — new script, supports stages: `normalise | resolve | events | quality | complete`
- Migrations 006 and 007 applied (matcher lookup indexes)

### Known database state

- ~63k entities total (Calgary + Edmonton + partial Vancouver)
- Vancouver: 206,242 source records stored; resolution counts are 122,177 NEW, 70,474 CANDIDATE, 5 MATCHED, and 13,586 UNRESOLVED (the latter lack supported business identity). Events retry and quality status remain unverified. `run_status=COMPLETED` is stale from an earlier pass and does not prove the later stages finished.
- 4 failed historical runs (harmless, retain for audit)

---

## What To Do Next (operational mode)

The Kiro spec implementation is complete. The pipeline is validated end-to-end. The project is in operational mode — importing real data.

### Priority next actions

1. **Finish Vancouver** — monitor logs, then run `--from-stage complete` (see Vancouver run details above)
2. **Import remaining Class A sources** after Vancouver is done:
   ```powershell
   python scripts/validate_pipeline_e2e.py --source-key saskatoon_all_biz
   python scripts/validate_pipeline_e2e.py --source-key corporations_canada_csv
   # montreal — no limit needed, uses pagination
   python scripts/validate_pipeline_e2e.py --source-key montreal_commercial
   ```
   These are full imports (no --limit), will take several minutes each.

2. **Fix n8n UI (optional — for scheduled cron jobs)** — see the n8n blocker section below.

3. **Set CORPS_CANADA_API_KEY in .env** to enable director enrichment workflows.

---

## n8n Scheduling Status

- n8n 1.45.1 is routed under `/n8n/` using `N8N_PATH=/n8n/`; the UI assets load and unauthenticated visits redirect to sign-in.
- The 23 workflow definitions are pushed to the n8n database. `scripts/push_workflows.ps1` updates the existing workflow IDs from `n8n/workflows/`; it does not activate them.
- `Pipeline Postgres` (`pipeline-postgres`) is stored in n8n and was verified to connect to the `baa` database from the n8n container.
- `API_BASE_URL=http://api:8000` is configured for the n8n container. Keep this internal Docker address unchanged.
- Workflows are inactive. Scheduled automation is not yet running; next verify the workflow nodes in the signed-in UI and activate only after manual tests pass.

### Immediate options

1. **Import remaining Class A sources via the API** — use `python scripts/validate_pipeline_e2e.py --source-key <key>` one source at a time. These are full imports when `--limit` is omitted; the 200-row Calgary run below was a bounded validation, not another full import.
2. **Finish n8n scheduling setup** — sign in at `http://localhost/n8n/`, verify workflow nodes and the Postgres credential, then manually test before activating schedules.
3. **Set `CORPS_CANADA_API_KEY` in `.env`** and restart the `api` container to enable director enrichment.

### Open issues / known gaps

- Calgary Socrata rows omit province. Existing Calgary-linked entities were patched to `AB` and re-scored after the full import; newly discovered rows may still normalize with `province=NULL` until the source-specific normalization gap is handled.
- NNI terms still unresolved — do not enable the NNI n8n workflow until the NNI Regulations PDF is reviewed and `source.terms_status` is updated to `CLEARED`.
- Québec City Permits source (`quebec_city_permits`) has an adapter and n8n workflow but produces event-grain records with no business identity. These records remain `UNRESOLVED` in the source layer — that is by design and correct per the spec. Do not re-architect this; it is not broken.

---

## How to Restart / Resume Work

### Start the stack

```powershell
docker compose up -d
```

PostgreSQL data volume is persistent. Migrations don't need to re-run.

### Run the smoke test

```powershell
python scripts/smoke_test_pipeline.py --limit 200
```

### Run Alembic migrations (if a new migration is added)

```powershell
Push-Location backend
$env:DATABASE_URL = "postgresql+asyncpg://baa:<password>@localhost:5433/baa"
alembic upgrade head
Pop-Location
```

### Rebuild API or frontend after code changes

```powershell
docker compose build api   # or frontend
docker compose up -d api   # or frontend
```

### Import a source manually (without n8n)

```powershell
python scripts/validate_pipeline_e2e.py --source-key calgary
# Without --limit, this fetches the full source according to its incremental cursor.
# Use --limit 200 for a bounded validation that bypasses the cursor.
```

---

## Phase Progress

```
Phase 1 — Source Discovery            ✅ COMPLETE
Phase 1.5 — Canada-Wide Gap Analysis  ✅ COMPLETE
Phase 2 — Source Validation           ✅ COMPLETE (VR01–VR20)
Phase 2.5 — Architecture Readiness    ✅ COMPLETE
Phase 2.6 — Gap Resolution            ✅ COMPLETE — source landscape FROZEN
Phase 3 — Data Profiling              ✅ complete enough; source landscape frozen
Phase 4 — Architecture                ✅ documented in .kiro/specs/canada-b2b-pipeline/
Phase 5 — Implementation              ✅ COMPLETE — all non-optional tasks done, smoke test passed
Phase 6 — Operations                  IN PROGRESS — stack running, importing real data
```

---

## Architecture Rules (non-negotiable)

1. Never overwrite source values — provenance model preserves originals + conflict history
2. Never fabricate — employee NULL = NULL, not estimated. 500+ stays 500+.
3. Never flatten grains — corporation ≠ licence ≠ event. Each source's grain is preserved.
4. Pipeline-generated entity ID — never borrow an ID from a single source as the canonical key
5. Event model not a flag — `federal_incorporation` ≠ `municipal_licence_first_issue` ≠ `provincial_registration`
6. Email/phone = nullable — no estimation, no fabrication
7. Person roles are distinct — DIRECTOR ≠ OWNER ≠ PRESIDENT
8. Province gaps are first-class — flagged in schema, not silently under-represented
9. NNI is conditional — not cleared until NNI Regulations PDF reviewed
10. Sales-ready threshold — name + address + province + status=active + at least one of (phone | email | website | director_name)

---

## Validated Source Landscape (FROZEN — do not add sources)

### Discovery layer (Class A)

| Source | Province | Rows | Key fields |
|---|---|---|---|
| Corporations Canada CBCA CSV | Federal | 645,005 | name, address, BN, corp number, status |
| Calgary business licences | AB | ~23k | name, address, first_iss_dt — Socrata `vdjc-pybd` |
| Edmonton business licences | AB | ~43k | name, address, originalissuedate |
| Vancouver business licences | BC | ~206k | name, address, status, issueddate, employee count |
| Saskatoon all businesses | SK | 7,472 | name, address, NAICS sub-sector |
| Montréal Commercial Premises | QC | large | name, address, SCIAN, occupancy |

### New-business event signals (Class B)

| Source | Signal type |
|---|---|
| CBCA monthly incorporations HTML | FEDERAL_INCORPORATION |
| Calgary first_iss_dt | MUNICIPAL_LICENCE_FIRST_ISSUE |
| Edmonton originalissuedate | MUNICIPAL_LICENCE_FIRST_ISSUE |
| Manitoba Companies Office weekly PDF | PROVINCIAL_REGISTRATION |
| Saskatoon new businesses XLSX | MUNICIPAL_LICENCE_FIRST_ISSUE |
| Québec City Permits | MUNICIPAL_PERMIT_ISSUED (event-grain only, no business identity) |
| Winnipeg business licences | LICENCE_STATUS_CHANGE (closure detection only — not a discovery master) |

### Enrichment sources (Class C)

| Source | Key fields |
|---|---|
| Corporations Canada API (60 req/min, needs API key) | directors |
| BC OrgBook API (targeted lookup only) | legal_name, status, registration_date |
| Ontario Select Licence | phone, email, website |
| BC Indigenous Business Listings | phone, email, contact name, employee range |
| NNI Nunavut (TERMS UNRESOLVED) | phone, email, contact name, employee integer |
| Ontario regulated sector ×6 | phone/postal for dairy/tobacco/fuel/meat |

### Benchmark only (Class D — no individual records ever)

- StatsCan business counts by province × NAICS × size

### Confirmed gaps (permanent — do not research further)

| Province | Status | Reason |
|---|---|---|
| ON general | GAP | No free general-business master; regulated-sector only |
| QC general | GAP | REQ non-commercial blocked; Montréal only |
| NS | GAP | RJSC WAF-blocked |
| NB | GAP | No open-data source |
| PE | CLOSED | Auth required |
| NL | CLOSED | Reuse explicitly prohibited |

---

## Compliance Notes

- StatsCan Business Register: individual records confidential — do not use
- BC OrgBook: bulk enumeration prohibited, targeted lookup only
- NNI: terms unresolved — do not enable until cleared
- Corporations Canada API: 60 req/min, user-key header auth, Public Plan
- Calgary / Edmonton / Vancouver / Saskatoon / BC Indigenous / Montréal: OGL or CC-BY — commercial use permitted

---

## Repository and Environment

- `.kiro/` and `.vscode/` are local workspace folders — intentionally ignored, not in GitHub
- `.env` credentials are local and never pushed — use `.env.example` as the template
- Frontend lockfile was generated in a Linux Docker container so optional dependencies for Linux builds are included
- Next.js 15 App Router: `params` and `searchParams` must be awaited in page components

---

## Key Reference Documents

| Document | Purpose |
|---|---|
| `reports/ARCHITECTURE_READINESS_MATRIX.md` | Full source catalogue, province coverage, compliance constraints |
| `reports/validation_rounds/VR20_PROVINCE_GAP_FINAL.md` | Final province gap findings |
| `reports/SOURCE_DISCOVERY_TRACKER.md` | Master tracker for all VR results |
| `.kiro/specs/canada-b2b-pipeline/tasks.md` | Authoritative implementation checklist (all non-optional tasks complete) |
| `scripts/smoke_test_pipeline.py` | Bounded pipeline validation (200 Calgary rows) |
| `scripts/validate_pipeline_e2e.py` | Full import validation (use when ready for full data load) |

---

## Data Files in data/raw/ (do not delete)

- `saskatoon_all_businesses_20260925.xlsx`
- `saskatoon_new_businesses_20260925.xlsx`
- `manitoba_filings_2026-09-19.pdf` + `.txt`
- `manitoba_filings_2026-09-12.pdf` + `.txt`
- `ontario_select_licence_business_20260925.csv`
- `ontario_select_licence_individual_20260925.csv`

---

## Pip Dependencies Already Installed (baa_env)

```
pip install openpyxl beautifulsoup4 pdfplumber requests
```

---

## Deferred Items (not blocking — resolve opportunistically)

- NS RJSC: WAF block, not prohibited — browser DevTools needed
- Yukon SD: OGL confirmed, 403 block — manual browser download needed
- NWT CROS: `justice.gov.nt.ca/app/cros-rsel/search` — basic info free
- NNI: regulations PDF not reviewed — do not mark cleared yet
