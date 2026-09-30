# Research Round 03 — BC OrgBook

**Date:** 2026-09-25
**Source:** GPT research pass — OrgBook BC public service, API documentation, FAQ, BC Government terms
**Status:** Research complete — API testing not yet done

---

## TL;DR

OrgBook BC is a legitimate BC government service with a free public API and ~30-minute freshness.
**Major correction from previous assumption:** bulk downloading / full-database scraping is explicitly prohibited.
OrgBook's real role for this project is **targeted identity verification and enrichment** — not a BC discovery/ingestion feed.
Address, phone, email, directors, and ownership are also explicitly NOT available from this source.

---

## 1. What OrgBook BC Actually Is

- Public directory operated by BC Ministry of Citizens' Services
- Contains organizations legally registered in BC
- Information issued by authorized credential issuers (BC Registries + some licensing/permit authorities)
- Supports search by: organization/legal name, CRA Business Number, BC Registries ID
- Uses Verifiable Credentials — data is digitally signed by issuing organization (strong provenance)

---

## 2. Bulk Download / Full Scraping — EXPLICITLY PROHIBITED

This is the most important finding and a correction to our earlier tracker assumption.

OrgBook FAQ explicitly states:
- Bulk downloading of the database is **not permitted**
- Designed for individual entity lookups and application-embedded search
- Website has a **10-page search-result limit** specifically to prevent database scraping
- Scraping the full database is against the Terms of Service

**Previous tracker assumption (now corrected):**
> "OrgBook API → structured JSON → normalization → business master"

**Corrected role:**
> Use OrgBook as targeted verification/enrichment when we already have a candidate business from another source.

These are materially different roles.

---

## 3. API — Public, No Auth Required for Read

- API v4 is recommended for production integrations
- Read access requires no authentication
- Subject to BC Government Terms of Use
- High-volume requests should be throttled
- Open-source client and API documentation available via bcgov GitHub repos

---

## 4. Confirmed Fields

| Field | Available |
| --- | --- |
| Legal name | ✅ |
| DBA / assumed / translated name | ✅ |
| BC Registries ID | ✅ |
| CRA Business Number | Sometimes |
| Entity type (Corp, SP, etc.) | ✅ |
| Registration status | ✅ |
| Registration date | ✅ (where credential provides it) |
| Registration timeline / history | ✅ |
| Selected licences / permit credentials | ✅ |
| Address | ❌ — legislatively prohibited |
| Phone | ❌ |
| Email | ❌ |
| Website | ❌ |
| Directors | ❌ — explicitly excluded |
| Ownership / beneficial owner | ❌ — explicitly excluded |
| Employee count | ❌ |
| NAICS | ❌ |

**Address/contact restriction:** OrgBook FAQ explicitly states it is not permitted to display address or contact information due to legislative restrictions. Directors and ownership are also deliberately excluded.

---

## 5. Registration Credential — Rich Timeline Data

The API's registration credential can contain:
- Entity status, entity type, home jurisdiction, registered jurisdiction
- Registration ID, registration date, effective date, expiry date
- Status-effective date, status/reason information
- Name, assumed/DBA name, translated name, name-effective date

The credential-set endpoint returns credentials with:
- Creation timestamp, update timestamp
- First/last effective date
- Individual credential effective dates
- Revoked status and revoked dates

This allows constructing a **timeline of registration events** for any organization — useful for:
- Detecting registration / name changes / dissolution
- Distinguishing current entity from historical entity
- Identifying lifecycle events (incorporation, name change, status change)

**Important nuance:**
```
recent registration event ≠ newly opened operating business
```
A corporation can exist before operating; a company can register a DBA; historical entities have multiple events.
Treat registration events as lifecycle signals, not automatic "new customer prospect."

---

## 6. Freshness

OrgBook data updated within approximately **30 minutes** of changes at BC Registries.

This is one of the strongest freshness characteristics found so far:
- ODBus v1: historical (~2022)
- Ontario Select Licence: monthly
- Corporations Canada bulk: daily
- OrgBook: ~30 minutes after registry change

However: "OrgBook reflects BC Registry changes quickly" ≠ "OrgBook is a complete real-time BC business enumeration feed."
The former is documented. The latter is not supported and bulk enumeration is prohibited.

---

## 7. Sole Proprietorships Are Included

OrgBook includes entity types beyond corporations:
- `entity_type = SP` (Sole Proprietorship) confirmed in API documentation examples
- Sole proprietors appear in OrgBook when registered with BC Registries

This is useful because Corporations Canada primarily covers CBCA corporations, while OrgBook captures different BC entity types.

