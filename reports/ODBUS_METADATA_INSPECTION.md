# ODBus Metadata & Source Inspection

Generated from `ODBus_2023.zip`.

## 1. Dataset overview

- Archive: `ODBus_2023.zip`
- Main dataset rows: **446,575**
- Main dataset columns: **32**
- Main dataset encoding: `utf-8-sig`
- Record-layout encoding: `cp1252`
- Sources-table encoding: `cp1252`

## 2. ODBus record layout

This section reproduces the structured field-definition table contained in `ODBus-record-layout.csv`.

| Field name | Data type | Description | Field type |
| --- | --- | --- | --- |
| idx | object | Unique record ID automatically generated during data processing. | Internally generated during data processing. |
| business_name | object | Business name. | Provided as is from original data. |
| alt_business_name | object | Alternative business name. | Provided as is from original data. |
| business_sector | object | Business sector. | Provided as is from original data. |
| business_subsector | object | Business subsector. | Provided as is from original data. |
| business_description | object | Description of the business. | Provided as is from original data. |
| business_id_no | float64 | Business identification number. | Provided as is from original data. |
| licence_number | float64 | Licence identification number. | Provided as is from original data. |
| licence_type | object | Category of licence. | Provided as is from original data. |
| derived_NAICS | float64 | Two digit NAICS code. | Provided as is from original data or derived from NAICS description data. |
| source_NAICS_primary | float64 | Two to six digit NAICS identification number. | Provided as is from original data. |
| source_NAICS_secondary | float64 | Secondary two to six digit NAICS identification number . | Provided as is from original data. |
| NAICS_descr | object | NAICS code description. | Provided as is from original data. |
| NAICS_descr2 | object | Secondary NAICS code description. | Provided as is from original data. |
| latitude | float64 | Latitude. | Provided as is from original data. |
| longitude | float64 | Longitude. | Provided as is from original data. |
| full_address | object | Full address of business. | A combination of address components or provided as is. |
| postal_code | object | Postal Code. | Parsed from a full address object or provided as is. |
| unit | object | Civic unit or suite number. | Parsed from a full address object or provided as is. |
| street_no | object | Civic street number. | Parsed from a full address object or provided as is. |
| street_name | object | Civic street name. | Parsed from a full address object or provided as is. |
| street_direction | object | Civic street direction. | Parsed from a full address object or provided as is. |
| street_type | object | Civic street type. | Parsed from a full address object or provided as is. |
| city | object | Municipality name. | Parsed from a full address object or provided as is |
| prov_terr | object | Province or territory code. | Converted to two letter codes after parsing from a full address object or indicated by providers. |
| total_no_employees | integer | Total number of employees. | Provided as is from original data. |
| status | object | Statuts of business licence (e.g., Active, Pending, etc.). | Standardized from original data. |
| provider | object | Name of the entity that provided the dataset. | Created based on origins of input dataset. |
| geo_source | object | An indication of whether the latitude and longitude were provided in the original source, or if they were geocoded for the ODBus. | Created based on origins of geocoordinates. |
| CSDUID | float64 | Census subdivision unique identifier. | Imputed from either geographic coordinates or CSD name using GeoSuite 2021. |
| CSDNAME | object | Census subdivision name. | Imputed from geographic coordinates and city names using GeoSuite 2021. |
| PRUID | int64 | Province unique identifier. | Converted from province code. |

## 3. ODBus source table

`ODBus_Sources.csv` contains **69 rows** and **13 columns**.

