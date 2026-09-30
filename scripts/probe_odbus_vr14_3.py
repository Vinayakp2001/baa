"""
VR14.3 — ODBus High-Value Source Deep Validation
Resolve actual data endpoints for Tier A sources confirmed reachable in VR14.2.
Sources: New Westminster (new this year), Calgary, Edmonton, Vancouver, Winnipeg,
         Victoria (current year), Delta (moved), Surrey (moved), Kelowna (400),
         BC Licensed Establishments + Wineries (current resource IDs)
Output: reports/validation_rounds/VR14_3_ODBUS_HIGH_VALUE_SOURCES.json
        reports/validation_rounds/VR14_3_ODBUS_HIGH_VALUE_SOURCES.md
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import csv
import io
import ssl
import time
import re

OUTPUT_JSON = "reports/validation_rounds/VR14_3_ODBUS_HIGH_VALUE_SOURCES.json"
OUTPUT_MD   = "reports/validation_rounds/VR14_3_ODBUS_HIGH_VALUE_SOURCES.md"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/csv, text/html, */*",
}

# ---------------------------------------------------------------------------
# Socrata sources — use the standard export API:
#   /api/views/{4x4}/rows.csv?accessType=DOWNLOAD
# and the metadata API:
#   /api/views/{4x4}.json  (gives rowsUpdatedAt, columns, row count)
# ---------------------------------------------------------------------------
SOCRATA_SOURCES = [
    {
        "source_id": 2,
        "city": "Calgary",
        "province": "AB",
        "name": "Calgary Business Licences",
        "portal": "https://data.calgary.ca",
        "four_by_four": "vdjc-pybd",
        "licence_url": "https://data.calgary.ca/stories/s/Open-Calgary-Terms-of-Use/u45n-7awa",
    },
    {
        "source_id": 4,
        "city": "Edmonton",
        "province": "AB",
        "name": "City of Edmonton - Business Licences",
        "portal": "https://data.edmonton.ca",
        "four_by_four": "qhi4-bdpu",
        "licence_url": "https://data.edmonton.ca/stories/s/City-of-Edmonton-Open-Data-Terms-of-Use/msh8-if28/",
    },
    {
        "source_id": 28,
        "city": "Vancouver",
        "province": "BC",
        "name": "Business licences",
        "portal": "https://opendata.vancouver.ca",
        "four_by_four": None,  # Vancouver uses OpenDataSoft — different API
        "licence_url": "https://opendata.vancouver.ca/pages/licence/",
        "api_type": "opendatasoft",
        "dataset_id": "business-licences",
    },
    {
        "source_id": 33,
        "city": "Winnipeg",
        "province": "MB",
        "name": "Business Licenses",
        "portal": "https://data.winnipeg.ca",
        "four_by_four": "d5k3-sfzx",
        "licence_url": "https://data.winnipeg.ca/open-data-licence",
    },
]

# ---------------------------------------------------------------------------
# New Westminster — ArcGIS Hub / opendata.newwestcity.ca
# These use ArcGIS FeatureServer or Hub download
# ---------------------------------------------------------------------------
NEW_WEST_SOURCES = [
    {
        "source_id": 19,
        "city": "New Westminster",
        "province": "BC",
        "name": "Business Licenses (New this Year)",
        "hub_url": "https://opendata.newwestcity.ca/datasets/business-licenses-new-this-year",
        "api_url": "https://opendata.newwestcity.ca/datasets/business-licenses-new-this-year.geojson",
        "csv_url": "https://opendata.newwestcity.ca/datasets/business-licenses-new-this-year/explore",
        "licence_url": "http://opendata.newwestcity.ca/licence",
    },
    {
        "source_id": 18,
        "city": "New Westminster",
        "province": "BC",
        "name": "Business Licenses (All)",
        "hub_url": "https://opendata.newwestcity.ca/datasets/business-licenses-all",
        "api_url": "https://opendata.newwestcity.ca/datasets/business-licenses-all.geojson",
        "csv_url": "https://opendata.newwestcity.ca/datasets/business-licenses-all/explore",
        "licence_url": "http://opendata.newwestcity.ca/licence",
    },
]

# ---------------------------------------------------------------------------
# Victoria — ArcGIS Hub
# ---------------------------------------------------------------------------
VICTORIA_SOURCES = [
    {
        "source_id": 32,
        "city": "Victoria",
        "province": "BC",
        "name": "Business Licences - Current Year",
        "hub_url": "https://opendata.victoria.ca/datasets/business-licences-current-year",
        "geojson_url": "https://opendata.victoria.ca/datasets/business-licences-current-year.geojson",
        "licence_url": "https://opendata.victoria.ca/pages/open-data-licence",
    },
    {
        "source_id": 30,
        "city": "Victoria",
        "province": "BC",
        "name": "Business Licences - Past 5 Years",
        "hub_url": "https://opendata.victoria.ca/datasets/VicMap::business-licences-past-5-years",
        "geojson_url": "https://opendata.victoria.ca/datasets/VicMap::business-licences-past-5-years.geojson",
        "licence_url": "https://opendata.victoria.ca/pages/open-data-licence",
    },
]

# ---------------------------------------------------------------------------
# BC Data Catalogue — resolve current resource IDs for dead 2017 URLs
# ---------------------------------------------------------------------------
BC_CATALOGUE_SOURCES = [
    {
        "source_id": 13,
        "name": "Licensed Establishments in B.C.",
        "dataset_id": "2b71813e-fb00-4a8a-a60e-a67a46c81d2d",
        "catalogue_url": "https://catalogue.data.gov.bc.ca/dataset/2b71813e-fb00-4a8a-a60e-a67a46c81d2d",
        "api_url": "https://catalogue.data.gov.bc.ca/api/3/action/package_show?id=2b71813e-fb00-4a8a-a60e-a67a46c81d2d",
        "licence_url": "https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc",
    },
    {
        "source_id": 14,
        "name": "BC Winery Locations",
        "dataset_id": "1d21922b-ec4f-42e5-8f6b-bf320a286157",
        "catalogue_url": "https://catalogue.data.gov.bc.ca/dataset/1d21922b-ec4f-42e5-8f6b-bf320a286157",
        "api_url": "https://catalogue.data.gov.bc.ca/api/3/action/package_show?id=1d21922b-ec4f-42e5-8f6b-bf320a286157",
        "licence_url": "https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc",
    },
]

# ---------------------------------------------------------------------------
# Moved sources — follow new URLs
# ---------------------------------------------------------------------------
MOVED_SOURCES = [
    {
        "source_id": 8,
        "city": "Delta",
        "province": "BC",
        "name": "Business Licences",
        "new_url": "https://www.delta.ca/city-hall/municipal-information/open-data-catalogue",
    },
    {
        "source_id": 26,
        "city": "Surrey",
        "province": "BC",
        "name": "Business Licenses",
        "new_url": "https://opendata-surrey.hub.arcgis.com/",
        "search_url": "https://opendata-surrey.hub.arcgis.com/search?q=business+licences",
    },
    {
        "source_id": 9,
        "city": "Kelowna",
        "province": "BC",
        "name": "Business Licence",
        "search_url": "https://opendata.kelowna.ca/search?q=business+licences",
        "alt_url": "https://opendata.kelowna.ca/datasets/business-licences/explore",
    },
]


def fetch(url, max_bytes=32768, timeout=20):
    """Fetch URL, return (status, final_url, content_type, body_text, error)."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            body = resp.read(max_bytes)
            ct = resp.headers.get("Content-Type", "")
            try:
                text = body.decode("utf-8", errors="replace")
            except Exception:
                text = ""
            return resp.status, resp.url, ct, text, None
    except urllib.error.HTTPError as e:
        try:
            body = e.read(2048).decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return e.code, url, "", body, f"HTTP {e.code}"
    except Exception as ex:
        return 0, url, "", "", str(ex)[:120]