---

## 8. Historical Entities Are Retained

- OrgBook includes **all entities ever registered** with BC Registries — both active and historical
- Historical entities findable via "Show Archived" / `inactive` API parameter
- Valuable for: dissolution detection, name-change history, avoiding treating old companies as active

---

## 9. Licence and Permit Credentials — Additional Layer

OrgBook is not limited to registration credentials. Different authorized issuers can publish credentials:

```
Organization
    ├── Registration credential (BC Registries)
    ├── Business Number credential
    ├── Licence credential (various issuers)
    ├── Permit credential (various issuers)
    └── Other issuer credentials
```

The `/v4/issuer` endpoint lists all credential issuers.
The `/v4/credential-type` endpoint lists all credential types with schema, attributes, labels, and last issue date.

**Research implication:** Before researching a separate BC licence dataset, check whether OrgBook already exposes it as a credential type from an authorized issuer — this could eliminate redundant source research.

---

## 10. Licensing / Terms

- Data provided under **BC Government Access Only Data Terms and Conditions**
- NOT simply "Open Government Licence"
- Free public API; no authentication for read
- Bulk extraction explicitly prohibited
- High-volume requests should be throttled

Do not label this as "OGL/open data" in the tracker — it is a more restricted use classification.

---

## 11. Comparison with Corporations Canada

| Capability | Corporations Canada | BC OrgBook |
| --- | --- | --- |
| Jurisdiction | Federal | BC |
| Bulk dataset | ✅ | ❌ prohibited |
| API | ✅ | ✅ |
| API auth | Public plan (free) | None for read |
| Legal name | ✅ | ✅ |
| Alternate / DBA names | ✅ history via API | ✅ |
| Business number | ✅ | Sometimes |
| Registration ID | Corp number | BC Registries ID |
| Status | ✅ | ✅ |
| Registration / activity history | ✅ | ✅ |
| Address | ✅ | ❌ |
| Phone / email / website | ❌ | ❌ |
| Directors | ✅ (API) | ❌ |
| ISC / ownership | ✅ (CBCA) | ❌ |
| Licences / permits | ❌ | ✅ selected |
| Employee count / NAICS | ❌ | ❌ |
| Bulk enumeration | ✅ | Prohibited |
| Freshness | Daily bulk / real-time API | ~30 min after registry |

---

## 12. Confirmed Corrections to Previous Tracker

| Previous assumption | Corrected finding |
| --- | --- |
| OrgBook could be a BC master discovery source via API | ❌ Bulk enumeration explicitly prohibited |
| OrgBook may contain addresses / contact info | ❌ FAQ explicitly says these fields cannot be displayed (legislative restriction) |
| OrgBook useful for directors / decision-makers | ❌ Directors and ownership deliberately excluded |

---

## 13. Legitimate Use Case for This Project

**Targeted verification pattern:**
```
Candidate business from another source
    (name, city, province, postal code)
            ↓
Query OrgBook by name or CRA BN or BC Registry ID
            ↓
Retrieve: legal name, DBA, entity type, status,
          registration date, timeline, selected licences
            ↓
Confirm / enrich identity layer
```

This is much more defensible than trying to enumerate all BC organizations.

---

## 14. Confirmed Source Profile

| Dimension | Finding |
| --- | --- |
| Source | BC OrgBook |
| Operator | BC Ministry of Citizens' Services |
| Jurisdiction | British Columbia |
| Entity types | Corporations, sole proprietors, other registered entities |
| Active entities | Yes |
| Historical entities | Yes |
| Legal name + DBA | Yes |
| Registration ID | Yes |
| CRA BN | Sometimes |
| Status + timeline | Yes |
| Selected licences/permits | Yes |
| Address / phone / email / website | No — legislatively restricted |
| Directors / ownership | No — deliberately excluded |
| Employees / NAICS | No |
| API | Yes — v4, no auth for read |
| Bulk download | Prohibited |
| Freshness | ~30 min after BC Registry changes |
| Cost | Free |
| Terms | BC Government Terms / Access Only Data Terms |
| Bulk scraping | Against ToS |
| Best use | Targeted identity/status verification of known candidates |

---

## 15. Next Actions

- [ ] Test OrgBook API v4 — validate actual response fields, credential types available, issuer list
- [ ] Check `/v4/credential-type` — what licence/permit types are already in OrgBook (may eliminate need to research separate BC licence sources)
- [ ] Confirm CRA BN availability per entity type
- [ ] Check whether a public notification/change feed exists for production integration (not confirmed yet)
- [ ] Verify BC Government Terms of Use specifically for commercial pipeline use
