# 1a. Competitor verification

Checked 2026-09-28. **How the evidence was gathered:** "Excerpt" lines are verbatim. They come from raw page or README text pulled with `curl`/`requests` and grepped (not from a summariser), from the GitHub REST API (repository metadata and last commit), or from the Crossref API (paper metadata and abstracts). The "Conclusion" lines are my own reading of that evidence, kept separate. "COULD NOT VERIFY" means I found no source excerpt for that point.

## Summary table

| Tool | Live / maintained | Road removal / disruption scenario | Hazard input | India data | Population | Facility access | Intended user | Overlap |
|---|---|---|---|---|---|---|---|---|
| World Bank **RAM** | **No.** Site ruralaccess.info doesn't resolve; last code commit 2019-05-20 | Yes: road network editing ("impact of road changes") | Not a hazard input as such; only "model the impacts of floods or earthquakes" through network edits | COULD NOT VERIFY | Yes ("population centers") | Yes (travel time to nearest POI) | Road/disaster planners | **Medium-high** (same question; dead code) |
| **MaPLoRds** | Partly: site serves over HTTP, but its **HTTPS certificate has expired**; paper 2025 | "criticality per road links and sub-links"; method COULD NOT VERIFY | Yes (landslides, floods, flash floods) | No (Serbia) | COULD NOT VERIFY | COULD NOT VERIFY | Serbian local municipalities | **Low-medium** |
| **Nepal Road Resilience DSS** (ICEM / World Bank) | Site live (HTTP 200); project 2018–2019 | "criticality assessment"; whether it removes links: COULD NOT VERIFY | Yes (multi-hazard index) | No (Nepal, 8 corridors) | Yes ("population dependent on road sections") | Proxy only ("road intersections as a proxy for access") | World Bank and Nepal Department of Roads | **Low-medium** |
| **PMGSY GRIMMS** (C-DAC) | Page live; awards 2013–2014; no recent date | COULD NOT VERIFY | COULD NOT VERIFY | Yes, but listed states exclude Kerala | Habitations, not population figures | COULD NOT VERIFY | PMGSY administrators | **Low** |
| **PMGSY GeoSadak** | **Portal domain doesn't resolve** (2026-09-28, from two networks); 2022 mirror exists | COULD NOT VERIFY | COULD NOT VERIFY | Yes (all states incl. Kerala, per mirror) | Habitation layer (see 1c) | Facilities layer (see 1c) | PMGSY / public open data | **Low** as a tool, **high** as a data source |
| **ISRO NDEM** | Live (JS app); access **restricted to authorised officials over VPN** | COULD NOT VERIFY | Yes (disaster layers) | Yes | COULD NOT VERIFY | Yes ("shortest path to facility", "Proximity tool … Hospitals") | State and national disaster managers | **Medium** (capability exists; closed) |
| **RA2CE** (Deltares), *not named by you* | **Yes**: last commit 2026-05-07 | **Yes**: "single- or multi-link failure scenarios", "isolated locations" | **Yes**: flood depth rasters etc. | No India data; generic (OSM or shapefile) | Origin counts ("origin_count") | **Yes**: "origin closest destination" | Infrastructure analysts | **HIGH** |
| **AccessGrid AI**, *not named* | Repo created 2026-09-19, 0 stars, no licence | Yes: "simulates road closures" | Yes (preset flood/hazmat scenarios) | **Yes**: Mohali/Chandigarh/Panchkula (urban) | Yes (optional raster, **"synthetic fallback"**) | Yes (hospital access) | Planners / emergency responders | **Medium-high** (same idea, urban, very new) |
| **AccessMod 5** (UNIGE / WHO), *not named* | Yes: last commit 2026-06-05 | COULD NOT VERIFY | COULD NOT VERIFY | Generic | Yes ("catchments of peoples") | Yes | Health planners | **Medium** |
| **GOSTnets** (World Bank), *not named* | Yes: last commit 2026-03-03 | Library only; COULD NOT VERIFY | No | Generic (OSM) | COULD NOT VERIFY | COULD NOT VERIFY | Analysts (Python) | **Low-medium** (building block) |
| **snail / open-gira** (GitHub org "nismod"), *not named* | Yes: last commits 2026-09-08 / 2026-07-24 | COULD NOT VERIFY | Implied by "risk" in description; COULD NOT VERIFY | Generic / global | COULD NOT VERIFY | COULD NOT VERIFY | Researchers | **Low-medium** |

Academic work that overlaps in method is listed at the bottom.

---

