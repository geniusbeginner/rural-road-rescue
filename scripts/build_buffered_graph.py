import json
import math
import pickle
import re
import sys
from collections import Counter
import numpy as np
import geopandas as gpd
import shapely
import networkx as nx
from shapely.geometry import shape, Point

sys.path.insert(0, "scripts")
from build_graph import haversine_m
from checkpoint3_4 import build_weighted_graph, SPEED_KMH
from checkpoint2 import build_kdtree, snap_point, SNAP_CAP_M
from snapping import fix_spur_snaps

BUFFERS_KM = [10, 5]
BUFFER_EDGE_RULE_M = 500  # labelled parameter, approved -- not a finding

# Explicit, reproducible facility rule for the buffer ring (outside the district).
# The 50 -> 34 step for the original list was a manual pass that no tag/name/distance rule
# reproduces, so this is stated separately and also checked against the in-district 34.
# Same facility types as the curated 34: PHC / FHC / CHC / urban PHC / taluk / district / government hospital.
# A first, broader version (any govt name or operator:type=government) pulled in AYUSH dispensaries,
# a veterinary hospital, a school and sub-centres, so it was narrowed to this.
GOVT_NAME_RE = re.compile(
    r"(primary|family|community|urban primary)\s+health\s+(centre|center)|\b(phc|chc|fhc)\b|"
    r"taluk.*hospital|district hospital|general hospital|gov(ernmen)?t\.?\s+hospital",
    re.I)
EXCLUDE_RE = re.compile(r"ayurved|homoe|homeo|homio|siddha|unani|veterinary|sub\s*-?\s*(family\s+)?(health\s+)?cent", re.I)
FACILITY_KINDS = {"hospital", "clinic", "centre", "yes", "doctors", "doctor"}
DEDUPE_M = 100

def load_json(p):
    return json.load(open(p, encoding="utf-8"))

def projected(lons, lats):
    return gpd.GeoSeries(gpd.points_from_xy(lons, lats), crs=4326).to_crs(32643).values

def element_latlon(e):
    if e["type"] == "node":
        return e["lat"], e["lon"]
    c = e.get("center")
    return (c["lat"], c["lon"]) if c else (None, None)

def facility_rule(tags):
    kind = tags.get("amenity") or tags.get("healthcare")
    if kind not in FACILITY_KINDS and tags.get("healthcare") not in FACILITY_KINDS:
        return False
    name = tags.get("name", "") + " " + tags.get("name:en", "")
    return bool(GOVT_NAME_RE.search(name)) and not EXCLUDE_RE.search(name) and tags.get("operator:type") != "private"

def extended_facilities(district):
    raw = load_json("data/osm/wayanad_health_buf10km.json")["elements"]
    cands = []
    for e in raw:
        tags = e.get("tags", {})
        lat, lon = element_latlon(e)
        if lat is None or not facility_rule(tags):
            continue
        cands.append({"name": tags.get("name") or tags.get("name:en") or "(unnamed)", "lat": lat, "lon": lon,
                      "osm": f"{e['type']}/{e['id']}", "inside_district": district.contains(Point(lon, lat))})
    inside = [c for c in cands if c["inside_district"]]
    outside = [c for c in cands if not c["inside_district"]]

    # sanity: what the same rule yields inside the district vs the hand-curated 34
    final34 = load_json("data/health_facilities_final.json")
    hit34 = sum(1 for f in final34 if any(haversine_m(f["lat"], f["lon"], c["lat"], c["lon"]) <= DEDUPE_M for c in inside))
    print(f"\n[facility rule check] inside district the rule selects {len(inside)} elements; "
          f"{hit34}/34 curated facilities have a rule-selected element within {DEDUPE_M} m")

    kept = []
    for c in sorted(outside, key=lambda c: c["name"]):
        if any(haversine_m(c["lat"], c["lon"], k["lat"], k["lon"]) <= DEDUPE_M for k in kept):
            continue
        kept.append(c)
    print(f"[facility rule] outside district, inside 10 km buffer: {len(outside)} matched, {len(kept)} after {DEDUPE_M} m dedupe")
    return kept

