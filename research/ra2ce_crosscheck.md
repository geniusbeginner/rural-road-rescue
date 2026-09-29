# RA2CE cross-check

Run 2026-09-29 on branch `ra2ce-crosscheck`: 11:20–12:05 UTC, about 45 of the 90-minute budget. RA2CE 1.2.2 from PyPI, in an isolated venv at `C:\Users\avant\.venvs\ra2ce`; the pipeline's own environment was not touched. Code is in `scripts/ra2ce_crosscheck/`; small outputs are in `research/ra2ce/`; RA2CE's working folders (857 MB) are gitignored in `research/ra2ce/work/`.

Line numbers refer to the installed RA2CE 1.2.2. The links in the Summary are pinned to GitHub tag `v1.2.2`, where the cited files are byte-identical. Later sections link to `master`, where the same files are identical as of 2026-09-29.

## Summary

**RA2CE confirmed our SH59 finding, but only through a forced synthetic-hazard input.** With only the SH59 link disrupted, RA2CE's closest-destination analysis reports exactly **Chooralmala, Kalladi and Mundakai** as having "no access" (3 of 142 origins), and no other origin's route changes. It gives the same result on the tracks-included (V0) and tracks-excluded (V1) networks.

- **Same nearest facility, same distances.** Before the disruption, RA2CE routes all three to Community Health Center Meppadi, as we do, with lengths 20–30 m (0.2%) shorter than ours.
- **Found without being told where to look, but not singled out.** RA2CE's whole-network single-link redundancy analysis gives the SH59 link `detour = 0`. So does **38.5% of all links (12,367 of 32,122)**, including 43 primary or trunk links. It has no consequence-based ranking, so it doesn't pick this corridor out.
- **The Bailey Bridge ambiguity reproduces exactly.** With tracks included, disrupting the Bailey chain leaves every village with access (Mundakai reroutes +1,223 m). With tracks excluded, **Mundakai alone** loses access. That's our "depends on whether tracks count as roads" result.
### How this project differs from RA2CE (for "how is this different from existing tools?")

All links point to the RA2CE **v1.2.2** release tag. The cited files at that tag are byte-identical to the installed package the results came from, and all three points below also hold on `master` as of 2026-09-29.

