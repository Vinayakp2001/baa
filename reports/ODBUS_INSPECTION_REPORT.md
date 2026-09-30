# ODBus Inspection Report

Generated from `ODBus_2023.zip`.

## Archive

- ZIP: `C:\Users\LENOVO\Desktop\baa\data\raw\ODBus_2023.zip`
- Archive members: 6

### Files in archive

- `ODBus_v1/`
- `ODBus_v1/ODBus Metadata.docx`
- `ODBus_v1/ODBus Metadata.pdf`
- `ODBus_v1/ODBus-record-layout.csv`
- `ODBus_v1/ODBus_Sources.csv`
- `ODBus_v1/ODBus_v1.csv`

## Tabular file inspection

| File | Encoding | Delimiter | Rows | Columns |
| --- | --- | --- | --- | --- |
| ODBus_v1/ODBus-record-layout.csv | cp1252 | ',' | 32 | 4 |
| ODBus_v1/ODBus_Sources.csv | cp1252 | ',' | 69 | 13 |
| ODBus_v1/ODBus_v1.csv | utf-8-sig | ',' | 446,575 | 32 |

## Main ODBus dataset

- Rows: **446,575**
- Columns: **32**
- Detected ID column: `business_id_no`
- Detected business-name column: `business_name`

### Columns

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

### Detected business-data fields

| Logical field | Detected columns |
| --- | --- |
| business_name | `business_name`, `alt_business_name`, `street_name`, `CSDNAME` |
| business_id | `idx`, `business_id_no`, `provider`, `CSDUID`, `PRUID` |
| province | `prov_terr`, `provider` |
| municipality | `city` |
| postal_code | `postal_code` |
| address | `full_address`, `street_no`, `street_name`, `street_direction`, `street_type` |
| naics | `derived_NAICS`, `source_NAICS_primary`, `source_NAICS_secondary`, `NAICS_descr`, `NAICS_descr2` |
| employee | `total_no_employees` |
| status | `status` |
| licence | `licence_number`, `licence_type` |
| latitude | `latitude` |
| longitude | `longitude` |

### Missingness

| Column | Missing/blank rows | Missing % |
| --- | --- | --- |
| idx | 2 | 0.0 |
| alt_business_name | 1 | 0.0 |
| business_sector | 1 | 0.0 |
| business_subsector | 1 | 0.0 |
| business_description | 1 | 0.0 |
| business_id_no | 1 | 0.0 |
| licence_number | 1 | 0.0 |
| licence_type | 1 | 0.0 |
| derived_NAICS | 1 | 0.0 |
| source_NAICS_primary | 1 | 0.0 |
| source_NAICS_secondary | 1 | 0.0 |
| NAICS_descr | 1 | 0.0 |
| NAICS_descr2 | 1 | 0.0 |
| latitude | 1 | 0.0 |
| longitude | 1 | 0.0 |
| full_address | 1 | 0.0 |
| postal_code | 1 | 0.0 |
| unit | 1 | 0.0 |
| street_no | 1 | 0.0 |
| street_name | 1 | 0.0 |
| street_direction | 1 | 0.0 |
| street_type | 1 | 0.0 |
| city | 1 | 0.0 |
| prov_terr | 1 | 0.0 |
| total_no_employees | 1 | 0.0 |
| status | 1 | 0.0 |
| provider | 1 | 0.0 |
| geo_source | 1 | 0.0 |
| CSDUID | 1 | 0.0 |
| CSDNAME | 1 | 0.0 |
| PRUID | 1 | 0.0 |
| business_name | 0 | 0.0 |

### Province distribution

| Province | Rows |
| --- | --- |
| ON | 205122 |
| BC | 163200 |
| AB | 76526 |
| NT | 1445 |
| NU | 171 |
| NB | 110 |
| <MISSING> | 1 |

### Employee-related distributions

#### `total_no_employees`