| Province/ Territory | City | Dataset Name | Link to Dataset | Link to Dataset License | Attribution Statement (if provided) | License Title  (if provided) | Date last updated as of date of download | Unnamed: 8 | Unnamed: 9 | Unnamed: 10 | Unnamed: 11 | Unnamed: 12 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AB | Banff | Business Licences | https://maps.banff.ca/opendata/ | https://banff.ca/881/Open-Data | Contains information licensed under the Open Government Licence - Banff |  | 1/5/2018 |  |  |  |  |  |
| AB | Calgary | Calgary Business Licences | https://data.calgary.ca/Business-and-Economic-Activity/Calgary-Business-Licences/vdjc-pybd | https://data.calgary.ca/stories/s/Open-Calgary-Terms-of-Use/u45n-7awa | Contains information licensed under the Open Government Licence - City of Calgary. | Open Government Licence -  City of Calgary | .. |  |  |  |  |  |
| AB | Chestermere | Businesses | https://data-chestermere.opendata.arcgis.com/datasets/businesses-2/explore?location=51.036600%2C-113.824000%2C13.01&showTable=true | https://www.chestermere.ca/DocumentCenter/View/13563/OPEN-DATA-LICENCE | Contains information licensed under the Open Data License - City of Chestermere. | Open Government Licence -  City of Calgary | 1/26/2021 |  |  |  |  |  |
| AB | Edmonton | City of Edmonton - Business Licenses | https://data.edmonton.ca/Sustainable-Development/City-of-Edmonton-Business-Licenses/qhi4-bdpu | https://data.edmonton.ca/stories/s/City-of-Edmonton-Open-Data-Terms-of-Use/msh8-if28/ | Contains information licensed under the Open Government Licence - City of Edmont |  | 11/16/2021 |  |  |  |  |  |
| AB | Strathcona County | Business Directory | https://data.strathcona.ca/Business-Economy/Business-Directory/mbdk-4nqc/data | https://open.canada.ca/en/open-government-licence-canada | Contains information licensed under the Open Government Licence - Canada. | Open Government Licence - Canada | 11/13/2021 |  |  |  |  |  |
| BC | Burnaby | Business Licences | https://data.burnaby.ca/pages/open-government-licence | https://data.burnaby.ca/pages/open-government-licence | Contains information licensed under the Open Government Licence - British Columbia. |  | 9/14/2021 |  |  |  |  |  |
| BC | Chilliwack | Business Licenses | https://www.chilliwack.com/main/page.cfm?id=2331&odAction=viewItem&odID=142 | https://www.chilliwack.com/main/page.cfm?id=2391 |  |  | .. |  |  |  |  |  |
| BC | Delta | Business Licences | https://www.delta.ca/your-government/municipal-information/open-data-catalogue | https://www.delta.ca/your-government/municipal-information/open-data/open-data-government-license | Contains information licensed under the Open Government Licence - Delta. | Open Government Licence - Delta | .. |  |  |  |  |  |
| BC | Kelowna | Business Licence | https://opendata.arcgis.com/datasets/f2c521d63ecc46e3a704f38ad79fbbbc_8.geojson | http://apps.kelowna.ca/images/opendata/opengovernmentlicence.pdf | Contains information licensed under the Open Government Licence - City of Kelowna | Open Government License of Kelowna | 8/11/2021 |  |  |  |  |  |
| BC | Langley | Business Licenses | https://data-tol.opendata.arcgis.com/datasets/business-licenses/explore?location=49.097898%2C-122.569883%2C11.00 | https://www.tol.ca/connect/talk-to-us/freedom-of-information/open-data-license/ | Contains information licensed under the Open Government License - Township of Langley. | Open Government License - Township of Langley | 11/17/2021 |  |  |  |  |  |
| BC | Maple Ridge | Business Licences | https://opengov.mapleridge.ca/datasets/business-licences/explore?location=49.235000%2C-122.545000%2C11.76&showTable=true | https://opengov.mapleridge.ca/pages/open-government-licence | Contains information licensed under the Open Government Licence - Maple Ridge | Open Government Licence - Maple Ridge | 8/10/2021 |  |  |  |  |  |
| BC |  | BC Indigenous Business Listings | https://catalogue.data.gov.bc.ca/dataset/bdc81d33-1ab5-4882-9764-8701e8971bb7/resource/f805f66e-8294-4f8d-bdd9-2400eb3938d0/download/bcindigenousbusinesslistings.csv | https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc | Contains information licensed under the Open Government Licence - British Columbia |  | .. |  |  |  |  |  |
| BC |  | Licensed Establishments in B.C. | https://catalogue.data.gov.bc.ca/dataset/2b71813e-fb00-4a8a-a60e-a67a46c81d2d/resource/df13ab03-8e5d-44c6-a3be-b29cb7756877/download/weball2017-11-21.csv | https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc | Contains information licensed under the Open Government Licence - British Columbia |  | .. |  |  |  |  |  |
| BC |  | BC Winery Locations | https://catalogue.data.gov.bc.ca/dataset/1d21922b-ec4f-42e5-8f6b-bf320a286157/resource/ba973b76-072e-4e68-94b7-b7501a9438b5/download/webwinery2017-11-21.csv | https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc | Contains information licensed under the Open Government Licence - British Columbia |  | .. |  |  |  |  |  |
| BC | Nanaimo | Business Licenses | https://www.nanaimo.ca/open-data-catalogue/DataBrowser/nanaimo/BusinessLicences | https://www.nanaimo.ca/your-government/maps-data/open-data-catalogue/open-data-catalogue-licence | Contains information licenced under the Open Government Licence - Nanaimo | Open Government Licence - Nanaimo | .. |  |  |  |  |  |
| BC | New Westminster | Business Licenses (Childcare) | https://opendata.newwestcity.ca/datasets/newwestcity::business-licenses-childcare/explore | https://opendata.newwestcity.ca/pages/terms-of-use | Contains information licenced under the Open Government Licence - City of New Westminster. | Open Government Licence | .. |  |  |  |  |  |
| BC | New Westminster | Business Licenses (Active - Resident) | https://opendata.newwestcity.ca/datasets/business-licenses-residents/explore | http://opendata.newwestcity.ca/licence | Contains information licenced under the Open Government Licence - City of New Westminster. |  | 11/4/2021 |  |  |  |  |  |
| BC | New Westminster | Business Licenses (All) | http://opendata.newwestcity.ca/datasets/business-licenses-all | http://opendata.newwestcity.ca/licence | Contains information licenced under the Open Government Licence - City of New Westminster. | Open Government Licence - City of New Westminster | 11/4/2021 |  |  |  |  |  |
| BC | New Westminster | Business Licenses (New this Year) | https://opendata.newwestcity.ca/datasets/business-licenses-new-this-year/explore | http://opendata.newwestcity.ca/licence | Contains information licenced under the Open Government Licence - City of New Westminster. |  | 11/4/2021 |  |  |  |  |  |
| BC | New Westminster | Business Licenses (Inter-Municipal) | https://opendata.newwestcity.ca/datasets/business-licenses-intermunicipal/explore | http://opendata.newwestcity.ca/licence | Contains information licenced under the Open Government Licence - City of New Westminster. |  | 11/4/2021 |  |  |  |  |  |
| BC | New Westminster | Business Licenses (Non-Residents) | https://opendata.newwestcity.ca/datasets/business-licenses-nonresidents/explore | http://opendata.newwestcity.ca/licence | Contains information licenced under the Open Government Licence - City of New Westminster. |  | 11/4/2021 |  |  |  |  |  |
| BC | Port Moody | Business Directory | https://data.portmoody.ca/datasets/16ebf34b002d41b4b207d167f75ef08f_0/explore?location=49.289213%2C-122.854153%2C13.83 | https://www.portmoody.ca/en/city-hall/open-data-terms-of-use.aspx | Contains information licensed under the Open Government Licence - Port Moody. | Version 2.0 of the Open Government Licence - British Columbia | 11/17/2021 |  |  |  |  |  |
| BC | Port Moody | Business Licenses | https://data.portmoody.ca/datasets/b82634bcf4b247cebaa3096a487ba6f8_0/explore | https://www.portmoody.ca/en/city-hall/open-data-terms-of-use.aspx | Contains information licensed under the Open Government Licence - Port Moody. |  | 11/11/2021 |  |  |  |  |  |
| BC | Prince George | Business License | https://data-cityofpg.opendata.arcgis.com/datasets/business-license-1/explore | https://pgmapinfo.princegeorge.ca/opendata/CityofPrinceGeorge_Open_Government_License_Open_Data.pdf | Contains information licensed under the Open Government License - City of Prince George. | Open Government Licence - Nanaimo | 11/17/2021 |  |  |  |  |  |
| BC | Squamish | Business License Annual 2021 | https://data.squamish.ca/datasets/squamish::business-licence-annual-2021/ | https://squamish.ca/discover-squamish/maps-and-data/open-data/ | Contains information licensed under the Open Government Licence - Squamish |  | 11/15/2021 |  |  |  |  |  |
| BC | Surrey | Business Licenses | https://data.surrey.ca/dataset/business-licences | https://data.surrey.ca/pages/open-government-licence-surrey | Contains information licensed under the Open Government License - City of Surrey. |  | 10/13/2021 |  |  |  |  |  |
| BC | Township of Langley | Business Licenses | https://data-tol.opendata.arcgis.com/datasets/business-licenses | https://www.tol.ca/opengovlicense | Contains information licensed under the Open Government License - Township of Langley. |  | .. |  |  |  |  |  |
| BC | Vancouver | Business licences | https://opendata.vancouver.ca/explore/dataset/business-licences/information/?disjunctive.status&disjunctive.businesssubtype | https://opendata.vancouver.ca/pages/licence/ | Contains information licensed under the Open Government Licence - Vancouver. |  | 11/18/2021 |  |  |  |  |  |
| BC | Vancouver | Business licences 1997 to 2012 | https://opendata.vancouver.ca/explore/dataset/business-licences-1997-to-2012/information/?disjunctive.status&disjunctive.businesssubtype | https://opendata.vancouver.ca/pages/licence/ | Contains information licensed under the Open Government Licence - Vancouver. |  | 3/5/2020 |  |  |  |  |  |
| BC | Victoria | Business Licences - Past 5 Years | https://opendata.victoria.ca/datasets/VicMap::business-licences-past-5-years/explore?location=48.427948%2C-123.358200%2C14.81 | https://opendata.victoria.ca/pages/open-data-licence | Contains information licensed under the Open Government Licence - City of Victoria |  | .. |  |  |  |  |  |
| BC | Victoria | Business Licences Issued Past 10 Years (2011-2020) | https://opendata.victoria.ca/datasets/business-licences-issued-past-10-years-2011-2020/explore | https://opendata.victoria.ca/pages/open-data-licence | Contains information licensed under the Open Government Licence - City of Victoria. |  | 2/12/2021 |  |  |  |  |  |
| BC | Victoria | Business Licences - Current Year | https://opendata.victoria.ca/datasets/business-licences-current-year/explore?location=48.427800%2C-123.358200%2C13.67 | https://opendata.victoria.ca/pages/open-data-licence | Contains information licensed under the Open Government Licence - City of Victoria. |  | 8/11/2021 |  |  |  |  |  |
| MB | Winnipeg | Business Licenses | https://data.winnipeg.ca/Neighbourhood-Liveability-Property-Standards-Licen/Business-Licenses/d5k3-sfzx | https://data.winnipeg.ca/open-data-licence | Contains information licensed under the Open Government Licence - Winnipeg. | Open Government Licence - Canada | 11/1/2021 |  |  |  |  |  |
| NB | Moncton | Grocery stores | https://open.moncton.ca/datasets/grocery-stores/explore?location=46.089028%2C-64.771766%2C12.79&showTable=true | https://ago-item-storage.s3.us-east-1.amazonaws.com/3ec310926cbd436cbaa609d8ee9fac15/Open_Data_Terms_of_Use.pdf?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAwaCXVzLWVhc3QtMSJHMEUCIQD4OImUnBbQKt7fZxWv7W%2B6Ll0XjtmL3AJFM2MgqBEWPQIgAzcTJ%2FZGwLoVaxScWIa8Sp8k3JLeFgbc7TDun%2BxNJiwqgwQIxP%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARAAGgw2MDQ3NTgxMDI2NjUiDFaxpYcL1tc8NXa24irXA3PowJXr4ouiYvG0dCqHGbt0I4WJFf6cZaNkaY%2BN8D11SK8%2BefibeqQtIh3Vbm5M4rK0FpVgqOdlIqHi3A%2FBlys7iqKsTXSPlU0aI1b9vxLxDChYI4a9FFLv%2FifmtnLS84fmbf1HDVBRy5CIEzGNZhFL%2FRYinnmqOA1WrTdsDZtRJebU3iVAlRSBE%2B4ZFLGnmyejK6G8R2wA4jfI380x8c92oqz1gBaXAxpZRBTTYx2JvwwJFh0vwgGWY9WBpprFORFfILvOHYfGUVjucs1jzD3Ns4B5A%2FZ84ikRUQisC7towimIKF8R%2F3tBfHVImuKreqT3Vnk5oACFrjkGRJk8F4gJrjUNgKiEWbx2PPM6ER9SbJPcRijS9RaxG5VrQTeA4yhIUNxBcMd4SLkcBsLMTf4SAI7RxouJ%2Bv4jQAchSvu%2Bv4UCGobhKeu3ywfR5NFf7HFj3k78Ach%2Bsgqv2dDMeHVgUguHQwb%2BzgnyXe5EPfn9dNT5O4rjry%2BPnsDpTdRnA%2B98ruE7%2BrJP0ODPql4IzAPUE79BlUwr5MkEtgJPmbBtfvDnpk63fXLUoXL3Ifzs35OExv5Rkjk6Tc%2FWfs1STi0TksF9UTpeDKyYTW%2Fv13z6qXoLA1LPIjCZy9qMBjqlAWmFyJvYgkmrxwrcmJ1IjWo2yuzazKK%2F1wqwwJHiDn0Z8oq1k%2FcxbCKaO9v4bw5i6HBAANQR0Ds%2BGYhhu%2FK2C8N3sg4bxlfPI1zcBKyRL1ILBQ7J5MPSY4msMEnvGuFmJ8XecSWgKzcBEIdSSUWpcEyQiyg5reVVCEr%2F8DnpdAHspHZqIu8O1uldDuzl11VinPZUcdbOgTeZAn4jIPqAVBd6o8YpUA%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20211118T204142Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAYZTTEKKE6PXCSKHH%2F20211118%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=68ce5006077d3f204724edbd917e13fabdd01748d36d04b7abc01ce236d3ad01 |  |  | 3/23/2020 |  |  |  |  |  |
| NB | Moncton | Pharmacies | https://open.moncton.ca/datasets/pharmacies/explore?location=46.092990%2C-64.785448%2C12.68&showTable=true | https://ago-item-storage.s3.us-east-1.amazonaws.com/3ec310926cbd436cbaa609d8ee9fac15/Open_Data_Terms_of_Use.pdf?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAwaCXVzLWVhc3QtMSJIMEYCIQCAdW%2Bag2UJXkrHPQH%2BrLi%2FNNPneGBq%2BkOzIFdY%2By%2FqyAIhAMEdtTZ2pqazx8FE7lsk3tvIMwSKdZxeBJ97AQEAks3tKoMECMX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQABoMNjA0NzU4MTAyNjY1IgxK%2BkPSVpdRdQEV%2Fcwq1wMoLNv5Oqpdi%2BKbtXaVqt5PVe%2BNuO74Dku8vxIWorVwOVkhHLw1j9xlXFhYEoHVXnbdfjXdpO1JE4xaPUpv7P5wIP3epNOsiPDz2lyZaVgbGciBx3KyqJ%2B3CMuO5%2BqJlFfU3a2OsdI5RKRZMOD6rZmMs8wCtUfEYW3XfDjcc3fQEnMRvBsW9ACh4HTWlyHU7D1%2FWA1NlappMu0qFuSYm9nQfcXY9EmDSsS4aEDIyDeVGOGjS3LNaqzsDQqx82eAFZnd1v7%2BGBO0182Ik9I5Zbqo1jN1VZPfRN284rqCAsU95zo%2BP21NGNKLAnIU0xcTPd3b9%2BVBdzs3IUbF6ZaMqGZgBUt9ctBLFNppDSCQb4bNrWgcs%2FtHRqLK4Nd57w1FGFmpAq87yaTFY19ocm%2Bu0gGOAk0aeu1ihws4QtY%2B12%2BmHdsyy9E%2BYjO8hOp%2Bc4utSUExjTLcaGydxCxchveYlZ9GhiKqWiFLqutWQhZNL%2BwbEb04UPS0J%2FGH5csPeq7GHz7YRwAuQ27BiVDB3V4SIqDbflvCqhhkv7I4Qi79gmseXewGKnu4rDjWQdk5HCrddYxmADLwHxtYuDiJCHeZmSGgk1%2FUs9WYx1jS%2F%2FIQBBfy3b96SOJYKmkw9t7ajAY6pAFgjdaIMyNTraXpqkja443w0r6BKp9VtaIHgc9mrxl4i5XypAVYBHXvbtQKpAnc7u74ShGfBfkQI1eJMKsFf4ofaeN5qkkLLKiU6w2edrtIbArcB5RT1pbHigE7%2F7z2tr7dWoBXyEC8UmdDMjO6jxYKEQMs0FEATg3X%2FwxFhWKdP9kecXRzZWh%2BqkukycGH9qbyHzkd2I%2BQtXxMAHKOR2PTQrom1g%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20211118T204555Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAYZTTEKKERCR5V7F5%2F20211118%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=1031a04a5935401192056b030c256cfda974db29d168ca94628ae49000d13d83 |  |  | 3/19/2020 |  |  |  |  |  |
| NB | Saint John | Grocery Stores | https://catalogue-saintjohn.opendata.arcgis.com/datasets/grocery-stores/explore?location=45.278564%2C-66.049994%2C12.00&showTable=true |  | Contains information licensed under the Open Government Licence - City of Saint John |  | 5/25/2020 |  |  |  |  |  |
| NT | Yellowknife | Business Directory | https://www.yellowknife.ca/en/doing-business/doing-business-open-data.aspx | https://www.yellowknife.ca/en/discovering-yellowknife/resources/geomatic_services/City_of_Yellowknife_Open_Data_LIcence__Terms_of_Use.pdf | Contains public sector Datasets made available under the City of Yellowknife's Open Data License v.1 |  | .. |  |  |  |  |  |
| ON | Ajax | Business Directory | https://opendata.ajax.ca/datasets/DurhamRegion::business-directory/explore?location=44.129582%2C-78.898350%2C9.00 | https://www.durham.ca/en/regional-government/resources/Documents/OpenDataLicenceAgreement.pdf | Contains public sector Information made available under the Regional Municipality of Durham's Open Data Licence | The Regional Municipality of Durham's Open Data Licence | 11/30/2021 |  |  |  |  |  |
| ON | Brampton | Brampton Business Directory | https://geohub.brampton.ca/datasets/brampton-business-directory/explore?location=43.730712%2C-79.750850%2C10.00 | https://creativecommons.org/licenses/by/4.0/ |  | CC BY 4.0 | 11/22/2021 |  |  |  |  |  |
| ON | Caledon | Caledon Business Directory 2018 | https://data.peelregion.ca/datasets/caledon-business-directory-2018/explore?showTable=true | https://data.peelregion.ca/pages/license | Contains public sector Information made available under The Regional Municipality of Peel's Open Data Licence - Version 1.0. | UK Government's Open Government Licence | .. |  |  |  |  |  |
| ON | Cambridge | Business Directory | https://geohub.cambridge.ca/datasets/KitchenerGIS::business-directory/explore?location=43.431511%2C-80.473736%2C12.77 | https://geohub.cambridge.ca/datasets/KitchenerGIS::business-directory/explore?location=43.431492%2C-80.473736%2C12.77 | Contains information licensed under the Open Government Licence - The Corporation of the City of Kitchener. |  | .. |  |  |  |  |  |
| ON | Durham (Oshawa, Ajax, Pickering, Whitby) | Business Directory | https://opendata.durham.ca/datasets/business-directory/explore?location=44.131050%2C-78.898350%2C9.75 | https://www.durham.ca/en/regional-government/resources/Documents/OpenDataLicenceAgreement.pdf | Contains public sector Information made available under the Regional Municipality of Durham's Open Data Licence |  | 11/30/2020 |  |  |  |  |  |
| ON | Durham Region (Oshawa, Pickering) | Business Directory | https://opendata.pickering.ca/datasets/DurhamRegion::business-directory/explore?location=44.131050%2C-78.898350%2C10.23 | https://www.durham.ca/en/regional-government/resources/Documents/OpenDataLicenceAgreement.pdf | Contains public sector Information made available under the RegionalMunicipality of Durham's Open Data Licence |  | .. |  |  |  |  |  |
| ON | Guelph | Business Licenses | http://data.open.guelph.ca/dataset/business-licence/resource/c5deda33-3375-4aea-a55f-17b16c490d42 | http://data.open.guelph.ca/pages/open-government-licence | Contains information provided by the City of Guelph under an open government license | City of Hamilton's Open Data Licence | 11/22/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Basic Food Shops | https://open.hamilton.ca/datasets/59afd6534e4849ccae93c9ed0049a445_14/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Food Establishments | https://open.hamilton.ca/datasets/85c1b5c9e931470d94f0c9ff5acaa341_2/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Kennels and Pet Shops | https://open.hamilton.ca/datasets/c5a848d9c40f4e83acb1cd73ab9f4508_3/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Limousines | https://open.hamilton.ca/datasets/d276c7eb2b2d4a3c972ad18e55cbbcdc_13/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Lodging Houses | https://open.hamilton.ca/datasets/981c055e3c2448b3be3a4644993f59fc_4/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Mobile Food Service Vehicles | https://open.hamilton.ca/datasets/cd820e6df0b74ed2a3c7a9df539de67f_5/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Places of Amusement | https://open.hamilton.ca/datasets/5de18a38cd37457dae49f22c0a9b76b3_7/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Public Garages | https://open.hamilton.ca/datasets/c1e7c884bbea4f26a32118ecf830b764_8/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Public Halls | https://open.hamilton.ca/datasets/044e4d91ba0f4fb2ba162dcd327e6dcc_9/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Trade Contractors & Masters | https://open.hamilton.ca/datasets/f48cbeb4be8847c1bd09731663ef696c_1/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Residential Care Facilities | https://open.hamilton.ca/datasets/e37b13a002544e359350c31b2d48ee47_10/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Salvage Yards | https://open.hamilton.ca/datasets/04317a5ccfe04dad98f8b7a35f3388d1_11/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Hamilton | Licensed Second Hand Shops | https://open.hamilton.ca/datasets/b1f09efe93a549d3b3f600d1d93b5305_12/explore | https://www.hamilton.ca/city-initiatives/strategies-actions/open-data-licence-terms-and-conditions | Contains public sector Data made available under the City of Hamilton's Open Data Licence | City of Hamilton's Open Data Licence | 10/15/2021 |  |  |  |  |  |
| ON | Kitchener/Waterloo | Business Directory | https://geohub.cambridge.ca/datasets/KitchenerGIS::business-directory/explore?location=43.431239%2C-80.473736%2C11.00 | https://www.kitchener.ca/en/council-and-city-administration/open-data-licence.aspx | Contains information licensed under the Open Government Licence - The Corporation of the City of Kitchener | Open Government License - The Corporation of the City of Kitchener | 11/23/2021 |  |  |  |  |  |
| ON | Mississauga | 2019 Mississauga Business Directory | https://opendata.arcgis.com/datasets/f8fa454b6c2d4b1f99a0b51149e2afc1_0.geojson | http://www5.mississauga.ca/research_catalogue/CityofMississauga_TermsofUse.pdf |  | Custom | 2020-03-03 |  |  |  |  |  |
| ON |  | Ontario Environment Business Directory | https://data.ontario.ca/dataset/ontario-environment-business-directory | https://www.ontario.ca/page/copyright-information | © King's Printer for Ontario, 20__.* *The year of first publication of the legal materials is to be completed. | King's Printer for Ontario | .. |  |  |  |  |  |
| ON | Ottawa | Cultural Spaces Inventory | https://open.ottawa.ca/datasets/cultural-spaces-inventory/explore?location=45.619229%2C-75.668228%2C8.48&showTable=true | https://ottawa.ca/en/city-hall/open-transparent-and-accountable-government/open-data#open-data-licence-version-2-0 | Contains information licensed under the Open Government Licence - City of Ottawa. | Open Government Licence - City of Ottawa | .. |  |  |  |  |  |
| ON | Ottawa | Street Food Vendors | https://open.ottawa.ca/datasets/street-food-vendors/explore?location=45.398751%2C-75.710140%2C3.83&showTable=true | https://ottawa.ca/en/city-hall/open-transparent-and-accountable-government/open-data#open-data-licence-version-2-0 | Contains information licensed under the Open Government Licence - City of Ottawa. | Open Government Licence - City of Ottawa | 3/2/2020 |  |  |  |  |  |
| ON | Peel | Business Establishments | https://data.peelregion.ca/datasets/business-establishments/explore | https://www.statcan.gc.ca/en/reference/licence | Source: Statistics Canada, name of product, reference date. Reproduced and distributed on an as is basis with the permission of Statistics Canada. |  | 3/9/2021 |  |  |  |  |  |
| ON |  | Select License and Registration Data | https://data.ontario.ca/dataset/select-licence-and-registration-data | https://www.ontario.ca/page/open-government-licence-ontario | Contains information licensed under the Open Government Licence - Ontario. |  | 4/7/2021 |  |  |  |  |  |
| ON |  | Ontario Environment Business Directory | https://data.ontario.ca/dataset/ontario-environment-business-directory | https://www.ontario.ca/page/copyright-information-c-queens-printer-ontario | Contains information licensed under the Open Government Licence - Ontario. | King's Printer for Ontario, 2022.* |  |  |  |  |  |  |
| ON | Toronto | Business Licences and Permits | https://open.toronto.ca/dataset/municipal-licensing-and-standards-business-licences-and-permits/ | https://open.toronto.ca/open-data-license/ | Contains information licensed under the Open Government Licence - Toronto | Open Government Licence | .. |  |  |  |  |  |
| ON | Welland | Welland Business Directory | https://open.welland.ca/datasets/83cab91d949a48fdbc26763dbe6c3778_2/explore | https://open.welland.ca/pages/terms-of-use | Contains information licensed under the Open Government Licence - City of Welland. | Open Government Licence | .. |  |  |  |  |  |
| ON | Welland | Welland Business Directory | https://open.welland.ca/datasets/welland-business-directory | https://niagaraopendata.ca/pages/open-government-license-2-0-city-of-welland | Contains information licensed under the Open Government Licence - City of Welland. |  | 1/15/2021 |  |  |  |  |  |
| ON | York Region (Markham, Vaughn, Richmond Hill) | York Region 2019 Business Directory | https://insights-york.opendata.arcgis.com/documents/york::york-region-2019-business-directory/about | https://insights-york.opendata.arcgis.com/documents/york-region-open-data-licence/explore | Contains public sector  information made available under The Regional Municipality of York's Open Data Licence | UK Government's Open Government Licence | 8/13/2021 |  |  |  |  |  |

