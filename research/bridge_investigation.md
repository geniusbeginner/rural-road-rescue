# Why isn't the Bailey Bridge (OSM way 380928388) a single-link cut?

Investigation run 2026-09-28. No files in `data/` or `scripts/` were modified; the demo and map are untouched. New code is in `scripts/investigation/`; outputs are in `research/investigation/`. The raw pre-event extract is gitignored (`research/investigation/raw/`) and described in `pre_event_manifest.json`.

## Summary

- **Outcome: 4 (something else), with elements of 3.** OSM shows **two** river crossings between Chooralmala and Mundakai, both before the event and now:
  - the failed bridge (way 380928388)
  - an unpaved track bridge about 1.1 km upstream (way 794270381, 9.1 m, imported from DigitalGlobe imagery in 2020)

  Removing either one alone leaves the two settlements connected. **Removing both disconnects them, in the 2024-07-29 graph and in the 2026 graph.** The failure was therefore a 2-link cut, which a single-link bridge search can't flag by design.
- **Did the second crossing also fail in 2024?** Since 2024-12-31, OSM has tagged the track bridge `destroyed=yes`, `damage:event=2024WayanadLandslide`. The Scientific Reports paper says "Two key bridges … were washed away". Whether those two bridges are 380928388 and 794270381 is **COULD NOT VERIFY**, because no source names the second bridge.
- **Why "elements of 3":** the alternate route is a data-quality weak point.
  - It runs on unpaved imported tracks.
  - It crosses a stream (way 794270375) with no bridge, culvert or ford tag.
  - No source says it was usable by vehicles; three sources say the main bridge was the only road.
  - In the 2026 graph it also passes through two ways that OSM explicitly tags as destroyed, which our road filter doesn't exclude.
- **Outcome 1 is ruled out.** In the pre-event graph the failed bridge is **not** a single-link cut.
- **Completeness caveat:** the pre-event network is not much sparser overall (district edges 0.982× of 2026; within 3 km 0.908×). But tracks near the bridge are 0.686×, and 28 of the 183 ways in the 2026 enclave were created after 2024-07-29.
- **Census:** 817,420 (Wayanad district) and 7,548 (Vellarimala) are both confirmed in the primary Census of India 2011 District Census Handbook, Part XII B.

---

## A. Local topology (2026-09-16 buffered graph)
Output: `research/investigation/a_local_topology.txt`, `a_edges_within_1500m.csv`, `a_alternate_path_edges.csv`, `a_summary.json`, `a_waterways_2026-09-16.json`.

**Setup**
- The Level-2 enclave has 3,894 nodes; both settlement snap nodes are inside it.
- The Bailey Bridge is one edge: 3842230570–3842230578, 35.4 m, `highway=tertiary, bridge=yes, access=permissive, surface=metal, layer=1, name=Bailey Bridge`.
- **Within 1,500 m of 11.4992, 76.1601 inside the enclave:** 1,697 edges on 103 ways (full list with tags in `a_edges_within_1500m.csv`).
- **Waterways in the box (Overpass, same 2026-09-16 date):** 34 (1 river, 33 streams).

**Edges crossing a waterway: 21.**
- The bridge-tagged ones:
  - 380928388 (Bailey Bridge) over Punnappuzha
  - 794270381 (`highway=track, bridge=yes, surface=unpaved`) over Punnappuzha
  - 794678803 (`highway=tertiary, bridge=yes`) over "poonapuzha" (a tributary)
- 794678801 is `tunnel=yes, layer=-1` (a track under the tributary).
- The other 17 are untagged crossings of small streams (vellaarimala thodu, chooralmala thodu) by primary, unclassified and track ways.

**A5: which bank each point is on**

Method: I split a 2 km disc by the Punnappuzha main stem (ways 794270374 + 794270376 + 794270372 from junction node 7428736768 + 793762963 + 1530896408), giving 2 pieces with relative areas 0.518 / 0.482. Output: `a2_bank_check.txt`.

The first bank test, in `a_local_topology.txt`, is **invalid**: its disc split into only 1 piece because the river lines didn't cross it. The table below supersedes it.

| Point | Piece | Distance to river line |
|---|---|---|
| Paper coordinate 11.4992N 76.1601E | 0 | ~4 m (mid-bridge, so no bank assignment is meaningful) |
| Chooralmala settlement point / snap node 3842230572 | **1 / 1** | 19 / 22 m |
| Mundakai settlement point / snap node 3842228221 | **0 / 0** | 153 / 147 m |
| Bailey ends 3842230570 / 3842230578 | 1 / 0 | 16 / 18 m |
| Track bridge 794270381 ends 7428737126 / 7428737125 | 1 / 0 | 5 / 5 m |

