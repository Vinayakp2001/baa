"""Source adapter implementations."""

from .bc_indigenous import BCIndigenousAdapter
from .bc_orgbook import BCOrgBookAPIAdapter
from .calgary import CalgaryAdapter
from .corporations_canada_api import CorporationsCanadaAPIAdapter
from .corporations_canada_csv import CorporationsCanadaCSVAdapter
from .corporations_canada_html import CorporationsCanadaHTMLAdapter
from .edmonton import EdmontonAdapter
from .manitoba_weekly_pdf import ManitobaWeeklyPDFAdapter
from .montreal import MontrealCommercialPremisesAdapter
from .nni import NNIAdapter
from .ontario_regulated import (
    CSBIFAdapter,
    DairyDistributorsAdapter,
    DairyPlantsAdapter,
    FuelAdapter,
    MeatPlantsAdapter,
    OntarioRegulatedBaseAdapter,
    TobaccoAdapter,
)
from .ontario_select_licence import OntarioSelectLicenceAdapter
from .quebec_city_permits import QuebecCityPermitsAdapter
from .saskatoon_all_biz import SaskatoonAllBizAdapter
from .saskatoon_new_biz import SaskatoonNewBizAdapter
from .vancouver import VancouverAdapter
from .winnipeg import WinnipegAdapter

__all__ = [
    "BCIndigenousAdapter",
    "BCOrgBookAPIAdapter",
    "CalgaryAdapter",
    "CorporationsCanadaAPIAdapter",
    "CorporationsCanadaCSVAdapter",
    "CorporationsCanadaHTMLAdapter",
    "CSBIFAdapter",
    "DairyDistributorsAdapter",
    "DairyPlantsAdapter",
    "EdmontonAdapter",
    "FuelAdapter",
    "ManitobaWeeklyPDFAdapter",
    "MeatPlantsAdapter",
    "MontrealCommercialPremisesAdapter",
    "NNIAdapter",
    "OntarioRegulatedBaseAdapter",
    "OntarioSelectLicenceAdapter",
    "QuebecCityPermitsAdapter",
    "SaskatoonAllBizAdapter",
    "SaskatoonNewBizAdapter",
    "TobaccoAdapter",
    "VancouverAdapter",
    "WinnipegAdapter",
]
