from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.ingestion.adapters.registry import create_ingestion_adapter
from src.ingestion.contracts import RawArtifact, SourceGrain
from src.normalisation.normaliser import normalise_record


CSV_SAMPLE = """NUMERO_PERMIS,DATE_DELIVRANCE,ADRESSE_TRAVAUX,DOMAINE,LOTS_IMPACTES,TYPE_PERMIS,ARRONDISSEMENT,RAISON,LONGITUDE,LATITUDE
QC-2026-123,2026-09-25,100 Rue Exemple,Construction,1234567,Certificat,La Cite-Limoilou,Travaux, -71.2,46.8
"""


def test_quebec_permits_parse_as_raw_event_records_without_business_identity() -> None:
    adapter = create_ingestion_adapter(
        "QuebecCityPermitsAdapter",
        "quebec_city_permits",
    )
    metadata = adapter.get_metadata()
    run_id = uuid.uuid4()
    artifact = RawArtifact(
        source_key="quebec_city_permits",
        ingestion_run_id=run_id,
        retrieval_url="https://example.test/vdq-permis.csv",
        retrieval_timestamp=datetime.now(timezone.utc),
        http_status=200,
        content_type="text/csv",
        checksum_sha256="sample-checksum",
        payload_ref=CSV_SAMPLE,
    )

    records = adapter.parse(artifact)
    validation = adapter.validate(records)
    normalised = normalise_record(records[0])

    assert validation.passed
    assert len(records) == 1
    assert records[0].source_record_id == "QC-2026-123"
    assert records[0].source_grain == SourceGrain.EVENT
    assert records[0].raw_payload["NUMERO_PERMIS"] == "QC-2026-123"
    assert normalised.name is not None
    assert normalised.name.legal_name is None
    assert normalised.name.trade_name is None
    assert normalised.address is not None
    assert normalised.address.address_line1 == "100 Rue Exemple"
    assert normalised.address.city == "Québec"
    assert normalised.address.province == "QC"
    assert normalised.issued_date is not None
    assert "2026-09-25" in normalised.issued_date
    assert normalised.extra is not None
    assert normalised.extra["numero_permis"] == "QC-2026-123"
    assert normalised.extra["event_type"] == "MUNICIPAL_PERMIT_ISSUED"
    assert metadata.licence == "Creative Commons Attribution 4.0 (CC-BY 4.0)"
    assert metadata.default_grain == SourceGrain.EVENT