def subset_topology(topo, poly):
    elements = topo["elements"]
    node_ll = {e["id"]: (e["lat"], e["lon"]) for e in elements if e["type"] == "node"}
    ids = list(node_ll)
    inside = shapely.contains_xy(poly, np.array([node_ll[i][1] for i in ids]), np.array([node_ll[i][0] for i in ids]))
    inside_set = {i for i, ok in zip(ids, inside) if ok}
    ways = [e for e in elements if e["type"] == "way" and any(n in inside_set for n in e["nodes"])]
    keep_nodes = {n for w in ways for n in w["nodes"]}
    return {"elements": [e for e in elements if e["type"] == "node" and e["id"] in keep_nodes] + ways}

def component_stats(G, label):
    comps = sorted((len(c) for c in nx.connected_components(G)), reverse=True)
    print(f"[{label}] {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(comps)} connected components")
    print(f"[{label}] largest components: {comps[:5]}  | size-1: {sum(1 for s in comps if s == 1)}, "
          f"size 2-10: {sum(1 for s in comps if 2 <= s <= 10)}, size >10: {sum(1 for s in comps if s > 10)}")
    return comps

def resnap(points, nodes, old_by_name, label):
    tree, ids, _, _ = build_kdtree(nodes)
    out, changed = [], []
    for p in points:
        node_id, dist = snap_point(p, tree, ids, nodes)
        r = {**{k: p[k] for k in ("name", "lat", "lon")}, "node_id": node_id, "dist_m": dist, "snapped": dist <= SNAP_CAP_M}
        out.append(r)
        old = old_by_name.get((p["name"], p["lat"], p["lon"]))
        if old is not None and old["node_id"] != node_id:
            changed.append((p["name"], old["node_id"], old["dist_m"], node_id, dist))
    print(f"[{label}] snapped within {SNAP_CAP_M} m: {sum(r['snapped'] for r in out)}/{len(out)}; "
          f"snap node changed vs original graph: {len(changed)}")
    for c in changed:
        print(f"    {c[0]:35s} old node {c[1]} ({c[2]:.0f} m) -> new node {c[3]} ({c[4]:.0f} m)")
    return out

