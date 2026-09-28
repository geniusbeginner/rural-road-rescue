"""C2. Build the pre-event (2024-07-29) graph with the same code path as build_buffered_graph.py
(build_weighted_graph, node distance attributes, 500 m snapping). Settlements and facilities are FIXED at the
current set: 142 OSM settlements + curated 34 + 31 rule-selected buffer-ring facilities. Then completeness
comparison vs the 2026-09-16 graph. Read-only on data/; pickle goes to research/investigation/raw/ (gitignored)."""
import json
import math
import pickle
import sys
import time
from collections import Counter
import geopandas as gpd
import networkx as nx
import requests
import shapely
from shapely.geometry import shape

sys.path.insert(0, "scripts")
from checkpoint3_4 import build_weighted_graph          # pure function, unchanged
from checkpoint2 import build_kdtree, snap_point, SNAP_CAP_M  # pure functions, unchanged

PRE = "research/investigation/raw/wayanad_roads_topology_buf10km_2024-07-29.json"
NOW = "data/osm/wayanad_roads_topology_buf10km.json"
BAILEY_PT = (11.4992, 76.1601)
EVENT = "2024-07-29T00:00:00Z"
LEVEL2_CUT = (3249489400, 3842231008)

def hv(a, b):
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

def main():
    pre = json.load(open(PRE, encoding="utf-8"))
    pw = {e["id"]: e for e in pre["elements"] if e["type"] == "way"}
    print("=== date sanity checks on the pre-event extract ===")
    print(f"  way 1347557913 (created 2024-12-31) present: {1347557913 in pw}")
    print(f"  way 1426730512 (created 2025-09-02) present: {1426730512 in pw}")
    print(f"  way 380928388 tags: {pw.get(380928388, {}).get('tags')}")
    print(f"  way 794270381 tags: {pw.get(794270381, {}).get('tags')}")

    # ---- build (same code path) ----
    G, nodes = build_weighted_graph(PRE)
    district = shape(json.load(open("data/osm/wayanad_boundary.geojson")))
    buf = shape(json.load(open("data/osm/wayanad_buffer_10km.geojson")))
    dline = gpd.GeoSeries([district.exterior], crs=4326).to_crs(32643).iloc[0]
    dpoly = gpd.GeoSeries([district], crs=4326).to_crs(32643).iloc[0]
    bline = gpd.GeoSeries([buf.exterior], crs=4326).to_crs(32643).iloc[0]
    ids = list(nodes)
    pts = gpd.GeoSeries(gpd.points_from_xy([nodes[i][1] for i in ids], [nodes[i][0] for i in ids]), crs=4326).to_crs(32643).values
    db, ins, de = shapely.distance(pts, dline), shapely.contains(dpoly, pts), shapely.distance(pts, bline)
    for k, n in enumerate(ids):
        G.nodes[n].update(d_boundary_m=float(db[k]), inside=bool(ins[k]), d_bufedge_m=float(de[k]))
    comps = sorted((len(c) for c in nx.connected_components(G)), reverse=True)
    print(f"[pre-event] {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(comps)} components, largest {comps[:3]}")

    # ---- snap fixed settlements and facilities ----
    now = pickle.load(open("data/graph_buf10km.pkl", "rb"))
    Gn = now["G"]
    tree, tids, _, _ = build_kdtree(nodes)
    def resnap(items, label):
        out, changed = [], []
        for p in items:
            nid, dist = snap_point(p, tree, tids, nodes)
            r = {k: p[k] for k in ("name", "lat", "lon")} | {"node_id": nid, "dist_m": dist, "snapped": dist <= SNAP_CAP_M}
            if "osm" in p: r["osm"] = p["osm"]
            out.append(r)
            if nid != p["node_id"]:
                changed.append((p["name"], p["node_id"], round(p["dist_m"]), nid, round(dist)))
        print(f"[{label}] snapped {sum(r['snapped'] for r in out)}/{len(out)}; snap node differs from 2026 graph: {len(changed)}")
        for c in changed:
            print(f"    {c[0]:30s} 2026 node {c[1]} ({c[2]} m) -> pre-event node {c[3]} ({c[4]} m)")
        return out
    villages = resnap(now["villages"], "villages (fixed 142)")
    fac34 = resnap(now["facilities34"], "facilities curated 34 (fixed)")
    ring = resnap(now["facilities_ring"], "facilities buffer ring 31 (fixed)")
    pickle.dump({"G": G, "nodes": nodes, "villages": villages, "facilities34": fac34, "facilities_ring": ring,
                 "buffer_km": 10, "osm_date": "2024-07-29"}, open("research/investigation/raw/graph_pre_event.pkl", "wb"))

    # ---- completeness comparison ----
    print("\n=== COMPLETENESS: edges by highway class, pre-event (2024-07-29) vs 2026-09-16 ===")
    def by_class(Gx, sel):
        return Counter(d["highway"] for u, v, d in Gx.edges(data=True) if sel(Gx, u, v))
    inside = lambda Gx, u, v: Gx.nodes[u]["inside"] and Gx.nodes[v]["inside"]
    near = lambda Gx, u, v: min(hv(BAILEY_PT, (Gx.nodes[u]["lat"], Gx.nodes[u]["lon"])),
                                hv(BAILEY_PT, (Gx.nodes[v]["lat"], Gx.nodes[v]["lon"]))) <= 3000
    for label, sel in (("WHOLE DISTRICT (both ends inside)", inside), ("WITHIN 3 km OF 11.4992,76.1601", near)):
        a, b = by_class(G, sel), by_class(Gn, sel)
        print(f"\n{label}")
        print(f"  {'class':15s} {'pre':>8s} {'2026':>8s} {'diff':>7s} {'pre/2026':>9s}")
        for k in sorted(set(a) | set(b), key=lambda k: -b.get(k, 0)):
            print(f"  {k:15s} {a.get(k,0):8d} {b.get(k,0):8d} {a.get(k,0)-b.get(k,0):7d} {a.get(k,0)/b[k] if b.get(k) else float('nan'):9.3f}")
        print(f"  {'TOTAL':15s} {sum(a.values()):8d} {sum(b.values()):8d} {sum(a.values())-sum(b.values()):7d} {sum(a.values())/sum(b.values()):9.3f}")

    # ways in the 2026 Level-2 enclave area: which are absent pre-event, and their creation dates
    G2 = Gn.copy(); G2.remove_edge(*LEVEL2_CUT)
    enclave = min((nx.node_connected_component(G2, n) for n in LEVEL2_CUT), key=len)
    enc_ways = {d["way_id"] for u, v, d in Gn.subgraph(enclave).edges(data=True)}
    pre_ways = {d["way_id"] for u, v, d in G.edges(data=True)}
    missing = sorted(enc_ways - pre_ways)
    print(f"\n2026 Level-2 enclave: {len(enclave)} nodes, {len(enc_ways)} ways; ways absent from pre-event graph: {len(missing)}")
    created_after = []
    for w in missing:
        r = requests.get(f"https://api.openstreetmap.org/api/0.6/way/{w}/history.json",
                         headers={"User-Agent": "rural-road-research/0.1"}, timeout=60)
        els = r.json()["elements"] if r.status_code == 200 else []
        created = els[0]["timestamp"] if els else f"HTTP {r.status_code}"
        hw_first = els[0].get("tags", {}).get("highway") if els else None
        # when did it first carry a road highway class?
        first_road = next((e["timestamp"] for e in els if e.get("tags", {}).get("highway")), None)
        if created > EVENT: created_after.append(w)
        print(f"  way {w}: created {created} (first highway tag {hw_first}, first version with highway at {first_road}); "
              f"2026 tags {({k: v for k, v in Gn.edges[[ (u,v) for u,v,d in Gn.edges(data=True) if d['way_id']==w][0]].items() if k=='highway'})}")
        time.sleep(0.5)
    print(f"Enclave-area ways created after {EVENT}: {len(created_after)} -> {created_after}")
    json.dump({"enclave_ways_2026": len(enc_ways), "absent_pre_event": missing, "created_after_event": created_after},
              open("research/investigation/c_completeness.json", "w"), indent=1)

if __name__ == "__main__":
    main()