def probe_socrata_metadata(portal, four_by_four):
    """Fetch Socrata metadata JSON for dataset."""
    meta_url = f"{portal}/api/views/{four_by_four}.json"
    status, final, ct, body, err = fetch(meta_url, max_bytes=65536)
    if status == 200 and body:
        try:
            return json.loads(body), None
        except Exception as e:
            return None, f"JSON parse error: {e}"
    return None, err or f"HTTP {status}"


def probe_socrata_csv_sample(portal, four_by_four, rows=5):
    """Fetch first N rows of Socrata dataset as CSV."""
    csv_url = f"{portal}/api/views/{four_by_four}/rows.csv?accessType=DOWNLOAD&$limit={rows}"
    status, final, ct, body, err = fetch(csv_url, max_bytes=16384, timeout=30)
    return status, ct, body, err


def probe_geojson_sample(url):
    """Fetch GeoJSON, return first feature's properties."""
    status, final, ct, body, err = fetch(url, max_bytes=65536, timeout=30)
    if status == 200 and body:
        try:
            data = json.loads(body)
            features = data.get("features", [])
            total = len(features)
            props = features[0].get("properties", {}) if features else {}
            return status, total, list(props.keys()), props, None
        except Exception as e:
            return status, 0, [], {}, f"JSON parse: {e}"
    return status, 0, [], {}, err


