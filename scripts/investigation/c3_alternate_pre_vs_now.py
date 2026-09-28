"""C3. For both graphs (pre-event 2024-07-29, now 2026-09-16): remove the bridge edge at the failed-bridge location,
test Chooralmala<->Mundakai connectivity, list the alternate path, and list EVERY edge crossing the Punnappuzha
main stem (waterways fetched at the matching date). Read-only on data/."""
import csv
import json
import math
import pickle
import time
import requests
import networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import linemerge, unary_union

PAPER = (11.4992, 76.1601)
BRIDGE_EDGE = (3842230570, 3842230578)  # way 380928388 in both graphs
TAGS = ["highway", "bridge", "tunnel", "culvert", "ford", "layer", "access", "surface", "tracktype", "motor_vehicle",
        "name", "destroyed", "destroyed:highway", "damage:event", "import", "source"]
CFG = {"pre": ("2024-07-29T00:00:00Z", "research/investigation/raw/graph_pre_event.pkl",
               "research/investigation/raw/wayanad_roads_topology_buf10km_2024-07-29.json"),
       "now": ("2026-09-16T10:45:02Z", "data/graph_buf10km.pkl", "data/osm/wayanad_roads_topology_buf10km.json")}

def overpass(q):
    for i in range(6):
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=300,
                          headers={"User-Agent": "rural-road-research/0.1 (bridge investigation)"})
        if r.status_code == 200:
            return r.json()
        time.sleep(20 * (i + 1))
    raise SystemExit(f"Overpass failed: HTTP {r.status_code}")

def main_stem(wd):
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in wd["elements"] if e["type"] == "node"}
    ways = {e["id"]: (e.get("tags", {}), e["nodes"]) for e in wd["elements"] if e["type"] == "way"}
    need = [794270374, 794270376, 794270372, 793762963, 1530896408]
    print("   main-stem ways present:", {w: (w in ways) for w in need}, "tags:", {w: ways[w][0] for w in need if w in ways})
    line = lambda ns: LineString([nodes[n] for n in ns if n in nodes])
    j = (set(ways[794270372][1]) & set(ways[794270376][1])).pop()
    i = ways[794270372][1].index(j)
    parts = [ways[794270374][1], ways[794270376][1], ways[794270372][1][i:]] + \
            [ways[w][1] for w in (793762963, 1530896408) if w in ways]  # downstream segments only if mapped at this date
    return linemerge(unary_union([line(p) for p in parts])), {w: (t, line(ns)) for w, (t, ns) in ways.items()}

