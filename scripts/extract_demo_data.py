import json
import math
import pickle
import networkx as nx

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def local_ways(topo, center_lat, center_lon, radius_km, isolated_node_set=None):
    node_coords = {}
    for el in topo["elements"]:
        if el["type"] == "node":
            node_coords[el["id"]] = (el["lat"], el["lon"])

    ways_out = []
    for el in topo["elements"]:
        if el["type"] != "way":
            continue
        nds = el.get("nodes", [])
        coords = [node_coords[n] for n in nds if n in node_coords]
        if not coords:
            continue
        if not any(haversine_km(center_lat, center_lon, lat, lon) <= radius_km for lat, lon in coords):
            continue
        is_cluster = False
        if isolated_node_set is not None:
            in_cluster = sum(1 for n in nds if n in isolated_node_set)
            is_cluster = in_cluster >= max(1, len(nds) // 2)
        ways_out.append({
            "coords": [[round(lon, 6), round(lat, 6)] for lat, lon in coords],
            "highway": el.get("tags", {}).get("highway", "unknown"),
            "cluster": is_cluster,
        })
    return ways_out

def main():
    print("Loading topology + graph...")
    with open("data/osm/wayanad_roads_topology.json", encoding="utf-8") as f:
        topo = json.load(f)
    with open("data/graph_weighted.pkl", "rb") as f:
        blob = pickle.load(f)
    G, nodes = blob["G"], blob["nodes"]

    cp2 = json.load(open("data/checkpoint2_results.json", encoding="utf-8"))
    villages = {v["name"]: v for v in cp2["villages"]}
    facilities = cp2["facilities"]

    # --- Chooralmala / Kalladi / Mundakai ---
    BRIDGE_EDGE = (3249489501, 5870049103)
    G2 = G.copy()
    G2.remove_edge(*BRIDGE_EDGE)
    comp_a = nx.node_connected_component(G2, BRIDGE_EDGE[0])
    comp_b = nx.node_connected_component(G2, BRIDGE_EDGE[1])
    isolated_nodes = comp_a if len(comp_a) < len(comp_b) else comp_b
    bridge_lat, bridge_lon = nodes[BRIDGE_EDGE[0] if len(comp_a) < len(comp_b) else BRIDGE_EDGE[1]]
    print(f"Chooralmala isolated component: {len(isolated_nodes)} nodes (other side was {max(len(comp_a), len(comp_b))})")

    cho_ways = local_ways(topo, bridge_lat, bridge_lon, radius_km=6, isolated_node_set=isolated_nodes)
    print(f"Chooralmala local context ways (<=6km): {len(cho_ways)}  "
          f"(cluster={sum(1 for w in cho_ways if w['cluster'])})")

    dramatic = json.load(open("data/dramatic_case_result.json", encoding="utf-8"))
    cho_villages = [
        {
            "name": villages[n]["name"],
            "lat": villages[n]["lat"],
            "lon": villages[n]["lon"],
            "before_time_min": round(dramatic["before"][n]["time_min"], 1),
            "before_facility": dramatic["before"][n]["facility"],
            "after_time_min": dramatic["after"][n]["time_min"],
            "after_facility": dramatic["after"][n]["facility"],
        }
        for n in ["Chooralmala", "Kalladi", "Mundakai"]
    ]

    # --- Thaloor ---
    THALOOR_EDGE = (411458544, 12498671848)
    G3 = G.copy()
    G3.remove_edge(*THALOOR_EDGE)
    comp_a = nx.node_connected_component(G3, THALOOR_EDGE[0])
    comp_b = nx.node_connected_component(G3, THALOOR_EDGE[1])
    th_isolated = comp_a if len(comp_a) < len(comp_b) else comp_b
    th_lat, th_lon = nodes[THALOOR_EDGE[0] if len(comp_a) < len(comp_b) else THALOOR_EDGE[1]]
    print(f"Thaloor isolated component: {len(th_isolated)} nodes (chose smaller side; other side was {max(len(comp_a), len(comp_b))})")

    th_ways = local_ways(topo, th_lat, th_lon, radius_km=4, isolated_node_set=th_isolated)
    print(f"Thaloor local context ways (<=4km): {len(th_ways)}  (cluster={sum(1 for w in th_ways if w['cluster'])})")

    th_village = {"name": villages["Thaloor"]["name"], "lat": villages["Thaloor"]["lat"], "lon": villages["Thaloor"]["lon"]}

    # boundary segment near Thaloor
    boundary = json.load(open("data/osm/wayanad_boundary.geojson", encoding="utf-8"))
    ring = boundary["coordinates"][0] if boundary["type"] == "Polygon" else boundary["coordinates"][0][0]
    nearby_boundary = [pt for pt in ring if haversine_km(th_lat, th_lon, pt[1], pt[0]) <= 5]
    print(f"Boundary points near Thaloor (<=5km): {len(nearby_boundary)}")

    # full district boundary, lightly simplified (every 3rd point) for main-map orientation
    boundary_full = ring[::3]

    output = {
        "primary_finding": {
            "id": "chooralmala",
            "label": "Chooralmala / Kalladi / Mundakai",
            "verdict": "confirmed_disconnection",
            "summary": "Removing this edge severs Chooralmala, Kalladi, and Mundakai from their nearest health facility entirely -- before/after travel time goes from 11.7-21.1 min to unreachable.",
            "bridge_point": [round(bridge_lon, 6), round(bridge_lat, 6)],
            "ways": cho_ways,
            "villages": cho_villages,
            "population": 7548,
            "revenue_village": "Vellarimala",
            "before_time_range": [11.7, 21.1],
            "isolated_component_size": len(isolated_nodes),
        },
        "false_positive_case": {
            "id": "thaloor",
            "label": "Thaloor",
            "verdict": "artifact_rejected",
            "summary": "In the bridge-tree screening, this edge showed the same headline signal as Chooralmala: isolated_facilities = 0, meaning it appeared to cut its village off from every health facility. It didn't survive the follow-up check. Kept in the demo specifically to show the check that catches this class of false positive.",
            "rejection_reason": "Both this edge and the confirmed Chooralmala edge scored isolated_facilities = 0 in the fast bridge-tree screen -- on that metric alone they looked equally dramatic. But this isolated component's nearest node sits only 113m from the district boundary polygon, consistent with the road continuing outside the clipped OSM extract rather than actually ending. Chooralmala's isolation was confirmed with a full weighted shortest-path before/after test; this one was rejected before that step.",
            "bridge_point": [round(th_lon, 6), round(th_lat, 6)],
            "ways": th_ways,
            "village": th_village,
            "boundary_nearby": [[round(p[0], 6), round(p[1], 6)] for p in nearby_boundary],
            "distance_to_boundary_m": 113,
            "isolated_component_size": len(th_isolated),
            "revenue_village": "Nenmeni",
            "population": 31225,
        },
        "facilities": [
            {"name": f["name"], "lat": f["lat"], "lon": f["lon"]} for f in facilities
        ],
        "boundary_full": [[round(p[0], 6), round(p[1], 6)] for p in boundary_full],
    }

    with open("data/demo_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f)

    import os
    size_kb = os.path.getsize("data/demo_data.json") / 1024
    print(f"\nWrote data/demo_data.json ({size_kb:.0f} KB)")

if __name__ == "__main__":
    main()
