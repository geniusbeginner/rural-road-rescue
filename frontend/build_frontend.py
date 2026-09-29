"""Build rural-road-rescue.html from committed data. Presentation layer only.

Reads data/, research/ and git history read-only; writes only rural-road-rescue.html.
Every number shown on the page is taken from a committed JSON/CSV (or a named historical commit via `git show`),
and the build ASSERTS each derived value against its source, aborting on any mismatch.

Enclave road geometry is not stored in any committed file, so it is derived here: for each enclave, its committed
outermost cut edge is removed from the corresponding graph and the smaller side is taken; the side's node count
must equal the committed node count (asserted). Graphs: data/graph_buf10km.pkl (today, V0) and the road-definition
variant extracts in research/investigation/raw/f_{pre,now}_V{0,1,2}.json (built with the unchanged
scripts/checkpoint3_4.build_weighted_graph). No analysis is re-run or changed.
Run from the repository root: python frontend/build_frontend.py
"""
import csv
import hashlib
import html
import json
import pickle
import re
import subprocess
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import MultiLineString, shape
from shapely.ops import linemerge

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from checkpoint3_4 import build_weighted_graph  # noqa: E402  (unchanged pipeline function)

OUT = ROOT / "rural-road-rescue.html"
TEMPLATE = ROOT / "frontend" / "template.html"
VENDOR = ROOT / "frontend" / "vendor" / "leaflet-1.9.4"
# commits holding "before" values (parents of the commits that corrected them)
BEFORE = {"demo": "0c9e692", "atlas": "d57b48c", "facilities": "a9afbf0"}
CKM = ["Chooralmala", "Kalladi", "Mundakai"]
BAILEY_EDGE = (3842230570, 3842230578)
TRACK_BRIDGE_EDGE = (7428737125, 7428737126)
MUNDAKAI_SNAP = 3842228221
VALLEY_BBOX = (11.44, 76.08, 11.56, 76.21)  # lat_min, lon_min, lat_max, lon_max: local context roads


def load(p):
    return json.load(open(ROOT / p, encoding="utf-8"))


def git_show(commit, path):
    r = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, f"git show {commit}:{path} failed: {r.stderr}"
    return r.stdout


def check(cond, msg):
    if not cond:
        raise SystemExit(f"BUILD ASSERTION FAILED: {msg}")


# ---------------------------------------------------------------- geometry
def small_side(G, u, v):
    """Nodes on the smaller side of bridge (u, v), by lock-step BFS (never traverses the large side fully)."""
    seen, q = [{u}, {v}], [deque([u]), deque([v])]
    while True:
        for i in (0, 1):
            if not q[i]:
                return seen[i]
            x = q[i].popleft()
            for y in G.neighbors(x):
                if {x, y} == {u, v}:
                    continue
                if y in seen[1 - i]:
                    raise SystemExit(f"edge {u}-{v} is not a bridge in this graph")
                if y not in seen[i]:
                    seen[i].add(y)
                    q[i].append(y)


def lines_for(G, nodes, tol=0.00002):
    segs = [((G.nodes[a]["lon"], G.nodes[a]["lat"]), (G.nodes[b]["lon"], G.nodes[b]["lat"]))
            for a in nodes for b in G.neighbors(a) if b in nodes and a < b]
    if not segs:
        return []
    merged = linemerge(MultiLineString(segs)).simplify(tol, preserve_topology=False)
    geoms = getattr(merged, "geoms", [merged])
    return [[[round(y, 5), round(x, 5)] for x, y in g.coords] for g in geoms if not g.is_empty]


class Geoms:
    def __init__(self):
        self.store, self.index = {}, {}

    def add(self, G, nodes):
        key = hashlib.sha1(",".join(map(str, sorted(nodes))).encode()).hexdigest()[:12]
        if key not in self.store:
            self.store[key] = lines_for(G, nodes)
        return key


def enclave_geom(G, edge, expected_nodes, geoms, label):
    u, v = edge
    check(G.has_edge(u, v), f"{label}: cut edge {u}-{v} missing from graph")
    side = small_side(G, u, v)
    check(len(side) == expected_nodes, f"{label}: derived side has {len(side)} nodes, committed value {expected_nodes}")
    return geoms.add(G, side), side