def probe_opendatasoft(dataset_id, portal):
    """Vancouver uses OpenDataSoft API."""
    api_url = f"{portal}/api/explore/v2.1/catalog/datasets/{dataset_id}?limit=1"
    status, final, ct, body, err = fetch(api_url, max_bytes=32768)
    if status == 200 and body:
        try:
            return json.loads(body), None
        except Exception as e:
            return None, f"JSON parse: {e}"
    # Try v1 API
    api_url_v1 = f"{portal}/api/datasets/1.0/{dataset_id}/"
    status2, _, _, body2, err2 = fetch(api_url_v1, max_bytes=32768)
    if status2 == 200 and body2:
        try:
            return json.loads(body2), None
        except Exception:
            pass
    return None, err or f"HTTP {status}"


def extract_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip()[:100] if m else None


def main():
    results = []

    # -----------------------------------------------------------------------
    # 1. Socrata sources
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("SOCRATA SOURCES")
    print("=" * 60)

    for src in SOCRATA_SOURCES:
        sid = src["source_id"]
        city = src["city"]
        name = src["name"]
        portal = src["portal"]
        print(f"\n[{sid:02d}] {city} — {name}")

        rec = {
            "source_id": sid,
            "city": city,
            "province": src["province"],
            "source_name": name,
            "portal": portal,
            "api_type": src.get("api_type", "socrata"),
            "licence_url": src["licence_url"],
            "metadata_status": None,
            "row_count": None,
            "columns": [],
            "record_grain": None,
            "date_last_updated": None,
            "current_year_evidence": False,
            "has_name": False,
            "has_address": False,
            "has_postal": False,
            "has_phone": False,
            "has_email": False,
            "has_naics": False,
            "has_status": False,
            "has_licence_number": False,
            "has_new_business_signal": False,
            "download_url": None,
            "automation_status": "UNKNOWN",
            "production_candidate": False,
            "notes": "",
            "sample_row": None,
        }

        if src.get("api_type") == "opendatasoft":
            # Vancouver
            dataset_id = src.get("dataset_id", "business-licences")
            meta, err = probe_opendatasoft(dataset_id, portal)
            if meta:
                rec["metadata_status"] = "ok"
                # v2.1
                dataset = meta.get("dataset", meta)
                fields = dataset.get("fields", [])
                if not fields:
                    fields = meta.get("fields", [])
                rec["columns"] = [f.get("name", f.get("label", "?")) for f in fields]
                rec["row_count"] = dataset.get("metas", {}).get("default", {}).get("records_count")
                rec["date_last_updated"] = dataset.get("metas", {}).get("default", {}).get("modified")
                rec["download_url"] = f"{portal}/explore/dataset/{dataset_id}/export/?format=csv"
                print(f"  OpenDataSoft metadata OK. Cols: {rec['columns'][:8]}")
            else:
                rec["metadata_status"] = f"error: {err}"
                print(f"  OpenDataSoft metadata error: {err}")
                # Fall back to portal page inspection
                status, final, ct, body, ferr = fetch(f"{portal}/explore/dataset/{dataset_id}/information/", max_bytes=65536)
                if status == 200:
                    title = extract_title(body)
                    rec["notes"] = f"Portal page accessible. Title: {title}"
                    if any(y in body for y in ["2024", "2025", "2026"]):
                        rec["current_year_evidence"] = True
        else:
            four_by_four = src["four_by_four"]
            meta, err = probe_socrata_metadata(portal, four_by_four)
            if meta:
                rec["metadata_status"] = "ok"
                rec["row_count"] = meta.get("rowsUpdatedAt") and None  # rowsUpdatedAt is a timestamp not count
                # Get count from cachedContents
                rec["row_count"] = (meta.get("cachedContents") or {}).get("non_null") or \
                                   (meta.get("cachedContents") or {}).get("count")
                rec["date_last_updated"] = meta.get("rowsUpdatedAt")
                cols = meta.get("columns", [])
                rec["columns"] = [c.get("fieldName", c.get("name", "?")) for c in cols]
                rec["download_url"] = f"{portal}/api/views/{four_by_four}/rows.csv?accessType=DOWNLOAD"
                rec["automation_status"] = "API_AVAILABLE"

                # Field detection
                col_str = " ".join(rec["columns"]).lower()
                rec["has_name"] = any(x in col_str for x in ["name", "business_name", "tradename"])
                rec["has_address"] = any(x in col_str for x in ["address", "street", "location"])
                rec["has_postal"] = any(x in col_str for x in ["postal", "zip", "postcode"])
                rec["has_phone"] = "phone" in col_str
                rec["has_email"] = "email" in col_str
                rec["has_naics"] = "naics" in col_str
                rec["has_status"] = "status" in col_str
                rec["has_licence_number"] = any(x in col_str for x in ["licence", "license", "permit"])

                if rec["date_last_updated"]:
                    import datetime
                    ts = rec["date_last_updated"]
                    rec["current_year_evidence"] = str(ts)[:4] in ["2024", "2025", "2026"]

                print(f"  Socrata metadata OK")
                print(f"  Columns ({len(rec['columns'])}): {rec['columns'][:10]}")
                print(f"  Last updated: {rec['date_last_updated']}")
                print(f"  Row count: {rec['row_count']}")

                # CSV sample
                csv_status, csv_ct, csv_body, csv_err = probe_socrata_csv_sample(portal, four_by_four, rows=3)
                if csv_status == 200 and csv_body:
                    try:
                        reader = csv.DictReader(io.StringIO(csv_body))
                        sample_rows = list(reader)
                        if sample_rows:
                            rec["sample_row"] = dict(sample_rows[0])
                            print(f"  CSV sample OK. Fields: {list(sample_rows[0].keys())[:8]}")
                    except Exception as e:
                        print(f"  CSV parse error: {e}")
                else:
                    print(f"  CSV sample: HTTP {csv_status} — {csv_err}")
            else:
                rec["metadata_status"] = f"error: {err}"
                print(f"  Socrata metadata error: {err}")

        results.append(rec)
        time.sleep(1)

    # -----------------------------------------------------------------------
    # 2. New Westminster — ArcGIS Hub GeoJSON
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("NEW WESTMINSTER — ArcGIS Hub")
    print("=" * 60)

    for src in NEW_WEST_SOURCES:
        sid = src["source_id"]
        name = src["name"]
        print(f"\n[{sid:02d}] New Westminster — {name}")

        rec = {
            "source_id": sid,
            "city": "New Westminster",
            "province": "BC",
            "source_name": name,
            "api_type": "arcgis_hub",
            "licence_url": src["licence_url"],
            "geojson_url": src["api_url"],
            "hub_url": src["hub_url"],
            "row_count": None,
            "columns": [],
            "sample_row": None,
            "current_year_evidence": False,
            "has_name": False,
            "has_address": False,
            "has_postal": False,
            "has_phone": False,
            "has_email": False,
            "has_naics": False,
            "has_status": False,
            "has_licence_number": False,
            "has_new_business_signal": sid == 19,
            "download_url": src["api_url"],
            "automation_status": "UNKNOWN",
            "production_candidate": False,
            "notes": "",
        }

        status, total, cols, sample, err = probe_geojson_sample(src["api_url"])
        if status == 200 and cols:
            rec["row_count"] = total
            rec["columns"] = cols
            rec["sample_row"] = sample

            col_str = " ".join(cols).lower()
            rec["has_name"] = any(x in col_str for x in ["name", "business"])
            rec["has_address"] = any(x in col_str for x in ["address", "street"])
            rec["has_postal"] = any(x in col_str for x in ["postal", "zip"])
            rec["has_phone"] = "phone" in col_str
            rec["has_email"] = "email" in col_str
            rec["has_naics"] = "naics" in col_str
            rec["has_status"] = "status" in col_str
            rec["has_licence_number"] = any(x in col_str for x in ["licence", "license"])
            rec["automation_status"] = "API_AVAILABLE"

            # Check dates in sample
            sample_str = str(sample)
            rec["current_year_evidence"] = any(y in sample_str for y in ["2024", "2025", "2026"])

            print(f"  GeoJSON OK. Features in sample: {total}")
            print(f"  Columns: {cols[:12]}")
            print(f"  Sample: {str(sample)[:200]}")
        else:
            # Try fetching just a small count via ArcGIS FeatureServer
            fs_url = src["api_url"].replace(".geojson", "/FeatureServer/0/query?where=1=1&returnCountOnly=true&f=json")
            s2, _, _, b2, e2 = fetch(fs_url)
            if s2 == 200 and b2:
                try:
                    d = json.loads(b2)
                    rec["row_count"] = d.get("count")
                    print(f"  GeoJSON failed ({err}), FeatureServer count: {d.get('count')}")
                except Exception:
                    pass
            rec["notes"] = f"GeoJSON fetch: HTTP {status} — {err}"
            print(f"  Error: {err}")

        results.append(rec)
        time.sleep(1)

    # -----------------------------------------------------------------------
    # 3. Victoria — ArcGIS Hub
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("VICTORIA — ArcGIS Hub")
    print("=" * 60)

    for src in VICTORIA_SOURCES:
        sid = src["source_id"]
        name = src["name"]
        print(f"\n[{sid:02d}] Victoria — {name}")

        rec = {
            "source_id": sid,
            "city": "Victoria",
            "province": "BC",
            "source_name": name,
            "api_type": "arcgis_hub",
            "licence_url": src["licence_url"],
            "geojson_url": src["geojson_url"],
            "hub_url": src["hub_url"],
            "row_count": None,
            "columns": [],
            "sample_row": None,
            "current_year_evidence": False,
            "has_name": False, "has_address": False, "has_postal": False,
            "has_phone": False, "has_email": False, "has_naics": False,
            "has_status": False, "has_licence_number": False,
            "has_new_business_signal": False,
            "download_url": src["geojson_url"],
            "automation_status": "UNKNOWN",
            "production_candidate": False,
            "notes": "",
        }

        status, total, cols, sample, err = probe_geojson_sample(src["geojson_url"])
        if status == 200 and cols:
            rec["row_count"] = total
            rec["columns"] = cols
            rec["sample_row"] = sample
            col_str = " ".join(cols).lower()
            rec["has_name"] = any(x in col_str for x in ["name", "business"])
            rec["has_address"] = any(x in col_str for x in ["address", "street"])
            rec["has_postal"] = any(x in col_str for x in ["postal", "zip"])
            rec["has_status"] = "status" in col_str
            rec["has_licence_number"] = any(x in col_str for x in ["licence", "license"])
            rec["automation_status"] = "API_AVAILABLE"
            sample_str = str(sample)
            rec["current_year_evidence"] = any(y in sample_str for y in ["2024", "2025", "2026"])
            print(f"  GeoJSON OK. Cols: {cols[:10]}")
            print(f"  Sample: {str(sample)[:200]}")
        else:
            rec["notes"] = f"GeoJSON: HTTP {status} — {err}"
            print(f"  Error: {err}")

        results.append(rec)
        time.sleep(1)

    # -----------------------------------------------------------------------
    # 4. BC Data Catalogue — resolve current resource IDs
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("BC DATA CATALOGUE — resolve current resource IDs")
    print("=" * 60)

    for src in BC_CATALOGUE_SOURCES:
        sid = src["source_id"]
        name = src["name"]
        print(f"\n[{sid:02d}] BC — {name}")

        rec = {
            "source_id": sid,
            "city": "BC (provincial)",
            "province": "BC",
            "source_name": name,
            "api_type": "bc_ckan",
            "licence_url": src["licence_url"],
            "catalogue_url": src["catalogue_url"],
            "current_resource_url": None,
            "row_count": None,
            "columns": [],
            "sample_row": None,
            "current_year_evidence": False,
            "automation_status": "UNKNOWN",
            "production_candidate": False,
            "notes": "",
        }

        status, final, ct, body, err = fetch(src["api_url"], max_bytes=65536)
        if status == 200 and body:
            try:
                data = json.loads(body)
                pkg = data.get("result", {})
                resources = pkg.get("resources", [])
                rec["notes"] = f"{len(resources)} resources found"
                print(f"  CKAN API OK. {len(resources)} resources:")
                for r in resources:
                    url = r.get("url", "")
                    fmt = r.get("format", "")
                    desc = r.get("description", r.get("name", ""))
                    modified = r.get("last_modified", r.get("metadata_modified", ""))
                    print(f"    [{fmt}] {desc[:50]} — {modified} — {url[:80]}")
                    if fmt.upper() in ("CSV", "XLSX", "JSON") and not rec["current_resource_url"]:
                        rec["current_resource_url"] = url
                        rec["automation_status"] = "API_AVAILABLE"
                        if any(y in str(modified) for y in ["2024", "2025", "2026"]):
                            rec["current_year_evidence"] = True
            except Exception as e:
                rec["notes"] = f"CKAN parse error: {e}"
                print(f"  CKAN parse error: {e}")
        else:
            rec["notes"] = f"CKAN API: HTTP {status} — {err}"
            print(f"  CKAN API error: {err}")

        results.append(rec)
        time.sleep(1)

    # -----------------------------------------------------------------------
    # 5. Moved sources — follow new URLs
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("MOVED SOURCES — follow new URLs")
    print("=" * 60)

    for src in MOVED_SOURCES:
        sid = src["source_id"]
        city = src["city"]
        name = src["name"]
        url = src.get("search_url") or src.get("new_url") or src.get("alt_url")
        print(f"\n[{sid:02d}] {city} — {name}")
        print(f"  Probing: {url}")

        rec = {
            "source_id": sid,
            "city": city,
            "province": src["province"],
            "source_name": name,
            "api_type": "moved",
            "probed_url": url,
            "http_status": None,
            "page_title": None,
            "current_year_evidence": False,
            "dataset_links_found": [],
            "notes": "",
            "automation_status": "UNKNOWN",
            "production_candidate": False,
        }

        status, final, ct, body, err = fetch(url, max_bytes=32768)
        rec["http_status"] = status
        if status == 200 and body:
            rec["page_title"] = extract_title(body)
            rec["current_year_evidence"] = any(y in body for y in ["2024", "2025", "2026"])
            # Look for dataset/download links
            links = re.findall(r'href=["\']([^"\']*business[^"\']*)["\']', body, re.IGNORECASE)
            rec["dataset_links_found"] = list(set(links[:10]))
            print(f"  HTTP {status}. Title: {rec['page_title']}")
            print(f"  Business links found: {rec['dataset_links_found'][:5]}")
            if rec["current_year_evidence"]:
                print(f"  ✅ Current year evidence")
        else:
            rec["notes"] = f"HTTP {status} — {err}"
            print(f"  Error: HTTP {status} — {err}")

        results.append(rec)
        time.sleep(1)

    # -----------------------------------------------------------------------
    # Save outputs
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for r in results:
        sid = r.get("source_id", "?")
        city = r.get("city", "?")
        name = r.get("source_name", "?")
        cols = r.get("columns", [])
        rows = r.get("row_count", "?")
        current = "✅" if r.get("current_year_evidence") else "—"
        auto = r.get("automation_status", "UNKNOWN")
        print(f"  [{sid:02d}] {city} — {name}")
        print(f"       rows={rows} | cols={len(cols)} | current={current} | auto={auto}")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"total": len(results), "sources": results}, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {OUTPUT_JSON}")

    write_md(results)
    print(f"Saved: {OUTPUT_MD}")


