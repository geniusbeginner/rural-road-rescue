"""Follow-up A: road-definition sensitivity. One snapshot x variant per invocation; results saved immediately.
  V0 = all 16 classes (current filter)
  V1 = V0 minus highway=track
  V2 = V1 minus ways with a lifecycle tag: key starting 'destroyed:', 'disused:', 'abandoned:', or plain key
       'destroyed'/'disused'/'abandoned' with value != 'no'.
Same code path: filtered raw extract -> checkpoint3_4.build_weighted_graph -> node distance attrs -> 500 m snapping ->
enclave functions copied verbatim from scripts/enclave_analysis.py (via c_enclave_analysis_pre_event.py).
Settlements and facilities are fixed (142 OSM settlements, curated 34 + 31 buffer ring). Read-only on data/.
Usage: python f_variants.py {pre|now} {V0|V1|V2}"""
import json
import math
import os
import pickle
import sys
import time
import geopandas as gpd
import networkx as nx
import shapely
from shapely.geometry import shape

sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/investigation")
from checkpoint3_4 import build_weighted_graph
from checkpoint2 import build_kdtree, snap_point, SNAP_CAP_M
from c_enclave_analysis_pre_event import run, flag, edge_info, population, load_crosswalk

SRC = {"pre": "research/investigation/raw/wayanad_roads_topology_buf10km_2024-07-29.json",
       "now": "data/osm/wayanad_roads_topology_buf10km.json"}
OUT = "research/investigation/f_variants"
BRIDGE = (3842230570, 3842230578)      # way 380928388, failed bridge / Bailey site
LEVEL1 = (3249489501, 5870049103)      # SH59 Level-1 outermost edge
LEVEL2 = (3249489400, 3842231008)
LIFE = ("destroyed", "disused", "abandoned")
SHOW = ["highway", "surface", "tracktype", "bridge", "access", "motor_vehicle", "name"]

def lifecycle(tags):
    return {k: v for k, v in tags.items()
            if any(k.startswith(p + ":") for p in LIFE) or (k in LIFE and v != "no")}

def keep(tags, var):
    if var in ("V1", "V2") and tags.get("highway") == "track":
        return False
    if var == "V2" and lifecycle(tags):
        return False
    return True

