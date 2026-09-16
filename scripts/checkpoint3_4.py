import json
import sys
import time
from collections import Counter
import networkx as nx

sys.path.insert(0, "scripts")
from build_graph import haversine_m

# Assumed free-flow speeds (km/h) by road class -- rural Kerala context, no official source,
# used only where OSM's own maxspeed tag is absent (98.2% of edges).
SPEED_KMH = {
    "trunk": 50, "trunk_link": 40,
    "primary": 45, "primary_link": 35,
    "secondary": 40, "tertiary": 35,
    "unclassified": 25, "residential": 25,
    "living_street": 15, "service": 15,
    "road": 25,
    "track": 15,  # flagged: usability varies, this is an optimistic floor
}

def build_weighted_graph(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    elements = data["elements"]
    nodes = {}
    ways = []
    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way":
            ways.append(el)

    G = nx.Graph()
    for nid, (lat, lon) in nodes.items():
        G.add_node(nid, lat=lat, lon=lon)

    speed_source_counts = Counter()
    for w in ways:
        tags = w.get("tags", {})
        highway = tags.get("highway", "unknown")
        maxspeed_tag = tags.get("maxspeed")
        speed_kmh = None
        source = "assumed"
        if maxspeed_tag:
            digits = "".join(c for c in maxspeed_tag if c.isdigit())
            if digits:
                speed_kmh = float(digits)
                source = "osm_maxspeed_tag"
        if speed_kmh is None:
            speed_kmh = SPEED_KMH.get(highway, 20)
            source = "assumed"
        speed_source_counts[source] += 1

        nds = w.get("nodes", [])
        for a, b in zip(nds[:-1], nds[1:]):
            if a not in nodes or b not in nodes or G.has_edge(a, b):
                continue
            lat1, lon1 = nodes[a]
            lat2, lon2 = nodes[b]
            dist_m = haversine_m(lat1, lon1, lat2, lon2)
            time_min = (dist_m / 1000) / speed_kmh * 60
            G.add_edge(a, b, length_m=dist_m, highway=highway, speed_kmh=speed_kmh,
                       speed_source=source, time_min=time_min, way_id=w["id"])

    print(f"Weighted graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Speed assignment source (by way): {dict(speed_source_counts)}")
    return G, nodes

def main():
    print("=== Checkpoint 3: edge weighting ===")
    G, nodes = build_weighted_graph("data/osm/wayanad_roads_topology.json")

    edge_speeds = [d["speed_kmh"] for _, _, d in G.edges(data=True)]
    print(f"Speed range assigned: {min(edge_speeds):.0f}-{max(edge_speeds):.0f} km/h, "
          f"mean {sum(edge_speeds)/len(edge_speeds):.1f} km/h")
    total_km = sum(d["length_m"] for _, _, d in G.edges(data=True)) / 1000
    print(f"Total network length: {total_km:.1f} km")

    print("\n=== Checkpoint 4: betweenness screening ===")
    t0 = time.time()
    K = 300
    bc = nx.edge_betweenness_centrality(G, k=K, weight="time_min", seed=42)
    print(f"Approximate edge betweenness centrality computed (k={K} sampled sources) in {time.time()-t0:.1f}s")

    ranked = sorted(bc.items(), key=lambda kv: -kv[1])
    top = ranked[:30]

    print(f"\nTop 30 candidate segments by betweenness centrality:")
    results = []
    for rank, ((u, v), score) in enumerate(top, 1):
        d = G[u][v]
        lat1, lon1 = nodes[u]
        lat2, lon2 = nodes[v]
        mid_lat, mid_lon = (lat1 + lat2) / 2, (lon1 + lon2) / 2
        maplink = f"https://www.openstreetmap.org/?mlat={mid_lat}&mlon={mid_lon}#map=17/{mid_lat}/{mid_lon}"
        print(f"  #{rank:2d} score={score:.4f}  highway={d['highway']:12s} len={d['length_m']:5.0f}m  "
              f"way_id={d['way_id']}  {maplink}")
        results.append({
            "rank": rank, "score": score, "u": u, "v": v, "highway": d["highway"],
            "length_m": d["length_m"], "way_id": d["way_id"],
            "mid_lat": mid_lat, "mid_lon": mid_lon,
        })

    highway_mix = Counter(r["highway"] for r in results)
    print(f"\nRoad class mix among top 30: {dict(highway_mix)}")

    json.dump(results, open("data/checkpoint4_top_candidates.json", "w", encoding="utf-8"), indent=2)
    return G, nodes, results

if __name__ == "__main__":
    main()
