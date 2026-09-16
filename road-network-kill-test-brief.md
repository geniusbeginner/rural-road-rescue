# Rural Road Network Vulnerability — Kill Test Brief

**Timebox: 2–3 hours total. If Checkpoint 2 hasn't passed by then, stop and switch projects — don't extend.**

## Objective

Determine whether a usable road network graph can be built for one Indian rural district this week, with villages and health facilities attached, such that removing a road segment and recomputing shortest paths produces a real, defensible accessibility-loss number.

## District priority order

Try in this order. Move to the next only if the current one fails at Checkpoint 1.

1. Wayanad, Kerala
2. Nilgiris, Tamil Nadu
3. Idukki, Kerala
4. Chikkamagaluru, Karnataka

## Data sources, in order of attempt

**Roads:**
- PMGSY / GeoSadak — attempt bulk download of line geometry (shapefile/GeoJSON), not just a map viewer. Confirm this is an actual downloadable file, not a portal that only renders a map.
- OSM — clip an extract to the district boundary as the parallel/fallback source. Use both if PMGSY works — OSM catches non-PMGSY roads (state highways, district roads) that PMGSY may not cover.

**Villages:**
- Census 2011 village-level population data
- LGD (Local Government Directory) for administrative codes/boundaries to join against

**Health facilities:**
- Try any public state/OGD source first
- If nothing usable turns up within 30 minutes, geocode 5–10 facilities by hand for this one district — that's an acceptable, honest fallback for a demo

## Checkpoint sequence — run in order, don't skip ahead

### Checkpoint 1 — Get real geometry
Load road lines into GeoPandas. Report actual feature count. This is a pass/fail on whether a downloadable file exists at all, not whether it's clean yet.

### Checkpoint 2 — Snap rates (the real feasibility gate)
Do **not** test this with `nx.number_connected_components()` — rural networks naturally have disconnected fragments (tracks, artifacts, genuinely isolated segments) that don't matter for this purpose. Instead, snap villages and facilities to the road network with a **capped snap distance** (do not snap anything further than ~500m — an unbounded snap will falsely connect villages that are genuinely poorly served, which corrupts exactly the result we care about).

Report:
- % of villages snapped within 500m — **pass threshold: ≥95%**
- % of health facilities snapped — **pass threshold: 100%, and manually eyeball each one on a map.** With only 10–30 facilities in a rural district, one mis-snap disproportionately corrupts the result.
- % of village→facility pairs that return a valid route — **pass threshold: ≥90%**

Report the actual failing villages/pairs too — that's real data about where the network has genuine gaps, not noise to discard.

### Checkpoint 3 — Weight the edges
Assign edge weights using distance and road-class-derived speed if tags support it. Unweighted hop-count shortest paths won't give real travel times.

### Checkpoint 4 — Screen for candidate vulnerable links
Run betweenness centrality (or articulation points) across the network. Take the top 20–30 segments as candidates for simulation.

**Important distinction to hold onto going forward:** betweenness centrality is a screening filter to avoid wasting time removing 18,000 segments one by one. It is not the number to present. The number that goes in the pitch is always the real, computed result from Checkpoint 5 — never the centrality score standing in for it.

### Checkpoint 5 — The real test
Take the single highest-betweenness candidate. Remove it. Recompute shortest paths from every village to its nearest health facility. Report the actual change:

```
Villages affected: N
Population affected: N
Nearest facility travel time: X min → Y min
Facilities that become unreachable within 60 min: N
```

**This sentence, with real numbers, is the pass condition for the whole test.** If you can produce it, stop researching and start building the product. If you can't after 2–3 hours, stop and switch to the medicine-pricing fallback.

## Instructions for how work should be reported back

- Show actual command output and real counts at every checkpoint — not a summary of what was expected to work or should have happened.
- If something fails, say so immediately and clearly rather than working around it silently.
- Flag anything uncertain (a licence restriction, a portal that's view-only rather than downloadable, a suspiciously round number) rather than proceeding as if it's confirmed.
