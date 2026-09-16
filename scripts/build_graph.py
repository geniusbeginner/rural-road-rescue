import json
import math
import networkx as nx

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def build_graph(path):
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

    dropped_edges = 0
    for w in ways:
        nds = w.get("nodes", [])
        highway = w.get("tags", {}).get("highway", "unknown")
        for a, b in zip(nds[:-1], nds[1:]):
            if a not in nodes or b not in nodes:
                dropped_edges += 1
                continue
            lat1, lon1 = nodes[a]
            lat2, lon2 = nodes[b]
            dist = haversine_m(lat1, lon1, lat2, lon2)
            if G.has_edge(a, b):
                continue
            G.add_edge(a, b, length_m=dist, highway=highway, way_id=w["id"])

    print(f"Ways: {len(ways)}  Nodes: {len(nodes)}  Dropped edge refs: {dropped_edges}")
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    n_components = nx.number_connected_components(G)
    print(f"Connected components (informational only, not a gate per brief): {n_components}")
    return G, nodes

if __name__ == "__main__":
    G, nodes = build_graph("data/osm/wayanad_roads_topology.json")
