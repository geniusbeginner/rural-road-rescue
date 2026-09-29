"""Convert our 10 km buffered graph, villages and facilities into RA2CE 1.2.2 inputs.
Run with the isolated RA2CE venv (C:/Users/avant/.venvs/ra2ce). Reads data/ only; writes research/ra2ce/work/.

Conversion choices (documented in research/ra2ce_crosscheck.md):
- network: one LineString per junction-to-junction chain of our graph (nodes of degree != 2 are chain ends), so RA2CE
  rebuilds the same topology from line endpoints (cut_at_intersections / merge_lines / snapping are disabled in the run).
- attributes kept: highway, way ids, our length in metres. NOT kept: our speed table (RA2CE computes its own; we weigh by
  length) and the OSM `bridge` tag (RA2CE never disrupts edges tagged bridge=yes, see origin_closest_destination.py).
- origins = our 142 villages, destinations = our 34 facilities, both placed on their snapped graph-node positions;
  origin_count 'POP' = 1 (population is not attributable per settlement under our rule).
- hazard: a single-cell GeoTIFF over the midpoint of the SH59 edge only (synthetic; value 1.0 m, threshold 0.5).
"""
import json
import pickle
from pathlib import Path
import geopandas as gpd
import networkx as nx
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point

W = Path("research/ra2ce/work")
SH59 = (3249489501, 5870049103)
BAILEY = (3842230570, 3842230578)
CELL = 0.0001  # degrees (~11 m) - one cell only


def chains(G):
    """Split the graph into maximal paths whose interior nodes have degree 2."""
    ends = {n for n in G if G.degree(n) != 2}
    seen, out = set(), []
    for s in ends:
        for nb in G.neighbors(s):
            if frozenset((s, nb)) in seen:
                continue
            path = [s, nb]
            seen.add(frozenset((s, nb)))
            while path[-1] not in ends:
                nxt = [x for x in G.neighbors(path[-1]) if x != path[-2]]
                if not nxt or frozenset((path[-1], nxt[0])) in seen:
                    break
                seen.add(frozenset((path[-1], nxt[0])))
                path.append(nxt[0])
            out.append(path)
    # pure cycles with no end node
    for u, v in G.edges():
        if frozenset((u, v)) not in seen:
            cyc = nx.find_cycle(G, u)
            path = [cyc[0][0]] + [e[1] for e in cyc]
            for a, b in zip(path, path[1:]):
                seen.add(frozenset((a, b)))
            out.append(path)
    return out


def hazard_cell(G, edge, name):
    a, b = edge
    lat = (G.nodes[a]["lat"] + G.nodes[b]["lat"]) / 2
    lon = (G.nodes[a]["lon"] + G.nodes[b]["lon"]) / 2
    path = W / f"hazard_{name}.tif"
    with rasterio.open(path, "w", driver="GTiff", height=1, width=1, count=1, dtype="float32", crs="EPSG:4326",
                       transform=from_origin(lon - CELL / 2, lat + CELL / 2, CELL, CELL), nodata=-9999) as dst:
        dst.write(np.array([[1.0]], dtype="float32"), 1)
    return {"file": str(path), "center": [lat, lon], "cell_deg": CELL}


def main():
    import sys
    W.mkdir(parents=True, exist_ok=True)
    b = pickle.load(open("data/graph_buf10km.pkl", "rb"))
    G = b["G"]
    suffix = ""
    if "--no-tracks" in sys.argv:  # variant V1 of research/followup_validation.md: drop highway=track edges
        G = G.copy()
        G.remove_edges_from([(u, v) for u, v, d in G.edges(data=True) if d["highway"] == "track"])
        G.remove_nodes_from([n for n in list(G) if G.degree(n) == 0])
        suffix = "_v1"
        print(f"V1: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges after dropping tracks")
    ch = chains(G)
    assert sum(len(p) - 1 for p in ch) == G.number_of_edges(), "chain decomposition must cover every edge once"
    rows = []
    for i, p in enumerate(ch):
        geom = LineString([(G.nodes[n]["lon"], G.nodes[n]["lat"]) for n in p])
        hw = [G[a][c]["highway"] for a, c in zip(p, p[1:])]
        ways = sorted({G[a][c]["way_id"] for a, c in zip(p, p[1:])})
        rows.append({"lid": i, "highway": max(set(hw), key=hw.count), "way_ids": ",".join(map(str, ways)),
                     "our_len_m": round(sum(G[a][c]["length_m"] for a, c in zip(p, p[1:])), 1),
                     "has_sh59": any(frozenset((a, c)) == frozenset(SH59) for a, c in zip(p, p[1:])),
                     "has_bailey": any(frozenset((a, c)) == frozenset(BAILEY) for a, c in zip(p, p[1:])),
                     "geometry": geom})
    net = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    net.to_file(W / f"network{suffix}.shp")
    if suffix:  # origins/destinations/hazards are shared with the V0 run
        print(f"chains {len(ch)}; SH59 chain {net.loc[net.has_sh59, ['lid','our_len_m']].to_dict('records')}; "
              f"Bailey chain {net.loc[net.has_bailey, ['lid','way_ids','our_len_m']].to_dict('records')}")
        return
    pt = lambda n: Point(G.nodes[n]["lon"], G.nodes[n]["lat"])
    o = gpd.GeoDataFrame([{"o_name": v["name"][:60], "POP": 1, "node": str(v["node_id"]), "geometry": pt(v["node_id"])}
                          for v in b["villages"]], crs="EPSG:4326")
    d = gpd.GeoDataFrame([{"d_name": f["name"][:60], "category": "health", "node": str(f["node_id"]), "geometry": pt(f["node_id"])}
                          for f in b["facilities34"]], crs="EPSG:4326")
    o.to_file(W / "origins.shp")
    d.to_file(W / "destinations.shp")
    hz = {"sh59": hazard_cell(G, SH59, "sh59"), "bailey": hazard_cell(G, BAILEY, "bailey")}
    info = {"graph_nodes": G.number_of_nodes(), "graph_edges": G.number_of_edges(), "chains": len(ch),
            "sh59_chain": net.loc[net.has_sh59, ["lid", "highway", "way_ids", "our_len_m"]].to_dict("records"),
            "bailey_chain": net.loc[net.has_bailey, ["lid", "highway", "way_ids", "our_len_m"]].to_dict("records"),
            "origins": len(o), "destinations": len(d), "hazard": hz}
    json.dump(info, open(W.parent / "prepare_inputs.json", "w"), indent=1, default=str)
    print(json.dumps(info, indent=1, default=str))


if __name__ == "__main__":
    main()