## 4. Provider analysis

- Provider column: `provider`
- Province column: `prov_terr`
- Distinct provider values: **35**

### Records by provider

| Provider | Records | Share % |
| --- | --- | --- |
| City of Toronto | 125681 | 28.14 |
| City of Vancouver | 66846 | 14.97 |
| City of Edmonton | 38573 | 8.64 |
| Regional Municipality of York | 34997 | 7.84 |
| City of Calgary | 34302 | 7.68 |
| City of Burnaby | 18768 | 4.2 |
| City of Surrey | 17099 | 3.83 |
| City of Mississauga | 16506 | 3.7 |
| Government of British Columbia | 11201 | 2.51 |
| City of Kelowna | 10917 | 2.44 |
| Regional Municipality of Durham | 10095 | 2.26 |
| City of Brampton | 9826 | 2.2 |
| City of Victoria | 7107 | 1.59 |
| Township of Langley | 6911 | 1.55 |
| City of Nanaimo | 6189 | 1.39 |
| City of Prince George | 4399 | 0.99 |
| City of New Westminster | 4285 | 0.96 |
| City of Chilliwack | 3358 | 0.75 |
| City of Maple Ridge | 3014 | 0.67 |
| City of Hamilton | 2790 | 0.62 |
| City of Squamish | 2721 | 0.61 |
| Stathcona County | 2474 | 0.55 |
| City of Kitchener | 1898 | 0.43 |
| City of Yellowknife | 1445 | 0.32 |
| Regional Municipality of Peel | 1408 | 0.32 |
| Town of Banff | 942 | 0.21 |
| City of Welland | 941 | 0.21 |
| City of Port Moody | 693 | 0.16 |
| City of Ottawa | 522 | 0.12 |
| Province of Ontario | 249 | 0.06 |
| Government of Nunavut | 171 | 0.04 |
| City of Chestermere | 138 | 0.03 |
| City of Moncton | 92 | 0.02 |
| City of Saint John | 16 | 0.0 |
| <MISSING> | 1 | 0.0 |

### Provider × province distribution

| Provider | Province/Territory | Records |
| --- | --- | --- |
| City of Toronto | ON | 125681 |
| City of Vancouver | BC | 66538 |
| City of Edmonton | AB | 38573 |
| Regional Municipality of York | ON | 34997 |
| City of Calgary | AB | 34302 |
| City of Burnaby | BC | 18768 |
| City of Surrey | BC | 17099 |
| City of Mississauga | ON | 16506 |
| Government of British Columbia | BC | 11201 |
| City of Kelowna | BC | 10917 |
| Regional Municipality of Durham | ON | 10095 |
| City of Brampton | ON | 9826 |
| City of Victoria | BC | 7107 |
| Township of Langley | BC | 6911 |
| City of Nanaimo | BC | 6189 |
| City of Prince George | BC | 4399 |
| City of New Westminster | BC | 4285 |
| City of Chilliwack | BC | 3358 |
| City of Maple Ridge | BC | 3014 |
| City of Hamilton | ON | 2790 |
| City of Squamish | BC | 2721 |
| Stathcona County | AB | 2474 |
| City of Kitchener | ON | 1898 |
| City of Yellowknife | NT | 1445 |
| Regional Municipality of Peel | ON | 1408 |
| Town of Banff | AB | 942 |
| City of Welland | ON | 941 |
| City of Port Moody | BC | 693 |
| City of Ottawa | ON | 522 |
| Province of Ontario | ON | 249 |
| City of Vancouver | ON | 209 |
| Government of Nunavut | NU | 171 |
| City of Chestermere | AB | 138 |
| City of Vancouver | AB | 97 |
| City of Moncton | NB | 92 |
| City of Saint John | NB | 16 |
| City of Vancouver | NB | 2 |
| <MISSING> | <MISSING> | 1 |

## 5. Main dataset fields

- `idx`
- `business_name`
- `alt_business_name`
- `business_sector`
- `business_subsector`
- `business_description`
- `business_id_no`
- `licence_number`
- `licence_type`
- `derived_NAICS`
- `source_NAICS_primary`
- `source_NAICS_secondary`
- `NAICS_descr`
- `NAICS_descr2`
- `latitude`
- `longitude`
- `full_address`
- `postal_code`
- `unit`
- `street_no`
- `street_name`
- `street_direction`
- `street_type`
- `city`
- `prov_terr`
- `total_no_employees`
- `status`
- `provider`
- `geo_source`
- `CSDUID`
- `CSDNAME`
- `PRUID`

## 6. PDF metadata text

The following is extracted text from the supplied `ODBus Metadata.pdf`. It is included for inspection; interpretation should follow the original metadata.