- Distance from the paper coordinate to the Chooralmala snap node: **27 m**; to the Mundakai snap node: **1,505 m**.
- Chooralmala and Mundakai are on opposite banks, so this is not a snapping-across-water artifact.

**Connectivity, Chooralmala → Mundakai**

| | Connected | Edges | Length | Time |
|---|---|---|---|---|
| With bridge | yes | 91 | 1,997 m | 3.42 min |
| Without bridge | **yes** | 209 | 5,243 m | 16.00 min |

- Edge connectivity is 1 in both cases. The minimum cut is edge 3842228224–6894943729 (way 380928408, the Level 3 corridor) on Mundakai's own spur.

**Alternate path without the bridge** (every edge is in `a_alternate_path_edges.csv`):

| Way | Edges | Length | Tags | Crossing |
|---|---|---|---|---|
| 30778557 | 5 | 94 m | primary, asphalt, "Kalpetta - Meppadi Road" | |
| 380928406 | 66 | 2,220 m | unclassified | |
| 622913247 | 1 | 13 m | track, unpaved | |
| 622913215 | 104 | 2,245 m | track, unpaved | crosses stream 794270375 (unnamed) **with no bridge, culvert or ford tag** |
| **794270381** | 1 | 9 m | track, **bridge=yes**, unpaved, layer=1, **destroyed=yes, destroyed:highway=yes, damage:event=2024WayanadLandslide** | crosses Punnappuzha |
| **1347557913** | 1 | 23 m | track, unpaved, **destroyed=yes, damage:event=2024WayanadLandslide** | |
| 794270380 | 5 | 128 m | track, unpaved | |
| 380928408 | 26 | 510 m | tertiary, access=permit | |

## B. Edit history
Output: `b_edit_history.txt`, `b_edit_history.json`, `b2_destroyed_tags.txt` (OSM API `/api/0.6/{way,node}/<id>/history.json`).

**Ways on the alternate path, plus the bridge**

| Way | Role | Created | Changed after 2024-07-29? |
|---|---|---|---|
| 380928388 | failed bridge, now "Bailey Bridge" | **2015-11-18** with `bridge=yes, highway=tertiary, layer=1` | v2 **2024-12-31**: tags only (name, access, surface, wikimedia_commons). End node 3842230570 **moved 2024-08-04** |
| 30778557 | alternate / L2 | 2009-02-04 | v14 2024-08-04 (nodes), v15 2024-12-31 (nodes, tags) |
| 380928406 | alternate | 2015-11-18 | v2–v4 **2024-07-30 to 2024-07-31** (nodes) |
| 622913247 | alternate | 2018-09-04 | no |
| 622913215 | alternate | 2018-09-04 (`import=yes, source=digitalglobe`) | v4 2024-07-31 (nodes), v5 2024-08-03 (tags) |
| **794270381** | alternate river crossing | **2020-04-21** (`bridge=yes, highway=track, import=yes, source=digitalglobe`) | v2 **2024-12-31**: tags → `destroyed=yes, damage:event=2024WayanadLandslide` |
| **1347557913** | alternate | **2024-12-31** (created already tagged `destroyed=yes`) | **CREATED AFTER EVENT** |
| 794270380 | alternate | 2020-04-21 | v2 2024-12-31 (nodes) |
| 380928408 | alternate / L3 | 2015-11-18 | v6 2024-12-31 (nodes), v7 2024-12-31 (tags → `access=permit`) |

**Nodes checked:** 12 (way junctions on the path, ends of crossing edges, Bailey ends). Three moved after the event: 3842230421, 3842230570 and 3842230604, all on 2024-08-04. The track-bridge nodes (7428737122/25/26) are unchanged since 2020-04-21.

**Destroyed or damage-tagged ways in the whole 2026 extract:** 4, all still carrying a `highway` tag and all in the graph:
- 794270379: `destroyed:highway=residential`
- 794270381: `destroyed=yes`
- 1347557909: `destroyed:highway=residential`
- 1347557913: `destroyed=yes`

**B3: bridge inventory**