1. **RA2CE can disrupt a link only through a hazard map; there's no direct "remove this link" test.**
   - Its isolation analysis loops over hazard scenarios and disrupts only edges whose hazard value exceeds the threshold: [`multi_link_isolated_locations.py` L174](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/losses/multi_link_isolated_locations.py#L174) and [L182–L195](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/losses/multi_link_isolated_locations.py#L182-L195).
   - Its facility-access analysis does the same: [`origin_closest_destination.py` L179](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/losses/origin_closest_destination.py#L179) and [L198–L206](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/losses/origin_closest_destination.py#L198-L206).
   - The analysis settings ([`AnalysisSectionLosses`, L79–L185](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/analysis_config_data/analysis_config_data.py#L79-L185)) have no field for a list of links to remove.
   - The one no-hazard link test, `SINGLE_LINK_REDUNDANCY` ([`analysis_losses_enum.py` L7](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/analysis_config_data/enums/analysis_losses_enum.py#L7)), reports only whether each link has a detour, with no villages or facilities.
   - **Ours:** we remove the link from the road network directly and recompute every village's reachability to every facility. To reproduce our SH59 test in RA2CE we had to build a synthetic hazard map.

2. **RA2CE never disrupts a link tagged `bridge=yes` in these analyses.**
   - Isolation analysis: [`multi_link_isolated_locations.py` L190–L193](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/losses/multi_link_isolated_locations.py#L190-L193).
   - Facility-access analysis: [`origin_closest_destination.py` L198–L199](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/losses/origin_closest_destination.py#L198-L199).
   - Both require `("bridge" not in e[-1]) or (e[-1]["bridge"] != "yes")` before an edge can be disrupted.
   - **Consequence:** with OSM's tags as they are, RA2CE could not fail the Bailey Bridge (the 2024 failure site), or the Meenakshi and Kalladi bridges inside the SH59 corridor. The Meenakshi Bridge is the site of the July 2026 blockage. **Ours:** bridges are treated like any other road link; they're often exactly the links that fail.

3. **RA2CE's isolation analysis doesn't consider health facilities or population.**
   - "Isolated" means **outside the largest connected piece of the network** after disruption: [`remove_edges_from_largest_component`, L65–L87](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/losses/multi_link_isolated_locations.py#L65-L87), applied at [L201](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/analysis/losses/multi_link_isolated_locations.py#L201). The module never mentions a destination.
   - Population is whatever number the user puts in a column ([`origins_destinations.py` L61](https://github.com/Deltares/ra2ce/blob/v1.2.2/ra2ce/network/origins_destinations.py#L61)).
   - **Be precise if challenged:** RA2CE's separate closest-destination analysis *does* compute loss of access to facilities; that's the mode that confirmed our SH59 result. But it inherits points 1 and 2 (hazard-only disruption, bridges exempt), and neither mode attributes Census population.
   - **Ours:** isolation means "no road route to any curated health facility", and population comes from Census 2011 revenue-village totals with a no-double-counting rule.

## 1. Setup

| Time (UTC) | Step |
|---|---|
| 11:20:03 | Created branch `ra2ce-crosscheck` from `main`; created the venv (`python -m venv`, Python 3.13.2) |
| 11:20:41–11:25:03 | `pip install ra2ce==1.2.2`: exit 0; `pip check`: "No broken requirements found." Key versions: rasterio 1.5.1, osmnx 2.1.1, geopandas 1.2.0, networkx 3.7, pyarrow 23.0.0 (all from wheels) |

- **Install method** ([`docs/getting_started/installation.rst`](https://github.com/Deltares/ra2ce/blob/master/docs/getting_started/installation.rst)):
  - The recommended route is conda-forge (miniforge, micromamba or pixi); none was installed here.
  - "Python package mode" is also documented: "RA2CE is available on PyPI and can be installed using `pip`: `pip install ra2ce`". That's what I used.
  - The doc says Python ">=3.11,<3.14", and `pyproject.toml` says `>=3.11,<3.15`. 3.13 satisfies both.
  - The README's installation link (`deltares.github.io/ra2ce/installation/installation.html`) returns 404; the `.rst` in the repo is current.
- **Setup took about 5 minutes. No blockers.**

### Input formats (from the docs and code, before writing any calls)

- **Network** ([`network_config_data.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/network/network_config_data/network_config_data.py) `NetworkSection`; [`source_enum.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/network/network_config_data/enums/source_enum.py)):
  - `source` is one of `OSB_BPF`, `OSM_DOWNLOAD`, `SHAPEFILE` or `PICKLE`, with `primary_file`, `file_id` and `link_type_column` (default `"highway"`).
  - `CleanupSection` defaults: `snapping_threshold=False`, `merge_lines=False`, `cut_at_intersections=False`.
- **Origins and destinations** (`OriginsDestinationsSection`): point files `origins` and `destinations`, plus `origin_count` (a column name) and `category`. See [`examples/accessibility_closest_origin_destinations.ipynb`](https://github.com/Deltares/ra2ce/blob/master/examples/accessibility_closest_origin_destinations.ipynb).
- **Hazard** (`HazardSection`): `hazard_map` (a list of `.tif`), `aggregate_wl`, `hazard_crs`, `overlay_segmented_network`.
- **Analyses** ([`analysis_losses_enum.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/analysis/analysis_config_data/enums/analysis_losses_enum.py)):
  - The types include `SINGLE_LINK_REDUNDANCY`, `OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION`, `MULTI_LINK_ORIGIN_CLOSEST_DESTINATION` and `MULTI_LINK_ISOLATED_LOCATIONS`.
  - They're configured with `AnalysisSectionLosses(analysis, weighing, threshold (default 0.0), calculate_route_without_disruption, …)`.
- **Run:** `Ra2ceHandler.from_config(network=…, analysis=…)`, then `.configure()`, then `.run_analysis()`. See the notebook above and [`examples/criticality_single_link_redundancy.ipynb`](https://github.com/Deltares/ra2ce/blob/master/examples/criticality_single_link_redundancy.ipynb).

### Does isolation require a hazard raster? **Yes.** This is a real product difference, not just a workaround.

- **[`multi_link_isolated_locations.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/analysis/losses/multi_link_isolated_locations.py):**
  - Line 174 loops `for hazard in self.hazard_names.names`.
  - Lines 182–195 select as "directly disrupted" only edges whose hazard attribute is `> float(analysis.threshold)`.
  - Its docstring (line 142): "identifies locations that are flooded or isolated due to the disruption of the network caused by a hazard."
- **[`origin_closest_destination.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/analysis/losses/origin_closest_destination.py):** lines 198–206 apply the same hazard-threshold rule.
- **No configuration field or analysis type in 1.2.2 takes a list of links to remove.** `SINGLE_LINK_REDUNDANCY` removes every link in turn, but reports only per-link detours, with no origins or destinations.
- **The difference:** we test topology directly (remove a link, recompute reachability to facilities). RA2CE's isolation and accessibility modes route through **hazard exposure**. To reproduce a single-link test, we had to build a synthetic hazard.

### Two more product differences found in the same code
1. **Bridges are exempt from hazard disruption.** `multi_link_isolated_locations.py` lines 190–193 and `origin_closest_destination.py` lines 198–199 require `("bridge" not in e[-1]) or (e[-1]["bridge"] != "yes")`. A `bridge=yes` edge is never disrupted in these modes, so RA2CE could not fail the Bailey Bridge (or the Meenakshi or Kalladi bridges) from OSM tags as they are.
2. **"Isolated" means outside the largest connected component.** `multi_link_isolated_locations.py` lines 199–201 call `remove_edges_from_largest_component` on the disrupted graph. Our definition is "no road route to any health facility". The two agree only when every facility is in the largest component.

## 2. Data conversion (`scripts/ra2ce_crosscheck/prepare_inputs.py`)

**Network.** Our 10 km buffered graph (343,373 nodes, 347,948 edges) became **33,018 lines**, one per junction-to-junction chain (chain ends are nodes of degree ≠ 2).
- Each edge is used exactly once (checked by assertion).
- `cut_at_intersections`, `merge_lines` and snapping stay off, so RA2CE builds its nodes from line endpoints and reproduces our topology. Allowing it to cut at geometric intersections would wrongly connect bridges to the roads beneath them.
- RA2CE's base graph came out with **27,873 nodes and 32,122 links**, after its own simplification.
- Kept columns: `lid`, `highway` (the chain's most common class), `way_ids`, and our length.

**Losses and forced assumptions**
1. **Speeds.** Our speed table isn't passed; RA2CE computes its own (`avg_speed.csv`, "calculating and saving them instead"). All comparisons use `WeighingEnum.LENGTH`, so travel times aren't compared.
2. **The `bridge` tag is deliberately dropped.** Otherwise RA2CE would refuse to disrupt bridge-tagged links (see above).
3. **Origins and destinations are placed on our snapped node positions**, so RA2CE's nearest-node snapping reproduces ours.
4. **`origin_count` = 1 per village,** because our population rule doesn't attribute population per settlement.
5. **Multi-way chains.** A chain can span several OSM ways. For example, the Bailey chain (`lid` 30621, 178.4 m) covers parts of ways 30778557, 380928381 and 380928388. Disrupting it has the same reachability effect as removing the bridge edge alone, because a degree-2 chain is cut-equivalent, but it's a longer piece of road.

**V1 network** (`--no-tracks`): dropping `highway=track` edges gives 311,747 nodes and 315,652 edges, identical to our V1 graph in `followup_validation.md`, and 30,124 chains.

## 3. SH59 corridor: FORCED VIA SYNTHETIC HAZARD INPUT

- **Hazard raster.** A single-cell GeoTIFF: 1×1, EPSG:4326, cell 0.00002° (about 2.2 m), value 1.0, nodata −9999. It's centred on the midpoint of edge 3249489501–5870049103 (11.52444515, 76.1372773). Settings: `aggregate_wl=MAX`, `threshold=0.5`, `overlay_segmented_network=False`.
- **A first attempt with a 0.0001° cell (about 11 m) reached the edge's endpoints** and disrupted 3 links: the target, an adjacent SH59 chain, and a 534 m residential link. It was discarded. The 2.2 m cell disrupts **exactly 1 link**: `lid` 24382, primary, 43 m, our SH59 chain.
- **Analysis:** `MULTI_LINK_ORIGIN_CLOSEST_DESTINATION`, length weighting, `calculate_route_without_disruption=True`.

| | RA2CE V0 | RA2CE V1 (no tracks) | Ours |
|---|---|---|---|
| Villages with no access after disruption | **Chooralmala, Kalladi, Mundakai** (3 of 142) | **Chooralmala, Kalladi, Mundakai** | Chooralmala, Kalladi, Mundakai |
| Other origins whose route changed | 0 | not examined | 0 |
| Closest facility before | Community Health Center Meppadi (all 3) | not examined | Community Health Center Meppadi (all 3) |
| Route length before: Kalladi / Chooralmala / Mundakai | 8,284 / 12,785 / 14,777 m | not examined | 8,304 / 12,810 / 14,807 m (RA2CE is 20–30 m, 0.20–0.24%, shorter) |

Travel time is not compared, because RA2CE's speeds differ from ours. Our times are 11.7, 17.7 and 21.1 min.

**RA2CE bug hit (1.2.2).** The first run crashed after the analysis had finished, while exporting its node/edge GeoPackage. [`networks_utils.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/network/networks_utils.py) `add_x_y_to_nodes` (lines 1095–1099) falls back to the tuple `(0.0, 0.0)` for a node with no geometry, then calls `.x` on it (`AttributeError: 'tuple' object has no attribute 'x'`). The node without coordinates is the destination-category super-node RA2CE adds (named `"health"`, after our `category` value).
- `run_od.py` patches only that export helper, in our script: it skips nodes without coordinates and records them. RA2CE's code is unmodified.
- In later runs it skipped exactly one node, `"health"`. The rerun that reused the saved graph skipped 0.
- The analysis results (origins, destinations, routes) are unaffected.

## 4. Does RA2CE find the corridor on its own? `SINGLE_LINK_REDUNDANCY`, no hazard

- Whole network, 32,122 links, 15 s.
- The SH59 link (`lid` 24382) gets **`detour = 0`** (no alternative route), agreeing with us.
- The adjacent 686 m SH59 chain (`lid` 24391) has a detour (+3,539 m). That's consistent with our result: it lies on the Meppadi side of the corridor's outermost cut, where the network has loops.
- **But `detour = 0` applies to 12,367 links (38.5%):** 6,157 residential, 3,396 unclassified, 1,159 service, 996 track, 82 tertiary, 79 secondary, 39 primary, 4 trunk, and others. `diff_length` is empty for all of them, and the output has no measure of consequence (no population or facilities).
- **So RA2CE flags the corridor as having no detour, but doesn't rank it above thousands of dead-end residential links.** Our bridge tree plus facility layer is what separates it out. Full counts are in `research/ra2ce/slr_summary.json`.

## 5. Bailey Bridge ambiguity (same synthetic-hazard method, 2.2 m cell at 11.49920405, 76.1600773)

| Network | Link disrupted | Villages losing access | Route changes |
|---|---|---|---|
| V0, tracks included | `lid` 30621, tertiary, 178 m | **none** | Mundakai 14,777 → 16,000 m (+1,223 m) |
| V1, tracks excluded | `lid` 27933, tertiary, 84 m (RA2CE split our chain) | **Mundakai only** | – |
| Single-link redundancy (V0) | `lid` 30621 | – | detour = 1, +5,854 m |

- **RA2CE reproduces our "depends on whether tracks count as roads" result exactly.** It has no special handling for unpaved or low-confidence links; `highway` is just a link type.
- **It would have hidden the question entirely if the OSM `bridge=yes` tag had been kept,** because the bridge exemption stops the Bailey Bridge being disrupted at all.

## 6. Feature comparison

| Question | RA2CE 1.2.2 | Evidence | Ours |
|---|---|---|---|
| Population integration | **User-supplied.** An `origin_count` column in the origins file; the tutorial spreads a census total over building footprints by hand | [`network/origins_destinations.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/network/origins_destinations.py) line 61: "The name of the attribute in the origin shapefile that can be used for counting the flow over the network (e.g. nr. of people)"; [`docs/tutorials/accessibility.prepare_data_origin_destinations.rst`](https://github.com/Deltares/ra2ce/blob/master/docs/tutorials/accessibility.prepare_data_origin_destinations.rst) lines 48, 101–156 (`population = {"Beira": 533825}`, "Redistribute population proportionally to building footprint area") | Census 2011 revenue-village totals with a no-double-counting attribution rule |
| Artifact detection (boundary clipping, as in the Thaloor case) | **None found** | Code search for `boundary`, `clip`, `artifact` and `edge effect` finds only geometric uses (`line.boundary`, the OSM download polygon, the hazard-extent check). The largest-component isolation rule (see above) would flag clipped fragments as isolated | 10 km buffered re-extraction; real/suspect flags; 5 km vs 10 km check |
| India-specific data (PMGSY, Census) | **India-agnostic.** Network sources are OSM download, shapefile, pickle or OSB_BPF | [`source_enum.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/network/network_config_data/enums/source_enum.py); a search for `india`, `pmgsy`, `census` and `geosadak` in the package finds nothing | India-specific: Census DCHB, GeoSadak evaluated, Kerala eHealth facility checks |
| Validation against real events | **No built-in ground-truth checking found.** It's a simulation and loss-estimation tool | A search of `docs/overview.rst` and `docs/getting_started/about.rst` for validat, historic, observ, ground truth and calibrat finds nothing | Checked against the 30 July 2024 and 7 July 2026 events (area and corridor level) |
| Direct single-link removal test for reachability | **No.** Only through a hazard raster; only per-link detour without origins/destinations | See section 1 | Yes (bridge tree plus facility reachability) |
| Bridge-tagged links in hazard modes | **Never disrupted** | `multi_link_isolated_locations.py` lines 190–193; `origin_closest_destination.py` lines 198–199 | Treated like any other edge |
| Interface | **Technical users.** Python API (`Ra2ceHandler`), a command line (`python -m ra2ce --network_ini … --analyses_ini …`), `.ini` files, Jupyter/Binder notebooks. No GUI found | [`ra2ce/__main__.py`](https://github.com/Deltares/ra2ce/blob/master/ra2ce/__main__.py) lines 27–39 (`@click.command()`, `--network_ini`); the installation doc's Binder section | Scripts plus a static HTML demo |
| Hazard damage, economic losses, adaptation benefit–cost | **Yes.** This is its core purpose (damages, losses, adaptation modules and notebooks) | `examples/damages_*.ipynb`, `adaptation.ipynb`, `losses_*.ipynb` in the repo | No |

## What couldn't be tested within the time cap
- RA2CE's `MULTI_LINK_ISOLATED_LOCATIONS` was **not run**. Its isolation definition and hazard requirement were established from the code only. I didn't test whether its largest-component rule would falsely flag the old boundary-clipped Thaloor fragment on an unbuffered network.
- **Travel times were not compared;** only lengths were, because of the speed difference.
- `single_link_redundancy` was run only on V0, not V1.
- The RA2CE version is 1.2.2, the latest on PyPI and matching GitHub tag `v1.2.2`. The GitHub releases list showed v1.2.1 as its latest *release*, but the `v1.2.2` tag exists, and the cited files are identical there and on `master`. I didn't run `master`.