```text

--- PDF PAGE 1 ---
Catalogue no. 21260003 
Issue no. 2023001 
 
 
.. ........................................................................ 
 
Exploring Open Data 
 
 
 
The Open Database of Businesses (ODBus) 
 
Metadata document: concepts, methodology and data quality 
 
 
Version 1.0 
 
 
 
 
 
 
 
 
Data Exploration and Integration Lab (DEIL) 
Centre for Special Business Projects (CSBP) 
  
Release date: November 28, 2023 
 
 
 
 
 
 
 
 
 
 
 
 
 
 


--- PDF PAGE 2 ---
Concepts, Methodology and Data Quality 
 
1 
 
How to obtain more information 
For information about this product or the wide range of services and data available from Statistics Canada, visit our 
website, www.statcan.gc.ca.  
  
You can also contact us by:  
  
Email at STATCAN.infostats-infostats.STATCAN@canada.ca  
 
Telephone, from Monday to Friday, 8:30 a.m. to 4:30 p.m., at the following 
numbers:  
• Statistical Information Service      1-800-263-1136 
• National telecommunications device for the hearing impaired   1-800-363-7629 
• Fax line         1-514-283-9350 
 
Depository Services Program 
• Inquiries line       1-800-635-7943 
• Fax line        1-800-565-7757 
 
 
Standards of service to the public 
Statistics Canada is committed to serving its clients in 
a prompt, reliable and courteous manner. To this end, 
Statistics Canada has developed standards of service 
that its employees observe. To obtain a copy of these 
service standards, please contact Statistics Canada 
toll-free at 1-800-263-1136. The service standards are 
also published on www.statcan.gc.ca under “Contact 
us” > “Standards of service to the public.” 
 
 
Note of appreciation 
Canada owes the success of its statistical system to a 
long‑standing partnership between Statistics Canada, 
the citizens of Canada, its businesses, governments 
and other institutions. Accurate and timely statistical 
information could not be produced without their 
continued co‑operation and goodwill. 
 
 
 
Published by authority of the Minister responsible for Statistics Canada 
© His Majesty the King in Right of Canada as represented by the Minister of Industry, 2023 
All rights reserved. Use of this publication is governed by the Statistics Canada Open Licence Agreement. 
Cette publication est aussi disponible en français. 
 
 
 
  

--- PDF PAGE 3 ---
Concepts, Methodology and Data Quality
 
2 
 
Table of Contents 
1. OVERVIEW .......................................................................................................................................................................... 3 
2. DATA SOURCES ................................................................................................................................................................... 3 
3. REFERENCE PERIOD ............................................................................................................................................................ 3 
4. TARGET POPULATION ......................................................................................................................................................... 3 
DIFFERENTIATION FROM THE BUSINESS REGISTER .................................................................................................................................. 4 
5. COMPILATION METHODOLOGY .......................................................................................................................................... 4 
GEOCODING ................................................................................................................................................................................... 5 
IMPUTATION OF NAICS CODES .......................................................................................................................................................... 5 
IMPUTATION OF CENSUS SUBDIVISION (CSD) NAMES .............................................................................................................................. 6 
DATA STANDARDIZATION .................................................................................................................................................................. 6 
Address Parsing ...................................................................................................................................................................... 6 
Removal of duplicates ............................................................................................................................................................ 6 
Cleaning and Standardization ................................................................................................................................................ 6 
6. DATA DICTIONARY ............................................................................................................................................................. 7 
7. DATA ACCURACY ................................................................................................................................................................ 7 
8. CONTACT US ....................................................................................................................................................................... 7 
 
 
 
 
 
 
 
 
 
 
 
  

--- PDF PAGE 4 ---
Concepts, Methodology and Data Quality
 
3 
 
1. Overview 
For the purpose of exploring open data for official statistics and to support geospatial research across various 
domains, the Data Exploration and Integration Lab (DEIL) undertook a project to create a harmonized database of 
businesses released as open data by various levels of government and other entities within Canada. This 
document details the process of collecting, compiling, and standardizing the individual datasets of the Open 
Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.1  
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from 
available open sources, and many business micro datasets are derived from business licence registration, this 
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple 
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated 
periodically as new open datasets become available.  
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE 
is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing 
a collection of datasets released under a single licence, as well as open-source code to link these datasets 
together. Access to the LODE datasets and code are available through the Statistics Canada website and can be 
found at: 
https://www.statcan.gc.ca/eng/lode 
2. Data sources 
The ODBus is comprised of data from 70 sources. The data providers, which include multiple levels of government 
and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including 
attribution to each data source as per the licence requirements. For further information on the individual licences, 
users should consult directly with the information provided on the open data portals of the various data providers. 
While the province of Quebec also provides their entire business registry 2 as open data, this was not included in 
the ODBus due to licencing incompatibility. 
3. Reference period 
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset 
was last updated by the provider (when known). Data were gathered between May 2022 and December 2022. 
Users are cautioned that the download date should not be used to indicate the reference period of the data. If 
specific information concerning the reference period of data is required, users should contact the appropriate data 
providers. 
4. Target population 
The Open Database of Businesses targets businesses across Canada that are provided within open business 
directories and business license datasets. The scope of businesses collected relies upon the availability of open 
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that 
require a licence to operate are more likely to be included than other types of businesses, although this varies by 
the data source. Depending on the data provider, if businesses are registered separa tely for different licences 
 
1 https://open.canada.ca/en/open-government-licence-canada  
2 https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises 

--- PDF PAGE 5 ---
Concepts, Methodology and Data Quality
 
4 
 
based on business activity, then the same business may appear in multiple records due to their unique licences.  
This database does not define or identify hierarchical structures of businesses and may contain single operating 
locations where goods or services are provided as well as head offices and regional offices. 
Businesses with and without employees are both in scope for this database, however, it is not possible to 
determine within which category a business falls unless the data provider listed an employee count within the 
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a 
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list 
of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data 
download. 
Only minimal editing of the original datasets was performed. As work on the experimental ODBus progresses, 
definitions and thresholds will evolve. Users are reminded that unedited data can be obtained directly from the 
open data portals or from the various data providers, as listed in the Supplemental table of sources mentioned 
above. 
Differentiation from the Business Register 
The Business Register (BR) is Statistics Canada's continuously maintained central repository of information on 
businesses and institutions operating in Canada 3. The ODBus database is separate from the Business Register as 
well as other business data collected at Statistics Canada through surveys and other adm inistrative sources. The 
BR was not used to validate any business entries and cannot be compared to the OD Bus as the data sources, 
processing methods and maintenance are different. 
There are 446,573 records in the ODBus, however this does not cover all businesses in Canada. This count also 
does not include the Enterprise Register of Québec4, which contains over 2.6 million business records. As 
previously mentioned, these records were not included due to license incompatibility. As of December 2022, the 
official release based on the Business Register reports that there were 1,336,336 employer businesses in Canada 
and 3,021,567 non-employer businesses with annual revenues greater than $30,000.5 
5. Compilation methodology 
The primary processing component for the database comprised reformatting the source data to CSV format and 
mapping the original dataset attributes to standard variable (column) names.  To compile the data into a single 
database, the following steps were taken: 
• The original data files and fields were converted to standard formats and fields using the custom 
software OpenTabulate6. 
• Concatenated address data were parsed and separated into their corresponding components (e.g., 
unit, street number and name, city name, etc.) using libpostal7 a natural language processing 
solution for address parsing. 
• Entries missing latitude and longitude information were geocoded by matching parsed addresses 
against the Open Database of Addresses. 
• Deduplication using literal string matching. This was done in a conservative manner to avoid false 
positives (for more details, see Data standardization). 
 
3 Business Register (BR) (statcan.gc.ca) 
4 Registre des entreprises - Registre des entreprises - Données Québec (donneesquebec.ca) 
5 The Daily — Canadian business counts, December 2022 (statcan.gc.ca) 
6 https://pypi.org/project/opentabulate/  
7 https://github.com/openvenues/libpostal  
 

--- PDF PAGE 6 ---
Concepts, Methodology and Data Quality
 
5 
 
• Cleaning and standardization (for more details, see Data standardization). 
While effort was made to ensure that the data is correct, it is possible that the scripts used to process and parse 
the addresses may unintentionally cause other, undetected, errors. Should any such errors be reported, they will 
be corrected in future versions of the ODBus.  
In general, the data included in the ODBus represents what is available from the original sources without 
imputation. The exception to this is the geocoding of entries missing coordinates, and the imputation of CSD 
names and NAICS codes, as discussed below. 
Geocoding 
Records that did not include geocoordinates from the source were geocoded by matching entries against the Open 
Database of Addresses (ODA)8.  
Fuzzy matching was used to compare parsed addresses (street number, street name, city) to corresponding 
columns in the ODA. Records that scored above a conservatively set threshold were taken to be valid matches . 
The geo_source column indicates whether the coordinates of a record were provided by the original source or if 
they were geocoded. 
Imputation of NAICS codes 
The original data sources use a variety of standards, classifications, and nomenclature to describe the business 
type. This database retains all the original descriptions from the data sources, described in section 6 Data 
dictionary. 
However, with the goal of standardizing the enterprise classification, the ODBus uses Statistics Canada’s business 
classification standard, the North American Industry Classification System (NAICS) 9 to provide a standard definition 
of business type. 
Based on the NAICS sector definitions given in Table 1, information found in the source business descriptions and 
business sectors were used to match 86% of business to their corresponding two -digit NAICS codes. Of the NAICS 
codes available in the Open Database of Businesses, 25% were present in the original source material and 61% 
were deduced using keywords found in the business description that were matching the sector definitions. 
Imputation of NAICS codes is done conservatively to avoid false positives. 
Table 1: North American Industry Classification System (NAICS) Canada 2022 Version 1.0  
Code Sector 
11 Agriculture, forestry, fishing and hunting 
21 Mining, quarrying, and oil and gas extraction 
22 Utilities 
23 Construction 
31-33 Manufacturing 
41 Wholesale trade 
44-45 Retail trade 
48-49 Transportation and warehousing 
51 Information and cultural industries 
52 Finance and insurance 
53 Real estate and rental and leasing 
54 Professional, scientific and technical services 
 
8 https://www.statcan.gc.ca/en/lode/databases/oda 
9 https://www.statcan.gc.ca/en/subjects/standard/naics/2022/v1/index 

--- PDF PAGE 7 ---
Concepts, Methodology and Data Quality
 
6 
 
55 Management of companies and enterprises 
56 Administrative and support, waste management and remediation services  
61 Educational services 
62 Health care and social assistance 
71 Arts, entertainment and recreation 
72 Accommodation and food services 
81 Other services (except public administration) 
91 Public administration 
 
Imputation of census subdivision (CSD) names 
Census subdivision (CSD)10 names were derived from latitude and longitude coordinates. These are placed into 
the corresponding CSDs by linking the coordinate points to the CSD polygons through a spatial join operation using 
the Python package GeoPandas11. 
Data standardization 
Due to the different standards adopted in the original sources, steps that were taken to standardize the data could 
possibly produce errors. The key principles of the methodology used were the avoidance of false positives and of 
significant alterations to the data. The methodology and limitations of each technique are described below. Trivial 
cleaning techniques, such as removal of whitespace characters and punctuation removal, are omitted from 
discussion. 
Address Parsing 
The libpostal address parser, an open-source natural language processing solution to parsing addresses, was 
used to split concatenated address strings into strings corresponding to address variables, such as street name 
and street number. Occasionally, addresses were split incorrectly due to unconventional formatting of the original 
address. While effort was made to identify and correct these entries in the final database, some incorrectly parsed 
entries may have remained undetected. Exceptions are entries with street numbers of the form of two numbe rs 
separated by a hyphen or space. Entries of this form usually indicate that the address parser incorrectly parsed a 
numbered street name (e.g., “123 100 ave” is parsed into the street number “123 100” and the street name “ave” ), 
or else that a unit has not been identified correctly (as in “3-100 main st”). Numbers of this form are automatically 
separated, where the right most number is prepended to the street name if the street name is a variant of the word 
“street” or “avenue.”  
Removal of duplicates 
Potential duplicate results were identified by searching for exact matches between variables. Entries were marked 
as duplicates if they matched across the following variables: business names, licence numbers, street numbers, 
street names, postal code, business sector, business description, licence type and primary NAICS code. In cases 
where one record had a null value and the other record had a value for a particular variable, they would be 
considered a match if the remaining variables all had matching values. 
In total, 10,330 records were identified as duplicates. The majority of these occurred between datasets which 
contained businesses from the same geographical area. 
Cleaning and Standardization  
Business records that did not contain a business name were removed from the final database due to limited 
identification possibilities. Business status was changed to a unified labeling namely Active, Not Active, Pending and 
 
10 https://www12.statcan.gc.ca/census-recensement/2021/ref/dict/az/Definition-eng.cfm?ID=geo012  
11 GeoPandas is a Python package for the manipulation of geospatial data: http://geopandas.org/index.html. 

--- PDF PAGE 8 ---
Concepts, Methodology and Data Quality
 
7 
 
Closed, where Closed was removed from the final dataset. The standardisation was as f ollows:  
The following codes and labels were change to “Active”: '1', 'OPEN', 'Licensed', 'Approved', 'APPROVED', 
 'Issued', and 'ISSUED’  
The following codes and labels were changed to “Not Active”: 'Move in Progress', 'Invalid Status Code', and 
 'Close in Progress' 
The following codes and labels were changed to “Pending”: 'Pending', 'Pending Renewal', 'Renewal  
 Licensed', 'Renewal Notification Sent', 'renewal notice', and 'RENEWAL NOTICE'  
The following codes and labels were changed to “Closed”: ‘Out of Business', 'Inactive', and 'Cancelled' 
The latitudes and longitudes of businesses were rounded to 5 decimal points; however, certain records may 
provide less precision if they were received as such from the source material. All personal information such as 
mailing address, phone number, and fax were removed from the final database.  
While the scope of this database covers businesses in Canada and obvious out-of-country businesses were 
removed, it is possible that a few businesses outside of Canada may remain. Some businesses were classified by 
the data providers as “out of town.” Some investigation suggested these businesses did reside in the same location 
as the data provider; however, they conduct business elsewhere and therefore were classified as such. They were 
left as is in the final dataset. 
6. Data dictionary 
The data dictionary describing the variables of the ODBus is available in a supplementary CSV file that 
accompanies the data download, titled “ODBus_record_layout”. 
7. Data accuracy 
All business data in the ODBus were collected from open data sources, either from open data portals or otherwise 
public webpages. In general, other than the processing required to harmonize the different sources into one 
database, the underlying datasets were taken “as is.” 
Natural language processing methods are used to do the parsing and separation of address strings into address 
variables, such as street number and postal code. The methods are reputable for performance and accuracy, but 
as with all statistical learning methods, they have limitations as well. Poor or unconventional formatting of 
addresses may result in incorrect parsing. At this stage, no further integration with other address sources was 
attempted; hence, although address records are generally expected to be correct, residual errors may be present in 
the current version of the database. 
8. Contact Us 
The LODE open databases are modelled on ongoing improvement. To provide information on additions, updates, 
corrections, or omissions, or for more information, please contact us at statcan.lode-ecdo.statcan@statcan.gc.ca. 
Please include the title of the open database in the subject line of the email.  
 
```