| Way | Where | Name (latest) | Created | Notes |
|---|---|---|---|---|
| 380928376 | L1 corridor | Meenakshi Bridge | 2015-11-18 | named 2022-02-16; tags edited 2025-01-06, 2025-09-02 |
| 380928389 | L1 corridor | Kalladi Bridge | 2015-11-18 | tertiary, unnamed until 2025-09-02 |
| 380928388 | failed-bridge site | Bailey Bridge | 2015-11-18 | **not** created after the event; the original bridge way was retagged on 2024-12-31 |
| 794270381 | Punnappuzha, 1.1 km upstream | none | 2020-04-21 | tagged destroyed by the 2024 landslide on 2024-12-31 |
| 794270379 | Punnappuzha, further south (11.482044, 76.151284) | none | 2020-04-21 | `destroyed:highway=residential` from 2024-12-31 |
| 794678803 | tributary "poonapuzha" | none | 2020-04-22 as **tunnel=yes, layer=-1** | retagged `bridge=yes` on 2024-12-31 |

No bridge way near the site was created after 2024-07-29. **Changes after the event are tag and node edits only**, apart from way 1347557913, which isn't a bridge.

**Bridges reported damaged or built, July–August 2024**
- **GSI FIR (30.07.2024)**, https://bhusanket.gsi.gov.in/Public_Portal_News_pdf/FIR_Mundakkai-Chooralmala.cleaned.pdf: "Collapse of bridge over Punapuzha, which is the only connective way of Mund akkai to Chooramala and other parts of Wayanad, isolated Mundakkai". Also: "Bridge connecting Mundakkai to Chooralmala washed away."
- **Onmanorama, 2024-07-30**, https://www.onmanorama.com/news/kerala/2024/07/30/wayanad-landslide-houses-town-chooralmala-washed-away-live.html: "The rescue mission is yet to reach Mundakkai as the bridge connecting the two villages has been destroyed completely."
- **DD News, 2024-08-01**, https://ddnews.gov.in/en/wayanad-tragedy-army-erecting-temporary-bailey-bridge-in-chooralmala-toll-risen-to-167/: "the Madras Engineer Group (MEG), an engineering unit of the Indian Army that began work on erecting a temporary Bailey Bridge in landslide affected Chooralmala". *Extracted through WebFetch's summariser because a direct fetch was reset by the server, so treat it as less certain than raw-text excerpts.*
- **Onmanorama, 2024-08-01**, https://www.onmanorama.com/news/kerala/2024/08/01/wayanad-landslide-army-constructs-bailey-bridge-in-chooralmala.html: "The prefabricated truss bridge is built in the same place where a 100-ft long concrete bridge was blown to smithereens". Also: "Around 3 am on Thursday, the army men started work on another 100-ft footbridge parallel to the Bailey Bridge."
- **ICL**, https://www.landslides.org/report/mundakkai-landslide-wayanad/: "Three bridges were destroyed during the massive debris flow."
- **Scientific Reports 2025** (see item 4): "Two key bridges … were washed away".

**Comparison (inference):** the reported concrete bridge and the Bailey replacement match OSM way 380928388: same site, retagged 2024-12-31. Sources give **2 or 3** destroyed bridges, and OSM tags 2 bridge ways near Mundakai as destroyed (794270381, 794270379). No source names them, so matching them to the reported bridges is COULD NOT VERIFY. I didn't check whether the parallel footbridge is in OSM; it wouldn't be in our vehicle-class graph anyway.

