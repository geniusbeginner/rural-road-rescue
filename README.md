# The Lifeline — Wayanad case study

Which single road segments, if cut, leave villages with no route in our OSM-derived network to any facility in our curated dataset? This project answers that question for Wayanad district, Kerala, from open data, and checks the answer against real landslide events.

The headline result: removing any of 141 individual road links along the SH59 (Kalpetta–Meppadi) corridor eliminates access from Kalladi, Chooralmala and Mundakai (Vellarimala revenue village, population 7,548 per Census 2011) to every facility in our curated dataset, leaving no route in our OSM-derived network (138 links in the 2024 snapshot). This holds in a 2024-07-29 and a 2026-09-16 snapshot of the network, and under three definitions of which roads count. The area this corridor serves was cut off in the 30 July 2024 landslides, and the corridor itself was blocked by a landslide on 7 July 2026. The analysis does **not** identify the specific bridge that failed in 2024; see the limitations below.

The interactive site is `rural-road-rescue.html` (a single-page application with embedded analysis data and frontend assets; it loads OpenStreetMap map tiles and Google Fonts over the network). It covers the map with a timeline and road-definition toggle, the full enclave atlas, how the result was validated, the errors we found and fixed, and the RA2CE comparison. The earlier demo, `rural-road-map-v1.html`, is kept unchanged.

## Pipeline

| Stage | Script(s) | Main outputs |
|---|---|---|
| 1. Road network (OSM, district extract) | `build_graph.py` | reads `data/osm/wayanad_roads_topology.json` |
| 2. Snap villages and facilities (500 m cap) | `checkpoint2.py` | `data/checkpoint2_results.json` |
| 3. Edge weights (OSM `maxspeed`, else class defaults) and betweenness screen | `checkpoint3_4.py`, `checkpoint4b_aggregate.py` | `data/checkpoint4_top_*.json`, `data/graph_weighted.pkl` |
| 4. Removal test on a high-betweenness corridor | `checkpoint5.py` | `data/checkpoint5_results.json` |
| 5. Census population crosswalk (revenue villages) | `village_crosswalk.py` | `data/village_crosswalk.csv` |
| 6. Exhaustive single-cut search (bridge tree) | `fast_bridge_search.py`, `dramatic_case_test.py` | `data/fast_bridge_results.json`, `data/dramatic_case_result.json` |
| 7. Buffered re-extraction (10 km past the district line, OSM pinned to 2026-09-16) | `buffered_extract.py`, `build_buffered_graph.py` | `data/osm/wayanad_roads_topology_buf10km.json`, `data/graph_buf{10,5}km.pkl` |
| 8. Enclave atlas (real/suspect flags, population rule, spur-snap fix) | `enclave_analysis.py`, `snapping.py` | `data/enclave_atlas.json` |
| 9. Demo data and map | `extract_demo_data.py`, `embed_demo_data.py` | `data/demo_data.json`, `rural-road-map-v1.html` |

The health-facility list (`data/health_facilities_final.json`, 34 facilities) comes from `facility_curation.py`. That script documents the selection rule, and every manual decision with its reason and source (Kerala eHealth institution list, Wayanad district site, OSM landmark checks). One facility's public/private status is unverified.

The investigation scripts in `scripts/investigation/` (pre-event snapshot, road-definition variants, lifecycle tags) are research tools. They read from `data/` and write only to `research/`. `scripts/ra2ce_crosscheck/` reruns the SH59 result in Deltares' RA2CE 1.2.2 (run in a separate environment; see `research/ra2ce_crosscheck.md`).

## Reproducing the results

Requirements: Python 3.13; `pip install -r requirements.txt` installs the exact versions that produced the committed results.

Run from the repository root, in this order:

```
python scripts/checkpoint2.py
python scripts/checkpoint3_4.py          # ~7 min (betweenness, fixed seed)
python scripts/checkpoint4b_aggregate.py # ~9 min; writes data/graph_weighted.pkl
python scripts/checkpoint5.py
python scripts/village_crosswalk.py
python scripts/fast_bridge_search.py
python scripts/dramatic_case_test.py
python scripts/extract_demo_data.py
python scripts/embed_demo_data.py
python scripts/build_buffered_graph.py   # writes data/graph_buf10km.pkl, data/graph_buf5km.pkl and the 5 km extract
python scripts/enclave_analysis.py
```

`.pkl` graphs are not in the repository; the steps above regenerate them. `scripts/buffered_extract.py` re-downloads the 10 km extract from Overpass with the snapshot date pinned; it is only needed if the committed extract is missing. `python scripts/facility_curation.py` prints the facility list and every manual decision (`--write` rewrites `data/health_facilities_final.json`).

### Frontend (`rural-road-rescue.html`)

```
python frontend/build_frontend.py   # rebuilds rural-road-rescue.html from the committed JSON; asserts every displayed number
python frontend/test_frontend.py    # click-through test, desktop + phone; screenshots to frontend/test_shots/ (gitignored)
```