# ---------------------------------------------------------------- build
def main():
    atlas = load("data/enclave_atlas.json")
    fv = {(s, v): load(f"research/investigation/f_variants/{s}_{v}.json") for s in ("pre", "now") for v in ("V0", "V1", "V2")}
    demo = load("data/demo_data.json")
    geoms = Geoms()

    print("loading graphs ...", flush=True)
    graphs = {("now", "V0"): pickle.load(open(ROOT / "data/graph_buf10km.pkl", "rb"))["G"]}
    for s in ("pre", "now"):
        for v in ("V0", "V1", "V2"):
            if (s, v) not in graphs:
                graphs[(s, v)], _ = build_weighted_graph(str(ROOT / f"research/investigation/raw/f_{s}_{v}.json"))
            g = graphs[(s, v)]
            if (s, v) != ("now", "V0"):
                check((g.number_of_nodes(), g.number_of_edges()) == (fv[(s, v)]["nodes"], fv[(s, v)]["edges"]),
                      f"graph {s} {v} size differs from f_variants JSON")

    # ---- enclave states ------------------------------------------------------------------------------
    def enc_record(e, src, gid, kind):
        return {"key": "|".join(e["villages"]), "villages": e["villages"], "nodes": e["nodes"], "n_cuts": e["n_cuts"],
                "flag": e["flag"], "population": e["population_attributed"], "partial": e["partial"],
                "cut": e["cut"], "gid": gid, "source": src, "kind": kind, **e.get("extra", {})}

    states = {}
    # today V0 = current enclave atlas (spur-snap fix + audited facility list)
    recs = []
    for e in atlas["enclaves"]:
        oc = e["outermost_cut"]
        gid, _ = enclave_geom(graphs[("now", "V0")], (oc["u"], oc["v"]), e["road_nodes"], geoms, f"atlas {e['villages']}")
        recs.append(enc_record({"villages": e["villages"], "nodes": e["road_nodes"], "n_cuts": e["n_single_link_cuts_producing_it"],
                                "flag": e["flag_10km"], "population_attributed": e["population_attributed"],
                                "partial": sorted(e["revenue_villages_partial_unattributed"]),
                                "cut": {k: oc[k] for k in ("u", "v", "way_id", "highway", "length_m", "u_latlon", "v_latlon")},
                                "extra": {"facilities_inside": e["facilities_inside"], "flag_5km": e["flag_5km"],
                                          "min_distance_to_district_boundary_m": e["min_distance_to_district_boundary_m"],
                                          "nodes_outside_district": e["nodes_outside_district"],
                                          "full": e["revenue_villages_full"]}},
                               "data/enclave_atlas.json", gid, "atlas"))
    states["today|V0"] = recs
    for s, lab in (("pre", "pre"), ("now", "today")):
        for v in ("V0", "V1", "V2"):
            if (lab, v) == ("today", "V0"):
                continue
            recs = []
            for e in fv[(s, v)]["iv_enclaves"]:
                oc = e["outermost_edge"]
                gid, _ = enclave_geom(graphs[(s, v)], (oc["u"], oc["v"]), e["nodes"], geoms, f"{s} {v} {e['villages']}")
                recs.append(enc_record({"villages": e["villages"], "nodes": e["nodes"], "n_cuts": e["n_cuts"], "flag": e["flag"],
                                        "population_attributed": e["population_attributed"], "partial": sorted(e["partial_unattributed"]),
                                        "cut": {k: oc[k] for k in ("u", "v", "way_id", "highway", "length_m", "u_latlon", "v_latlon")}},
                                       f"research/investigation/f_variants/{s}_{v}.json", gid, "variant"))
            states[f"{lab}|{v}"] = recs
    for k, recs in states.items():
        check(any(r["villages"] == CKM for r in recs), f"{k}: Chooralmala/Kalladi/Mundakai enclave missing")
    check(len(states["today|V0"]) == 14, "today V0 should list the 14 atlas enclaves")
    # The variants run through the same pipeline as the atlas (spur-snap fix, audited facilities), so the
    # today/V0 variant must reproduce the atlas exactly; this ties the V1/V2 states to the same basis.
    sig = lambda e: (tuple(e["villages"]), e["nodes"], e["n_cuts"], e["flag"], e.get("population_attributed", e.get("population")))
    check(sorted(map(sig, fv[("now", "V0")]["iv_enclaves"])) == sorted(map(sig, states["today|V0"])),
          "f_variants now_V0 does not reproduce data/enclave_atlas.json")

    # ---- Kalladi 2026 event: SH59 Level-1 corridor blocked (today snapshot, per road definition)
    kalladi = {}
    for v in ("V0", "V1", "V2"):
        l1 = fv[("now", v)]["iii_level1"]
        ckm = next(r for r in states[f"today|{v}"] if r["villages"] == CKM)
        check(l1["is_village_isolating_cut"] and sorted(l1["villages"]) == CKM, f"Level-1 cut {v} not isolating C/K/M")
        check(l1["isolated_nodes"] == ckm["nodes"], f"Level-1 {v}: iii {l1['isolated_nodes']} vs enclave {ckm['nodes']}")
        check(l1["population_attributed"] == ckm["population"] == 7548, f"Level-1 {v} population")
        kalladi[v] = {"key": ckm["key"], "nodes": l1["isolated_nodes"], "population": l1["population_attributed"],
                      "villages": l1["villages"], "gid": ckm["gid"], "source": f"research/investigation/f_variants/now_{v}.json (iii_level1)"}

    # ---- 2024 aftermath (RECONSTRUCTED): pre-event V0 graph with failed bridge + track bridge removed
    c4 = load("research/investigation/c4_multi_crossing_cut.json")["PRE 2024-07-29"]
    combo = next(r for r in c4["combos"] if len(r["removed"]) == 2 and r["removed"][0].startswith("380928388")
                 and r["removed"][1].startswith("794270381"))
    check(combo["connected"] is False, "c4: removing both crossings must disconnect Chooralmala-Mundakai")
    Gp = graphs[("pre", "V0")]
    for e in (BAILEY_EDGE, TRACK_BRIDGE_EDGE):
        check(Gp.has_edge(*e), f"pre V0 graph lacks {e}")
    from networkx import restricted_view, node_connected_component
    mund_side = node_connected_component(restricted_view(Gp, [], [BAILEY_EDGE, TRACK_BRIDGE_EDGE]), MUNDAKAI_SNAP)
    check(len(mund_side) < 5000, "reconstructed Mundakai side unexpectedly large")
    aftermath = {"gid": geoms.add(Gp, mund_side), "removed": combo["removed"], "connected": combo["connected"],
                 "source": "research/investigation/c4_multi_crossing_cut.json (PRE 2024-07-29)"}

    # ---- failed bridge status per state/definition (from f_variants i_failed_bridge)
    bailey = {f"{'today' if s == 'now' else 'pre'}|{v}": {
        "is_cut": fv[(s, v)]["i_failed_bridge"]["is_village_isolating_cut"],
        "villages": fv[(s, v)]["i_failed_bridge"].get("villages", []),
        "nodes": fv[(s, v)]["i_failed_bridge"].get("isolated_nodes"),
        "alt": ({"length_m": round(fv[(s, v)]["i_failed_bridge"]["alternate"]["length_m"]),
                 "time_min": round(fv[(s, v)]["i_failed_bridge"]["alternate"]["time_min"], 2),
                 "ways": [{"way_id": w["way_id"], "highway": w["highway"], "surface": w["surface"], "lifecycle": w["lifecycle"]}
                          for w in fv[(s, v)]["i_failed_bridge"]["alternate"]["ways"]]}
                if fv[(s, v)]["i_failed_bridge"]["alternate"]["connected_without_bridge"] else None),
        "source": f"research/investigation/f_variants/{s}_{v}.json (i_failed_bridge)"} for s in ("pre", "now") for v in ("V0", "V1", "V2")}

    # ---- context layers
    G0 = graphs[("now", "V0")]
    major = {"trunk", "primary", "secondary", "tertiary"}
    seg = {"major": [], "local": []}
    la0, lo0, la1, lo1 = VALLEY_BBOX
    for a, b, d in G0.edges(data=True):
        A, B = G0.nodes[a], G0.nodes[b]
        s_ = ((A["lon"], A["lat"]), (B["lon"], B["lat"]))
        if d["highway"] in major:
            seg["major"].append(s_)
        elif la0 <= A["lat"] <= la1 and lo0 <= A["lon"] <= lo1:
            seg["local"].append(s_)
    context = {}
    for k, ss in seg.items():
        m = linemerge(MultiLineString(ss)).simplify(0.00005, preserve_topology=False)
        context[k] = [[[round(y, 5), round(x, 5)] for x, y in g.coords] for g in getattr(m, "geoms", [m]) if not g.is_empty]
    bnd = shape(load("data/osm/wayanad_boundary.geojson")).exterior.simplify(0.0005)
    boundary = [[round(y, 5), round(x, 5)] for x, y in bnd.coords]

    # ---- points and markers
    cp2 = load("data/checkpoint2_results.json")
    villages = [{"name": x["name"], "lat": round(x["lat"], 5), "lon": round(x["lon"], 5)} for x in cp2["villages"]]
    facilities = [{"name": f["name"], "lat": round(f["lat"], 5), "lon": round(f["lon"], 5)} for f in load("data/health_facilities_final.json")]
    check(len(villages) == 142 and len(facilities) == 34, "142 villages / 34 facilities")
    c3 = {x["way_id"]: x for x in load("research/investigation/c3_alternate_pre_vs_now.json")["pre"]["crossings"]}
    topo = load("data/osm/wayanad_roads_topology_buf10km.json")
    nd = {e["id"]: (e["lat"], e["lon"]) for e in topo["elements"] if e["type"] == "node"}
    meen = next(e for e in topo["elements"] if e["type"] == "way" and e["id"] == 380928376)
    check(meen["tags"].get("name") == "Meenakshi Bridge", "way 380928376 should be the Meenakshi Bridge")
    mpts = [nd[n] for n in meen["nodes"]]
    ckm_cut = next(r for r in states["today|V0"] if r["villages"] == CKM)["cut"]
    markers = {
        "sh59": {"lat": round((ckm_cut["u_latlon"][0] + ckm_cut["v_latlon"][0]) / 2, 6), "lon": round((ckm_cut["u_latlon"][1] + ckm_cut["v_latlon"][1]) / 2, 6),
                 "label": f"SH59 cut: {ckm_cut['highway']} link on OSM way {ckm_cut['way_id']} ({ckm_cut['length_m']} m)"},
        "failed_bridge": {"lat": c3[380928388]["lat"], "lon": c3[380928388]["lon"], "label": "Chooralmala–Mundakkai bridge, failed 30 Jul 2024 (now the Bailey Bridge, OSM way 380928388)"},
        "track_bridge": {"lat": c3[794270381]["lat"], "lon": c3[794270381]["lon"], "label": "Unpaved track bridge, OSM way 794270381 (tagged destroyed by the 2024 landslide since 2024-12-31)"},
        "meenakshi": {"lat": round(sum(p[0] for p in mpts) / len(mpts), 6), "lon": round(sum(p[1] for p in mpts) / len(mpts), 6),
                      "label": "Meenakshi Bridge, Kalladi (OSM way 380928376): landslide 7 Jul 2026"},
    }

    # ---- validation matrix (research/followup_validation.md numbers, from f_variants)
    matrix = {}
    for s in ("pre", "now"):
        for v in ("V0", "V1", "V2"):
            l1 = fv[(s, v)]["iii_level1"]
            matrix[f"{s}|{v}"] = {"level1_cut": l1["is_village_isolating_cut"], "level1_nodes": l1["isolated_nodes"],
                                  "level1_pop": l1["population_attributed"], "bailey_cut": fv[(s, v)]["i_failed_bridge"]["is_village_isolating_cut"],
                                  "bailey_villages": fv[(s, v)]["i_failed_bridge"].get("villages", []),
                                  "enclaves": len(fv[(s, v)]["iv_enclaves"]),
                                  "no_route_villages": fv[(s, v)]["v_no_facility_route"]["total"]}
    check(all(m["level1_cut"] for m in matrix.values()), "Level 1 must be a cut in all six")

    # ---- event excerpts: each must appear verbatim in the named research file
    def quote(path, text, url, who, date):
        body = open(ROOT / path, encoding="utf-8").read()
        check(text in body, f"excerpt not found verbatim in {path}: {text[:60]}")
        check(url in body, f"url not found in {path}: {url}")
        return {"text": text, "url": url, "who": who, "date": date, "file": path}
    events = [
        {"date": "30 Jul 2024", "title": "Landslides at Mundakkai and Chooralmala", "relation": "The area this corridor serves was cut off; the failed bridge lies beyond the corridor, up the valley.",
         "quotes": [quote("research/bridge_investigation.md", "Collapse of bridge over Punapuzha, which is the only connective way of Mundakkai to Chooramala [sic] and other parts of Wayanad, isolated Mundakkai", "https://bhusanket.gsi.gov.in/Public_Portal_News_pdf/FIR_Mundakkai-Chooralmala.cleaned.pdf", "Geological Survey of India, First Information Report", "30.07.2024"),
                    quote("research/bridge_investigation.md", "washed away the bridge near Chooralmala (11.4992° N, 76.1601° E), severing the critical connection between Chooralmala and Mundakkai", "https://www.nature.com/articles/s41598-025-07828-3", "Ramesh et al., Scientific Reports 15", "2025"),
                    quote("research/kalladi_2026_check.md", "As per reports, the rescue team can transport the rescue vehicles, cutters, food and water to Mundakkai only after the completion of the bridge.", "http://web.archive.org/web/20260421013527/https://ddnews.gov.in/en/wayanad-tragedy-army-erecting-temporary-bailey-bridge-in-chooralmala-toll-risen-to-167/", "DD News (archived copy)", "1 Aug 2024")]},
        {"date": "7 Jul 2026", "title": "Landslide at Kalladi, near the Meenakshi Bridge", "relation": "Inside this corridor: the Meenakshi Bridge (OSM way 380928376) is on the SH59 Level 1 stretch.",
         "quotes": [quote("research/kalladi_2026_check.md", "According to the district administration, 18 people were caught in the landslide near the Meenakshi Bridge at the Kalladi-Anakkampoyil tunnel construction site, completely disrupting traffic on the Meppadi-Chooralmala road.", "https://aninews.in/news/national/general-news/keralam-three-killed-seven-missing-after-landslide-at-kalladi-tunnel-construction20260707175128/", "ANI", "7 Jul 2026"),
                    quote("research/kalladi_2026_check.md", "Road traffic in the area has been completely disrupted.", "https://www.etvbharat.com/en/state/landslide-hits-wayanad-tunnel-project-site-in-kerala-several-trapped-rescue-operation-underway-enn26070702157", "ETV Bharat", "7 Jul 2026")]},
    ]

    # ---- RA2CE comparison
    ra_sum, ra_len, ra_slr = load("research/ra2ce/sh59_summary.json"), load("research/ra2ce/sh59_length_comparison.json"), load("research/ra2ce/slr_summary.json")
    check(sorted(ra_sum["no_access"]) == CKM, "RA2CE no-access set")
    ra_md = open(ROOT / "research/ra2ce_crosscheck.md", encoding="utf-8").read()
    urls = set(re.findall(r"\((https://github\.com/Deltares/ra2ce/blob/v1\.2\.2/[^)]+)\)", ra_md))
    def link(file_and_anchor):
        """file_and_anchor e.g. 'multi_link_isolated_locations.py#L182-L195'; must be a permalink used in the report."""
        hits = [u for u in urls if u.endswith("/" + file_and_anchor)]
        check(len(hits) == 1, f"permalink not found in ra2ce_crosscheck.md: {file_and_anchor}")
        f, anchor = file_and_anchor.split("#")
        return {"label": f"{f} {anchor.replace('-', '–')}", "url": hits[0]}
    ra2ce = {
        "no_access": ra_sum["no_access"], "lengths": ra_len,
        "slr": {"links": ra_slr["links"], "detour0": ra_slr["detour_counts"]["0"], "share_pct": ra_slr["share_detour0_pct"],
                "primary_trunk_detour0": len(ra_slr["detour0_primary_trunk"]), "sh59": ra_slr["sh59_chain_lid24382"][0]["detour"]},
        "differences": [
            {"title": "Disruption only through a hazard map", "ours": "We remove the link from the road network directly and recompute every village's reachability to every facility.",
             "theirs": "Links are disrupted only where a hazard raster exceeds a threshold; no field accepts a list of links to remove. Our SH59 test had to be forced through a synthetic 2 m hazard cell.",
             "links": [link("multi_link_isolated_locations.py#L182-L195"), link("origin_closest_destination.py#L198-L206"),
                       link("analysis_config_data.py#L79-L185")]},
            {"title": "Bridges are never disrupted", "ours": "Bridges are ordinary road links; they are often the links that fail.",
             "theirs": "Both hazard analyses require an edge not to be tagged bridge=yes before disrupting it, so the Bailey, Meenakshi and Kalladi bridges could not fail with OSM tags as they are.",
             "links": [link("multi_link_isolated_locations.py#L190-L193"), link("origin_closest_destination.py#L198-L199")]},
            {"title": "Isolation without facilities or population", "ours": "Isolated means no road route to any curated health facility; population comes from Census 2011 with a no-double-counting rule.",
             "theirs": "Its isolation analysis means outside the largest connected piece of the network, and never refers to a destination. Its separate closest-destination analysis does measure facility access, but only through hazard disruption, with bridges exempt.",
             "links": [link("multi_link_isolated_locations.py#L65-L87"), link("multi_link_isolated_locations.py#L201"),
                       link("origins_destinations.py#L61")]},
        ],
    }

    # ---- ledger: errors we found and fixed
    old_demo = json.loads(git_show(BEFORE["demo"], "data/demo_data.json"))["false_positive_case"]
    new_demo = demo["false_positive_case"]
    check(old_demo["distance_to_boundary_m"] == 113 and old_demo["population"] == 31225, "old Thaloor values")
    check(new_demo["distance_to_boundary_m"] == 0 and new_demo["population"] is None, "new Thaloor values")
    check("286 of the 306" in new_demo["rejection_reason"] and new_demo["isolated_component_size"] == 306, "Thaloor 286/306")
    old_atlas = json.loads(git_show(BEFORE["atlas"], "data/enclave_atlas.json"))["enclaves"]
    spur_old = [e for e in old_atlas if e["spur_snap_villages"]]
    check(sorted(e["villages"][0] for e in spur_old) == ["Chundale", "Meenangadi", "Sultan Bathery"], "old spur enclaves")
    check(not any(e["spur_snap_villages"] for e in atlas["enclaves"]), "spur enclaves gone now")
    sb = next(e for e in spur_old if e["villages"] == ["Sultan Bathery"])
    check(sb["population_attributed"] == 23333 and sb["road_nodes"] == 1, "Sultan Bathery 23,333 / 1 node")
    cw = list(csv.DictReader(open(ROOT / "data/village_crosswalk.csv", encoding="utf-8")))
    rv_of = {r["osm_settlement"]: r["revenue_village"] for r in cw}
    pop_of = {r["revenue_village"]: int(float(r["population_2011"])) for r in cw if r["population_2011"]}
    members = {}
    for r in cw:
        members.setdefault(r["revenue_village"], set()).add(r["osm_settlement"])
    cp5 = load("data/checkpoint5_results.json")["affected"]
    aff = {a["village"] for a in cp5}
    rvs = sorted({rv_of[a] for a in aff})
    full = [rv for rv in rvs if members[rv] <= aff]
    partial = [rv for rv in rvs if rv not in full]
    reconstructed = sum(pop_of[rv] for rv in rvs)
    attributed = sum(pop_of[rv] for rv in full)
    check((reconstructed, attributed) == (24773, 11462), f"Kalpetta-Panamaram arithmetic {reconstructed} {attributed}")
    deltas = [a["after_min"] - a["before_min"] for a in cp5]
    check(all(a["after_min"] is not None for a in cp5), "Kalpetta-Panamaram is a reroute (all still reachable)")
    old_fac = json.loads(git_show(BEFORE["facilities"], "data/health_facilities_final.json"))
    new_fac = load("data/health_facilities_final.json")
    keyf = lambda f: (f["name"], round(f["lat"], 6), round(f["lon"], 6))
    added = [f for f in new_fac if keyf(f) not in {keyf(x) for x in old_fac}]
    removed = [f for f in old_fac if keyf(f) not in {keyf(x) for x in new_fac}]
    check(len(old_fac) == len(new_fac) == 34, "facility counts 34 -> 34")
    ledger = {
        "thaloor": {"before_commit": BEFORE["demo"], "distance_before": old_demo["distance_to_boundary_m"], "distance_after": new_demo["distance_to_boundary_m"],
                    "population_before": old_demo["population"], "population_after_note": new_demo["population_note"],
                    "component": new_demo["isolated_component_size"], "reason": new_demo["rejection_reason"]},
        "spur": {"before_commit": BEFORE["atlas"], "villages": sorted(e["villages"][0] for e in spur_old),
                 "sultan_population": sb["population_attributed"], "sultan_nodes": sb["road_nodes"],
                 "atlas_before": len(old_atlas), "atlas_after": len(atlas["enclaves"])},
        "kalpetta": {"affected": sorted(aff), "revenue_villages": {rv: pop_of[rv] for rv in rvs}, "full": full, "partial": partial,
                     "partial_detail": {rv: {"inside": len(members[rv] & aff), "total": len(members[rv])} for rv in partial},
                     "reconstructed": reconstructed, "attributed": attributed,
                     "delta_min": [round(min(deltas), 1), round(max(deltas), 1)]},
        "facilities": {"before_commit": BEFORE["facilities"], "before": len(old_fac), "after": len(new_fac),
                       "added": [{"name": f["name"], "reason": f.get("reason", "")} for f in added],
                       "removed": [f["name"] for f in removed]},
    }

    # ---- caveats + sources (carried over from the v1 page, unchanged in substance)
    v1 = open(ROOT / "rural-road-map-v1.html", encoding="utf-8").read()
    cav_block = re.search(r'<div class="panel caveats">(.*?)</ul>', v1, re.S).group(1)
    caveats = [re.sub(r"\s+", " ", li).strip() for li in re.findall(r"<li>(.*?)</li>", cav_block, re.S)]
    check(len(caveats) == 6, f"expected 6 caveats from v1, found {len(caveats)}")
    sources = demo["primary_finding"]["sources"]

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    data = {"states": states, "kalladi": kalladi, "aftermath": aftermath, "bailey": bailey, "geoms": geoms.store,
            "context": context, "boundary": boundary, "villages": villages, "facilities": facilities, "markers": markers,
            "matrix": matrix, "events": events, "ra2ce": ra2ce, "ledger": ledger, "caveats": caveats, "sources": sources,
            "population_source": demo["primary_finding"]["population_source"],
            "build": {"commit": head, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "assertions": "passed"}}

    tpl = TEMPLATE.read_text(encoding="utf-8")
    page = (tpl.replace("/*__LEAFLET_CSS__*/", (VENDOR / "leaflet.css").read_text(encoding="utf-8"))
               .replace("/*__LEAFLET_JS__*/", (VENDOR / "leaflet.js").read_text(encoding="utf-8"))
               .replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
    check("__DATA__" not in page and "__LEAFLET" not in page, "template placeholders left")
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.name}: {OUT.stat().st_size / 1e6:.2f} MB; geometries {len(geoms.store)}; states {sorted(states)}; all assertions passed")


if __name__ == "__main__":
    main()