## World Bank Rural Accessibility Map (RAM)
- **URLs:** https://github.com/WorldBank-Transport/ram-backend, https://github.com/WorldBank-Transport/ram-frontend, https://github.com/WorldBank-Transport/ram (docs), documentation site http://ruralaccess.info/
- **Live/maintained:** From the GitHub API: ram-backend last commit **2019-05-17**, ram-frontend **2019-05-20**, ram (docs) **2019-10-31**, rah (hub) **2018-09-26**. None is archived; all are MIT. `ruralaccess.info` returned **DNS ENOTFOUND** from both WebFetch and a local `nslookup`.
- **Excerpt (ram-backend README):** "The Rural Accessibility Map allows you to assess the accessibility of rural populations in relation to critical services. Using the Open Source Routing Machine, calculates travel times from population centers to the nearest POI."
- **Excerpt (repository description, GitHub API):** "Calculate regional ETAs, at scale. Measure accessibility. Calculate impact of road changes."
- **Excerpt (ram-backend README):** "ram-iD, a customized version of iD - the popular OSM editor - to allow editing of the road network"
- **Excerpt (https://developmentseed.org/projects/rural-accessibility/):** "Road planners use RAM to determine what road investments will have the greatest impact on access to schools, markets, and hospitals. Disaster planners can use RAM to model the impacts of floods or earthquakes on mobility." Also: "RAM draws its data from OpenStreetMap (OSM) … However you can easily adjust it to use your own points of interest and road network". Also: "Travel times to education facilities near Vientiane, the capital of Laos."
- **Inputs (from the excerpts):** road network (OSM or custom), points of interest, population centres.
- **Hazard input:** no hazard layer is described; flood and earthquake impacts are "modelled" by editing roads. **India data:** COULD NOT VERIFY.
- **Conclusion:** RAM asks the same question as this project (population to nearest facility, change a road, see the effect) but has been unmaintained since 2019 and its site is gone. Overlap medium-high in concept, low as a live competitor.

## MaPLoRds
- **URL:** https://maplords.rgf.bg.ac.rs/ (HTTPS failed: "certificate verify failed: certificate has expired"). http://maplords.rgf.bg.ac.rs/Project returned HTTP 200.
- **Paper (Crossref, DOI 10.1007/978-3-031-72736-8_20):** "MaPLoRds: Mobile Application for Local Road Network Risk Assessment", in *Progress in Landslide Research and Technology*, Vol. 3 Issue 2, 2024 (issued 2025). Authors: Abolmasov, Stanković, Vulović, Marjanović, Đurić, Gudžić. Springer's own page redirected to a login/cookie service, so I didn't use it.
- **Excerpt (Crossref abstract):** "MaPLoRds is a software system developed to enable local municipality users to assess the resilience of their local road network from natural hazards in climate-changing conditions. … A tool for mobile devices (mobile application) is developed to facilitate the data collection in the field and a web application is developed for data analysis, resilience, and priority assessment based on the methodology."
- **Excerpt (/Project page):** "Technical Assistance - Improving Resilience and Safety of the Local Road Transport Network in the Republic of Serbia." "The Methodology evaluates how vulnerable and exposed the local road transport network is to certain hazards, as well as the level of risk and criticality posed by these hazards." "Background 2 – Criticality assessment, per road links and sub-links". Pilots: "Aleksandrovac Municipality … population of 23,551 and a local road network of 407.4km".
- **Removal scenario / population in the analysis / facility access:** COULD NOT VERIFY. The page says "criticality … per road links" but doesn't describe the method.
- **Conclusion:** hazard-exposure scoring for Serbian municipalities, with data collected in the field. Low-medium overlap.

## Nepal Road Resilience DSS
- **URL:** https://nsroads.icem.com.au/ (HTTP 200)
- **Excerpt (site):** "The purpose of the Decision Support System (DSS) is to support The World Bank and the Nepal Department of Roads in prioritising investments in strategic road infrastructure across Nepal. The DSS integrates hydrological, seismic, climate and socio-economic data and information to identify sites of highest vulnerability to climate and seismic threats." "The geographical scope of the project is the eight road corridors which are targeted by the Road Sector Development Project (RSDP) and Nepal-India Regional Trade and Transport Project (NIRTTP)."
- **Excerpt (https://icem.com.au/driving-socio-economic-development-forward-in-nepal-with-resilient-road-networks/, dated February 12, 2020):** "From June 2018 to September 2019, ICEM supported the Government of Nepal through a multi-hazard risk assessment of over 700 km of national roads". Also: "criticality also considered 'local importance' based on settlements and cultivated lands near roads, and road intersections as a proxy for access to economic markets and services; and 'strategic importance', which considers traffic counts and population dependent on road sections."
- **Removal scenario:** COULD NOT VERIFY whether criticality comes from removing links or from an index.
- **Conclusion:** an index-based corridor prioritisation. Facility access appears only as a proxy. Low-medium overlap.

## PMGSY GRIMMS
- **URL:** https://cdac.gov.in/index.aspx?id=st_ssdm_ssdm_grimms (www.cdac.gov.in fails with a certificate hostname mismatch; the bare domain works)
- **Excerpt:** "GIS enabled Road Information Management & Monitoring System (GRIMMS) to provide GIS interface to the Online Monitoring and Management System (OMMS) and manage various activities under 'Pradhan Mantri Gram Sadak Yojana (PMGSY)'." "Guiding investment decisions to match habitation with appropriate roads". "States Covered - Rajasthan, Himachal Pradesh, Odisha, Mizoram, Tripura, Manipur." Awards from "2014" and "2013".
- **Removal, hazard and facility access:** COULD NOT VERIFY. **Kerala:** not in the listed states.
- **Conclusion:** a monitoring and MIS map front-end. Low overlap.

## PMGSY GeoSadak
- **URL:** https://geosadak-pmgsy.nic.in/OpenData. **Couldn't open:** DNS resolution failed from this machine (`getaddrinfo failed`) and from WebFetch (`ENOTFOUND`). https://pmgsy.nic.in/geosadak timed out after 40 s.
- **Mirror:** https://github.com/datameet/pmgsy-geosadak (last push 2022-07-18). **Excerpt:** "Ministry of Rural Development, 2022. PMGSY Rural Connectivity Datasets, https://geosadak-pmgsy.nic.in/opendata/. Published under India's Government Open Data License".
- **Conclusion:** a data source, not an analysis tool (see 1c). As a competitor, low.

## ISRO NDEM
- **URL:** https://ndem.nrsc.gov.in/ (HTTP 200, but the page is a JavaScript app with no readable text); https://ndem.nrsc.gov.in/tpl/About.php returned **404**.
- **Source used:** NDEM User Manual v2.0 (NRSC-RSAA-NDEM-May 2015-TR-705), https://bhuvan-app1.nrsc.gov.in/disaster/get/ndem_vpn_user_manual.pdf. **This is a 2015 document, so it may not reflect the current portal.**
- **Excerpts:** "emergency management such as network tools for finding shortest path to facility, evacuation plan, query on emergency facility". "Proximity Tool: Proximity tool is developed to know the available facilities (Relief Shelters, Hospitals and Railway Stations etc.) around a desired location". "Network Analysis Tool: Network Analysis tool is to get shortest distance". "Only duly authorized persons of the State Governments can obtain the". "NDEM portal is secured; only authorized".
- **Removal scenario and population:** COULD NOT VERIFY.
- **Conclusion:** has shortest-path-to-facility tools and hazard layers for India, but access is restricted to authorised government users. Medium overlap in capability; not openly available.

## RA2CE (Deltares): not in your list, highest overlap
- **URLs:** https://github.com/Deltares/ra2ce, docs https://deltares.github.io/ra2ce/
- **Maintained:** last commit **2026-05-07** (GitHub API).
- **Excerpt (README):** "RA2CE helps to quantify resilience of critical infrastructure networks, prioritize interventions and adaptation measures". "Ra2ce is shared with GPL3 license".
- **Excerpt (docs home page):** "Given a network sourced from OpenStreetMap or a shapefile, and one or more hazard maps (e.g. flood". "Identify critical links, measure redundancy, and compute detour costs under single- or multi-link failure scenarios." "Overlay flood depths and other hazard maps onto networks to identify exposed segments across return periods."
- **Evidence from source code (repository tree, master):** `ra2ce/analysis/losses/multi_link_isolated_locations.py`, whose docstring reads: "A DataFrame summarizing the number of isolated locations per category for the given hazard". `ra2ce/analysis/losses/single_link_redundancy.py`. `ra2ce/analysis/losses/origin_closest_destination.py` (class docstring: "The origin closest destination analyses using NetworkX graphs."; method: "Calculates per origin the location of its closest destination"), whose config includes `origin_count`.
- **India data:** none shipped; takes any OSM area.
- **Conclusion:** RA2CE already does single-link failure, detecting isolated locations, and origin-to-nearest-destination (for example, a hospital) weighted by origin counts, with hazard overlays, on OSM. **This is the closest existing open-source tool to this project.** Checked from the source tree, not by running it: I didn't confirm whether it does exhaustive bridge (single-cut) enclave enumeration the way our bridge tree does.

## AccessGrid AI: not in your list
- **URL:** https://github.com/Aliussman/accessgrid-ai. **Created 2026-09-19**, last commit 2026-09-20, 0 stars, no licence (GitHub API).
- **Excerpt (README):** "Emergency-access digital twin and decision-support platform for the Mohali / Chandigarh / Panchkula (Tri-City) metropolitan area." "A planner or emergency responder simulates road closures, flood inundations, or security cordons; AccessGrid computes which population loses hospital access within the emergency time budget". "`POP_RASTER` — Optional GeoTIFF raster path; synthetic fallback used if unset."
- **Conclusion:** the same idea in India, but urban, nine days old, with an optional synthetic population. Medium-high overlap in concept; maturity not established.

## AccessMod 5: not in your list
- **URL:** https://github.com/unige-geohealth/accessmod (last commit 2026-06-05)
- **Excerpt (README):** "`AccessMod 5` is a tool to analyze geographical accessibility to or from given locations, using anisotropic movements and multimodal transport processes … This package may help to analyze catchments of peoples who can reach a central point in a given time". "developed by the GeoHealth group at the University of Geneva, in collaboration with the World Health Organization".
- **Road-removal scenario / hazard:** COULD NOT VERIFY.
- **Conclusion:** the standard tool for access to health facilities. Medium overlap.

## GOSTnets, snail, open-gira, OSMnx (libraries): not in your list
- GOSTnets (https://github.com/worldbank/GOSTnets), last commit 2026-03-03. Description: "Convenience wrapper for networkx analysis using geospatial information, focusing on OSM".
- snail (https://github.com/nismod/snail), last commit 2026-09-08. Description: "spatial networks impact assessment library".
- open-gira (https://github.com/nismod/open-gira), last commit 2026-07-24. Description: "Open-data Global Infrastructure Risk/Resilience Analysis".
- OSMnx (https://github.com/gboeing/osmnx), last commit 2026-07-31. Description: "Download, model, analyze, and visualize street networks and other geospatial features from OpenStreetMap."
- **Conclusion:** building blocks rather than competing products. I only checked the GitHub API descriptions, not their READMEs.

## Academic work on road-network failure (method overlap)
All metadata is from Crossref (`api.crossref.org/works/<doi>`).
- **Petricola, Reinmuth, Lautenbach, Hatfield, Zipf (2022).** "Assessing road criticality and loss of healthcare accessibility during floods: the case of Cyclone Idai, Mozambique 2019." *International Journal of Health Geographics*, doi 10.1186/s12942-022-00315-2. **Excerpt (abstract):** "Our analysis compares a raster- and a network- based approach that both build on open data with respect to their ability to assess the loss of accessibility due to a severe flood event." **High method overlap.** See 1b.
- **Banik, Paul, Roy (2025).** "A potential interaction-based approach for appraising robustness and identifying critical links of regional road networks exposed to repeated flooding: case study of Dibrugarh district, Assam, India." *Applied Geomatics*, doi 10.1007/s12518-025-00630-w. Crossref has no abstract, so the method can't be verified. **India, district-scale, critical links: medium-high overlap on the title alone.**
- **Joshi, Saharia, Ahmed, Sharma, Ramana (2025).** "Mapping infrastructure vulnerability to landslides in India using high-resolution geospatial data." *Natural Hazards*, doi 10.1007/s11069-025-07256-6. No abstract in Crossref. A search snippet (search engine only) mentions an "Indian Infrastructure Vulnerability to Landslides Dataset and Visualization tool"; **not verified against a primary source.**
- **Contreras et al. (2025).** "Risk Management of Rural Road Networks Exposed to Natural Hazards: Integrating Social Vulnerability and Critical Infrastructure Access in Decision-Making." *Sustainability*, doi 10.3390/su17157101. **Excerpt (abstract):** "this paper proposes a Vulnerability Access Index (VAI) to support road network decision-making that integrates the social vulnerability of rural communities exposed to natural events, their accessibility to nearby critical infrastructu[re]". Study country: COULD NOT VERIFY from the abstract excerpt.
- **"Risk and vulnerability analysis of road network in landslide prone areas in Munnar region, India"** (ScienceDirect, S2666691X24000496). **Search snippet only.** I couldn't confirm the DOI, authors or content (a DOI I guessed resolved to an unrelated paper, so it was discarded).

## Other India-specific search
- Searched for "India rural road network vulnerability critical links landslide flood accessibility tool". Apart from AccessGrid AI and the papers above, **no India-specific, openly available tool** that removes roads and computes loss of facility access turned up. That is absence of evidence from a limited search, not proof that none exists.
