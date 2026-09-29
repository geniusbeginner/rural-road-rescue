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
            "case_subtitle": "Vellarimala Network Vulnerability",
            "summary": ("Topology-only analysis identifies this stretch of road (SH59, Kalpetta–Meppadi) as the sole route "
                        "connecting Kalladi, Chooralmala and Mundakai (Vellarimala revenue village, population 7,548) to any "
                        "health facility. Cut it, and all three become unreachable from every health facility in our curated "
                        "dataset (34 facilities at PHC, CHC, Taluk and District Hospital level). This finding holds across "
                        "three different definitions of what counts as a road, and in both a 2024 and a 2026 snapshot of the network."),
            "events_context": ("The area this corridor serves has been cut off by real landslides twice. On 30 July 2024, "
                               "landslides at Mundakkai and Chooralmala killed more than 200 people and washed away the bridge "
                               "between Chooralmala and Mundakkai, isolating Mundakkai (GSI; Scientific Reports, 2025; DD News). "
                               "On 7 July 2026, a landslide near the Meenakshi Bridge at Kalladi — inside this corridor — "
                               "disrupted traffic on the Meppadi–Chooralmala road (ANI, citing the district administration; "
                               "ETV Bharat, citing KSDMA)."),
            "scope_note": ("We do not claim to have identified the exact bridge that failed in 2024; that bridge lies further up "
                           "the valley, beyond this corridor. What the analysis identifies is that this corridor is the area's "
                           "single point of failure for health access, which is consistent with both events."),
            "validation_events": [
                {"date": "30 Jul 2024", "text": "Landslides wash away the Chooralmala–Mundakkai bridge; Mundakkai cut off."},
                {"date": "7 Jul 2026", "text": "Landslide at Kalladi, inside this corridor, disrupts the Meppadi–Chooralmala road."},
            ],
            "sources": [
                {"label": "GSI First Information Report, Mundakkai–Chooralmala (30.07.2024)",
                 "url": "https://bhusanket.gsi.gov.in/Public_Portal_News_pdf/FIR_Mundakkai-Chooralmala.cleaned.pdf"},
                {"label": "Ramesh et al., Scientific Reports 15 (2025), doi:10.1038/s41598-025-07828-3",
                 "url": "https://www.nature.com/articles/s41598-025-07828-3"},
                {"label": "DD News, 1 Aug 2024 (archived copy)",
                 "url": "http://web.archive.org/web/20260421013527/https://ddnews.gov.in/en/wayanad-tragedy-army-erecting-temporary-bailey-bridge-in-chooralmala-toll-risen-to-167/"},
                {"label": "ANI, 7 Jul 2026",
                 "url": "https://aninews.in/news/national/general-news/keralam-three-killed-seven-missing-after-landslide-at-kalladi-tunnel-construction20260707175128/"},
                {"label": "ETV Bharat, 7 Jul 2026",
                 "url": "https://www.etvbharat.com/en/state/landslide-hits-wayanad-tunnel-project-site-in-kerala-several-trapped-rescue-operation-underway-enn26070702157"},
            ],
            "bridge_point": [round(bridge_lon, 6), round(bridge_lat, 6)],
            "ways": cho_ways,
            "villages": cho_villages,
            "population": 7548,
            "population_source": "Census of India 2011, District Census Handbook Part XII-B, Wayanad (Vellarimala, location code 627340)",
            "revenue_village": "Vellarimala",
            "before_time_range": [11.7, 21.1],
            "isolated_component_size": len(isolated_nodes),
        },
        "false_positive_case": {
            "id": "thaloor",
            "label": "Thaloor",
            "verdict": "artifact_rejected",
            "summary": "In the bridge-tree screening, this edge showed the same headline signal as Chooralmala: isolated_facilities = 0, meaning it appeared to cut its village off from every health facility. It didn't survive the follow-up check. Kept in the demo specifically to show the check that catches this class of false positive.",
            "rejection_reason": ("Confirmed as a data artifact by re-extracting the road network with a 10 km buffer past the "
                                 "district boundary (and re-checked at 5 km). In the buffered network, this settlement's road "
                                 "connects to the wider network: 286 of the 306 road nodes in the apparently isolated section lie "
                                 "outside the district, and 64 health facilities become reachable — all 34 curated Wayanad "
                                 "facilities plus 30 outside Wayanad. The apparent isolation was caused by clipping the road data "
                                 "at the administrative boundary, not a real road failure."),
            "bridge_point": [round(th_lon, 6), round(th_lat, 6)],
            "ways": th_ways,
            "village": th_village,
            "boundary_nearby": [[round(p[0], 6), round(p[1], 6)] for p in nearby_boundary],
            "distance_to_boundary_m": 0,
            "distance_source": "buffered-network validation (10 km buffered re-extraction)",
            "isolated_component_size": len(th_isolated),
            "revenue_village": "Nenmeni",
            "population": None,
            "population_note": "Population not attributable (partial revenue village: Thaloor is one of four OSM settlements in Nenmeni).",
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
