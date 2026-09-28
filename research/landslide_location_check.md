# 1d. Landslide location check: which link failed at Chooralmala/Mundakkai in July 2024?

Checked 2026-09-28. Excerpts are verbatim from raw page or PDF text, except the OSM tags, which come from the live OSM API (api.openstreetmap.org) and Overpass.

## What the sources say

**S-A. Scientific Reports (peer-reviewed).** Ramesh, M. V., Ekkirala, H. C., Singh, B., Kumar M, N., Ramesh, S., Sridharan, A., Vasudevan, N., Wadhawan, S. K. (2025-07-24). "Mundakkai-Chooralmala landslide: assessment of initiation, progression, and impact." *Scientific Reports* 15 (metadata from Crossref). Text from https://www.nature.com/articles/s41598-025-07828-3; the PMC copy returned a reCAPTCHA, so I didn't use it.
- "The flash floods caused by the cascading hazards washed away the bridge near Chooralmala (**11.4992° N, 76.1601° E**), severing the critical connection between Chooralmala and Mundakkai"
- "Two key bridges that connected this area to Meppadi town were washed away by debris, thereby cutting the only transport route for all the settlements towards the town."
- "The rapid debris flow, which traveled nearly 6 km, indirectly affected the villages of Attamala and Noolpuzha, disrupting their connectivity with the rest of the district"
- "The total run-out distance was measured to be more than 6 km along the Punnapuzha River flowing from SW to NE."

**S-B. Geological Survey of India, First Information Report (prepared 30.07.2024).** https://bhusanket.gsi.gov.in/Public_Portal_News_pdf/FIR_Mundakkai-Chooralmala.cleaned.pdf
- "Collapse of bridge over Punapuzha, which is the only connective way of Mund akkai to Chooramala and other parts of Wayanad, isolated Mundakkai and thus arised difficulties in rescue operations in this area."
- "33 Communication : Roads, bridges and transmission lines damaged. Bridge connecting Mundakkai to Chooralmala washed away."
- Landslide record: "6 NH/SH/Locality : Mundakkai-Chooralmala-Meppadi road", "7 Latitude : 11027'46"", "8 Longitude : 76008'03"". The degree sign was extracted as "0", so I read these as **11°27'46" N, 76°08'03" E** (my reading). These are the **landslide** record's coordinates, not the bridge's.

**S-C. Onmanorama, 2024-08-01.** https://www.onmanorama.com/news/kerala/2024/08/01/wayanad-landslide-army-constructs-bailey-bridge-in-chooralmala.html
- "the Indian Army built a 190-ft Bailey bridge to restore the connectivity between Chooralmala and Mundakkai … The prefabricated truss bridge is built in the same place where a 100-ft long concrete bridge was blown to smithereens by the mighty boulders from the hills."
- "Around 3 am on Thursday, the army men started work on another 100-ft footbridge parallel to the Bailey Bridge."

**S-D. The News Minute.** https://www.thenewsminute.com/kerala/wayanad-landslides-all-you-need-to-know-about-how-the-bailey-bridge-was-built
- "A British-era bridge connecting Mundakkai and Chooralmala was devastated by the triple landslides that occurred on July 30, making it difficult for rescuers to reach stranded residents on both sides of the Iruvanjippuzha river."
- Quoting Major Seeta Ashok Shelke: "it was the only road connecting Mundakkai and Chooralmala".

**S-E. Onmanorama, 2024-07-30 (same-day report).** https://www.onmanorama.com/news/kerala/2024/07/30/wayanad-landslide-houses-town-chooralmala-washed-away-live.html
- "The rescue mission is yet to reach Mundakkai as the bridge connecting the two villages has been destroyed completely."
- "The magnitude of the calamity at Mundakkai village, a few kilometres away from Chooralmala on the same road, is yet to be assessed as the entire region has been isolated."

**S-F. Deccan Herald (replacement bridge).** https://www.deccanherald.com/india/kerala/rs-35-cr-project-approved-for-new-bridge-at-landslide-hit-chooralmala-3412226
- "The bridge will be rebuilt with enhanced security features from Chooralmala town to Mundakkai road".

**Alternate road access at the time:** no source I found says there was one. Two sources say explicitly that there wasn't: S-B ("the only connective way of Mundakkai to Chooramala and other parts of Wayanad") and S-D ("the only road connecting Mundakkai and Chooralmala"). S-A says "cutting the only transport route for all the settlements towards the town". I didn't find a source describing any alternative, so the existence of one is **COULD NOT VERIFY**, and the three sources above all say there was none.

**Couldn't open:** newsonair.gov.in (connection closed by the remote end); PMC (reCAPTCHA); the Springer *Landslides* paper "Decoding the dynamics of July 2024 Mundakkai-Chooralmala landslide" (not attempted, because Springer redirects to a login elsewhere).