def main():
    out = {}
    for key, (date, pkl, topo) in CFG.items():
        print(f"\n================ {key.upper()} ({date}) ================")
        b = pickle.load(open(pkl, "rb")); G = b["G"]
        wt = {e["id"]: e.get("tags", {}) for e in json.load(open(topo, encoding="utf-8"))["elements"] if e["type"] == "way"}
        vil = {v["name"]: v for v in b["villages"]}
        s, t = vil["Chooralmala"]["node_id"], vil["Mundakai"]["node_id"]
        print(f"Chooralmala snap node {s}, Mundakai snap node {t}; bridge edge present: {G.has_edge(*BRIDGE_EDGE)} "
              f"(way {G.edges[BRIDGE_EDGE]['way_id'] if G.has_edge(*BRIDGE_EDGE) else '-'})")
        dlat = 0.03; dlon = dlat / math.cos(math.radians(PAPER[0]))
        q = f"""[out:json][timeout:120][date:"{date}"];
(way["waterway"~"^(river|stream|canal|drain|ditch|brook)$"]({PAPER[0]-dlat},{PAPER[1]-dlon},{PAPER[0]+dlat},{PAPER[1]+dlon}););
(._;>;);
out body;"""
        wd = overpass(q)
        json.dump({"query": q, "data": wd}, open(f"research/investigation/c3_waterways_{key}.json", "w"))
        stem, wlines = main_stem(wd)
        # every graph edge crossing the main stem (within ~3 km)
        cross = []
        for u, v, d in G.edges(data=True):
            a, c = (G.nodes[u]["lon"], G.nodes[u]["lat"]), (G.nodes[v]["lon"], G.nodes[v]["lat"])
            if abs(a[1] - PAPER[0]) > dlat or abs(a[0] - PAPER[1]) > dlon:
                continue
            if LineString([a, c]).intersects(stem):
                tg = wt.get(d["way_id"], {})
                cross.append({"u": u, "v": v, "way_id": d["way_id"], "lat": round(a[1], 6), "lon": round(a[0], 6),
                              "length_m": round(d["length_m"], 1), **{k: tg.get(k, "") for k in TAGS}})
        print(f"Edges crossing the Punnappuzha main stem within the {2*dlat:.2f} deg box: {len(cross)}")
        for c in cross:
            print("   " + " ".join(f"{k}={c[k]}" for k in ["way_id", "u", "v", "lat", "lon", "length_m"] + TAGS if c[k] != ""))
        # connectivity with / without the bridge edge
        H = nx.restricted_view(G, [], [BRIDGE_EDGE])
        res = {"crossings": cross}
        for label, E in (("with bridge", G), ("without bridge", H)):
            ok = nx.has_path(E, s, t)
            line = f"[{label}] connected: {ok}"
            if ok:
                p = nx.shortest_path(E, s, t, weight="length_m")
                L = sum(G[a][c]["length_m"] for a, c in zip(p, p[1:])); T = sum(G[a][c]["time_min"] for a, c in zip(p, p[1:]))
                line += f"; shortest {len(p)-1} edges, {L:.0f} m, {T:.2f} min"
                res[label] = {"n_edges": len(p) - 1, "length_m": L, "time_min": T}
                if label == "without bridge":
                    rows = []
                    for a, c in zip(p, p[1:]):
                        d = G[a][c]; tg = wt.get(d["way_id"], {})
                        crosses_stem = LineString([(G.nodes[a]["lon"], G.nodes[a]["lat"]), (G.nodes[c]["lon"], G.nodes[c]["lat"])]).intersects(stem)
                        other = [w for w, (tt, ln) in wlines.items() if w not in (794270374, 794270376, 794270372, 793762963, 1530896408)
                                 and LineString([(G.nodes[a]["lon"], G.nodes[a]["lat"]), (G.nodes[c]["lon"], G.nodes[c]["lat"])]).intersects(ln)]
                        rows.append({"u": a, "v": c, "u_lat": G.nodes[a]["lat"], "u_lon": G.nodes[a]["lon"], "way_id": d["way_id"],
                                     "length_m": round(d["length_m"], 1), "crosses_main_stem": crosses_stem,
                                     "crosses_other_waterway": ";".join(f"{w}:{wlines[w][0].get('waterway')}:{wlines[w][0].get('name','')}" for w in other),
                                     **{k: tg.get(k, "") for k in TAGS}})
                    with open(f"research/investigation/c3_alternate_path_{key}.csv", "w", newline="", encoding="utf-8") as f:
                        wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
                    runs = []
                    for r in rows:
                        if runs and runs[-1]["way_id"] == r["way_id"]:
                            runs[-1]["n"] += 1; runs[-1]["len"] += r["length_m"]
                            runs[-1]["stem"] |= r["crosses_main_stem"]; runs[-1]["other"] |= {r["crosses_other_waterway"]} - {""}
                        else:
                            runs.append({"way_id": r["way_id"], "n": 1, "len": r["length_m"], "stem": r["crosses_main_stem"],
                                         "other": {r["crosses_other_waterway"]} - {""}, "start": (r["u_lat"], r["u_lon"]),
                                         "tags": {k: r[k] for k in TAGS if r[k] != ""}})
                    print(line)
                    for x in runs:
                        print(f"   way {x['way_id']}: {x['n']} edges {x['len']:.0f} m start {x['start']} {x['tags']}"
                              + (" CROSSES MAIN STEM" if x["stem"] else "") + (f" crosses {sorted(x['other'])}" if x["other"] else ""))
                    res["alternate_ways"] = [x["way_id"] for x in runs]
                    continue
            print(line)
        out[key] = res
    json.dump(out, open("research/investigation/c3_alternate_pre_vs_now.json", "w"), indent=1, default=str)

if __name__ == "__main__":
    main()
