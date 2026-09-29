# Follow-up validation: road-definition sensitivity, which bridges failed, lifecycle tags

Run 2026-09-28. No files in `data/` or `scripts/` were modified; the demo and map are untouched. Code: `scripts/investigation/f_variants.py`, `f_summarize.py`, `f_lifecycle_tags.py`. Outputs: `research/investigation/f_variants/` (one JSON and text file per snapshot × variant, plus `summary.txt`) and `research/investigation/f_lifecycle_tags.{txt,json}`. Filtered intermediate extracts are in the gitignored `research/investigation/raw/`.

## Plain-language summary
Whether the bridge that failed in July 2024 counts as a single weak point **depends on whether unpaved tracks count as roads**.
- If tracks count (V0), it never shows up as a single point of failure, in either the 2024 or the 2026 map, because a track route with a small track bridge upstream provides a second crossing.
- If tracks are dropped (V1, and V2, which also drops ways tagged as destroyed), the failed bridge becomes a single-link cut in both years. It then cuts Mundakai off from every health facility (762 road nodes in 2024; 831 or 820 in 2026).
- Under the approved rule, no population is attributed to that Mundakai enclave. Mundakai is only one of Vellarimala's three settlements.
- Dropping tracks doesn't disconnect any of the 142 villages from all facilities (0 in every variant). But it adds a boundary "suspect" enclave (Bavali), removes one small one (Melmury), and shrinks the Chooralmala enclaves to about half their node counts.
- The SH59 Level 1 corridor stays a single-link cut isolating Kalladi, Chooralmala and Mundakai (7,548 people) in every variant and both years.
- The web search found **no source saying any vehicle route other than the destroyed bridge was used or usable** in July 2024, but also no source saying the track route was unusable. So under the fixed decision rule, the result is reported as "depends on whether tracks count as roads", and V1 is not recommended as the default.
- The Scientific Reports paper's "two key bridges" are not named anywhere in its text or captions.
- Separately, a July 2026 landslide at Kalladi was reported to have "almost buried" the Meenakshi Bridge and severed the Meppadi–Chooralmala road. That's inside our Level 1 corridor.

---

## A. Road-definition sensitivity
**Variants, fixed before running:**
- V0: all 16 classes.
- V1: V0 minus `highway=track`.
- V2: V1 minus any way with a key starting `destroyed:`, `disused:` or `abandoned:`, or a plain `destroyed`, `disused` or `abandoned` key not equal to `no`.

**Method:**
- Same code path for every graph: the filtered raw extract is passed to `checkpoint3_4.build_weighted_graph`, which adds node distances and 500 m snapping; then the enclave functions are copied verbatim from `scripts/enclave_analysis.py`.
- Settlements and facilities are fixed: 142 OSM settlements, the curated 34, and 31 buffer-ring facilities. All are re-snapped to each variant's own nodes.
- Run order: 2024 V0, V1, V2, then 2026 V0, V1, V2, saving after each graph.
- Build time was 12–44 s per graph, and 29–93 s per full run.

**Graph sizes**

| Snapshot | Var | Ways kept | Nodes | Edges | Components | Unsnapped villages / facilities | Village snaps moved vs V0 |
|---|---|---|---|---|---|---|---|
| 2024-07-29 | V0 | 18,091/18,091 | 335,165 | 339,421 | 128 | 0/0 | 0 |
| 2024-07-29 | V1 | 16,753/18,091 | 309,021 | 312,683 | 182 | 0/0 | 2 (Melmury, Choyimoola) |
| 2024-07-29 | V2 | 16,753/18,091 | 309,021 | 312,683 | 182 | 0/0 | 2 |
| 2026-09-16 | V0 | 19,272/19,272 | 343,373 | 347,948 | 77 | 0/0 | 0 |
| 2026-09-16 | V1 | 17,707/19,272 | 311,747 | 315,652 | 138 | 0/0 | 2 (Melmury, Choyimoola) |
| 2026-09-16 | V2 | 17,705/19,272 | 311,744 | 315,648 | 139 | 0/0 | 2 |

- In 2024, V2 is identical to V1 because no lifecycle tags existed before the event.
- In 2026, V2 removes 2 more ways than V1: 794270379 and 1347557909, both `destroyed:highway=residential`. The other two lifecycle-tagged ways are tracks, already removed in V1.

**(i) The failed bridge (way 380928388, edge 3842230570–3842230578)**