## OSM ways requested (live OSM API, fetched 2026-09-28)
- **way/380928376 "Meenakshi Bridge"** (version 5, 2025-09-02). Tags: `bridge=yes, highway=primary, layer=1, name=Meenakshi Bridge, alt_name=Hill Highway, ref=SH59, lanes=2, maxspeed=45, surface=asphalt, oneway=no, sidewalk=no`. Nodes: 3249489483 (11.5226774, 76.1337977), 3249489482 (11.5223714, 76.1336364). History: named "Kalpetta - Meppadi Road" in v1 (2015) and v2 (2017); "Meenakshi Bridge" from v3 (2022-02-16).
- **way/380928389 "Kalladi Bridge"** (version 3, 2025-09-02). Tags: `bridge=yes, highway=primary, layer=1, name=Kalladi Bridge, oneway=no, surface=asphalt`. Nodes: 3842231012 (11.5108533, 76.1319721), 3249489400 (11.5104282, 76.1321246). History: tertiary with no name in v1 (2015); primary in v2 (2020); named in v3 (2025-09-02).
- **Found while checking:** **way/380928388 "Bailey Bridge"**, centre 11.499204, 76.160077 (Overpass, current). Tags in our 2026-09-16 snapshot file (read-only lookup): `access=permissive, bridge=yes, highway=tertiary, layer=1, name=Bailey Bridge, surface=metal, wikimedia_commons=File:Bailey Bridge Wayanad 02.jpg`.

## Distance from each source location to each of our levels
**Method:** great-circle distance to each level's reported start point, end point, and the straight line between them. This approximates the level's position; it isn't the actual road geometry. For example, the Meenakshi Bridge lies inside Level 1's chain but is 293 m from Level 1's straight line.

| Source location | L1 start / end / line (m) | L2 start / end / line (m) | L3 start / end / line (m) |
|---|---|---|---|
| S-A washed-away bridge, 11.4992, 76.1601 | 3,753 / 3,294 / **3,294** | 3,294 / 2,566 / **2,566** | 1,121 / 1,506 / **1,121** |
| OSM "Bailey Bridge" way 380928388 centre | 3,751 / 3,291 / 3,291 | 3,291 / 2,563 / 2,563 | 1,121 / 1,505 / 1,121 |
| S-B GSI landslide record, 11°27'46", 76°08'03" | 6,871 / 5,303 / 5,303 | 5,303 / 5,293 / 5,283 | 3,841 / 3,493 / 3,493 |
| OSM Meenakshi Bridge (average of its 2 nodes) | 447 / 1,356 / 293 | 1,356 / 1,511 / 1,352 | 4,345 / 4,625 / 4,345 |
| OSM Kalladi Bridge (average of its 2 nodes) | 1,643 / 25 / 16 | 25 / 797 / 25 | 3,461 / 3,668 / 3,461 |

**Measured facts:**
- The peer-reviewed coordinate for the washed-away bridge (S-A) is **3.3 km from Level 1, 2.6 km from Level 2 and 1.1 km from Level 3**. It is about 3 m from the centre of the OSM "Bailey Bridge" way.
- The Kalladi Bridge node 3249489400 is the **shared endpoint of Levels 1 and 2** (11.510428, 76.132125).

## My conclusions (inference, not stated by the sources)
1. **None of our three nested cuts is the bridge that failed.** The documented failure point (S-A, confirmed by OSM's Bailey Bridge being "in the same place" per S-C and S-D) is 1.1–3.3 km from all three levels.
2. **Our graph doesn't treat the Bailey Bridge as a single-link cut.** Way 380928388 isn't among the 7 ways in the Level 1–3 chains printed in the earlier step 4 run (380928374, 380928376, 1426730512, 380928378, 380928389, 30778557, 380928408). If it were the only crossing, cutting it would separate Mundakai from Chooralmala, and it would appear in that chain. So the 2026 OSM network probably has another connection across the river between Level 2's end and Level 3's start. Three sources say that in July 2024 the bridge was the only route. **I haven't checked this in the graph, because this task is read-only for data/ and scripts/.** It's the most important open question for the demo.
3. OSM has a second tertiary bridge (way 794678803, centre 11.501637, 76.163433, about 0.4 km NE of the Bailey Bridge) and other bridge ways near Mundakai (794270381, a track at 11.48949, 76.154656). Whether either is the alternate crossing: **COULD NOT VERIFY** without running the graph.
4. Level 3 (way 380928408, `access=permit`) lies inside Mundakai (the OSM "Mundakai" place node is at 11.486475, 76.155725, next to Level 3's inner end). The permit tag *may* mean post-disaster access restrictions; **no source found**, so this is inference only.
5. S-A mentions "Two key bridges" washed away but names only the one near Chooralmala. The second: **COULD NOT VERIFY**.
