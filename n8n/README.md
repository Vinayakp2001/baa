# n8n Workflow Configuration

All workflow JSON files in `n8n/workflows/` are importable via the n8n UI
(**Settings → Import workflow**) or the n8n REST API.

## Workflows

### Ingestion pipeline

| File | Trigger | Purpose |
|------|---------|---------|
| `ingest-source.json` | Called by sub-workflow | Generic parameterised pipeline: start → fetch → normalise → resolve → events/detect → quality/score → complete |
| `ingest-source-error-handler.json` | n8n error trigger | Calls POST /ingestion/fail, then retries with exponential backoff: 1 min → 5 min → 30 min → 1 h (max 4 retries) |
| `ingest-calgary.json` | `0 6 * * *` daily | Calgary business licences |
| `ingest-edmonton.json` | `0 6 * * *` daily | Edmonton business licences |
| `ingest-vancouver.json` | `0 5 * * *` daily | Vancouver business licences |
| `ingest-winnipeg.json` | `0 7 * * *` daily | Winnipeg business licences |
| `ingest-corporations-canada-csv.json` | `0 4 * * 1` weekly | Corporations Canada CSV |
| `ingest-corporations-canada-html.json` | `0 8 1 * *` monthly | Corporations Canada monthly HTML |
| `ingest-manitoba-weekly-pdf.json` | `0 9 * * 5` weekly | Manitoba weekly PDF filings |
| `ingest-saskatoon-all-biz.json` | `0 8 * * 1` weekly | Saskatoon all businesses |
| `ingest-saskatoon-new-biz.json` | `0 8 * * 1` weekly | Saskatoon new businesses |
| `ingest-ontario-select-licence.json` | `0 8 1 * *` monthly | Ontario Select Licence |
| `ingest-ontario-dairy.json` | `0 8 1 * *` monthly | Ontario dairy distributors |
| `ingest-ontario-dairy-plants.json` | `0 8 1 * *` monthly | Ontario dairy plants |
| `ingest-ontario-meat.json` | `0 8 1 * *` monthly | Ontario meat processors |
| `ingest-ontario-tobacco.json` | `0 8 1 * *` monthly | Ontario tobacco dealers |
| `ingest-ontario-fuel.json` | `0 8 1 * *` monthly | Ontario fuel dealers |
| `ingest-ontario-csbif.json` | `0 8 1 * *` monthly | Ontario CSBIF |
| `ingest-bc-indigenous.json` | `0 8 1 * *` monthly | BC Indigenous business listings |
| `ingest-quebec-city-permits.json` | `0 9 * * 5` weekly | Québec City permits |
| `ingest-montreal-commercial.json` | `0 8 1 1 *` annually | Montréal commercial premises |

### Enrichment (event-triggered)

| File | Poll interval | Purpose |
|------|--------------|---------|
| `enrich-directors.json` | Every 15 min | Polls `business_event` for `FEDERAL_INCORPORATION` events without enrichment, batches corp_numbers, calls `POST /enrich/directors` |
| `enrich-orgbook.json` | Every 20 min | Polls `business` for BC entities with no OrgBook `legal_name` observation, calls `POST /enrich/orgbook` per entity |

## Setup

### Required n8n credentials

Create one **Postgres** credential named **`Pipeline Postgres`** pointing at the same
database as the API (`DB_POSTGRESDB_*` env vars in docker-compose).

### Required environment variable

Set `API_BASE_URL` in the n8n container environment (already in `docker-compose.yml`):

```
API_BASE_URL=http://api:8000
```

### Import order

1. `ingest-source-error-handler` — must exist before the main workflow references it
2. `ingest-source` — generic sub-workflow
3. All per-source `ingest-*.json` files
4. `enrich-directors` and `enrich-orgbook`

### Regenerating per-source workflows

If you add a new source to the registry, add an entry to `SOURCES` in
`n8n/generate_source_workflows.py` and run:

```bash
python n8n/generate_source_workflows.py
```