def write_md(results):
    lines = [
        "# VR14.3 — ODBus High-Value Source Deep Validation",
        "",
        "Generated: `2026-09-26`",
        "Script: `scripts/probe_odbus_vr14_3.py`",
        "JSON: `reports/validation_rounds/VR14_3_ODBUS_HIGH_VALUE_SOURCES.json`",
        "",
        "---",
        "",
        "## Summary Table",
        "",
        "| # | City | Prov | Dataset | Rows | Cols | Current | Auto | Candidate |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for r in results:
        cols = r.get("columns", [])
        lines.append(
            f"| {r.get('source_id','?')} | {r.get('city','?')} | {r.get('province','?')} "
            f"| {r.get('source_name','?')} | {r.get('row_count','?')} | {len(cols)} "
            f"| {'✅' if r.get('current_year_evidence') else '—'} "
            f"| {r.get('automation_status','?')} "
            f"| {'✅' if r.get('production_candidate') else '—'} |"
        )

    lines += ["", "---", ""]

    for r in results:
        lines += [
            f"## [{r.get('source_id','?')}] {r.get('city','?')} — {r.get('source_name','?')}",
            "",
            f"- Province: {r.get('province','?')}",
            f"- API type: {r.get('api_type','?')}",
            f"- Row count: {r.get('row_count','?')}",
            f"- Columns ({len(r.get('columns',[]))}): {r.get('columns',[])}",
            f"- Current year evidence: {r.get('current_year_evidence','?')}",
            f"- Has name: {r.get('has_name','?')}",
            f"- Has address: {r.get('has_address','?')}",
            f"- Has postal: {r.get('has_postal','?')}",
            f"- Has phone: {r.get('has_phone','?')}",
            f"- Has email: {r.get('has_email','?')}",
            f"- Has NAICS: {r.get('has_naics','?')}",
            f"- Has status: {r.get('has_status','?')}",
            f"- Has licence number: {r.get('has_licence_number','?')}",
            f"- New business signal: {r.get('has_new_business_signal','?')}",
            f"- Download URL: {r.get('download_url') or r.get('current_resource_url','?')}",
            f"- Automation status: {r.get('automation_status','?')}",
            f"- Production candidate: {r.get('production_candidate','?')}",
            f"- Notes: {r.get('notes','')}",
        ]

        sample = r.get("sample_row")
        if sample:
            lines += ["", "Sample row:"]
            for k, v in list(sample.items())[:15]:
                lines.append(f"  - {k}: {str(v)[:80]}")

        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
