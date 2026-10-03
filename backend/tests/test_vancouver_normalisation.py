from __future__ import annotations

import uuid

from src.ingestion.contracts import RawRecord, SourceGrain
from src.normalisation.normaliser import normalise_record


def test_vancouver_business_names_are_mapped_into_identity_fields() -> None:
    record = RawRecord(
        source_key="vancouver",
        ingestion_run_id=uuid.uuid4(),
        source_record_id="licence-1",
        raw_payload={
            "businessname": "Ali's Property Ltd",
            "businesstradename": "Ali's Property Management",
            "province": "NEW SOUTH WALES",
        },
        source_grain=SourceGrain.LICENCE,
    )

    normalised = normalise_record(record)

    assert normalised.name is not None
    assert normalised.name.legal_name == "ali's property limited"
    assert normalised.name.trade_name == "ali's property management"
    assert normalised.address is not None
    assert normalised.address.province is None


def test_full_canadian_province_name_maps_to_two_letter_code() -> None:
    record = RawRecord(
        source_key="vancouver",
        ingestion_run_id=uuid.uuid4(),
        source_record_id="licence-2",
        raw_payload={"province": "British Columbia"},
        source_grain=SourceGrain.LICENCE,
    )

    normalised = normalise_record(record)

    assert normalised.address is not None
    assert normalised.address.province == "BC"


def test_overlength_postal_value_is_preserved_only_in_raw_address() -> None:
    record = RawRecord(
        source_key="vancouver",
        ingestion_run_id=uuid.uuid4(),
        source_record_id="licence-3",
        raw_payload={"postal_code": "12345-678901"},
        source_grain=SourceGrain.LICENCE,
    )

    normalised = normalise_record(record)

    assert normalised.address is not None
    assert normalised.address.postal_code is None
    assert normalised.address.raw_address == "12345-678901"