| Snapshot | Var | Graph bridge? | Village-isolating cut? | Isolates | Population (approved rule) | Chooralmala→Mundakai without it |
|---|---|---|---|---|---|---|
| 2024 | V0 | no | **no** | – | – | connected: 195 edges, 5,055 m, 15.52 min |
| 2024 | V1 | yes | **yes** | Mundakai (762 nodes) | **0**; Vellarimala unattributed (1 of 3 settlements inside) | disconnected |
| 2024 | V2 | yes | **yes** | Mundakai (762 nodes) | **0**; Vellarimala unattributed | disconnected |
| 2026 | V0 | no | **no** | – | – | connected: 209 edges, 5,243 m, 16.00 min |
| 2026 | V1 | yes | **yes** | Mundakai (831 nodes) | **0**; Vellarimala unattributed | disconnected |
| 2026 | V2 | yes | **yes** | Mundakai (820 nodes) | **0**; Vellarimala unattributed | disconnected |

**Alternate route in V0**, the only variant where one exists (tags from the matching extract):

| Way | 2024 V0 | 2026 V0 | highway / surface / tracktype | Lifecycle tags |
|---|---|---|---|---|
| 30778557 | 4 edges, 96 m | 5 edges, 95 m | primary / asphalt / – | – |
| 380928406 | 67 edges, 2,214 m | 66 edges, 2,220 m | unclassified / – / – | – |
| 622913247 | 1 edge, 12 m | 1 edge, 13 m | **track / unpaved** / – | – |
| 622913215 | 103 edges, 2,249 m | 104 edges, 2,245 m | **track / unpaved** / – | – |
| 794270381 (bridge=yes) | 1 edge, 9 m | 1 edge, 9 m | **track / unpaved** / – | 2024: none. **2026: destroyed=yes, destroyed:highway=yes** |
| 1347557913 | – | 1 edge, 23 m | **track / unpaved** / – | **destroyed=yes, destroyed:highway=yes** |
| 794270380 | 1 edge, 23 m | 5 edges, 128 m | **track / unpaved** / – | – |
| 622913237 | 4 edges, 198 m | – | residential / – / – | – |
| 380928408 | 14 edges, 254 m | 26 edges, 510 m | tertiary / – / – (2026: access=permit) | – |

- No way on either route has a `tracktype` tag.
- In V1 and V2 the Mundakai-only enclave's outermost cut is the SH59 edge 3842230570–3842230572 (5.2 m in 2024, 8.0 m in 2026). That edge joins the bridge's end node to Chooralmala's snap node, and the failed bridge is the next cut inward (one node fewer).

