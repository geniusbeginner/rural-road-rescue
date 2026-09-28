# 1c. GeoSadak layers for Kerala

Checked 2026-09-28.

## Access status
- **Live portal https://geosadak-pmgsy.nic.in/OpenData:** COULD NOT OPEN. DNS resolution failed from this machine (`getaddrinfo failed`) and from WebFetch (`ENOTFOUND geosadak-pmgsy.nic.in`). https://pmgsy.nic.in/geosadak timed out after 40 s. I can't tell whether the portal is down, has moved, or blocks some networks, so **I couldn't list the layers the live portal offers today.**
- **What I used instead:** the community mirror https://github.com/datameet/pmgsy-geosadak (last push 2022-07-18, per the GitHub API). **These counts are from the 2022 mirror, not live data.**
- The mirror has no machine-readable licence (the GitHub API licence field is empty); its README states the government licence, quoted below.

## Licence (checked before downloading)
- **Mirror README excerpt:** "Ministry of Rural Development, 2022. PMGSY Rural Connectivity Datasets, https://geosadak-pmgsy.nic.in/opendata/. Published under India's Government Open Data License: https://data.gov.in/government-open-data-license-india". Also: "Terms and Conditions: Government Open Data License https://geosadak-pmgsy.nic.in/MsFiles/TnC.html".
- **Archived terms in the mirror (`PMGSY-TnC-archived.html`), excerpts:** users "are provided a worldwide, royalty-free, non-exclusive license to … (either in original, or in adapted and/or derivative forms), translate, display, add value, and create derivative works (including products and services), for all lawful commercial and non-commercial purposes". Users "must acknowledge the provider, source, and license of data by explicitly publishing the attribution statement". Required format: "[Name of Data Provider], [Year of Publication], [Name of Data], [Name of Data Repository/Website], [Version Number and/or Date of Publication (dd/mm)], [DOI / URL / URI]. Published under [Name of License]: [URL of License]."
- **Caveat:** this is the terms page as archived in 2022. I couldn't open the live terms page.

## Layers for Kerala
The mirror has five Kerala layers plus a national master table. **This list comes from the mirror's file tree, not the live portal.**

| Layer | Mirror file | Geometry | Kerala features | **Wayanad** features (`DISTRICT_I == 587`) |
|---|---|---|---|---|
| Habitation | data/Habitation/Kerala.zip (1.1 MB) | Point | 30,940 | **1,011** |
| Facilities | data/Facilities/Kerala.zip (1.4 MB) | Point | 31,875 | **984** |
| Bound_Block | data/Bound_Block/Kerala.zip (1.6 MB) | Polygon (148) / MultiPolygon (4) | 152 | 4 |
| Proposals | data/Proposals/Kerala.zip (0.3 MB) | LineString | 283 | 8 |
| Road_DRRP | data/Road_DRRP/Kerala.zip (39.5 MB); **not downloaded**, counted from our existing `data/pmgsy/Road_DRRP_Kerala/` | LineString (35,230 + 5 empty) | 35,235 | 876 |
| MasterData.xls | data/MasterData.xls (0.8 MB) | table | not read (see below) | |

**How I identified Wayanad (inference):** I couldn't open `MasterData.xls` because the `xlrd` package isn't installed, and I didn't install it. Instead I point-in-polygon tested against our OSM Wayanad boundary: 1,010 of the 1,011 habitations inside it have `DISTRICT_I = 587` (the other is blank), and all 984 facilities inside it have 587. So "587 = Wayanad" comes from this spatial match, **not from the official ID table.**

**Discrepancy:** our on-disk `data/pmgsy/Road_DRRP_Kerala.zip` is **39,650,382 bytes**; the mirror's `Road_DRRP/Kerala.zip` is **39,476,091 bytes**. They aren't the same file, so ours probably came from a different (perhaps later) download. I didn't compare their contents.

## Field names
- **Habitation:** `HAB_ID` (int), `STATE_ID` (int), `DISTRICT_I` (float), `BLOCK_ID` (int), `HAB_NAME` (str), **`TOT_POPULA`** (float)
- **Facilities:** `STATE_ID`, `DISTRICT_I`, `BLOCK_ID`, `HAB_ID` (links to a habitation), `FACILITY_I`, `FAC_DESC` (free text), `FAC_CATEGO` (category)
- **Bound_Block:** `BLOCK_ID`, `STATE_ID`, `DISTRICT_I`
- **Proposals:** `MRL_ID`, `STATE_ID`, `DISTRICT_I`, `BLOCK_ID`, `CN_CODE`, `PROPOSED_L`, `WORK_NAME`, `IMS_YEAR`, `IMS_BATCH`
- **Road_DRRP:** `ER_ID`, `STATE_ID`, `BLOCK_ID`, `DISTRICT_I`, `DRRP_ROAD_`, `RoadCatego`, `RoadName`, `RoadOwner`

## Does a habitation layer with population exist? **Yes.**
- `TOT_POPULA` in Wayanad (my counts): sum **850,509**; 0 nulls; 0 zeros; min 50; median 625; max 5,451.
- **Source caveats, OSM wiki (https://wiki.openstreetmap.org/wiki/India/PMGSY_rural_connectivty_data_import), excerpts:** "Habitation name and population value estimated by field engineer based on 2011 census". "Habitation locations less than 500m apart have been collapsed". "1 million+ rural habitation points (live data)".
- **Inference:** these are field-engineer estimates, not Census counts. The Wayanad sum (850,509) is higher than the 817,420 district figure in our own code comment (`scripts/village_crosswalk.py`). **I haven't checked 817,420 against a primary Census source.** Because habitations within 500 m were collapsed, a point can stand for more than one settlement.

## Does a health-facility layer exist? **Partly.** It's a general facilities layer with a "Medical" category.
- `FAC_CATEGO` values in Kerala: Agro 17,361; Transport/Admin 6,739; Education 3,899; **Medical 3,876**.
- Wayanad: Agro 443; **Medical 208**; Transport/Admin 185; Education 148.
- **"Medical" isn't limited to human health care.** Wayanad `FAC_DESC` values include "govt veterinary hospital" (8), "veterinary sub centre" (5), "govt ayurveda dispensary" (15), "govt homeo dispensary" (14), private hospitals ("st martin hospital", "leo hospital", "wims hospital"), and PHC/FHC/CHC entries ("family health centre" (8), "primary health centre" (6), "chc panamaram", "phc begur", "district hospital", "govt hospital kalpetta", "thqh sulthan batheri").
- `FAC_DESC` is free text with inconsistent spelling ("vetinary", "dispensery", "primary health cetre"), so using it would need manual classification.
- **OSM wiki excerpt:** "~800k POIs of rural public facilities like school, village office, market, bus stop (static data)".

## Samples saved (small; not used in the pipeline)
- `research/samples/geosadak_wayanad_habitation_sample15.geojson`: 15 Wayanad habitations
- `research/samples/geosadak_wayanad_health_facilities_sample15.geojson`: 15 Wayanad "Medical" facilities
- `research/samples/geosadak_wayanad_proposals_sample5.geojson`: 5 Wayanad proposals
- The full Kerala zips were downloaded to the session scratchpad only, not the repo.
- **Attribution required when these are used:** Ministry of Rural Development, 2022, PMGSY Rural Connectivity Datasets, https://geosadak-pmgsy.nic.in/opendata/, Government Open Data License – India.
