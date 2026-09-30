"""Allow-listed factory for bulk-ingestion adapters registered in the source table."""

from __future__ import annotations

from ..base_adapter import SourceAdapter
from . import (
    BCIndigenousAdapter,
    CalgaryAdapter,
    CSBIFAdapter,
    CorporationsCanadaCSVAdapter,
    CorporationsCanadaHTMLAdapter,
    DairyDistributorsAdapter,
    DairyPlantsAdapter,
    EdmontonAdapter,
    FuelAdapter,
    ManitobaWeeklyPDFAdapter,
    MeatPlantsAdapter,
    MontrealCommercialPremisesAdapter,
    NNIAdapter,
    OntarioSelectLicenceAdapter,
    QuebecCityPermitsAdapter,
    SaskatoonAllBizAdapter,
    SaskatoonNewBizAdapter,
    TobaccoAdapter,
    VancouverAdapter,
    WinnipegAdapter,
)


class AdapterNotAvailableError(ValueError):
    """Raised when a source is not supported by the bulk-ingestion endpoint."""


_ADAPTERS_BY_CLASS: dict[str, type[SourceAdapter]] = {
    "BCIndigenousAdapter": BCIndigenousAdapter,
    "CalgaryAdapter": CalgaryAdapter,
    "CorporationsCanadaCSVAdapter": CorporationsCanadaCSVAdapter,
    "CorporationsCanadaHTMLAdapter": CorporationsCanadaHTMLAdapter,
    "DairyDistributorsAdapter": DairyDistributorsAdapter,
    "DairyPlantsAdapter": DairyPlantsAdapter,
    "EdmontonAdapter": EdmontonAdapter,
    "FuelAdapter": FuelAdapter,
    "ManitobaWeeklyPDFAdapter": ManitobaWeeklyPDFAdapter,
    "MeatPlantsAdapter": MeatPlantsAdapter,
    "MontrealCommercialPremisesAdapter": MontrealCommercialPremisesAdapter,
    "NNIAdapter": NNIAdapter,
    "OntarioSelectLicenceAdapter": OntarioSelectLicenceAdapter,
    "QuebecCityPermitsAdapter": QuebecCityPermitsAdapter,
    "SaskatoonAllBizAdapter": SaskatoonAllBizAdapter,
    "SaskatoonNewBizAdapter": SaskatoonNewBizAdapter,
    "TobaccoAdapter": TobaccoAdapter,
    "VancouverAdapter": VancouverAdapter,
    "WinnipegAdapter": WinnipegAdapter,
    # Names seeded in migration 001 before the concrete adapter classes were finalized.
    "OntarioDairyAdapter": DairyDistributorsAdapter,
    "OntarioDairyPlantsAdapter": DairyPlantsAdapter,
    "OntarioFuelAdapter": FuelAdapter,
    "OntarioMeatAdapter": MeatPlantsAdapter,
    "OntarioTobaccoAdapter": TobaccoAdapter,
    "OntarioCSBIFAdapter": CSBIFAdapter,
}


def create_ingestion_adapter(adapter_class: str, source_key: str) -> SourceAdapter:
    """Instantiate a registered bulk adapter, binding it to the registry source key."""
    adapter_type = _ADAPTERS_BY_CLASS.get(adapter_class)
    if adapter_type is None:
        raise AdapterNotAvailableError(
            f"No bulk-ingestion adapter is implemented for source '{source_key}' "
            f"(adapter_class='{adapter_class}'). Targeted enrichment sources must use "
            "their dedicated enrichment endpoint."
        )

    adapter = adapter_type()
    adapter.source_key = source_key
    return adapter