## 7. DOCX metadata text

The following is extracted text from the supplied `ODBus Metadata.docx`.

```text
Exploring Open Data
The Open Database of Businesses (ODBus)
Metadata document: concepts, methodology and data quality
Version 1.0
Data Exploration and Integration Lab (DEIL)
Centre for Special Business Projects (CSBP)
Release date: November 28, 2023
How to obtain more information
For information about this product or the wide range of services and data available from Statistics Canada, visit our website, www.statcan.gc.ca.
You can also contact us by:
Email at STATCAN.infostats-infostats.STATCAN@canada.ca
Telephone, from Monday to Friday, 8:30 a.m. to 4:30 p.m., at the following numbers:
Statistical Information Service 					1-800-263-1136
National telecommunications device for the hearing impaired 		1-800-363-7629
Fax line						 		1-514-283-9350
Depository Services Program
Inquiries line							1-800-635-7943
Fax line								1-800-565-7757
Published by authority of the Minister responsible for Statistics Canada
© His Majesty the King in Right of Canada as represented by the Minister of Industry, 2023
All rights reserved. Use of this publication is governed by the Statistics Canada Open Licence Agreement.
Cette publication est aussi disponible en français.
1. Overview
For the purpose of exploring open data for official statistics and to support geospatial research across various domains, the Data Exploration and Integration Lab (DEIL) undertook a project to create a harmonized database of businesses released as open data by various levels of government and other entities within Canada. This document details the process of collecting, compiling, and standardizing the individual datasets of the Open Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from available open sources, and many business micro datasets are derived from business licence registration, this version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple business licences. This is further detailed in section 4, Target Population. The database is expected to be updated periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing a collection of datasets released under a single licence, as well as open-source code to link these datasets together. Access to the LODE datasets and code are available through the Statistics Canada website and can be found at:
https://www.statcan.gc.ca/eng/lode
2. Data sources
The ODBus is comprised of data from 70 sources. The data providers, which include multiple levels of government and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including attribution to each data source as per the licence requirements. For further information on the individual licences, users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry as open data, this was not included in the ODBus due to licencing incompatibility.
3. Reference period
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset was last updated by the provider (when known). Data were gathered between May 2022 and December 2022. Users are cautioned that the download date should not be used to indicate the reference period of the data. If specific information concerning the reference period of data is required, users should contact the appropriate data providers.
4. Target population
The Open Database of Businesses targets businesses across Canada that are provided within open business directories and business license datasets. The scope of businesses collected relies upon the availability of open data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that require a licence to operate are more likely to be included than other types of businesses, although this varies by the data source. Depending on the data provider, if businesses are registered separately for different licences based on business activity, then the same business may appear in multiple records due to their unique licences.
This database does not define or identify hierarchical structures of businesses and may contain single operating locations where goods or services are provided as well as head offices and regional offices.
Businesses with and without employees are both in scope for this database, however, it is not possible to determine within which category a business falls unless the data provider listed an employee count within the source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a complete listing of businesses or representative sample of business activity in Canada. Users may consult the list of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data download.
Only minimal editing of the original datasets was performed. As work on the experimental ODBus progresses, definitions and thresholds will evolve. Users are reminded that unedited data can be obtained directly from the open data portals or from the various data providers, as listed in the Supplemental table of sources mentioned above.
Differentiation from the Business Register
The Business Register (BR) is Statistics Canada's continuously maintained central repository of information on businesses and institutions operating in Canada. The ODBus database is separate from the Business Register as well as other business data collected at Statistics Canada through surveys and other administrative sources. The BR was not used to validate any business entries and cannot be compared to the ODBus as the data sources, processing methods and maintenance are different.
There are 446,573 records in the ODBus, however this does not cover all businesses in Canada. This count also does not include the Enterprise Register of Québec, which contains over 2.6 million business records. As previously mentioned, these records were not included due to license incompatibility. As of December 2022, the official release based on the Business Register reports that there were 1,336,336 employer businesses in Canada and 3,021,567 non-employer businesses with annual revenues greater than $30,000.
5. Compilation methodology
The primary processing component for the database comprised reformatting the source data to CSV format and mapping the original dataset attributes to standard variable (column) names.  To compile the data into a single database, the following steps were taken:
The original data files and fields were converted to standard formats and fields using the custom software OpenTabulate.
Concatenated address data were parsed and separated into their corresponding components (e.g., unit, street number and name, city name, etc.) using libpostal a natural language processing solution for address parsing.
Entries missing latitude and longitude information were geocoded by matching parsed addresses against the Open Database of Addresses.
Deduplication using literal string matching. This was done in a conservative manner to avoid false positives (for more details, see Data standardization).
Cleaning and standardization (for more details, see Data standardization).
While effort was made to ensure that the data is correct, it is possible that the scripts used to process and parse the addresses may unintentionally cause other, undetected, errors. Should any such errors be reported, they will be corrected in future versions of the ODBus.
In general, the data included in the ODBus represents what is available from the original sources without imputation. The exception to this is the geocoding of entries missing coordinates, and the imputation of CSD names and NAICS codes, as discussed below.
Geocoding
Records that did not include geocoordinates from the source were geocoded by matching entries against the Open Database of Addresses (ODA).
Fuzzy matching was used to compare parsed addresses (street number, street name, city) to corresponding columns in the ODA. Records that scored above a conservatively set threshold were taken to be valid matches. The geo_source column indicates whether the coordinates of a record were provided by the original source or if they were geocoded.
Imputation of NAICS codes
The original data sources use a variety of standards, classifications, and nomenclature to describe the business type. This database retains all the original descriptions from the data sources, described in section 6 Data dictionary.
However, with the goal of standardizing the enterprise classification, the ODBus uses Statistics Canada’s business classification standard, the North American Industry Classification System (NAICS) to provide a standard definition of business type.
Based on the NAICS sector definitions given in Table 1, information found in the source business descriptions and business sectors were used to match 86% of business to their corresponding two-digit NAICS codes. Of the NAICS codes available in the Open Database of Businesses, 25% were present in the original source material and 61% were deduced using keywords found in the business description that were matching the sector definitions. Imputation of NAICS codes is done conservatively to avoid false positives.
Table 1: North American Industry Classification System (NAICS) Canada 2022 Version 1.0
Imputation of census subdivision (CSD) names
Census subdivision (CSD) names were derived from latitude and longitude coordinates. These are placed into the corresponding CSDs by linking the coordinate points to the CSD polygons through a spatial join operation using the Python package GeoPandas.
Data standardization
Due to the different standards adopted in the original sources, steps that were taken to standardize the data could possibly produce errors. The key principles of the methodology used were the avoidance of false positives and of significant alterations to the data. The methodology and limitations of each technique are described below. Trivial cleaning techniques, such as removal of whitespace characters and punctuation removal, are omitted from discussion.
Address Parsing
The libpostal address parser, an open-source natural language processing solution to parsing addresses, was used to split concatenated address strings into strings corresponding to address variables, such as street name and street number. Occasionally, addresses were split incorrectly due to unconventional formatting of the original address. While effort was made to identify and correct these entries in the final database, some incorrectly parsed entries may have remained undetected. Exceptions are entries with street numbers of the form of two numbers separated by a hyphen or space. Entries of this form usually indicate that the address parser incorrectly parsed a numbered street name (e.g., “123 100 ave” is parsed into the street number “123 100” and the street name “ave”), or else that a unit has not been identified correctly (as in “3-100 main st”). Numbers of this form are automatically separated, where the right most number is prepended to the street name if the street name is a variant of the word “street” or “avenue.”
Removal of duplicates
Potential duplicate results were identified by searching for exact matches between variables. Entries were marked as duplicates if they matched across the following variables: business names, licence numbers, street numbers, street names, postal code, business sector, business description, licence type and primary NAICS code. In cases where one record had a null value and the other record had a value for a particular variable, they would be considered a match if the remaining variables all had matching values.
In total, 10,330 records were identified as duplicates. The majority of these occurred between datasets which contained businesses from the same geographical area.
Cleaning and Standardization
Business records that did not contain a business name were removed from the final database due to limited identification possibilities. Business status was changed to a unified labeling namely Active, Not Active, Pending and Closed, where Closed was removed from the final dataset. The standardisation was as follows:
The following codes and labels were change to “Active”: '1', 'OPEN', 'Licensed', 'Approved', 'APPROVED', 	'Issued', and 'ISSUED’
The following codes and labels were changed to “Not Active”: 'Move in Progress', 'Invalid Status Code', and 	'Close in Progress'
The following codes and labels were changed to “Pending”: 'Pending', 'Pending Renewal', 'Renewal 		Licensed', 'Renewal Notification Sent', 'renewal notice', and 'RENEWAL NOTICE'
The following codes and labels were changed to “Closed”: ‘Out of Business', 'Inactive', and 'Cancelled'
The latitudes and longitudes of businesses were rounded to 5 decimal points; however, certain records may provide less precision if they were received as such from the source material. All personal information such as mailing address, phone number, and fax were removed from the final database.
While the scope of this database covers businesses in Canada and obvious out-of-country businesses were removed, it is possible that a few businesses outside of Canada may remain. Some businesses were classified by the data providers as “out of town.” Some investigation suggested these businesses did reside in the same location as the data provider; however, they conduct business elsewhere and therefore were classified as such. They were left as is in the final dataset.
6. Data dictionary
The data dictionary describing the variables of the ODBus is available in a supplementary CSV file that accompanies the data download, titled “ODBus_record_layout”.
7. Data accuracy
All business data in the ODBus were collected from open data sources, either from open data portals or otherwise public webpages. In general, other than the processing required to harmonize the different sources into one database, the underlying datasets were taken “as is.”
Natural language processing methods are used to do the parsing and separation of address strings into address variables, such as street number and postal code. The methods are reputable for performance and accuracy, but as with all statistical learning methods, they have limitations as well. Poor or unconventional formatting of addresses may result in incorrect parsing. At this stage, no further integration with other address sources was attempted; hence, although address records are generally expected to be correct, residual errors may be present in the current version of the database.
8. Contact Us
The LODE open databases are modelled on ongoing improvement. To provide information on additions, updates, corrections, or omissions, or for more information, please contact us at statcan.lode-ecdo.statcan@statcan.gc.ca. Please include the title of the open database in the subject line of the email.

--- DOCX TABLE 1 ---
Standards of service to the public
Statistics Canada is committed to serving its clients in a prompt, reliable and courteous manner. To this end, Statistics Canada has developed standards of service that its employees observe. To obtain a copy of these service standards, please contact Statistics Canada toll-free at 1-800-263-1136. The service standards are also published on www.statcan.gc.ca under “Contact us” > “Standards of service to the public.” | Note of appreciation
Canada owes the success of its statistical system to a long‑standing partnership between Statistics Canada, the citizens of Canada, its businesses, governments and other institutions. Accurate and timely statistical information could not be produced without their continued co‑operation and goodwill.

--- DOCX TABLE 2 ---
Code | Sector
11 | Agriculture, forestry, fishing and hunting
21 | Mining, quarrying, and oil and gas extraction
22 | Utilities
23 | Construction
31-33 | Manufacturing
41 | Wholesale trade
44-45 | Retail trade
48-49 | Transportation and warehousing
51 | Information and cultural industries
52 | Finance and insurance
53 | Real estate and rental and leasing
54 | Professional, scientific and technical services
55 | Management of companies and enterprises
56 | Administrative and support, waste management and remediation services
61 | Educational services
62 | Health care and social assistance
71 | Arts, entertainment and recreation
72 | Accommodation and food services
81 | Other services (except public administration)
91 | Public administration
```

