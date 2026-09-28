# Research summary (2026-09-28)

Scope: items 1a–1f. `data/` and `scripts/` were not modified after commit 49c5e8d; the only access to them was reading two files (see Method notes). Details and verbatim excerpts are in each item's file.

## Findings per item

**1a. Competitors** (`competitors.md`)
- **RA2CE (Deltares; open source, GPL3, last commit 2026-05-07)** overlaps most. Its docs say "Identify critical links, measure redundancy, and compute detour costs under single- or multi-link failure scenarios". Its source tree has `multi_link_isolated_locations.py` and `origin_closest_destination.py`, and it takes OSM plus hazard rasters. I didn't confirm whether it enumerates every single-cut enclave the way our bridge tree does.
- **World Bank RAM** has the same core idea (population to nearest facility, edit roads) but is **dead**: last code commit 2019-05-20, and its domain ruralaccess.info doesn't resolve.
- **ISRO NDEM** has shortest-path-to-facility and proximity tools (2015 manual), but access is limited to "duly authorized persons of the State Governments".
- **Nepal DSS** is index-based corridor prioritisation; facility access is only a proxy.
- **MaPLoRds** does hazard/criticality scoring for Serbian municipalities; its HTTPS certificate has expired.
- **GRIMMS** is PMGSY monitoring; its listed states don't include Kerala.
- **GeoSadak** is a data source, and its portal is currently unreachable.
- **AccessGrid AI** (created 2026-09-19): road closures plus hospital-access loss for Mohali/Chandigarh/Panchkula, with a "synthetic fallback" population.
- **Academic:** Petricola et al. 2022 (Mozambique, road criticality plus healthcare access loss in floods) and Banik et al. 2025 (Dibrugarh, Assam: critical links under flooding; abstract not verifiable).

**1b. The "2023 study"** (`study_2023.md`)
- **Found:** Gangwal, Siders, Horney, Michael, Dong, "Critical facility accessibility and road criticality assessment considering flood-induced partial failure", *Sustainable and Resilient Infrastructure* 8(sup1):337–355. Online 2022-11-25; print issue 2023-01-30. https://doi.org/10.1080/23789689.2022.2149184
- Its study area is **Delaware, USA**. It models failure as **partial** ("travel speed reduction") and ranks roads with a **modified betweenness centrality**.

**1c. GeoSadak** (`geosadak_layers.md`)
- The live portal couldn't be reached from two networks. The 2022 datameet mirror has 5 Kerala layers: Habitation, Facilities, Bound_Block, Proposals, Road_DRRP.
- **Habitation, with population (`TOT_POPULA`):** 1,011 in Wayanad, summing to 850,509. Per the OSM wiki, the population is "estimated by field engineer based on 2011 census", and habitations within 500 m were collapsed.
- **Facilities:** 984 in Wayanad; `FAC_CATEGO` "Medical" = 208. This category mixes veterinary, AYUSH, private and government facilities.
- **Road_DRRP:** 876 in Wayanad.
- **Licence:** Government Open Data License – India, with attribution required.
- Three small samples are in `research/samples/`.

**1d. Landslide location** (`landslide_location_check.md`)
- The failed bridge is at **11.4992° N, 76.1601° E** (Scientific Reports 2025). That matches the OSM "Bailey Bridge" way 380928388 to within about 3 m.
- It is **3.3 km from Level 1, 2.6 km from Level 2 and 1.1 km from Level 3**. None of our nested cuts is the bridge that failed.
- GSI, TNM and Scientific Reports all say it was the only route. No source mentions an alternative.
- OSM tags as requested: Meenakshi Bridge (way 380928376) and Kalladi Bridge (way 380928389), both `bridge=yes, highway=primary`. Coordinates are in the file.

**1e. Back-test candidates** (`backtest_candidates.md`)
- **Strongest:** 2024 Mundakkai (coordinates and "only route" statements) and 2019 Puthumala (same valley; only "The area has been cut off" is sourced).
- **Other events:** Koottickal/Kokkayar 2021 (KSDMA table; "Around 50 people were stranded"), Pettimudi 2020 (GSI: "Road and transmission lines damaged"; the bridge claim is on Wikipedia only), Kavalappara 2019 (a footbridge), and the 2018 floods (district-level, Wikipedia only).