| Value | Rows |
| --- | --- |
| .. | 318230 |
| 0 | 22254 |
| 1 | 16871 |
| 1--4 | 14853 |
| 1 to 4 | 8375 |
| 5--9 | 7775 |
| 2 | 7637 |
| 10--19 | 4809 |
| 3 | 4728 |
| 5 to 9 | 3766 |
| 4 | 3540 |
| 20--49 | 3249 |
| 5 | 3081 |
| 10 to 19 | 2477 |
| 6 | 2366 |
| NOT AVAILABLE | 1980 |
| 20 to 49 | 1865 |
| 10 | 1608 |
| 8 | 1445 |
| 7 | 1418 |
| 50--99 | 1288 |
| 100--499 | 979 |
| 12 | 867 |
| 15 | 788 |
| 50 to 99 | 786 |
| 9 | 740 |
| 20 | 707 |
| 11 | 492 |
| 100 to 299 | 455 |
| 25 | 410 |
| 30 | 399 |
| 14 | 381 |
| 13 | 363 |
| 16 | 298 |
| 50 | 261 |
| 18 | 260 |
| 40 | 255 |
| 17 | 180 |
| 35 | 170 |
| 60 | 167 |
| 22 | 148 |
| 19 | 146 |
| 100 | 130 |
| 28 | 114 |
| 85 | 113 |
| 45 | 110 |
| 21 | 108 |
| 23 | 106 |
| 24 | 98 |
| 26 | 95 |

### NAICS distribution

| NAICS value | Rows |
| --- | --- |
| 72 | 78435 |
| 44 | 71158 |
| .. | 64428 |
| 23 | 50189 |
| 81 | 41762 |
| 54 | 23418 |
| 53 | 21505 |
| 62 | 17323 |
| 91 | 13256 |
| 41 | 10753 |
| 56 | 8497 |
| 61 | 7554 |
| 52 | 6718 |
| 71 | 6480 |
| 31 | 5640 |
| 48 | 4491 |
| 33 | 4219 |
| 45 | 3135 |
| 32 | 2203 |
| 51 | 1864 |
| 55 | 999 |
| 11 | 991 |
| 49 | 812 |
| 21 | 577 |
| 22 | 152 |
| 42 | 15 |
| <MISSING> | 1 |

### Status distribution

| Status | Rows |
| --- | --- |
| .. | 284422 |
| Active | 109590 |
| Pending | 52444 |
| Not Active | 118 |
| <MISSING> | 1 |

## Duplicate indicators

- Rows involved in duplicate IDs: **393,603**
- Rows involved in repeated normalized business names: **162,549**

> Repeated names are not automatically duplicates. Address, postal code, phone, corporation number, and other identifiers must be considered before entity merging.

## Sample records