## 8. Metadata keyword findings

### Date

```text
Centre for Special Business Projects (CSBP)
Release date: November 28, 2023
--- PDF PAGE 2 ---
Concepts, Methodology and Data Quality
```
```text
2. DATA SOURCES ................................................................................................................................................................... 3
3. REFERENCE PERIOD ............................................................................................................................................................ 3
4. TARGET POPULATION ......................................................................................................................................................... 3
DIFFERENTIATION FROM THE BUSINESS REGISTER .................................................................................................................................. 4
```
```text
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE
```
```text
the ODBus due to licencing incompatibility.
3. Reference period
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset
was last updated by the provider (when known). Data were gathered between May 2022 and December 2022.
```
```text
3. Reference period
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset
was last updated by the provider (when known). Data were gathered between May 2022 and December 2022.
Users are cautioned that the download date should not be used to indicate the reference period of the data. If
```
```text
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset
was last updated by the provider (when known). Data were gathered between May 2022 and December 2022.
Users are cautioned that the download date should not be used to indicate the reference period of the data. If
specific information concerning the reference period of data is required, users should contact the appropriate data
```
```text
was last updated by the provider (when known). Data were gathered between May 2022 and December 2022.
Users are cautioned that the download date should not be used to indicate the reference period of the data. If
specific information concerning the reference period of data is required, users should contact the appropriate data
providers.
```
```text
Users are cautioned that the download date should not be used to indicate the reference period of the data. If
specific information concerning the reference period of data is required, users should contact the appropriate data
providers.
4. Target population
```
```text
well as other business data collected at Statistics Canada through surveys and other adm inistrative sources. The
BR was not used to validate any business entries and cannot be compared to the OD Bus as the data sources,
processing methods and maintenance are different.
There are 446,573 records in the ODBus, however this does not cover all businesses in Canada. This count also
```
```text
8. Contact Us
The LODE open databases are modelled on ongoing improvement. To provide information on additions, updates,
corrections, or omissions, or for more information, please contact us at statcan.lode-ecdo.statcan@statcan.gc.ca.
Please include the title of the open database in the subject line of the email.
```
```text
Centre for Special Business Projects (CSBP)
Release date: November 28, 2023
How to obtain more information
For information about this product or the wide range of services and data available from Statistics Canada, visit our website, www.statcan.gc.ca.
```
```text
For the purpose of exploring open data for official statistics and to support geospatial research across various domains, the Data Exploration and Integration Lab (DEIL) undertook a project to create a harmonized database of businesses released as open data by various levels of government and other entities within Canada. This document details the process of collecting, compiling, and standardizing the individual datasets of the Open Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from available open sources, and many business micro datasets are derived from business licence registration, this version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple business licences. This is further detailed in section 4, Target Population. The database is expected to be updated periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing a collection of datasets released under a single licence, as well as open-source code to link these datasets together. Access to the LODE datasets and code are available through the Statistics Canada website and can be found at:
https://www.statcan.gc.ca/eng/lode
```
```text
While the province of Quebec also provides their entire business registry as open data, this was not included in the ODBus due to licencing incompatibility.
3. Reference period
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset was last updated by the provider (when known). Data were gathered between May 2022 and December 2022. Users are cautioned that the download date should not be used to indicate the reference period of the data. If specific information concerning the reference period of data is required, users should contact the appropriate data providers.
4. Target population
```
```text
3. Reference period
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset was last updated by the provider (when known). Data were gathered between May 2022 and December 2022. Users are cautioned that the download date should not be used to indicate the reference period of the data. If specific information concerning the reference period of data is required, users should contact the appropriate data providers.
4. Target population
The Open Database of Businesses targets businesses across Canada that are provided within open business directories and business license datasets. The scope of businesses collected relies upon the availability of open data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that require a licence to operate are more likely to be included than other types of businesses, although this varies by the data source. Depending on the data provider, if businesses are registered separately for different licences based on business activity, then the same business may appear in multiple records due to their unique licences.
```
```text
Differentiation from the Business Register
The Business Register (BR) is Statistics Canada's continuously maintained central repository of information on businesses and institutions operating in Canada. The ODBus database is separate from the Business Register as well as other business data collected at Statistics Canada through surveys and other administrative sources. The BR was not used to validate any business entries and cannot be compared to the ODBus as the data sources, processing methods and maintenance are different.
There are 446,573 records in the ODBus, however this does not cover all businesses in Canada. This count also does not include the Enterprise Register of Québec, which contains over 2.6 million business records. As previously mentioned, these records were not included due to license incompatibility. As of December 2022, the official release based on the Business Register reports that there were 1,336,336 employer businesses in Canada and 3,021,567 non-employer businesses with annual revenues greater than $30,000.
5. Compilation methodology
```
```text
8. Contact Us
The LODE open databases are modelled on ongoing improvement. To provide information on additions, updates, corrections, or omissions, or for more information, please contact us at statcan.lode-ecdo.statcan@statcan.gc.ca. Please include the title of the open database in the subject line of the email.
--- DOCX TABLE 1 ---
Standards of service to the public
```

### License

```text
© His Majesty the King in Right of Canada as represented by the Minister of Industry, 2023
All rights reserved. Use of this publication is governed by the Statistics Canada Open Licence Agreement.
Cette publication est aussi disponible en français.
--- PDF PAGE 3 ---
```
```text
document details the process of collecting, compiling, and standardizing the individual datasets of the Open
Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.1
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from
available open sources, and many business micro datasets are derived from business licence registration, this
```
```text
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from
available open sources, and many business micro datasets are derived from business licence registration, this
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
```
```text
available open sources, and many business micro datasets are derived from business licence registration, this
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
periodically as new open datasets become available.
```
```text
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE
```
```text
is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing
a collection of datasets released under a single licence, as well as open-source code to link these datasets
together. Access to the LODE datasets and code are available through the Statistics Canada website and can be
found at:
```
```text
and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including
attribution to each data source as per the licence requirements. For further information on the individual licences,
users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry 2 as open data, this was not included in
```
```text
The Open Database of Businesses targets businesses across Canada that are provided within open business
directories and business license datasets. The scope of businesses collected relies upon the availability of open
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that
require a licence to operate are more likely to be included than other types of businesses, although this varies by
```
```text
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that
require a licence to operate are more likely to be included than other types of businesses, although this varies by
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
1 https://open.canada.ca/en/open-government-licence-canada
```
```text
require a licence to operate are more likely to be included than other types of businesses, although this varies by
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
1 https://open.canada.ca/en/open-government-licence-canada
2 https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises
```
```text
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
1 https://open.canada.ca/en/open-government-licence-canada
2 https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises
--- PDF PAGE 5 ---
```
```text
4
based on business activity, then the same business may appear in multiple records due to their unique licences.
This database does not define or identify hierarchical structures of businesses and may contain single operating
locations where goods or services are provided as well as head offices and regional offices.
```
```text
does not include the Enterprise Register of Québec4, which contains over 2.6 million business records. As
previously mentioned, these records were not included due to license incompatibility. As of December 2022, the
official release based on the Business Register reports that there were 1,336,336 employer businesses in Canada
and 3,021,567 non-employer businesses with annual revenues greater than $30,000.5
```
```text
Potential duplicate results were identified by searching for exact matches between variables. Entries were marked
as duplicates if they matched across the following variables: business names, licence numbers, street numbers,
street names, postal code, business sector, business description, licence type and primary NAICS code. In cases
where one record had a null value and the other record had a value for a particular variable, they would be
```
```text
as duplicates if they matched across the following variables: business names, licence numbers, street numbers,
street names, postal code, business sector, business description, licence type and primary NAICS code. In cases
where one record had a null value and the other record had a value for a particular variable, they would be
considered a match if the remaining variables all had matching values.
```
```text
Closed, where Closed was removed from the final dataset. The standardisation was as f ollows:
The following codes and labels were change to “Active”: '1', 'OPEN', 'Licensed', 'Approved', 'APPROVED',
'Issued', and 'ISSUED’
The following codes and labels were changed to “Not Active”: 'Move in Progress', 'Invalid Status Code', and
```
```text
The following codes and labels were changed to “Pending”: 'Pending', 'Pending Renewal', 'Renewal
Licensed', 'Renewal Notification Sent', 'renewal notice', and 'RENEWAL NOTICE'
The following codes and labels were changed to “Closed”: ‘Out of Business', 'Inactive', and 'Cancelled'
The latitudes and longitudes of businesses were rounded to 5 decimal points; however, certain records may
```
```text
© His Majesty the King in Right of Canada as represented by the Minister of Industry, 2023
All rights reserved. Use of this publication is governed by the Statistics Canada Open Licence Agreement.
Cette publication est aussi disponible en français.
1. Overview
```
```text
1. Overview
For the purpose of exploring open data for official statistics and to support geospatial research across various domains, the Data Exploration and Integration Lab (DEIL) undertook a project to create a harmonized database of businesses released as open data by various levels of government and other entities within Canada. This document details the process of collecting, compiling, and standardizing the individual datasets of the Open Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from available open sources, and many business micro datasets are derived from business licence registration, this version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple business licences. This is further detailed in section 4, Target Population. The database is expected to be updated periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing a collection of datasets released under a single licence, as well as open-source code to link these datasets together. Access to the LODE datasets and code are available through the Statistics Canada website and can be found at:
```
```text
For the purpose of exploring open data for official statistics and to support geospatial research across various domains, the Data Exploration and Integration Lab (DEIL) undertook a project to create a harmonized database of businesses released as open data by various levels of government and other entities within Canada. This document details the process of collecting, compiling, and standardizing the individual datasets of the Open Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from available open sources, and many business micro datasets are derived from business licence registration, this version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple business licences. This is further detailed in section 4, Target Population. The database is expected to be updated periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing a collection of datasets released under a single licence, as well as open-source code to link these datasets together. Access to the LODE datasets and code are available through the Statistics Canada website and can be found at:
https://www.statcan.gc.ca/eng/lode
```
```text
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from available open sources, and many business micro datasets are derived from business licence registration, this version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple business licences. This is further detailed in section 4, Target Population. The database is expected to be updated periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing a collection of datasets released under a single licence, as well as open-source code to link these datasets together. Access to the LODE datasets and code are available through the Statistics Canada website and can be found at:
https://www.statcan.gc.ca/eng/lode
2. Data sources
```
```text
2. Data sources
The ODBus is comprised of data from 70 sources. The data providers, which include multiple levels of government and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including attribution to each data source as per the licence requirements. For further information on the individual licences, users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry as open data, this was not included in the ODBus due to licencing incompatibility.
3. Reference period
```
```text
4. Target population
The Open Database of Businesses targets businesses across Canada that are provided within open business directories and business license datasets. The scope of businesses collected relies upon the availability of open data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that require a licence to operate are more likely to be included than other types of businesses, although this varies by the data source. Depending on the data provider, if businesses are registered separately for different licences based on business activity, then the same business may appear in multiple records due to their unique licences.
This database does not define or identify hierarchical structures of businesses and may contain single operating locations where goods or services are provided as well as head offices and regional offices.
Businesses with and without employees are both in scope for this database, however, it is not possible to determine within which category a business falls unless the data provider listed an employee count within the source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a complete listing of businesses or representative sample of business activity in Canada. Users may consult the list of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data download.
```
```text
The Business Register (BR) is Statistics Canada's continuously maintained central repository of information on businesses and institutions operating in Canada. The ODBus database is separate from the Business Register as well as other business data collected at Statistics Canada through surveys and other administrative sources. The BR was not used to validate any business entries and cannot be compared to the ODBus as the data sources, processing methods and maintenance are different.
There are 446,573 records in the ODBus, however this does not cover all businesses in Canada. This count also does not include the Enterprise Register of Québec, which contains over 2.6 million business records. As previously mentioned, these records were not included due to license incompatibility. As of December 2022, the official release based on the Business Register reports that there were 1,336,336 employer businesses in Canada and 3,021,567 non-employer businesses with annual revenues greater than $30,000.
5. Compilation methodology
The primary processing component for the database comprised reformatting the source data to CSV format and mapping the original dataset attributes to standard variable (column) names.  To compile the data into a single database, the following steps were taken:
```
```text
Removal of duplicates
Potential duplicate results were identified by searching for exact matches between variables. Entries were marked as duplicates if they matched across the following variables: business names, licence numbers, street numbers, street names, postal code, business sector, business description, licence type and primary NAICS code. In cases where one record had a null value and the other record had a value for a particular variable, they would be considered a match if the remaining variables all had matching values.
In total, 10,330 records were identified as duplicates. The majority of these occurred between datasets which contained businesses from the same geographical area.
Cleaning and Standardization
```
```text
Business records that did not contain a business name were removed from the final database due to limited identification possibilities. Business status was changed to a unified labeling namely Active, Not Active, Pending and Closed, where Closed was removed from the final dataset. The standardisation was as follows:
The following codes and labels were change to “Active”: '1', 'OPEN', 'Licensed', 'Approved', 'APPROVED', 	'Issued', and 'ISSUED’
The following codes and labels were changed to “Not Active”: 'Move in Progress', 'Invalid Status Code', and 	'Close in Progress'
The following codes and labels were changed to “Pending”: 'Pending', 'Pending Renewal', 'Renewal 		Licensed', 'Renewal Notification Sent', 'renewal notice', and 'RENEWAL NOTICE'
```
```text
The following codes and labels were changed to “Not Active”: 'Move in Progress', 'Invalid Status Code', and 	'Close in Progress'
The following codes and labels were changed to “Pending”: 'Pending', 'Pending Renewal', 'Renewal 		Licensed', 'Renewal Notification Sent', 'renewal notice', and 'RENEWAL NOTICE'
The following codes and labels were changed to “Closed”: ‘Out of Business', 'Inactive', and 'Cancelled'
The latitudes and longitudes of businesses were rounded to 5 decimal points; however, certain records may provide less precision if they were received as such from the source material. All personal information such as mailing address, phone number, and fax were removed from the final database.
```