**1f. Data sources** (`data_sources.md`)
- **WorldPop:** CC BY 4.0, 100 m GeoTIFF, no login; the national file is 775 MB – 1.84 GB.
- **GSI susceptibility:** Bhukosh is unreachable, but KSDMA hosts the **GSI 2022 district shapefiles** (Wayanad.zip, 3.07 MB, no login). The KSDMA site states "All rights reserved".
- **KSDMA flood return-probability rasters:** "about 1.4 km and rescalled to 90 m"; also "All rights reserved".
- **NRSC 2018 flood layers:** the official download is COULD NOT VERIFY; a community mirror exists.
- **IMD rainfall:** 0.25° daily, 1901–2024; POST form with no visible login; citation requested, no licence.
- No samples were taken; the reasons are given per source.

## Could not verify
- GeoSadak live portal: layer list, current terms and current data (DNS failure, timeout). `MasterData.xls` wasn't read (no `xlrd`), so "district 587 = Wayanad" rests on a spatial match.
- Bhukosh portal: login requirement, formats and licence (connect timeout / refused).
- NDEM: current portal features (JavaScript-only page; About page 404); whether it has link-removal scenarios.
- RAM: India data; MaPLoRds: method, population use and facility access; Nepal DSS: whether criticality involves removing links.
- Whether RA2CE's isolated-locations analysis enumerates all single-cut enclaves.
- Banik et al. 2025 and Joshi et al. 2025 abstracts (not in Crossref). The Munnar road-vulnerability paper (search snippet only; a DOI I guessed was wrong and was discarded).
- Official public availability of NRSC's 2018 Kerala flood GIS layer, and whether the community mirror includes 2018.
- The second of the "Two key bridges" (Scientific Reports) that washed away in 2024.
- Whether `access=permit` on way 380928408 relates to post-2024 restrictions.
- Pettimudi bridge washout (Wikipedia and blog only), the Puthumala "road blocked at Kalladi" snippet, and the Kavalappara "Bhoodanam bridge" snippet.
- The 817,420 Wayanad Census 2011 total quoted in our own code comment: never checked against a primary source.
- Pages blocked by a login or captcha, not bypassed: Springer (login redirect), Taylor & Francis (bot challenge), PMC (reCAPTCHA).

## Contradictions with what's been assumed so far
1. **Our demo's "bridge" cut is not the bridge that failed in 2024.** The map is titled "Vellarimala Bridge Cut", and its primary edge 3249489501–5870049103 is a plain SH59 segment (not bridge-tagged), 3.3 km from the documented failure point. The documented failure is the Chooralmala–Mundakkai bridge (now OSM's Bailey Bridge, way 380928388).
2. **In our 2026 OSM graph, the Bailey Bridge is not a single-link cut**; it isn't in any of the three chains. Three sources say that in July 2024 this bridge was the only route. So either OSM now has another crossing (possibly built or mapped after 2024) or the graph has a spurious connection. **This is the top open question.** I didn't check it because data/ and scripts/ were read-only for this task.
3. **The "2023 study" isn't an India study and isn't a removal study.** It's from the US (Delaware), uses partial failure and betweenness, and first appeared online in Nov 2022. If it was cited as precedent for this exact method, that overstates it.
4. **Open tools already do link failure plus isolation plus nearest-facility analysis.** RA2CE does this, and RAM did before it died. If the pitch assumes no existing open tool does link-failure isolation with facility access, that doesn't hold. What stays distinctive has to be argued differently: for example, exhaustive enclave enumeration, the population rule, Indian data, and boundary-artifact handling.
5. **GeoSadak habitation population isn't Census data**, and it runs higher than our Census-based figure for Wayanad (850,509 vs 817,420). The 817,420 figure itself is unverified.
6. **GeoSadak Facilities could be used to check our curated 34**, but it's noisy: it mixes veterinary and AYUSH facilities under "Medical". It does list "district hospital" and "govt hospital kalpetta", which fits the earlier finding that the curated 34 may be missing government hospitals.

## Method notes
- Excerpts come from raw HTML or PDF text (Python `requests` + `pypdf`, then grep), the GitHub API, the Crossref API, the OpenAlex API, or the OSM API and Overpass. For none of them did I rely on a summariser's paraphrase.
- Two read-only lookups in `data/` (no graph run): `data/osm/wayanad_roads_topology_buf10km.json` (tags of ways 380928388, 794678803, 380928408) and `data/pmgsy/Road_DRRP_Kerala/` (field names and counts).
- Three phrases in the drafts came from my memory and were removed in follow-up commits: a district area, a university affiliation, and a locality.