| idx | business_name | alt_business_name | business_sector | business_subsector | business_description | business_id_no | licence_number | licence_type | derived_NAICS | source_NAICS_primary | source_NAICS_secondary | NAICS_descr | NAICS_descr2 | latitude | longitude | full_address | postal_code | unit | street_no | street_name | street_direction | street_type | city | prov_terr | total_no_employees | status | provider | geo_source | CSDUID | CSDNAME | PRUID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8bcde34e196bcbb440a2 | Healthconnect Pharmacy | .. | Community Pharmacy | .. | .. | .. | .. | .. | 44 | .. | .. | .. | .. | 46.09593 | -64.87099 | 10 Desbrisay Avenue, Unit 2, Moncton Nb | .. | Unit 2 | 10 | Desbrisay Avenue | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1307022 | Moncton | 13 |
| 87cfdddd858f54356f04 | Innomar Pharmacy Inc. | .. | Community Pharmacy | .. | .. | .. | .. | .. | 44 | .. | .. | .. | .. | 46.10593 | -64.80623 | 100 Arden Street, Suite 309, Moncton Nb | .. | Suite 309 | 100 | Arden Street | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1307022 | Moncton | 13 |
| 263962f164fdbeba64a0 | Express Scripts Canada Pharmacy | .. | Community Pharmacy | .. | .. | .. | .. | .. | 44 | .. | .. | .. | .. | 46.10351 | -64.70646 | 1040 Champlain Street, Dieppe Nb | .. | .. | 1040 | Champlain Street | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1307045 | Dieppe | 13 |
| f0ea2ef9552a6ade5430 | Tomavo | .. | Limited Groceries | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | 46.10473 | -64.81922 | 1063 Mountain Rd | .. | .. | 1063 | Mountain Rd | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1307022 | Moncton | 13 |
| 7f7958a5f4736f09aa22 | Cameron Street Clinic | .. | Community Pharmacy | .. | .. | .. | .. | .. | 44 | .. | .. | .. | .. | 46.08854 | -64.78849 | 107 Cameron Street P.O. Box 792 | .. | .. | 107 | Cameron Street | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1307022 | Moncton | 13 |
| 00a6c5155831532385b5 | Sobeys Pharmacy # 736 | .. | Community Pharmacy | .. | .. | .. | .. | .. | 44 | .. | .. | .. | .. | 46.04933 | -64.79456 | 1160 Findlay Boulevard, Dieppe Nb | .. | .. | 1160 | Findlay Boulevard | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1306020 | Riverview | 13 |
| 4f7243d1e7f761de3033 | Sobey's | .. | General Groceries | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | 46.04939 | -64.79474 | 1160 Findlay Blvd | .. | .. | 1160 | Findlay Blvd | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1306020 | Riverview | 13 |
| 4e453d5aed197d140ed5 | The Medicine Shoppe Pharmacy | .. | Community Pharmacy | .. | .. | .. | .. | .. | 44 | .. | .. | .. | .. | 46.10301 | -64.76212 | 120 Shediac Road , Moncton Nb | .. | .. | 120 | Shediac Road | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1307022 | Moncton | 13 |
| 86560a06c3a8174ef35c | Moncton Market | .. | Limited Groceries | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | 46.0873 | -64.77847 | 120 Westmorland St | .. | .. | 120 | Westmorland St | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1307022 | Moncton | 13 |
| b3677bc4972cbe7f63a6 | Taste of Homeland | .. | Limited Groceries | .. | .. | .. | .. | .. | .. | .. | .. | .. | .. | 46.10797 | -64.82567 | 1201 Mountain Rd | .. | .. | 1201 | Mountain Rd | .. | .. | Moncton | NB | .. | .. | City of Moncton | Source | 1307022 | Moncton | 13 |

## Data types

| Column | Pandas dtype |
| --- | --- |
| idx | str |
| business_name | str |
| alt_business_name | str |
| business_sector | str |
| business_subsector | str |
| business_description | str |
| business_id_no | str |
| licence_number | str |
| licence_type | str |
| derived_NAICS | str |
| source_NAICS_primary | str |
| source_NAICS_secondary | str |
| NAICS_descr | str |
| NAICS_descr2 | str |
| latitude | str |
| longitude | str |
| full_address | str |
| postal_code | str |
| unit | str |
| street_no | str |
| street_name | str |
| street_direction | str |
| street_type | str |
| city | str |
| prov_terr | str |
| total_no_employees | str |
| status | str |
| provider | str |
| geo_source | str |
| CSDUID | str |
| CSDNAME | str |
| PRUID | str |

## Initial interpretation

This report is an inspection artifact, not a final data-quality assessment. Before using ODBus in the production pipeline, verify:

1. Actual field semantics against the supplied ODBus metadata.
2. Geographic coverage across Canada.
3. Whether employee information is suitable for the required employee-size buckets.
4. Whether business status and licence information can support new-business/change detection.
5. Whether records can be safely linked to other sources.
6. The licensing terms and permitted commercial use.
7. Whether ODBus is current enough for the intended lead-generation use case.

The production system should treat ODBus as one source among multiple sources and preserve source provenance rather than overwriting conflicting observations.
