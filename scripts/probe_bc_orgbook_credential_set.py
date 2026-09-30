"""
VR09.1 — BC OrgBook credential-set lookup
Uses topic_source_id=A0091250, internal topic id=1354842 from VR09 autocomplete.
Tests only: GET /v4/topic/1354842/credential-set
No discovery, no enumeration, no additional load.
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
RAW     = ROOT / "data" / "raw"
REPORTS = ROOT / "reports" / "validation_rounds"

TIMESTAMP = datetime.now(timezone.utc).isoformat()
API_BASE  = "https://orgbook.gov.bc.ca/api/v4"

# From VR09 autocomplete result for "TELUS Communications Inc."
TOPIC_SOURCE_ID = "A0091250"
TOPIC_ID        = 1354842

SEP = "=" * 80


def fetch_json(url):
    print(f"  GET {url}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Canada-Pipeline-Validator/1.0; research use)",
            "Accept": "application/json",
        }
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            status = resp.status
        ms = int((time.time() - t0) * 1000)
        print(f"    -> {status}  {len(raw):,} bytes  {ms}ms")
        return json.loads(raw), status, ms, None
    except urllib.error.HTTPError as e:
        ms = int((time.time() - t0) * 1000)
        print(f"    -> HTTP {e.code} {e.reason}")
        return None, e.code, ms, f"HTTP {e.code}"
    except Exception as e:
        ms = int((time.time() - t0) * 1000)
        print(f"    -> ERROR {e}")
        return None, None, ms, str(e)


def main():
    print(SEP)
    print("VR09.1 — BC ORGBOOK CREDENTIAL-SET LOOKUP")
    print(f"topic_source_id={TOPIC_SOURCE_ID}, topic_id={TOPIC_ID}")
    print(SEP)

    url = f"{API_BASE}/topic/{TOPIC_ID}/credential-set"
    data, status, ms, err = fetch_json(url)

    result = {
        "generated": TIMESTAMP,
        "url": url,
        "topic_source_id": TOPIC_SOURCE_ID,
        "topic_id": TOPIC_ID,
        "status": status,
        "response_ms": ms,
        "error": err,
    }

    if err or not data:
        print(f"\nFailed: {err}")
        print("Appending failure note to VR09 report.")
        _append_to_report(result, None)
        return

    # data should be a list of credential-set objects
    items = data if isinstance(data, list) else data.get("results", [data])
    result["credential_count"] = len(items)
    print(f"  Credentials returned: {len(items)}")

    # Profile each credential
    cred_profiles = []
    all_attr_names = set()
    has_address = has_phone = has_email = has_directors = False

    for c in items:
        profile = {
            "id": c.get("id"),
            "credential_type": None,
            "issuer": None,
            "effective_date": c.get("effective_date"),
            "revoked": c.get("revoked"),
            "inactive": c.get("inactive"),
            "latest": c.get("latest"),
            "attributes": {},
        }

        # Credential type
        ct = c.get("credential_type", {})
        if isinstance(ct, dict):
            profile["credential_type"] = ct.get("description") or ct.get("schema_label")
        elif isinstance(ct, str):
            profile["credential_type"] = ct

        # Issuer
        issuer = c.get("issuer", {})
        if isinstance(issuer, dict):
            profile["issuer"] = issuer.get("name")
        elif isinstance(issuer, str):
            profile["issuer"] = issuer

        # Attributes
        attrs = c.get("attributes", [])
        for a in attrs:
            name = str(a.get("type") or a.get("name") or "").lower()
            val  = a.get("value") or a.get("text") or ""
            all_attr_names.add(name)
            profile["attributes"][name] = str(val)[:80]
            if "address" in name or "street" in name or "city" in name:
                has_address = True
            if "phone" in name or "telephone" in name:
                has_phone = True
            if "email" in name:
                has_email = True
            if "director" in name or "officer" in name:
                has_directors = True

        cred_profiles.append(profile)
        print(f"    Credential: type={profile['credential_type']} | "
              f"revoked={profile['revoked']} | attrs={list(profile['attributes'].keys())[:8]}")

    result["credential_profiles"] = cred_profiles
    result["all_attribute_names"] = sorted(all_attr_names)
    result["has_address"] = has_address
    result["has_phone"] = has_phone
    result["has_email"] = has_email
    result["has_directors"] = has_directors

    # Save raw JSON
    raw_path = RAW / f"bc_orgbook_credential_set_{TOPIC_ID}.json"
    raw_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"\n  Raw saved: {raw_path}")

    _append_to_report(result, cred_profiles)

    result_path = REPORTS / "VR09.1_BC_ORGBOOK_CREDENTIAL_SET.json"
    result_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"  JSON written: {result_path}")

    print(SEP)
    print("VR09.1 COMPLETE")
    print(SEP)


def _append_to_report(result, cred_profiles):
    report_path = REPORTS / "VR09_BC_ORGBOOK_API.md"

    lines = [
        "",
        "---",
        "",
        "## VR09.1 — Credential-Set Follow-up",
        "",
        f"Generated: `{result['generated']}`",
        "",
        f"- URL tested: `{result['url']}`",
        f"- topic_source_id: `{result['topic_source_id']}`",
        f"- topic_id: `{result['topic_id']}`",
        f"- HTTP status: `{result['status']}`",
        f"- Response time: `{result['response_ms']}ms`",
        f"- Error: `{result.get('error')}`",
        "",
    ]

    if result.get("error") or not cred_profiles:
        lines += [
            f"Credential-set endpoint returned no data or an error.",
            f"Credentials returned: `{result.get('credential_count', 0)}`",
            "",
            "**Open question:** Correct endpoint or topic ID format needs further investigation.",
        ]
    else:
        lines += [
            f"- Credentials returned: `{result['credential_count']}`",
            f"- All attribute names observed: {', '.join(f'`{a}`' for a in result.get('all_attribute_names', []))}",
            f"- Address in credentials: `{result['has_address']}`",
            f"- Phone in credentials: `{result['has_phone']}`",
            f"- Email in credentials: `{result['has_email']}`",
            f"- Directors in credentials: `{result['has_directors']}`",
            "",
            "### Credential Profiles",
            "",
            "| # | Type | Issuer | Revoked | Attributes |",
            "|---|---|---|---|---|",
        ]
        for i, c in enumerate(cred_profiles):
            attrs_str = ", ".join(f"`{k}`" for k in list(c["attributes"].keys())[:6])
            lines.append(
                f"| {i+1} | {c.get('credential_type','?')} | "
                f"{c.get('issuer','?')} | {c.get('revoked')} | {attrs_str} |"
            )

        lines += [
            "",
            "### Sample Attribute Values (first credential)",
            "",
        ]
        if cred_profiles:
            first_attrs = cred_profiles[0].get("attributes", {})
            for k, v in list(first_attrs.items())[:20]:
                lines.append(f"- `{k}`: `{v}`")

    lines.append("")
    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Appended to: {report_path}")


if __name__ == "__main__":
    main()