**(ii) Chooralmala–Mundakai edge connectivity**
- It's **1 in all six graphs.**
- The minimum cut the solver returns is always an edge on way 380928408 (Mundakai's own approach spur):
  - 2024: 5883092633–3842228221 (all variants)
  - 2026 V0: 6894943729–3842228224
  - 2026 V1/V2: 12465132728–3842228221
- These are just one of the possible minimum cuts. In V1 and V2 the failed bridge is also a size-1 cut, per (i).
- Snap nodes were unchanged in every variant: Chooralmala 3842230572, Mundakai 3842228221.

**(iii) SH59 Level 1, edge 3249489501–5870049103**

| Var | 2024-07-29 | 2026-09-16 |
|---|---|---|
| V0 | cut: Chooralmala, Kalladi, Mundakai; 4,013 nodes; population 7,548 | cut: same villages; 4,536 nodes; 7,548 |
| V1 | cut: same villages; 2,428 nodes; 7,548 | cut: same villages; 2,185 nodes; 7,548 |
| V2 | cut: same villages; 2,428 nodes; 7,548 | cut: same villages; 2,174 nodes; 7,548 |

**It stays a single-link cut in every variant, so the "major finding" rule isn't triggered.**

**(iv) Enclaves, compared with V0 of the same snapshot**

| Snapshot | Var | Enclaves | Real / suspect | Appear | Vanish | Changed size |
|---|---|---|---|---|---|---|
| 2024 | V0 | 15 | 15 / 0 | – | – | – |
| 2024 | V1, V2 | 15 | 14 / 1 | **Bavali** (1,086 nodes, suspect, pop 0) | **Melmury** (V0: 37 nodes) | C+K+M 4,013→2,428; C+M 3,548→1,990; Mundakai 414→763; Choyimoola 9→145 |
| 2026 | V0 | 14 | 14 / 0 | – | – | – |
| 2026 | V1 | 14 | 13 / 1 | **Bavali** (1,171 nodes, suspect, pop 0) | **Melmury** | C+K+M 4,536→2,185; C+M 3,894→1,815; Mundakai 752→832; Choyimoola 9→145; Churuli 46→81 |
| 2026 | V2 | 14 | 13 / 1 | Bavali (1,171, suspect) | Melmury | C+K+M →2,174; C+M →1,804; Mundakai →821; Choyimoola 9→145; Churuli 46→81 |

*Re-run 2026-09-30 through the current pipeline (spur-snap fix, audited facility list), `scripts/investigation/f_variants.py`. The only change from the first run is that the three one-node spur-snap artifacts (Chundale, Meenangadi, Sultan Bathery) are gone in all six variants: 18→15 enclaves in 2024 and 17→14 in 2026. Every other enclave, and results (i)–(iii) and (v), are identical. The 2026 V0 run reproduces `data/enclave_atlas.json` exactly; the frontend build checks this.*

- **Bavali's** outermost cut is edge 5575532300–5870322302 (way 583156293, primary, 17.8 m, at 11.8547, 76.1162). It's flagged suspect by the boundary rule; Bavali is also one of the boundary artifacts removed in the earlier buffer step.
- **Melmury vanishes** because its snap moves off the track spur it sat on.

**(v) Villages with no route to any facility in the base graph: 0 of 142 in all six graphs.** No villages are unsnapped and none are in a facility-free component. **Dropping tracks does not disconnect any village**, so V1 is not "too aggressive" by this measure. It does change enclave shapes and adds a boundary suspect, as in (iv).

**Decision rules (fixed in advance), applied:**
- The failed bridge is a single-link cut **only in V1 and V2** in both snapshots → **"depends on whether tracks count as roads."**
- Part B found no evidence that the track route was or wasn't motorable. So **V1 is not recommended as the default.**
- In V0 the remaining alternate route is the one in the table above: tracks 622913247 and 622913215, then track bridge 794270381.
- The SH59 Level 1 corridor stays a cut in all variants, so no major finding is flagged.

---

## B. Which bridges failed in July 2024?

**Scientific Reports paper** (https://www.nature.com/articles/s41598-025-07828-3; full raw HTML, 15 figure/table captions, no supplementary links found).
- Its only bridge sentences are these:
  - "The flash floods caused by the cascading hazards washed away the bridge near Chooralmala (11.4992° N, 76.1601° E), severing the critical connection between Chooralmala and Mundakkai"
  - "Two key bridges that connected this area to Meppadi town were washed away by debris, thereby cutting the only transport route for all the settlements towards the town."
- The figure captions in the HTML are labels only ("Fig. 1", "Fig. 2", …) or describe photos and tables. The only photo captions extracted don't mention bridges: "(a and b) Erosion Zones at the banks of the Punnapuzha River (c) Size of boulders transported … near Meppadi", "(d) Weathered rocks of the Vellarmala Hill (e) A partially destroyed Meppadi Juma Masjid".
- **Which two bridges the paper means: COULD NOT VERIFY** (they're not named in the text or captions, and figure images weren't examined).
- The paper also says: "Fieldwork was also limited due to access restrictions imposed by government authorities."

**Bridge by bridge (July 2024)**
- **Chooralmala–Mundakkai bridge (the Bailey site, way 380928388): destroyed.**
  - GSI FIR: "Bridge connecting Mundakkai to Chooralmala washed away."
  - Onmanorama 2024-08-01: "built in the same place where a 100-ft long concrete bridge was blown to smithereens"
  - Al Jazeera 2024-08-02, https://www.aljazeera.com/features/2024/8/2/bring-him-back-hope-meets-loss-in-indian-villages-hit-by-landslides: "A bridge that connected Chooralmala to the other two villages was destroyed in the landslides, slowing down the pace of rescue operations." Also, quoting a resident: "The bridge was the lifeline of the three villages." Also, a photo caption: "After the collapse of a bridge that connects the landslide-hit villages of Attamala and Chooralmala in Wayanad, rescue workers relied on ropes to carry retrieved bodies to the hospital".
  - The Wire, https://m.thewire.in/article/environment/kerala-landslide-wayanad-rescue/amp: "roads have collapsed, and a vital bridge has been washed away, rendering these areas inaccessible."
- **Meenakshi Bridge (way 380928376) and Kalladi Bridge (way 380928389), July 2024:** no report of damage found in the sources searched. COULD NOT VERIFY either way.
- **Meenakshi Bridge, July 2026 (a different event),** DownToEarth, https://www.downtoearth.org.in/natural-disasters/kalladi-landslide-in-wayanad-a-disaster-waiting-to-happen-experts:
  - "The July 7, 2026, landslide at Kalladi near Meppadi in Kerala's Wayanad district was a disaster waiting to happen"
  - "The Meenakshi Bridge was almost buried."
  - "The Meppadi-Chooralmala road was severed, rescue teams struggled to reach affected areas and dozens of families were shifted to relief camps."
  - "A bridge was buried"
  - **This event falls inside our Level 1 SH59 corridor**, which contains the Meenakshi Bridge. That's inference from matching the bridge name with the OSM `name` tag. It's the only reported real-world disruption of Level 1 I found.
- **Track bridge (way 794270381):** no news, government, army or academic report found that names it. Its only "destroyed" evidence is the OSM tag added 2024-12-31. COULD NOT VERIFY.
- **Count of bridges destroyed:** ICL says "Three bridges were destroyed during the massive debris flow" (https://www.landslides.org/report/mundakkai-landslide-wayanad/); Scientific Reports says "Two key bridges". None of these are named beyond the Chooralmala–Mundakkai bridge.

**Another motorable route in July 2024?**
- **No source found reporting that rescue or supply vehicles used another motorable route.**
- The sources found describe the bridge as the only connection:
  - GSI: "the only connective way of Mundakkai to Chooramala [sic] and other parts of Wayanad"
  - The News Minute: "it was the only road connecting Mundakkai and Chooralmala"
  - Al Jazeera: "The bridge was the lifeline of the three villages"
- Access before the Bailey bridge was by ropes and a temporary bridge:
  - The News Minute: "rescue efforts through ropes and a temporary bridge"
  - Al Jazeera photo caption above
  - Onmanorama 2024-07-31, https://www.onmanorama.com/news/kerala/2024/07/31/wayanad-landslide-mundakkai-chooralmala-search-rescue-death-toll-live.html: "A Bailey bridge is under construction by the Army connecting Mundakkai and Chooralmala."
- Whether the upstream track route was physically usable, or used, in July 2024: **COULD NOT VERIFY.**

**DD News re-verification:** a direct fetch failed twice. Python got "connection reset by remote host"; curl exited with code 35 (TLS connect error). The earlier excerpt ("the Madras Engineer Group (MEG) … began work on erecting a temporary Bailey Bridge in landslide affected Chooralmala") **remains summariser-derived (WebFetch) and unverified against raw text.**

---

## C. Lifecycle-tagged ways (2026-09-16 extract; reporting list only, V2 unchanged)
**Reporting list:** `destroyed`, `disused`, `abandoned`, `razed`, `demolished`, `removed`, `dismantled`, `was`, `construction`, `proposed`, as plain keys and as prefixes. `damage:*` is reported separately.

- **Ways with any lifecycle key: 4 of 19,272.** All 4 fall in V2's families; none of the wider families appears.
- **Keys:** `destroyed:highway` ×4, `destroyed` ×2.
- **By highway class:** residential 2, track 2.
- **`damage:*` tagged:** 2 (794270381, 1347557913, both `damage:event=2024WayanadLandslide`).

| Way | highway | bridge | Lifecycle tags | In V0 graph | Edges / of which graph bridges (2026 V0) | On a Chooralmala–Mundakai alternate path |
|---|---|---|---|---|---|---|
| 794270379 | residential | yes | destroyed:highway=residential | yes | 1 / 1 | no |
| 794270381 | track | yes | destroyed=yes, destroyed:highway=yes | yes | 1 / 0 | **yes (2024 and 2026)** |
| 1347557909 | residential | – | destroyed:highway=residential | yes | 3 / 3 | no |
| 1347557913 | track | – | destroyed=yes, destroyed:highway=yes | yes | 1 / 0 | **yes (2026)** |

- The "2024" mark for 794270381 means the same way ID is on the 2024 alternate path. Its lifecycle tags were added only on 2024-12-31.
- Nothing was changed in the data or the filters.

## Could not verify
- Which two bridges the Scientific Reports paper means (not named; figure images not examined).
- Any July 2024 damage to the Meenakshi or Kalladi bridges.
- Any report naming the track bridge 794270381, and whether the track route was motorable or used.
- A raw-text re-check of the DD News article (TLS failures).
