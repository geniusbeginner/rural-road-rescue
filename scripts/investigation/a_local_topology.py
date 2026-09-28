"""A. Local topology around the Bailey Bridge (OSM way 380928388) on the 2026-09-16 buffered graph.
Read-only on data/; writes only to research/investigation/."""
import csv
import json
import math
import pickle
import time
import requests
import networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import split, unary_union

OUT = "research/investigation"
PAPER_PT = (11.4992, 76.1601)          # Scientific Reports 2025 coordinate (lat, lon)
RADIUS_M = 1500
BAILEY_WAY = 380928388
LEVEL2_CUT = (3249489400, 3842231008)
SNAPSHOT_DATE = "2026-09-16T10:45:02Z"
TAGS = ["highway", "bridge", "access", "surface", "tracktype", "ford", "culvert", "layer", "name", "tunnel", "motor_vehicle"]

def hv(a, b):
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

def overpass(q):
    for i in range(6):
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=300,
                          headers={"User-Agent": "rural-road-research/0.1 (bridge investigation)"})
        if r.status_code == 200:
            return r.json()
        print(f"  overpass attempt {i+1}: HTTP {r.status_code}")
        time.sleep(20 * (i + 1))
    r.raise_for_status()

def main():
    b = pickle.load(open("data/graph_buf10km.pkl", "rb"))
    G = b["G"]
    topo = json.load(open("data/osm/wayanad_roads_topology_buf10km.json", encoding="utf-8"))
    wtags = {e["id"]: e.get("tags", {}) for e in topo["elements"] if e["type"] == "way"}
    ll = lambda n: (G.nodes[n]["lat"], G.nodes[n]["lon"])
    vil = {v["name"]: v for v in b["villages"]}
    cho, mun = vil["Chooralmala"], vil["Mundakai"]

    # enclave = isolated side of the Level-2 cut
    G2 = G.copy(); G2.remove_edge(*LEVEL2_CUT)
    sides = [nx.node_connected_component(G2, n) for n in LEVEL2_CUT]
    enclave = min(sides, key=len)
    print(f"Level-2 enclave: {len(enclave)} nodes (other side {max(len(s) for s in sides)})")
    print(f"Chooralmala snap node {cho['node_id']} in enclave: {cho['node_id'] in enclave}; "
          f"Mundakai snap node {mun['node_id']} in enclave: {mun['node_id'] in enclave}")

    bailey = [(u, v) for u, v, d in G.edges(data=True) if d["way_id"] == BAILEY_WAY]
    print(f"Bailey Bridge edges in graph: {bailey}")

    # edges within radius inside the enclave
    H = G.subgraph(enclave)
    near = [(u, v, d) for u, v, d in H.edges(data=True)
            if min(hv(PAPER_PT, ll(u)), hv(PAPER_PT, ll(v))) <= RADIUS_M]
    print(f"Enclave edges with an endpoint within {RADIUS_M} m of {PAPER_PT}: {len(near)} "
          f"(ways: {len({d['way_id'] for _,_,d in near})})")

    # waterways (same snapshot date as the graph)
    dlat = RADIUS_M / 111000 + 0.005
    dlon = dlat / math.cos(math.radians(PAPER_PT[0]))
    bbox = f"{PAPER_PT[0]-dlat},{PAPER_PT[1]-dlon},{PAPER_PT[0]+dlat},{PAPER_PT[1]+dlon}"
    q = f"""[out:json][timeout:120][date:"{SNAPSHOT_DATE}"];
(way["waterway"~"^(river|stream|canal|drain|ditch|brook)$"]({bbox}););
(._;>;);
out body;"""
    wd = overpass(q)
    json.dump({"query": q, "data": wd}, open(f"{OUT}/a_waterways_2026-09-16.json", "w", encoding="utf-8"))
    wnodes = {e["id"]: (e["lon"], e["lat"]) for e in wd["elements"] if e["type"] == "node"}
    wways = [e for e in wd["elements"] if e["type"] == "way"]
    wlines = {w["id"]: (w.get("tags", {}), LineString([wnodes[n] for n in w["nodes"] if n in wnodes]))
              for w in wways if sum(n in wnodes for n in w["nodes"]) >= 2}
    print(f"Waterway ways in bbox: {len(wlines)} "
          f"({ {t.get('waterway'):0 for t,_ in wlines.values()} and dict(__import__('collections').Counter(t.get('waterway') for t,_ in wlines.values())) })")

    rows = []
    for u, v, d in sorted(near, key=lambda e: e[2]["way_id"]):
        seg = LineString([(G.nodes[u]["lon"], G.nodes[u]["lat"]), (G.nodes[v]["lon"], G.nodes[v]["lat"])])
        crosses = [(wid, t.get("waterway"), t.get("name")) for wid, (t, line) in wlines.items() if seg.intersects(line)]
        t = wtags.get(d["way_id"], {})
        rows.append({"u": u, "v": v, "way_id": d["way_id"], "length_m": round(d["length_m"], 1),
                     "dist_to_point_m": round(min(hv(PAPER_PT, ll(u)), hv(PAPER_PT, ll(v)))),
                     **{k: t.get(k, "") for k in TAGS},
                     "crosses_waterway": ";".join(f"{w}:{ty}:{nm or ''}" for w, ty, nm in crosses)})
    with open(f"{OUT}/a_edges_within_1500m.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    cross_rows = [r for r in rows if r["crosses_waterway"]]
    print(f"\nEdges crossing a waterway: {len(cross_rows)}")
    for r in cross_rows:
        print(f"  way {r['way_id']} edge {r['u']}-{r['v']} {r['length_m']} m  highway={r['highway']} bridge={r['bridge'] or '-'} "
              f"culvert={r['culvert'] or '-'} ford={r['ford'] or '-'} access={r['access'] or '-'} tracktype={r['tracktype'] or '-'} "
              f"layer={r['layer'] or '-'} name={r['name'] or '-'}  crosses={r['crosses_waterway']}")
    by_way = {}
    for r in rows:
        by_way.setdefault(r["way_id"], r)
    print(f"\nAll ways within {RADIUS_M} m in enclave ({len(by_way)}):")
    for wid, r in sorted(by_way.items()):
        n = sum(1 for x in rows if x["way_id"] == wid)
        print(f"  way {wid}: {n} edges  " + " ".join(f"{k}={r[k]}" for k in TAGS if r[k]))

    # which river does the Bailey Bridge cross; bank analysis
    bu, bv = bailey[0]
    bseg = LineString([(G.nodes[bu]["lon"], G.nodes[bu]["lat"]), (G.nodes[bv]["lon"], G.nodes[bv]["lat"])])
    river_ids = [wid for wid, (t, line) in wlines.items() if bseg.intersects(line)]
    print(f"\nWaterways crossed by the Bailey Bridge edge: {[(wid, wlines[wid][0]) for wid in river_ids]}")
    bank = {}
    if river_ids:
        # the full river = all waterway ways sharing the crossed way's name (or just the crossed ways)
        names = {wlines[w][0].get("name") for w in river_ids} - {None}
        rid = [wid for wid, (t, _) in wlines.items() if wid in river_ids or (names and t.get("name") in names)]
        river = unary_union([wlines[w][1] for w in rid])
        circle = Point(PAPER_PT[1], PAPER_PT[0]).buffer(dlat)  # ~ bbox-sized disc in degrees
        pieces = list(split(circle, river).geoms)
        print(f"River ways used for bank split: {rid} (names {names}); disc split into {len(pieces)} pieces "
              f"(areas {[round(p.area*1e6,2) for p in pieces]} x1e-6 deg^2)")
        pts = {"paper coordinate 11.4992,76.1601": (PAPER_PT[1], PAPER_PT[0]),
               f"Chooralmala settlement point": (cho["lon"], cho["lat"]),
               f"Chooralmala snap node {cho['node_id']}": (G.nodes[cho["node_id"]]["lon"], G.nodes[cho["node_id"]]["lat"]),
               f"Mundakai settlement point": (mun["lon"], mun["lat"]),
               f"Mundakai snap node {mun['node_id']}": (G.nodes[mun["node_id"]]["lon"], G.nodes[mun["node_id"]]["lat"]),
               f"Bailey end node {bu}": (G.nodes[bu]["lon"], G.nodes[bu]["lat"]),
               f"Bailey end node {bv}": (G.nodes[bv]["lon"], G.nodes[bv]["lat"])}
        for k, (x, y) in pts.items():
            p = Point(x, y)
            idx = [i for i, pc in enumerate(pieces) if pc.buffer(1e-9).contains(p)]
            dr = min(p.distance(wlines[w][1]) for w in rid) * 111000
            bank[k] = idx
            print(f"  {k:45s} piece {idx}  (~{dr:.0f} m from river line)")
    for label, n in (("Chooralmala", cho["node_id"]), ("Mundakai", mun["node_id"])):
        print(f"Paper coordinate -> {label} snap node {n}: {hv(PAPER_PT, ll(n)):.0f} m")

    # connectivity with / without the bridge (paths between two enclave nodes stay inside the enclave)
    s, t = cho["node_id"], mun["node_id"]
    res = {}
    for label, E in (("with bridge", H), ("without bridge", nx.restricted_view(H, [], bailey))):
        conn = nx.has_path(E, s, t)
        out = {"connected": conn}
        if conn:
            for wname in ("length_m", "time_min"):
                p = nx.shortest_path(E, s, t, weight=wname)
                out[wname] = {"path": p,
                              "length_m": sum(G[a][c]["length_m"] for a, c in zip(p, p[1:])),
                              "time_min": sum(G[a][c]["time_min"] for a, c in zip(p, p[1:]))}
            out["edge_connectivity"] = nx.edge_connectivity(nx.Graph(E), s, t)
            out["min_edge_cut"] = sorted(tuple(sorted(e)) for e in nx.minimum_edge_cut(nx.Graph(E), s, t))
        res[label] = out
        print(f"\n[{label}] Chooralmala->Mundakai connected: {conn}")
        if conn:
            for wname in ("length_m", "time_min"):
                o = out[wname]
                print(f"  shortest by {wname}: {len(o['path'])-1} edges, {o['length_m']:.0f} m, {o['time_min']:.2f} min")
            print(f"  edge connectivity: {out['edge_connectivity']}; a minimum edge cut: "
                  f"{[(e, G[e[0]][e[1]]['way_id']) for e in out['min_edge_cut']]}")

    # alternate path edges, per edge, with tags
    alt = res["without bridge"]
    if alt["connected"]:
        p = alt["length_m"]["path"]
        erows = []
        for a, c in zip(p, p[1:]):
            d = G[a][c]; t = wtags.get(d["way_id"], {})
            seg = LineString([(G.nodes[a]["lon"], G.nodes[a]["lat"]), (G.nodes[c]["lon"], G.nodes[c]["lat"])])
            crosses = [(wid, tt.get("waterway"), tt.get("name")) for wid, (tt, line) in wlines.items() if seg.intersects(line)]
            erows.append({"u": a, "v": c, "u_lat": G.nodes[a]["lat"], "u_lon": G.nodes[a]["lon"], "way_id": d["way_id"],
                          "length_m": round(d["length_m"], 1), "time_min": round(d["time_min"], 3),
                          **{k: t.get(k, "") for k in TAGS},
                          "crosses_waterway": ";".join(f"{w}:{ty}:{nm or ''}" for w, ty, nm in crosses)})
        with open(f"{OUT}/a_alternate_path_edges.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(erows[0])); w.writeheader(); w.writerows(erows)
        print(f"\nAlternate path (shortest by length, bridge removed): {len(erows)} edges; per-way runs:")
        run = []
        for r in erows:
            if run and run[-1]["way_id"] == r["way_id"]:
                run[-1]["n"] += 1; run[-1]["len"] += r["length_m"]; run[-1]["cross"] |= {r["crosses_waterway"]} - {""}
            else:
                run.append({"way_id": r["way_id"], "n": 1, "len": r["length_m"], "cross": {r["crosses_waterway"]} - {""},
                            "tags": {k: r[k] for k in TAGS if r[k]}, "start": (r["u_lat"], r["u_lon"])})
        for x in run:
            print(f"  way {x['way_id']}: {x['n']} edges, {x['len']:.0f} m, start {x['start']}, {x['tags']}"
                  + (f"  CROSSES {sorted(x['cross'])}" if x["cross"] else ""))
        alt_ways = sorted({r["way_id"] for r in erows})
    else:
        alt_ways = []
    json.dump({"enclave_nodes": len(enclave), "bailey_edges": bailey, "bank_pieces": bank,
               "results": {k: {kk: (vv if kk not in ("length_m", "time_min") else {"length_m": vv["length_m"], "time_min": vv["time_min"], "n_edges": len(vv["path"]) - 1})
                               for kk, vv in v.items()} for k, v in res.items()},
               "alternate_path_ways": alt_ways},
              open(f"{OUT}/a_summary.json", "w"), indent=1, default=str)

if __name__ == "__main__":
    main()
