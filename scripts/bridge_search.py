import json
import pickle
import time
import networkx as nx

def main():
    print("Loading pickled weighted graph...")
    with open("data/graph_weighted.pkl", "rb") as f:
        blob = pickle.load(f)
    G, nodes = blob["G"], blob["nodes"]

    cp2 = json.load(open("data/checkpoint2_results.json", encoding="utf-8"))
    villages = cp2["villages"]
    facilities = cp2["facilities"]
    facility_nodes = set(f["node_id"] for f in facilities)
    facility_name_by_node = {f["node_id"]: f["name"] for f in facilities}
    village_by_node = {v["node_id"]: v["name"] for v in villages}

    t0 = time.time()
    bridges = list(nx.bridges(G))
    print(f"Total bridges (exact, not sampled) in network: {len(bridges)}  ({time.time()-t0:.1f}s)")

    track_bridges = [(u, v) for u, v in bridges if G[u][v]["highway"] == "track"]
    print(f"Bridges that are 'track'-class (zero-redundancy rough roads): {len(track_bridges)}")

    # For each track bridge, find the smaller-side component after removal, check if it contains a village
    candidates = []
    for u, v in track_bridges:
        edge_attrs = dict(G.get_edge_data(u, v))
        G.remove_edge(u, v)
        comp_u = nx.node_connected_component(G, u)
        G.add_edge(u, v, **edge_attrs)  # restore exactly as it was
        villages_in_comp = [nid for nid in comp_u if nid in village_by_node]
        if villages_in_comp:
            candidates.append({"edge": (u, v), "isolated_size": len(comp_u), "villages": villages_in_comp})

    print(f"Track bridges whose removal isolates >=1 village into the smaller component: {len(candidates)}")
    candidates.sort(key=lambda c: c["isolated_size"])
    for c in candidates[:15]:
        names = [village_by_node[n] for n in c["villages"]]
        print(f"  edge={c['edge']}  isolated_component_size={c['isolated_size']}  villages={names}")

    json.dump(
        [{"edge": list(c["edge"]), "isolated_size": c["isolated_size"],
          "villages": [village_by_node[n] for n in c["villages"]]} for c in candidates],
        open("data/track_bridge_candidates.json", "w", encoding="utf-8"), indent=2)

if __name__ == "__main__":
    main()
