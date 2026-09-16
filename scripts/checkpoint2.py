import json
import math
import sys
import numpy as np
from scipy.spatial import cKDTree
import networkx as nx

sys.path.insert(0, "scripts")
from build_graph import build_graph, haversine_m

SNAP_CAP_M = 500

def load_villages(path):
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for el in d["elements"]:
        tags = el.get("tags", {})
        if tags.get("place") not in ("village", "town"):
            continue
        out.append({"name": tags.get("name", "(unnamed)"), "lat": el["lat"], "lon": el["lon"]})
    return out

def load_facilities(path):
    return json.load(open(path, encoding="utf-8"))

def build_kdtree(nodes):
    ids = list(nodes.keys())
    # crude equirectangular projection centered on Wayanad for KDTree distance approx (fine at this scale)
    lat0 = 11.67
    coords = np.array([
        ((nodes[i][1] - 76.08) * 111320 * math.cos(math.radians(lat0)), (nodes[i][0] - lat0) * 110540)
        for i in ids
    ])
    tree = cKDTree(coords)
    return tree, ids, coords, lat0

def project(lat, lon, lat0=11.67):
    return (
        (lon - 76.08) * 111320 * math.cos(math.radians(lat0)),
        (lat - lat0) * 110540,
    )

def snap_point(pt, tree, ids, nodes):
    x, y = project(pt["lat"], pt["lon"])
    dist, idx = tree.query([x, y])
    node_id = ids[idx]
    nlat, nlon = nodes[node_id]
    actual_m = haversine_m(pt["lat"], pt["lon"], nlat, nlon)
    return node_id, actual_m

def main():
    print("=== Building filtered vehicle-road network graph ===")
    G, nodes = build_graph("data/osm/wayanad_roads_topology.json")
    tree, ids, coords, lat0 = build_kdtree(nodes)

    villages = load_villages("data/osm/wayanad_places.json")
    facilities = load_facilities("data/health_facilities_final.json")
    print(f"\nVillages (place=village|town): {len(villages)}")
    print(f"Health facilities (curated): {len(facilities)}")

    # --- Snap villages ---
    print(f"\n=== Village snap (cap {SNAP_CAP_M}m) ===")
    v_results = []
    for v in villages:
        node_id, dist = snap_point(v, tree, ids, nodes)
        ok = dist <= SNAP_CAP_M
        v_results.append({**v, "node_id": node_id, "dist_m": dist, "snapped": ok})
    v_ok = sum(1 for r in v_results if r["snapped"])
    v_pct = 100 * v_ok / len(v_results)
    print(f"Villages snapped within {SNAP_CAP_M}m: {v_ok}/{len(v_results)} = {v_pct:.1f}%  (pass threshold >=95%)")
    v_fail = [r for r in v_results if not r["snapped"]]
    if v_fail:
        print(f"\nFAILING villages ({len(v_fail)}):")
        for r in sorted(v_fail, key=lambda x: -x["dist_m"]):
            print(f"  {r['name']:30s} dist={r['dist_m']:.0f}m  ({r['lat']}, {r['lon']})")

    # --- Snap facilities ---
    print(f"\n=== Facility snap (cap {SNAP_CAP_M}m) — full manual list ===")
    f_results = []
    for f in facilities:
        node_id, dist = snap_point(f, tree, ids, nodes)
        ok = dist <= SNAP_CAP_M
        f_results.append({**f, "node_id": node_id, "dist_m": dist, "snapped": ok})
    f_ok = sum(1 for r in f_results if r["snapped"])
    f_pct = 100 * f_ok / len(f_results)
    for r in sorted(f_results, key=lambda x: -x["dist_m"]):
        flag = "OK " if r["snapped"] else "FAIL"
        maplink = f"https://www.openstreetmap.org/?mlat={r['lat']}&mlon={r['lon']}#map=18/{r['lat']}/{r['lon']}"
        print(f"  [{flag}] {r['name']:52s} dist={r['dist_m']:6.0f}m  {maplink}")
    print(f"\nFacilities snapped within {SNAP_CAP_M}m: {f_ok}/{len(f_results)} = {f_pct:.1f}%  (pass threshold = 100%)")

    # --- Route success: village -> nearest facility (straight-line), check graph path exists ---
    print(f"\n=== Village -> nearest-facility route check ===")
    route_results = []
    for v in v_results:
        # nearest facility by straight-line distance
        dists = [haversine_m(v["lat"], v["lon"], f["lat"], f["lon"]) for f in f_results]
        nearest_idx = int(np.argmin(dists))
        nearest_f = f_results[nearest_idx]
        has_path = False
        if v["snapped"] and nearest_f["snapped"]:
            has_path = nx.has_path(G, v["node_id"], nearest_f["node_id"])
        route_results.append({
            "village": v["name"], "facility": nearest_f["name"],
            "village_snap_ok": v["snapped"], "facility_snap_ok": nearest_f["snapped"],
            "has_path": has_path,
        })
    r_ok = sum(1 for r in route_results if r["has_path"])
    r_pct = 100 * r_ok / len(route_results)
    print(f"Village->nearest-facility pairs with a valid route: {r_ok}/{len(route_results)} = {r_pct:.1f}%  (pass threshold >=90%)")
    fails = [r for r in route_results if not r["has_path"]]
    if fails:
        print(f"\nFAILING pairs ({len(fails)}):")
        for r in fails:
            reason = []
            if not r["village_snap_ok"]:
                reason.append("village not snapped")
            if not r["facility_snap_ok"]:
                reason.append("facility not snapped")
            if r["village_snap_ok"] and r["facility_snap_ok"]:
                reason.append("snapped but no path in graph (disconnected component)")
            print(f"  {r['village']:30s} -> {r['facility']:45s} [{', '.join(reason)}]")

    json.dump({
        "villages": v_results, "facilities": f_results, "routes": route_results,
        "village_snap_pct": v_pct, "facility_snap_pct": f_pct, "route_pct": r_pct,
    }, open("data/checkpoint2_results.json", "w", encoding="utf-8"), indent=2, default=str)

if __name__ == "__main__":
    main()