def main(snap, var):
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    raw = json.load(open(SRC[snap], encoding="utf-8"))
    ways = [e for e in raw["elements"] if e["type"] == "way"]
    kept = [w for w in ways if keep(w.get("tags", {}), var)]
    need = {n for w in kept for n in w["nodes"]}
    filt = {"elements": [e for e in raw["elements"] if e["type"] == "node" and e["id"] in need] + kept}
    path = f"research/investigation/raw/f_{snap}_{var}.json"
    json.dump(filt, open(path, "w", encoding="utf-8"))
    wtags = {w["id"]: w.get("tags", {}) for w in ways}
    print(f"[{snap} {var}] ways kept {len(kept)}/{len(ways)} (dropped {len(ways)-len(kept)})")

    G, nodes = build_weighted_graph(path)
    district = shape(json.load(open("data/osm/wayanad_boundary.geojson")))
    buf = shape(json.load(open("data/osm/wayanad_buffer_10km.geojson")))
    to_p = lambda g: gpd.GeoSeries([g], crs=4326).to_crs(32643).iloc[0]
    ids = list(nodes)
    pts = gpd.GeoSeries(gpd.points_from_xy([nodes[i][1] for i in ids], [nodes[i][0] for i in ids]), crs=4326).to_crs(32643).values
    db, ins, de = shapely.distance(pts, to_p(district.exterior)), shapely.contains(to_p(district), pts), shapely.distance(pts, to_p(buf.exterior))
    for k, n in enumerate(ids):
        G.nodes[n].update(d_boundary_m=float(db[k]), inside=bool(ins[k]), d_bufedge_m=float(de[k]))
    ncomp = nx.number_connected_components(G)
    print(f"[{snap} {var}] graph {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {ncomp} components  ({time.time()-t0:.0f}s)")

    fixed = pickle.load(open("data/graph_buf10km.pkl", "rb"))
    tree, tids, _, _ = build_kdtree(nodes)
    def snapall(items):
        out = []
        for p in items:
            nid, dist = snap_point(p, tree, tids, nodes)
            r = {k: p[k] for k in ("name", "lat", "lon")} | {"node_id": nid, "dist_m": dist, "snapped": dist <= SNAP_CAP_M}
            out.append(r)
        return out
    villages = snapall(fixed["villages"])
    facs = snapall(fixed["facilities34"] + fixed["facilities_ring"])
    v0snap = None
    if var != "V0":
        v0snap = json.load(open(f"{OUT}/{snap}_V0.json"))["snaps"]
    snaps = {"villages": {v["name"] + f"@{v['lat']},{v['lon']}": [v["node_id"], round(v["dist_m"])] for v in villages},
             "facilities": {f["name"] + f"@{f['lat']},{f['lon']}": [f["node_id"], round(f["dist_m"])] for f in facs}}
    unsnapped_v = [v["name"] for v in villages if not v["snapped"]]
    unsnapped_f = [f["name"] for f in facs if not f["snapped"]]
    moved_v = []
    if v0snap:
        moved_v = [(k.split("@")[0], v0snap["villages"][k], snaps["villages"][k]) for k in snaps["villages"]
                   if snaps["villages"][k][0] != v0snap["villages"][k][0]]
    print(f"[{snap} {var}] villages snapped {len(villages)-len(unsnapped_v)}/142, unsnapped {unsnapped_v}; "
          f"facilities snapped {len(facs)-len(unsnapped_f)}/65, unsnapped {unsnapped_f}; villages whose snap moved vs V0: {len(moved_v)}")
    for m in moved_v:
        print(f"    {m[0]:28s} V0 node {m[1][0]} ({m[1][1]} m) -> node {m[2][0]} ({m[2][1]} m)")

    r = run(f"{snap} {var}", G, villages, facs)
    places, rv_of, pop_of, members = load_crosswalk()
    pid = lambda v: places[(v["name"], v["lat"], v["lon"])]
    cutmap = {frozenset(c["edge"]): c for c in r["cuts"]}
    def cutinfo(edge):
        if not G.has_edge(*edge):
            return {"edge_present": False}
        c = cutmap.get(frozenset(edge))
        info = {"edge_present": True, "is_graph_bridge": None, "is_village_isolating_cut": c is not None}
        if c:
            vs = [x for n in c["vil"] for x in r["vnode"][n]]
            info |= {"villages": sorted(x["name"] for x in vs), "isolated_nodes": c["n"],
                     **population({pid(x) for x in vs}, rv_of, pop_of, members)}
        return info

    vil = {v["name"]: v for v in villages}
    s, t = vil["Chooralmala"]["node_id"], vil["Mundakai"]["node_id"]
    res = {"snapshot": snap, "variant": var, "ways_kept": len(kept), "ways_total": len(ways),
           "nodes": G.number_of_nodes(), "edges": G.number_of_edges(), "components": ncomp,
           "unsnapped_villages": unsnapped_v, "unsnapped_facilities": unsnapped_f, "snap_moved_vs_V0": moved_v,
           "chooralmala_node": s, "mundakai_node": t, "snaps": snaps}

    # (i) failed bridge
    fb = cutinfo(BRIDGE)
    if fb["edge_present"]:
        fb["is_graph_bridge"] = frozenset(BRIDGE) in {frozenset(e) for e in nx.bridges(nx.Graph(G.subgraph(nx.node_connected_component(G, BRIDGE[0]))))}
    H = nx.restricted_view(G, [], [BRIDGE] if G.has_edge(*BRIDGE) else [])
    alt = {"connected_without_bridge": nx.has_path(H, s, t)}
    if alt["connected_without_bridge"]:
        p = nx.shortest_path(H, s, t, weight="length_m")
        runs = []
        for a, c in zip(p, p[1:]):
            d = G[a][c]; tg = wtags.get(d["way_id"], {})
            if runs and runs[-1]["way_id"] == d["way_id"]:
                runs[-1]["edges"] += 1; runs[-1]["length_m"] += d["length_m"]
            else:
                runs.append({"way_id": d["way_id"], "edges": 1, "length_m": d["length_m"],
                             "start": [G.nodes[a]["lat"], G.nodes[a]["lon"]],
                             **{k: tg.get(k, "") for k in SHOW}, "lifecycle": lifecycle(tg)})
        alt |= {"n_edges": len(p) - 1, "length_m": sum(G[a][c]["length_m"] for a, c in zip(p, p[1:])),
                "time_min": sum(G[a][c]["time_min"] for a, c in zip(p, p[1:])), "ways": runs}
    res["i_failed_bridge"] = fb | {"alternate": alt}
    print(f"\n(i) failed bridge {BRIDGE}: {json.dumps({k: v for k, v in fb.items()})}")
    print(f"    without it, Chooralmala->Mundakai connected: {alt['connected_without_bridge']}"
          + (f"; {alt['n_edges']} edges, {alt['length_m']:.0f} m, {alt['time_min']:.2f} min" if alt["connected_without_bridge"] else ""))
    for w in alt.get("ways", []):
        print(f"      way {w['way_id']}: {w['edges']} edges {w['length_m']:.0f} m start {w['start']} "
              + " ".join(f"{k}={w[k]}" for k in SHOW if w[k]) + (f" LIFECYCLE {w['lifecycle']}" if w["lifecycle"] else ""))

    # (ii) edge connectivity within the snapshot's V0 Level-2 enclave node set (all C-M paths lie inside it)
    if var == "V0":
        G2 = G.copy(); G2.remove_edge(*LEVEL2)
        enc = min((nx.node_connected_component(G2, n) for n in LEVEL2), key=len)
        pickle.dump(enc, open(f"research/investigation/raw/f_{snap}_V0_level2_enclave.pkl", "wb"))
    else:
        enc = pickle.load(open(f"research/investigation/raw/f_{snap}_V0_level2_enclave.pkl", "rb"))
    S = nx.Graph(G.subgraph([n for n in enc if n in G]))
    if s in S and t in S and nx.has_path(S, s, t):
        ec = nx.edge_connectivity(S, s, t)
        mc = [[*e, G.edges[e]["way_id"], wtags.get(G.edges[e]["way_id"], {}).get("highway")] for e in nx.minimum_edge_cut(S, s, t)]
    else:
        ec, mc = 0, "disconnected in base graph"
    res["ii_edge_connectivity"] = {"edge_connectivity": ec, "min_cut": mc}
    print(f"(ii) Chooralmala-Mundakai edge connectivity: {ec}; minimum cut: {mc}")

    # (iii) Level-1 corridor
    l1 = cutinfo(LEVEL1)
    res["iii_level1"] = l1
    print(f"(iii) Level-1 edge {LEVEL1}: " + json.dumps({k: v for k, v in l1.items() if k in ('edge_present', 'is_village_isolating_cut', 'villages', 'isolated_nodes', 'population_attributed')}))

    # (iv) enclaves
    encl = []
    for e in sorted(r["enclaves"], key=lambda e: -e["outermost"]["n"]):
        o = e["outermost"]
        vs = [x for n in e["vil"] for x in r["vnode"][n]]
        pop = population({pid(x) for x in vs}, rv_of, pop_of, members)
        encl.append({"villages": sorted(x["name"] for x in vs), "nodes": o["n"], "n_cuts": e["n_cuts"], "flag": flag(o),
                     "outermost_edge": edge_info(G, *o["edge"]), "population_attributed": pop["population_attributed"],
                     "partial_unattributed": list(pop["revenue_villages_partial_unattributed"])})
    res["iv_enclaves"] = encl
    print(f"(iv) enclaves: {len(encl)} (real {sum(e['flag']=='real' for e in encl)}, suspect {sum(e['flag']=='suspect' for e in encl)})")
    for e in encl:
        print(f"     {e['nodes']:6d} nodes {e['n_cuts']:4d} cuts {e['flag']:7s} pop {e['population_attributed']:>8,.0f}  {e['villages']}")

    # (v) villages with no route to any facility in the base graph
    nofac = sorted(n for c in r["nofac"] for n in r["names"](c["villages"]))
    res["v_no_facility_route"] = {"unsnapped": unsnapped_v, "in_facility_free_components": nofac,
                                  "total": len(unsnapped_v) + len(nofac)}
    print(f"(v) villages with no route to any facility: {len(unsnapped_v) + len(nofac)} "
          f"(unsnapped {len(unsnapped_v)}: {unsnapped_v}; facility-free components {len(nofac)}: {nofac})")
    json.dump(res, open(f"{OUT}/{snap}_{var}.json", "w"), indent=1, default=str)
    print(f"saved {OUT}/{snap}_{var}.json  (total {time.time()-t0:.0f}s)")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
