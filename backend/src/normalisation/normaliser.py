"""Normalisation orchestrator.

Applies all field normalisers to a RawRecord and produces a NormalisedRecord.
Field mapping uses a priority-ordered list of candidate keys per source type,
since field names differ across sources (e.g. "tradename" vs "business_name").

Requirements: 4.1–4.10
"""

from __future__ import annotations

from ..ingestion.contracts import RawRecord
from .address import normalise_address
from .date import normalise_date
from .email import normalise_email
from .employee import normalise_employee
from .naics import normalise_naics
from .name import normalise_business_name
from .phone import normalise_phone
from .schemas import (
    NormalisedAddress,
    NormalisedEmail,
    NormalisedEmployee,
    NormalisedNAICS,
    NormalisedName,
    NormalisedPhone,
    NormalisedRecord,
    NormalisedStatus,
    NormalisedURL,
)
from .status import normalise_status
from .url import normalise_url


def _first(payload: dict, *keys: str) -> str | None:
    """Return the first non-empty value found in payload for any of the given keys."""
    for key in keys:
        val = payload.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def normalise_record(record: RawRecord) -> NormalisedRecord:
    """Apply all normalisation pipelines to a single RawRecord.

    Field name mapping handles the heterogeneous key names across sources.
    Unknown fields are preserved in `extra`.
    """
    source_key = record.source_key
    p = record.raw_payload
    if source_key == "quebec_city_permits":
        p = {str(key).strip().lower(): value for key, value in p.items()}

    # --- Name ---
    legal_raw = _first(p, "corporate_name_form_1", "legal_name", "company_name", "name",
                       "business_name", "businessname", "canonical_name")
    trade_raw = _first(p, "tradename", "trade_name", "dba", "operating_name",
                       "businesstradename", "business_trade_name")
    name_r = normalise_business_name(legal_name=legal_raw, trade_name=trade_raw)
    name_out = NormalisedName(
        raw_legal_name=name_r.raw_legal_name,
        raw_trade_name=name_r.raw_trade_name,
        legal_name=name_r.legal_name,
        trade_name=name_r.trade_name,
    )

    # --- Address ---
    street = _first(p, "address", "address_line1", "street", "street_address",
                    "registered_office", "fulladdress", "address1", "adresse_travaux")
    city = _first(p, "city", "municipality", "town", "community", "neighbourhood")
    province = _first(p, "province", "prov", "province_code", "region")
    if source_key == "quebec_city_permits":
        city = city or "Québec"
        province = province or "QC"
    postal = _first(p, "postal_code", "postalcode", "postal", "zip")
    addr_r = normalise_address(street=street, city=city, province=province, postal_code=postal)
    addr_out = NormalisedAddress(
        raw_address=addr_r.raw_address,
        normalised_address=addr_r.normalised_address,
        address_line1=addr_r.address_line1,
        address_line2=addr_r.address_line2,
        city=addr_r.city,
        province=addr_r.province,
        postal_code=addr_r.postal_code,
        postal_valid=addr_r.postal_valid,
    )

    # --- Phone ---
    phone_raw = _first(p, "phone", "phone_number", "telephone", "tel", "contact_phone",
                       "business_phone")
    phone_r = normalise_phone(phone_raw)
    phone_out = NormalisedPhone(
        raw_phone=phone_r.raw_phone,
        normalised_phone=phone_r.normalised_phone,
        phone_valid=phone_r.phone_valid,
    )

    # --- Email ---
    email_raw = _first(p, "email", "email_address", "contact_email", "business_email")
    email_r = normalise_email(email_raw)
    email_out = NormalisedEmail(
        raw_email=email_r.raw_email,
        normalised_email=email_r.normalised_email,
        email_valid=email_r.email_valid,
    )

    # --- Website ---
    url_raw = _first(p, "website", "url", "web", "website_url", "homepage")
    url_r = normalise_url(url_raw)
    url_out = NormalisedURL(
        raw_url=url_r.raw_url,
        normalised_domain=url_r.normalised_domain,
        url_valid=url_r.url_valid,
    )

    # --- Status ---
    status_raw = _first(p, "status", "jobstatusdesc", "licence_status", "corp_status",
                        "business_status", "active_status")
    status_r = normalise_status(status_raw, source_key=source_key)
    status_out = NormalisedStatus(
        raw_status=status_r.raw_status,
        canonical_status=status_r.canonical_status,
    )

    # --- Employee ---
    employee_raw = _first(p, "numberofemployees", "employee_count", "employees",
                          "employee_range", "num_employees", "no_of_employees")
    emp_r = normalise_employee(employee_raw)
    emp_out = NormalisedEmployee(
        raw_employee_value=emp_r.raw_employee_value,
        employee_min=emp_r.employee_min,
        employee_max=emp_r.employee_max,
        employee_bucket=emp_r.employee_bucket,
        employee_exact=emp_r.employee_exact,
        data_quality_flag=emp_r.data_quality_flag,
    )

    # --- NAICS ---
    naics_raw = _first(p, "naics", "naics_code", "scian", "naics_sub_sector",
                       "industry_code", "licence_type_naics")
    naics_r = normalise_naics(naics_raw)
    naics_out = NormalisedNAICS(
        source_naics=naics_r.source_naics,
        naics_sector=naics_r.naics_sector,
    )

    # --- Dates ---
    def _dt_str(raw: str | None) -> str | None:
        dt = normalise_date(raw)
        return dt.isoformat() if dt else None

    issued_raw = _first(p, "first_iss_dt", "issueddate", "originalissuedate", "issue_date",
                        "original_issue_date", "most_recent_issue_date", "date_delivrance")
    expiry_raw = _first(p, "exp_dt", "expiry_date", "expiration_date", "licence_expiry")
    inc_raw = _first(p, "incorporation_date", "anniversary_date", "registration_date",
                     "incorporated_date")

    # --- Extra (pass-through unknown fields) ---
    known_keys = {
        "corporate_name_form_1", "legal_name", "company_name", "name", "business_name",
        "canonical_name", "tradename", "trade_name", "dba", "operating_name",
        "address", "address_line1", "street", "street_address", "registered_office",
        "fulladdress", "address1", "adresse_travaux", "city", "municipality", "town", "community",
        "neighbourhood", "province", "prov", "province_code", "region",
        "postal_code", "postalcode", "postal", "zip",
        "phone", "phone_number", "telephone", "tel", "contact_phone", "business_phone",
        "email", "email_address", "contact_email", "business_email",
        "website", "url", "web", "website_url", "homepage",
        "status", "jobstatusdesc", "licence_status", "corp_status", "business_status",
        "active_status", "numberofemployees", "employee_count", "employees",
        "employee_range", "num_employees", "no_of_employees",
        "naics", "naics_code", "scian", "naics_sub_sector", "industry_code",
        "licence_type_naics", "first_iss_dt", "issueddate", "originalissuedate",
        "issue_date", "original_issue_date", "most_recent_issue_date", "date_delivrance",
        "exp_dt", "expiry_date", "expiration_date", "licence_expiry",
        "incorporation_date", "anniversary_date", "registration_date", "incorporated_date",
    }
    extra = {k: v for k, v in p.items() if k not in known_keys and v is not None and v != ""}
    if source_key == "quebec_city_permits":
        extra["event_type"] = "MUNICIPAL_PERMIT_ISSUED"

    source_references = p.get("source_references") or []

    return NormalisedRecord(
        source_key=record.source_key,
        ingestion_run_id=record.ingestion_run_id,
        source_record_id=record.source_record_id,
        name=name_out,
        address=addr_out,
        phone=phone_out,
        email=email_out,
        website=url_out,
        status=status_out,
        employee=emp_out,
        naics=naics_out,
        issued_date=_dt_str(issued_raw),
        expiry_date=_dt_str(expiry_raw),
        incorporation_date=_dt_str(inc_raw),
        source_references=source_references,
        extra=extra if extra else None,
    )
