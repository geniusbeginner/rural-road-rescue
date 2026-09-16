import json
import pickle
import time
import networkx as nx

def nearest_facility(G, village_node, facility_nodes, facility_names, cutoff=180):
    try:
        lengths = nx.single_source_dijkstra_path_length(G, village_node, cutoff=cutoff, weight="time_min")
    except Exception:
        lengths = {}
    best_time, best_fac = None, None
    for fnode, fname in zip(facility_nodes, facility_names):
        t = lengths.get(fnode)
        if t is not None and (best_time is None or t < best_time):
            best_time, best_fac = t, fname
    return best_time, best_fac

def main():
    with open("data/graph_weighted.pkl", "rb") as f:
        blob = pickle.load(f)
    G, nodes = blob["G"], blob["nodes"]

    cp2 = json.load(open("data/checkpoint2_results.json", encoding="utf-8"))
    villages = cp2["villages"]
    facilities = cp2["facilities"]
    facility_nodes = [f["node_id"] for f in facilities]
    facility_names = [f["name"] for f in facilities]

    TARGET_EDGE = (3249489501, 5870049103)
    affected_names = {"Kalladi", "Chooralmala", "Mundakai"}
    target_villages = [v for v in villages if v["name"] in affected_names]
    print(f"Target villages: {[v['name'] for v in target_villages]}")

    edge_attrs = dict(G.get_edge_data(*TARGET_EDGE))
    print(f"Edge to remove: {TARGET_EDGE}, attrs: highway={edge_attrs['highway']}, len={edge_attrs['length_m']:.0f}m")

    print("\n=== BEFORE removal ===")
    before = {}
    for v in target_villages:
        t, fac = nearest_facility(G, v["node_id"], facility_nodes, facility_names)
        before[v["name"]] = {"time_min": t, "facility": fac}
        print(f"  {v['name']:15s} -> {fac} in {t:.1f} min" if t is not None else f"  {v['name']:15s} -> UNREACHABLE")

    G2 = G.copy()
    G2.remove_edge(*TARGET_EDGE)

    print("\n=== AFTER removal ===")
    after = {}
    for v in target_villages:
        t, fac = nearest_facility(G2, v["node_id"], facility_nodes, facility_names)
        after[v["name"]] = {"time_min": t, "facility": fac}
        print(f"  {v['name']:15s} -> {fac} in {t:.1f} min" if t is not None else f"  {v['name']:15s} -> UNREACHABLE (no path within 180min cutoff)")

    # Double check with no cutoff at all -- is it topologically fully disconnected, or just far?
    print("\n=== Verifying: is it topologically disconnected, or just >180min away? ===")
    for v in target_villages:
        reachable_any_facility = False
        comp = nx.node_connected_component(G2, v["node_id"])
        for fnode in facility_nodes:
            if fnode in comp:
                reachable_any_facility = True
                break
        print(f"  {v['name']:15s} in same connected component as ANY facility (unweighted)? {reachable_any_facility}  "
              f"(component size: {len(comp)})")

    result = {
        "target_edge": list(TARGET_EDGE), "edge_attrs": {k: v for k, v in edge_attrs.items()},
        "before": before, "after": after,
    }
    json.dump(result, open("data/dramatic_case_result.json", "w", encoding="utf-8"), indent=2, default=str)

if __name__ == "__main__":
    main()