The build needs files that are not committed: `data/graph_buf10km.pkl` (from `build_buffered_graph.py`) and the road-definition extracts `research/investigation/raw/f_{pre,now}_V{0,1,2}.json`. To regenerate those extracts (about 6 minutes in total), after the pipeline above:

```
python scripts/investigation/c_pre_event_extract.py   # downloads the 2024-07-29 OSM extract from Overpass (network needed);
                                                      # compare its hash with research/investigation/pre_event_manifest.json
python scripts/investigation/f_variants.py pre V0     # run V0 before V1/V2 for each snapshot: V1/V2 compare against it
python scripts/investigation/f_variants.py pre V1
python scripts/investigation/f_variants.py pre V2
python scripts/investigation/f_variants.py now V0
python scripts/investigation/f_variants.py now V1
python scripts/investigation/f_variants.py now V2
python scripts/investigation/f_summarize.py
```

The build also reads earlier values from git history (`git show` at the commits cited on the page), so it needs a full clone, not a shallow one. The test needs `playwright` and uses system Chrome, `$CHROME_PATH`, or Playwright's Chromium. It exits 1 if it finds any problem: layout overlap or overflow, blocked taps, unfilled narration, text below 4.5:1 contrast on its rendered background, a slow load fade, or console errors.

## Data sources and licences

- OpenStreetMap roads, places, health POIs and boundary, via Overpass (ODbL). © OpenStreetMap contributors.
- Census of India 2011, District Census Handbook Part XII-B, Wayanad (revenue-village populations).
- Revenue-village boundaries: `data/village_boundaries/village.shp` is DataMeet's Indian Village Boundaries, Kerala layer (https://github.com/datameet/indian_village_boundaries, file `kl/kl.geojson`, last changed in upstream commit `904948290b60`, 2016-09-20), converted to shapefile. Licence: **Open Database License (ODbL) 1.0**, © DataMeet community contributors. The download wasn't recorded at the time. The source was identified on 2026-10-01 by comparison: all 1,533 features match the upstream file row for row, with identical attributes and geometry (maximum vertex difference 0). Under the ODbL, the derived `data/village_boundaries/wayanad_villages_pop.geojson` and `data/village_crosswalk.csv` are also ODbL, and anything published from them must credit DataMeet. Village codes are from Census 2001 (`CEN_2001`); 8 codes appear twice in the upstream data.
- PMGSY GeoSadak data (Government Open Data License – India) was used for exploration only, and is not needed to run the pipeline.

### Files not in this repository

Some exploration-only files are ignored and were removed from the git history to keep the repository small. No script reads them.

- `data/pmgsy/` (about 109 MB): the PMGSY GeoSadak road layer for Kerala (`Road_DRRP_Kerala.zip`, its extracted `Road_DRRP.shp/.dbf/.shx/.prj`, and `pmgsy_wayanad_roads.geojson`). This was a manual download from https://geosadak-pmgsy.nic.in/OpenData, which was unreachable in September 2026. A 2022 community mirror is at https://github.com/datameet/pmgsy-geosadak (`data/Road_DRRP/Kerala.zip`); it is not byte-identical to the copy used here. There is no script to regenerate it.
- `data/osm/wayanad_roads_topology_buf5km.json` (24 MB): regenerate it by running `python scripts/build_buffered_graph.py`, which derives it from the committed 10 km extract (verified byte-identical).
- `data/osm/osm_wayanad_roads*.geojson`, `data/osm/wayanad_highways*.json` (about 82 MB): early OSM exports from the first feasibility check. They were superseded by `data/osm/wayanad_roads_topology.json`.

## Research writeups (`research/`)

- `SUMMARY.md`: overview of the background research
- `competitors.md`: existing tools (RA2CE, RAM, NDEM, …) and how they overlap with this project
- `bridge_investigation.md`: why the 2024 failed bridge is not a single-link cut (a two-crossing cut)
- `followup_validation.md`: sensitivity to road definitions, which bridges failed, lifecycle tags
- `kalladi_2026_check.md`: the 7 July 2026 Kalladi landslide on the SH59 corridor
- `ra2ce_crosscheck.md`: the SH59 result rerun in RA2CE 1.2.2, and the three ways RA2CE's method differs (with source line links)
- `landslide_location_check.md`, `backtest_candidates.md`, `data_sources.md`, `geosadak_layers.md`, `study_2023.md`

## Known limitations

- Travel speeds are assumed from road class where OSM has no `maxspeed` tag; times are estimates.
- Whether the failed 2024 bridge is a single point of failure depends on whether an unpaved track counts as a usable road. The analysis identifies the corridor, not that bridge (1.1–3.3 km away).
- The facility list is curated, not an official complete list.
- On phones, the v1 demo's (`rural-road-map-v1.html`) detail panel is long, and one map label collides with a travel-time chip. `rural-road-rescue.html` replaces it; v1 is kept unchanged.