def main():
    district = shape(load_json("data/osm/wayanad_boundary.geojson"))
    district_line_p = gpd.GeoSeries([district.exterior], crs=4326).to_crs(32643).iloc[0]
    district_p = gpd.GeoSeries([district], crs=4326).to_crs(32643).iloc[0]

    topo10 = load_json("data/osm/wayanad_roads_topology_buf10km.json")
    print(f"10 km raw extract osm3s: {topo10.get('osm3s')}")
    print(f"10 km raw extract: {Counter(e['type'] for e in topo10['elements'])}")
    classes = Counter(e.get("tags", {}).get("highway") for e in topo10["elements"] if e["type"] == "way")
    print(f"highway classes: {dict(classes.most_common())}")
    print(f"classes with no SPEED_KMH entry (fall back to existing 20 km/h default): "
          f"{ {k: v for k, v in classes.items() if k not in SPEED_KMH} }")

    cp2 = load_json("data/checkpoint2_results.json")
    old_v = {(v["name"], v["lat"], v["lon"]): v for v in cp2["villages"]}
    old_f = {(f["name"], f["lat"], f["lon"]): f for f in cp2["facilities"]}
    ext_fac = extended_facilities(district)

    # old graph, for inside-district edge comparison
    old = pickle.load(open("data/graph_weighted.pkl", "rb"))
    G_old = old["G"]
    component_stats(G_old, "original clipped graph")

    for km in BUFFERS_KM:
        buf_poly = shape(load_json(f"data/osm/wayanad_buffer_{km}km.geojson")) if km == 10 else \
            gpd.GeoSeries([district], crs=4326).to_crs(32643).buffer(km * 1000).simplify(100).to_crs(4326).iloc[0]
        if km != 10:
            json.dump(shapely.geometry.mapping(buf_poly), open(f"data/osm/wayanad_buffer_{km}km.geojson", "w"))
        topo = topo10 if km == 10 else subset_topology(topo10, buf_poly)
        path = f"data/osm/wayanad_roads_topology_buf{km}km.json"
        if km != 10:
            json.dump(topo, open(path, "w", encoding="utf-8"))
        print(f"\n================ {km} km buffer ================")
        G, nodes = build_weighted_graph(path)
        comps = component_stats(G, f"buf{km}")

        ids = list(nodes)
        pts = projected([nodes[i][1] for i in ids], [nodes[i][0] for i in ids])
        d_boundary = shapely.distance(pts, district_line_p)
        inside = shapely.contains(district_p, pts)
        buf_edge_p = gpd.GeoSeries([buf_poly.exterior], crs=4326).to_crs(32643).iloc[0]
        d_bufedge = shapely.distance(pts, buf_edge_p)
        for i, nid in enumerate(ids):
            G.nodes[nid]["d_boundary_m"] = float(d_boundary[i])
            G.nodes[nid]["inside"] = bool(inside[i])
            G.nodes[nid]["d_bufedge_m"] = float(d_bufedge[i])
        n_in = int(inside.sum())
        print(f"[buf{km}] nodes inside district: {n_in}, outside: {len(ids) - n_in}")
        e_in = sum(1 for u, v in G.edges() if G.nodes[u]["inside"] and G.nodes[v]["inside"])
        print(f"[buf{km}] edges with both ends inside district: {e_in}, other: {G.number_of_edges() - e_in}")
        big = max(nx.connected_components(G), key=len)
        print(f"[buf{km}] largest component: {len(big)} nodes, of which inside district: "
              f"{sum(1 for n in big if G.nodes[n]['inside'])}")

        if km == 10:
            old_e = {frozenset(e) for e in G_old.edges()}
            new_e_in = {frozenset((u, v)) for u, v in G.edges() if G.nodes[u]["inside"] and G.nodes[v]["inside"]}
            old_e_in = {e for e in old_e if all(district.contains(Point(G_old.nodes[n]["lon"], G_old.nodes[n]["lat"])) for n in e)}
            print(f"\n[snapshot check] inside-district edges: original {len(old_e_in)}, buffered {len(new_e_in)}, "
                  f"in both {len(old_e_in & new_e_in)}, original-only {len(old_e_in - new_e_in)}, "
                  f"buffered-only {len(new_e_in - old_e_in)}")
            print(f"[snapshot check] ALL original edges present in buffered graph: {len(old_e & set(frozenset(e) for e in G.edges()))}/{len(old_e)}")

        print()
        villages = resnap(cp2["villages"], nodes, old_v, f"buf{km} villages")
        fac34 = resnap(cp2["facilities"], nodes, old_f, f"buf{km} facilities (curated 34)")
        ring = [f for f in ext_fac if buf_poly.contains(Point(f["lon"], f["lat"]))]
        ringsnap = resnap(ring, nodes, {}, f"buf{km} facilities (buffer ring, rule-selected)")
        for f, s in zip(ring, ringsnap):
            s["osm"] = f["osm"]
        villages, spur_changes = fix_spur_snaps(G, villages, {f["node_id"] for f in fac34 + ringsnap if f["snapped"]}, SNAP_CAP_M)
        print(f"[buf{km} spur-snap fix] {len(spur_changes)} villages re-snapped off dead-end spur tips:")
        for c in spur_changes:
            print(f"    {c[0]:28s} node {c[1]} -> {c[2]} ({c[3]})")
        pickle.dump({"G": G, "nodes": nodes, "villages": villages, "facilities34": fac34,
                     "facilities_ring": ringsnap, "buffer_km": km},
                    open(f"data/graph_buf{km}km.pkl", "wb"))
        print(f"wrote data/graph_buf{km}km.pkl")

    json.dump(ext_fac, open("data/health_facilities_buffer_ring.json", "w", encoding="utf-8"), indent=1)

if __name__ == "__main__":
    main()
