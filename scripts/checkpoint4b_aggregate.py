import json
import time
from collections import defaultdict, Counter
import networkx as nx

from checkpoint3_4 import build_weighted_graph

def main():
    G, nodes = build_weighted_graph("data/osm/wayanad_roads_topology.json")

    t0 = time.time()
    K = 300
    bc = nx.edge_betweenness_centrality(G, k=K, weight="time_min", seed=42)
    print(f"Edge betweenness computed (k={K}) in {time.time()-t0:.1f}s")

    # Aggregate to way level: a "candidate segment" = one OSM way (a real, mappable road),
    # not a raw graph edge (OSM ways get split into many edges at every intersection node).
    way_scores = defaultdict(lambda: {"max_score": 0.0, "sum_score": 0.0, "edges": 0,
                                       "length_m": 0.0, "highway": None, "node_ids": []})
    for (u, v), score in bc.items():
        d = G[u][v]
        wid = d["way_id"]
        rec = way_scores[wid]
        rec["max_score"] = max(rec["max_score"], score)
        rec["sum_score"] += score
        rec["edges"] += 1
        rec["length_m"] += d["length_m"]
        rec["highway"] = d["highway"]
        rec["node_ids"].extend([u, v])

    ranked = sorted(way_scores.items(), key=lambda kv: -kv[1]["max_score"])
    top = ranked[:30]

    print(f"\nTop 30 DISTINCT road segments (aggregated by OSM way) by max edge betweenness:")
    results = []
    for rank, (wid, rec) in enumerate(top, 1):
        nid = rec["node_ids"][0]
        lat, lon = nodes[nid]
        maplink = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"
        print(f"  #{rank:2d} way_id={wid:12d} max_score={rec['max_score']:.4f} "
              f"highway={rec['highway']:12s} total_len={rec['length_m']:6.0f}m ({rec['edges']} sub-edges)  {maplink}")
        results.append({
            "rank": rank, "way_id": wid, "max_score": rec["max_score"],
            "highway": rec["highway"], "length_m": rec["length_m"], "n_edges": rec["edges"],
            "sample_lat": lat, "sample_lon": lon,
        })

    highway_mix = Counter(r["highway"] for r in results)
    print(f"\nRoad class mix among top 30 distinct ways: {dict(highway_mix)}")
    json.dump(results, open("data/checkpoint4_top_ways.json", "w", encoding="utf-8"), indent=2)

    # Save full graph + bc for reuse in checkpoint 5 (avoid recomputation)
    import pickle
    with open("data/graph_weighted.pkl", "wb") as f:
        pickle.dump({"G": G, "nodes": nodes, "bc_edges": bc}, f)
    print("\nSaved weighted graph + betweenness to data/graph_weighted.pkl for Checkpoint 5")

if __name__ == "__main__":
    main()