### Coverage

```text
users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry 2 as open data, this was not included in
the ODBus due to licencing incompatibility.
3. Reference period
```
```text
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list
of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data
download.
Only minimal editing of the original datasets was performed. As work on the experimental ODBus progresses,
```
```text
In total, 10,330 records were identified as duplicates. The majority of these occurred between datasets which
contained businesses from the same geographical area.
Cleaning and Standardization
Business records that did not contain a business name were removed from the final database due to limited
```
```text
The ODBus is comprised of data from 70 sources. The data providers, which include multiple levels of government and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including attribution to each data source as per the licence requirements. For further information on the individual licences, users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry as open data, this was not included in the ODBus due to licencing incompatibility.
3. Reference period
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset was last updated by the provider (when known). Data were gathered between May 2022 and December 2022. Users are cautioned that the download date should not be used to indicate the reference period of the data. If specific information concerning the reference period of data is required, users should contact the appropriate data providers.
```
```text
This database does not define or identify hierarchical structures of businesses and may contain single operating locations where goods or services are provided as well as head offices and regional offices.
Businesses with and without employees are both in scope for this database, however, it is not possible to determine within which category a business falls unless the data provider listed an employee count within the source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a complete listing of businesses or representative sample of business activity in Canada. Users may consult the list of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data download.
Only minimal editing of the original datasets was performed. As work on the experimental ODBus progresses, definitions and thresholds will evolve. Users are reminded that unedited data can be obtained directly from the open data portals or from the various data providers, as listed in the Supplemental table of sources mentioned above.
Differentiation from the Business Register
```
```text
Potential duplicate results were identified by searching for exact matches between variables. Entries were marked as duplicates if they matched across the following variables: business names, licence numbers, street numbers, street names, postal code, business sector, business description, licence type and primary NAICS code. In cases where one record had a null value and the other record had a value for a particular variable, they would be considered a match if the remaining variables all had matching values.
In total, 10,330 records were identified as duplicates. The majority of these occurred between datasets which contained businesses from the same geographical area.
Cleaning and Standardization
Business records that did not contain a business name were removed from the final database due to limited identification possibilities. Business status was changed to a unified labeling namely Active, Not Active, Pending and Closed, where Closed was removed from the final dataset. The standardisation was as follows:
```

### Business Unit

```text
Exploring Open Data
The Open Database of Businesses (ODBus)
Metadata document: concepts, methodology and data quality
Version 1.0
```
```text
Data Exploration and Integration Lab (DEIL)
Centre for Special Business Projects (CSBP)
Release date: November 28, 2023
--- PDF PAGE 2 ---
```
```text
long‑standing partnership between Statistics Canada,
the citizens of Canada, its businesses, governments
and other institutions. Accurate and timely statistical
information could not be produced without their
```
```text
© His Majesty the King in Right of Canada as represented by the Minister of Industry, 2023
All rights reserved. Use of this publication is governed by the Statistics Canada Open Licence Agreement.
Cette publication est aussi disponible en français.
--- PDF PAGE 3 ---
```
```text
4. TARGET POPULATION ......................................................................................................................................................... 3
DIFFERENTIATION FROM THE BUSINESS REGISTER .................................................................................................................................. 4
5. COMPILATION METHODOLOGY .......................................................................................................................................... 4
GEOCODING ................................................................................................................................................................................... 5
```
```text
domains, the Data Exploration and Integration Lab (DEIL) undertook a project to create a harmonized database of
businesses released as open data by various levels of government and other entities within Canada. This
document details the process of collecting, compiling, and standardizing the individual datasets of the Open
Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.1
```
```text
document details the process of collecting, compiling, and standardizing the individual datasets of the Open
Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.1
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from
available open sources, and many business micro datasets are derived from business licence registration, this
```
```text
Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.1
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from
available open sources, and many business micro datasets are derived from business licence registration, this
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
```
```text
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from
available open sources, and many business micro datasets are derived from business licence registration, this
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
```
```text
available open sources, and many business micro datasets are derived from business licence registration, this
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
periodically as new open datasets become available.
```
```text
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE
```
```text
is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing
a collection of datasets released under a single licence, as well as open-source code to link these datasets
together. Access to the LODE datasets and code are available through the Statistics Canada website and can be
found at:
```
```text
and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including
attribution to each data source as per the licence requirements. For further information on the individual licences,
users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry 2 as open data, this was not included in
```
```text
users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry 2 as open data, this was not included in
the ODBus due to licencing incompatibility.
3. Reference period
```
```text
4. Target population
The Open Database of Businesses targets businesses across Canada that are provided within open business
directories and business license datasets. The scope of businesses collected relies upon the availability of open
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that
```
```text
The Open Database of Businesses targets businesses across Canada that are provided within open business
directories and business license datasets. The scope of businesses collected relies upon the availability of open
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that
require a licence to operate are more likely to be included than other types of businesses, although this varies by
```
```text
directories and business license datasets. The scope of businesses collected relies upon the availability of open
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that
require a licence to operate are more likely to be included than other types of businesses, although this varies by
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
```
```text
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that
require a licence to operate are more likely to be included than other types of businesses, although this varies by
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
1 https://open.canada.ca/en/open-government-licence-canada
```
```text
require a licence to operate are more likely to be included than other types of businesses, although this varies by
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
1 https://open.canada.ca/en/open-government-licence-canada
2 https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises
```
```text
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
1 https://open.canada.ca/en/open-government-licence-canada
2 https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises
--- PDF PAGE 5 ---
```
```text
4
based on business activity, then the same business may appear in multiple records due to their unique licences.
This database does not define or identify hierarchical structures of businesses and may contain single operating
locations where goods or services are provided as well as head offices and regional offices.
```
```text
based on business activity, then the same business may appear in multiple records due to their unique licences.
This database does not define or identify hierarchical structures of businesses and may contain single operating
locations where goods or services are provided as well as head offices and regional offices.
Businesses with and without employees are both in scope for this database, however, it is not possible to
```
```text
locations where goods or services are provided as well as head offices and regional offices.
Businesses with and without employees are both in scope for this database, however, it is not possible to
determine within which category a business falls unless the data provider listed an employee count within the
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a
```
```text
Businesses with and without employees are both in scope for this database, however, it is not possible to
determine within which category a business falls unless the data provider listed an employee count within the
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list
```
```text
determine within which category a business falls unless the data provider listed an employee count within the
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list
of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data
```
```text
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list
of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data
download.
```
```text
above.
Differentiation from the Business Register
The Business Register (BR) is Statistics Canada's continuously maintained central repository of information on
businesses and institutions operating in Canada 3. The ODBus database is separate from the Business Register as
```
```text
Differentiation from the Business Register
The Business Register (BR) is Statistics Canada's continuously maintained central repository of information on
businesses and institutions operating in Canada 3. The ODBus database is separate from the Business Register as
well as other business data collected at Statistics Canada through surveys and other adm inistrative sources. The
```
```text
The Business Register (BR) is Statistics Canada's continuously maintained central repository of information on
businesses and institutions operating in Canada 3. The ODBus database is separate from the Business Register as
well as other business data collected at Statistics Canada through surveys and other adm inistrative sources. The
BR was not used to validate any business entries and cannot be compared to the OD Bus as the data sources,
```
```text
businesses and institutions operating in Canada 3. The ODBus database is separate from the Business Register as
well as other business data collected at Statistics Canada through surveys and other adm inistrative sources. The
BR was not used to validate any business entries and cannot be compared to the OD Bus as the data sources,
processing methods and maintenance are different.
```

### Employee