**Item 4: source check for the coordinates and "only route"** (raw HTML of https://www.nature.com/articles/s41598-025-07828-3, `dc.identifier` doi:10.1038/s41598-025-07828-3)
- **Coordinates:** "The flash floods caused by the cascading hazards washed away the bridge near Chooralmala (11.4992° N, 76.1601° E), severing the critical connection between Chooralmala and Mundakkai".
- **Two bridges: confirmed.** "Two key bridges that connected this area to Meppadi town were washed away by debris, thereby cutting the only transport route for all the settlements towards the town." The paper doesn't name the two bridges. Its "only transport route" refers to "all the settlements towards the town", not specifically to Chooralmala–Mundakkai.
- **"Only route" for Chooralmala–Mundakkai specifically:**
  - GSI FIR: "the only connective way of Mund akkai to Chooramala" (URL above).
  - The News Minute, https://www.thenewsminute.com/kerala/wayanad-landslides-all-you-need-to-know-about-how-the-bailey-bridge-was-built, quoting Maj. Seeta Ashok Shelke: "it was the only road connecting Mundakkai and Chooralmala".

## C. Pre-event snapshot (OSM as of 2024-07-29)
Output: `pre_event_manifest.json`, `c_build_pre_event.txt`, `c_completeness.json`, `c_enclave_pre_vs_now.txt/.json`, `c3_alternate_pre_vs_now.txt/.json`, `c3_alternate_path_{pre,now}.csv`, `c4_multi_crossing_cut.txt/.json`.

**Extract (manifest)**
- Overpass https://overpass-api.de/api/interpreter with `[date:"2024-07-29T00:00:00Z"]`, retrieved 2026-09-28T16:56:45Z (the first attempt got HTTP 504; the second got 200).
- File: 36,288,875 bytes, sha256 `e6b1194fec5389f57c39a9f63417bb3a3686f2a2102d40b241bb8b8fa004eb45`. Elements: 335,165 nodes, 18,091 ways (2026: 343,373 / 19,272).
- **Date checks:**
  - way 1347557913 (created 2024-12-31): absent ✔
  - way 1426730512 (created 2025-09-02): absent ✔
  - way 380928388 tags: `{layer:1, highway:tertiary, bridge:yes}` (the pre-retag state) ✔
  - way 794270381: no destroyed tags ✔

**Build**
- Same code path: `checkpoint3_4.build_weighted_graph`, the same node-distance attributes, and 500 m snapping. `enclave_analysis.py` functions were copied into `scripts/investigation/c_enclave_analysis_pre_event.py`; a diff shows they're identical above `main()`.
- **Settlements and facilities are fixed at the current set:** 142 OSM settlements, the curated 34, and the 31 buffer-ring facilities.
- Pre-event graph: 335,165 nodes, 339,421 edges, 128 components.
- **Snap changes against 2026:** 7 villages (Meppadi, Panamaram, Pachilakkadu, Nadakkal, Pulinjal, Thaloor, Kottathara) and 1 facility (PHC Adivaram). Chooralmala and Mundakai are unchanged (nodes 3842230572, 3842228221).

**Completeness check (edge counts by highway class)**

| | Pre-event | 2026 | Ratio |
|---|---|---|---|
| **Whole district, total** | 202,293 | 205,973 | **0.982** |
| secondary | 10,612 | 20,903 | 0.508 |
| tertiary | 19,894 | 14,473 | 1.375 |
| track | 13,401 | 17,605 | 0.761 |
| primary | 4,360 | 6,044 | 0.721 |
| unclassified | 66,047 | 60,202 | 1.097 |
| residential | 79,009 | 76,259 | 1.036 |
| **Within 3 km of 11.4992, 76.1601, total** | 3,620 | 3,985 | **0.908** |
| track | 1,165 | 1,699 | **0.686** |
| unclassified | 984 | 726 | 1.355 |
| residential | 973 | 1,048 | 0.928 |

(The full class tables are in `c_build_pre_event.txt`.)

- **2026 enclave area:** 183 ways, of which **28 were created after 2024-07-29**. 23 of those were created 2024-07-30 to 2024-08-06, 2 in 2024-12, 2 on 2024-12-31 and 1 in 2025-03. Three were first tagged `footway`/`path` and later retagged `track` (1304758392, 1304812836, 1304812838).
- **Reading:** the pre-event network isn't much sparser in total. The large class shifts (secondary ×0.51, tertiary ×1.38) suggest reclassification between snapshots, which affects speeds but not topology. Locally, the pre-event graph has 31% fewer track edges. That didn't create a false cut at the bridge: the bridge is not a cut in either graph.

**(i) The failed-bridge location in 2024**
- Way 380928388, edge 3842230570–3842230578, 39.2 m, `{layer:1, highway:tertiary, bridge:yes}`.
- **Single-link cut isolating a village: NO.** No edge within 50 m of the site is a cut.
- **Three edges cross the main stem pre-event:**
  - 380928388
  - 794270381 (track bridge at 11.489491, 76.154697)
  - 794270379 (residential bridge at 11.482044, 76.151284)
- **Pre-event alternate without the bridge:** connected, 195 edges, 5,055 m, 15.52 min. The route is the same as 2026 up to the track bridge: 30778557 → 380928406 → 622913247 → 622913215 (crossing unnamed stream 794270375 with no crossing tag) → **794270381** → 794270380 → 622913237 (residential) → 380928408.
- **Multi-crossing test** (both graphs give the same result):
  - removing 380928388 alone: connected
  - removing 794270381 alone: connected
  - removing 794270379 alone: connected
  - **removing 380928388 + 794270381: DISCONNECTED**
  - removing 380928388 + 794270379: connected
  - removing all three: disconnected

**(ii) Chain of single-link cuts isolating Mundakai: 2024 against 2026**

| Level | Isolates | 2024-07-29 | 2026-09-16 |
|---|---|---|---|
| 1 | Chooralmala, Kalladi, Mundakai | 138 cuts, 2,387 m, 4,013 nodes; outermost edge 3249489501–5870049103 (way 380928374, primary, 11.3 m), outer end 11.5244917, 76.1372991; inner end 11.5104282, 76.1321246 | 141 cuts, 2,388 m, 4,536 nodes; same outermost edge (11.4 m), same ends; also contains way 1426730512 (created 2025-09-02) |
| 2 | Chooralmala, Mundakai | 36 cuts, 885 m, 3,548 nodes; edge 3249489400–3842231008 (way 30778557, 10.2 m); ends 11.5104282, 76.1321246 → 11.5101033, 76.1393463 | identical edges and ends; 3,894 nodes |
| 3 | Mundakai | **14 cuts, 254 m, 414 nodes**; outermost 3842228231–5883092920 (way 380928408, tertiary, 7.6 m), outer end 11.487997, 76.155646; inner end 11.4863858, 76.1556489 | **20 cuts, 443 m, 752 nodes**; outermost 3842228241–3842228242 (12.3 m), outer end 11.4900185, 76.155845; inner end 11.4865851, 76.1550819 |

- Level 1 bridges pre-event: 380928376 (named "Meenakshi Bridge") and 380928389 (unnamed then).
- Enclave totals: 18 pre-event, 17 now. The extra pre-event enclave is "Kottathara" (6 nodes).

## D. Classification: **4 (something else), with elements of 3**

- **Not 1.** The pre-event graph does not flag the failed bridge as a single-link cut (C(i)).
- **Not clearly 2.** An alternate exists in OSM pre-event: an unpaved track and a 9.1 m track bridge, 794270381. But I found no source describing a usable alternate route in July 2024. GSI and The News Minute say the bridge was the "only connective way" / "only road".
- **Elements of 3 (data quality):**
  - The alternate's river crossing and its approach track are `import=yes, source=digitalglobe` features traced from imagery.
  - Its track crosses stream 794270375 with no bridge, culvert or ford tag.
  - No source confirms vehicle usability.
  - In the 2026 graph specifically, the alternate uses two ways OSM tags `destroyed=yes` (794270381, 1347557913); our filter keeps them because they still carry `highway=*`. **For the 2026 graph, the alternate is an artifact of including destroyed ways.**
- **Why 4:** in both graphs, the failed bridge and the upstream track bridge together form a **2-edge cut** between Chooralmala and Mundakai. OSM records the track bridge as destroyed by the same event, and the Scientific Reports paper reports "Two key bridges" washed away. If the second reported bridge is 794270381 (COULD NOT VERIFY), the event cut both crossings at once. That's something a single-link bridge search can't represent.

## E. Census check (primary source)
- **Source:** Census of India 2011, Kerala, Series 33, Part XII B, District Census Handbook, Wayanad (catalogue https://censusindia.gov.in/nada/index.php/catalog/669; PDF https://censusindia.gov.in/nada/index.php/catalog/669/download/2324/DH_2011_3203_PART_B_DCHB_WAYANAD.pdf, 2,331,222 bytes, 162 pages, no login; downloaded to the scratchpad only). Python's certificate check failed on this host (missing intermediate certificate); curl fetched it normally.
- **District:** "590 Wayanad - District Total 2,130.00 190,894 817,420 401,684 415,736" and "Wayanad is the least populated District with a population of 817420". **817,420 is confirmed.**
- **Vellarimala:** "627340 Vellarimala 5,420.00 1,711 7,548 3,692 3,856". **7,548 is confirmed.**
- **Cross-check (read-only parse of `scripts/village_crosswalk.py`):** its 49 revenue-village populations sum to **817,420**, exactly the DCHB district total.

## Flags raised during the investigation
1. Our road filter keeps ways tagged `destroyed=yes` / `destroyed:highway=*` (4 ways in the 2026 extract, all in this valley).
2. The Kalladi settlement snaps to node 3249489400, the end node of the Kalladi Bridge and the shared endpoint of the Level 1 and Level 2 cuts.
3. The Level 3 extent differs between snapshots (414 against 752 isolated nodes). The approach to Mundakai was re-edited on 2024-12-31.
4. Stream names changed between snapshots: in 2024 the main stem was "putthumala thodu" / "putthumala stream"; it's now "Punnappuzha".
5. The first bank test in `a_local_topology.txt` was invalid (a 1-piece split). It's superseded by `a2_bank_check.txt`.
6. Large reclassification between snapshots (secondary ×0.51, tertiary ×1.38, district-wide) affects travel times, but not the topology findings here.