```text
Statistics Canada has developed standards of service
that its employees observe. To obtain a copy of these
service standards, please contact Statistics Canada
toll-free at 1-800-263-1136. The service standards are
```
```text
locations where goods or services are provided as well as head offices and regional offices.
Businesses with and without employees are both in scope for this database, however, it is not possible to
determine within which category a business falls unless the data provider listed an employee count within the
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a
```
```text
Businesses with and without employees are both in scope for this database, however, it is not possible to
determine within which category a business falls unless the data provider listed an employee count within the
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list
```
```text
This database does not define or identify hierarchical structures of businesses and may contain single operating locations where goods or services are provided as well as head offices and regional offices.
Businesses with and without employees are both in scope for this database, however, it is not possible to determine within which category a business falls unless the data provider listed an employee count within the source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a complete listing of businesses or representative sample of business activity in Canada. Users may consult the list of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data download.
Only minimal editing of the original datasets was performed. As work on the experimental ODBus progresses, definitions and thresholds will evolve. Users are reminded that unedited data can be obtained directly from the open data portals or from the various data providers, as listed in the Supplemental table of sources mentioned above.
Differentiation from the Business Register
```
```text
Standards of service to the public
Statistics Canada is committed to serving its clients in a prompt, reliable and courteous manner. To this end, Statistics Canada has developed standards of service that its employees observe. To obtain a copy of these service standards, please contact Statistics Canada toll-free at 1-800-263-1136. The service standards are also published on www.statcan.gc.ca under “Contact us” > “Standards of service to the public.” | Note of appreciation
Canada owes the success of its statistical system to a long‑standing partnership between Statistics Canada, the citizens of Canada, its businesses, governments and other institutions. Accurate and timely statistical information could not be produced without their continued co‑operation and goodwill.
--- DOCX TABLE 2 ---
```

### Provider

```text
1. OVERVIEW .......................................................................................................................................................................... 3
2. DATA SOURCES ................................................................................................................................................................... 3
3. REFERENCE PERIOD ............................................................................................................................................................ 3
4. TARGET POPULATION ......................................................................................................................................................... 3
```
```text
businesses released as open data by various levels of government and other entities within Canada. This
document details the process of collecting, compiling, and standardizing the individual datasets of the Open
Database of Businesses (ODBus), which is made available under the Open Government Licence – Canada.1
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from
```
```text
In its current version (version 1.0), the ODBus contains approximately 450,000 records. As data collection is from
available open sources, and many business micro datasets are derived from business licence registration, this
version of the ODBus focuses on identifying individual licences. Businesses may be duplicated if they hold multiple
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
```
```text
business licences. This is further detailed in section 4, Target Population. The database is expected to be updated
periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE
is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing
```
```text
periodically as new open datasets become available.
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE
is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing
a collection of datasets released under a single licence, as well as open-source code to link these datasets
```
```text
This dataset is one of several datasets created as part of the Linkable Open Data Environment (LODE). The LODE
is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing
a collection of datasets released under a single licence, as well as open-source code to link these datasets
together. Access to the LODE datasets and code are available through the Statistics Canada website and can be
```
```text
is an initiative that aims to enhance the use and harmonization of open data from authoritative sources by providing
a collection of datasets released under a single licence, as well as open-source code to link these datasets
together. Access to the LODE datasets and code are available through the Statistics Canada website and can be
found at:
```
```text
a collection of datasets released under a single licence, as well as open-source code to link these datasets
together. Access to the LODE datasets and code are available through the Statistics Canada website and can be
found at:
https://www.statcan.gc.ca/eng/lode
```
```text
https://www.statcan.gc.ca/eng/lode
2. Data sources
The ODBus is comprised of data from 70 sources. The data providers, which include multiple levels of government
and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including
```
```text
2. Data sources
The ODBus is comprised of data from 70 sources. The data providers, which include multiple levels of government
and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including
attribution to each data source as per the licence requirements. For further information on the individual licences,
```
```text
The ODBus is comprised of data from 70 sources. The data providers, which include multiple levels of government
and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including
attribution to each data source as per the licence requirements. For further information on the individual licences,
users should consult directly with the information provided on the open data portals of the various data providers.
```
```text
and other entities, are outlined in a supplementary CSV file of data sources accompanying the data, including
attribution to each data source as per the licence requirements. For further information on the individual licences,
users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry 2 as open data, this was not included in
```
```text
attribution to each data source as per the licence requirements. For further information on the individual licences,
users should consult directly with the information provided on the open data portals of the various data providers.
While the province of Quebec also provides their entire business registry 2 as open data, this was not included in
the ODBus due to licencing incompatibility.
```
```text
3. Reference period
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset
was last updated by the provider (when known). Data were gathered between May 2022 and December 2022.
Users are cautioned that the download date should not be used to indicate the reference period of the data. If
```
```text
The supplementary CSV file on data sources lists either the update frequency or the date each underlying dataset
was last updated by the provider (when known). Data were gathered between May 2022 and December 2022.
Users are cautioned that the download date should not be used to indicate the reference period of the data. If
specific information concerning the reference period of data is required, users should contact the appropriate data
```
```text
specific information concerning the reference period of data is required, users should contact the appropriate data
providers.
4. Target population
The Open Database of Businesses targets businesses across Canada that are provided within open business
```
```text
The Open Database of Businesses targets businesses across Canada that are provided within open business
directories and business license datasets. The scope of businesses collected relies upon the availability of open
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that
require a licence to operate are more likely to be included than other types of businesses, although this varies by
```
```text
directories and business license datasets. The scope of businesses collected relies upon the availability of open
data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that
require a licence to operate are more likely to be included than other types of businesses, although this varies by
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
```
```text
require a licence to operate are more likely to be included than other types of businesses, although this varies by
the data source. Depending on the data provider, if businesses are registered separa tely for different licences
1 https://open.canada.ca/en/open-government-licence-canada
2 https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises
```
```text
1 https://open.canada.ca/en/open-government-licence-canada
2 https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises
--- PDF PAGE 5 ---
Concepts, Methodology and Data Quality
```
```text
Businesses with and without employees are both in scope for this database, however, it is not possible to
determine within which category a business falls unless the data provider listed an employee count within the
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list
```
```text
determine within which category a business falls unless the data provider listed an employee count within the
source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list
of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data
```
```text
complete listing of businesses or representative sample of business activity in Canada. Users may consult the list
of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data
download.
Only minimal editing of the original datasets was performed. As work on the experimental ODBus progresses,
```
```text
download.
Only minimal editing of the original datasets was performed. As work on the experimental ODBus progresses,
definitions and thresholds will evolve. Users are reminded that unedited data can be obtained directly from the
open data portals or from the various data providers, as listed in the Supplemental table of sources mentioned
```
```text
definitions and thresholds will evolve. Users are reminded that unedited data can be obtained directly from the
open data portals or from the various data providers, as listed in the Supplemental table of sources mentioned
above.
Differentiation from the Business Register
```
```text
businesses and institutions operating in Canada 3. The ODBus database is separate from the Business Register as
well as other business data collected at Statistics Canada through surveys and other adm inistrative sources. The
BR was not used to validate any business entries and cannot be compared to the OD Bus as the data sources,
processing methods and maintenance are different.
```
```text
well as other business data collected at Statistics Canada through surveys and other adm inistrative sources. The
BR was not used to validate any business entries and cannot be compared to the OD Bus as the data sources,
processing methods and maintenance are different.
There are 446,573 records in the ODBus, however this does not cover all businesses in Canada. This count also
```
```text
5. Compilation methodology
The primary processing component for the database comprised reformatting the source data to CSV format and
mapping the original dataset attributes to standard variable (column) names.  To compile the data into a single
database, the following steps were taken:
```
```text
The primary processing component for the database comprised reformatting the source data to CSV format and
mapping the original dataset attributes to standard variable (column) names.  To compile the data into a single
database, the following steps were taken:
• The original data files and fields were converted to standard formats and fields using the custom
```
```text
be corrected in future versions of the ODBus.
In general, the data included in the ODBus represents what is available from the original sources without
imputation. The exception to this is the geocoding of entries missing coordinates, and the imputation of CSD
names and NAICS codes, as discussed below.
```

### Identifier

```text
4
based on business activity, then the same business may appear in multiple records due to their unique licences.
This database does not define or identify hierarchical structures of businesses and may contain single operating
locations where goods or services are provided as well as head offices and regional offices.
```
```text
codes available in the Open Database of Businesses, 25% were present in the original source material and 61%
were deduced using keywords found in the business description that were matching the sector definitions.
Imputation of NAICS codes is done conservatively to avoid false positives.
Table 1: North American Industry Classification System (NAICS) Canada 2022 Version 1.0
```
```text
Due to the different standards adopted in the original sources, steps that were taken to standardize the data could
possibly produce errors. The key principles of the methodology used were the avoidance of false positives and of
significant alterations to the data. The methodology and limitations of each technique are described below. Trivial
cleaning techniques, such as removal of whitespace characters and punctuation removal, are omitted from
```
```text
4. Target population
The Open Database of Businesses targets businesses across Canada that are provided within open business directories and business license datasets. The scope of businesses collected relies upon the availability of open data provided from business directories and municipal, provincial, and federal sources. Therefore, businesses that require a licence to operate are more likely to be included than other types of businesses, although this varies by the data source. Depending on the data provider, if businesses are registered separately for different licences based on business activity, then the same business may appear in multiple records due to their unique licences.
This database does not define or identify hierarchical structures of businesses and may contain single operating locations where goods or services are provided as well as head offices and regional offices.
Businesses with and without employees are both in scope for this database, however, it is not possible to determine within which category a business falls unless the data provider listed an employee count within the source dataset. The ODBus is meant to enhance access to open data on businesses across Canada and is not a complete listing of businesses or representative sample of business activity in Canada. Users may consult the list of data sources to assess the current coverage of the ODBus in the Supplemental table provided with the data download.
```
```text
However, with the goal of standardizing the enterprise classification, the ODBus uses Statistics Canada’s business classification standard, the North American Industry Classification System (NAICS) to provide a standard definition of business type.
Based on the NAICS sector definitions given in Table 1, information found in the source business descriptions and business sectors were used to match 86% of business to their corresponding two-digit NAICS codes. Of the NAICS codes available in the Open Database of Businesses, 25% were present in the original source material and 61% were deduced using keywords found in the business description that were matching the sector definitions. Imputation of NAICS codes is done conservatively to avoid false positives.
Table 1: North American Industry Classification System (NAICS) Canada 2022 Version 1.0
Imputation of census subdivision (CSD) names
```
```text
Data standardization
Due to the different standards adopted in the original sources, steps that were taken to standardize the data could possibly produce errors. The key principles of the methodology used were the avoidance of false positives and of significant alterations to the data. The methodology and limitations of each technique are described below. Trivial cleaning techniques, such as removal of whitespace characters and punctuation removal, are omitted from discussion.
Address Parsing
The libpostal address parser, an open-source natural language processing solution to parsing addresses, was used to split concatenated address strings into strings corresponding to address variables, such as street name and street number. Occasionally, addresses were split incorrectly due to unconventional formatting of the original address. While effort was made to identify and correct these entries in the final database, some incorrectly parsed entries may have remained undetected. Exceptions are entries with street numbers of the form of two numbers separated by a hyphen or space. Entries of this form usually indicate that the address parser incorrectly parsed a numbered street name (e.g., “123 100 ave” is parsed into the street number “123 100” and the street name “ave”), or else that a unit has not been identified correctly (as in “3-100 main st”). Numbers of this form are automatically separated, where the right most number is prepended to the street name if the street name is a variant of the word “street” or “avenue.”
```

## 9. Questions to resolve from this inspection

1. What exactly does one ODBus row represent?
2. What does `business_id_no` uniquely identify?
3. Is `business_id_no` unique globally or only within a provider/source?
4. What does `provider` mean?
5. What organization/dataset does each provider value represent?
6. Why is geographic coverage concentrated in certain provinces/territories?
7. Which source contributes employee information?
8. How is `total_no_employees` constructed?
9. What does `..` mean in each important field?
10. What is the reference date or collection period?
11. What is the update frequency?
12. What are the licensing/commercial-use conditions?
13. Does the source support historical/change detection?
14. Which fields are source-derived versus ODBus-derived?
15. Can records represent multiple establishments or licences belonging to one business?

## 10. Interpretation status

> This report is an evidence-gathering artifact. It does not automatically resolve the semantic meaning of the ODBus fields. Decisions about record grain, identifiers, coverage, employee classification, licensing, or production use should be based on the supplied metadata and source documentation.
