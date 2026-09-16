import json
import pickle
import time
import networkx as nx

def nearest_facility(G, village_node, facility_nodes, facility_names, cutoff=120):
    try:
        lengths = nx.single_source_dijkstra_path_length(G, village_node, cutoff=cutoff, weight="time_min")
    except Exception:
        lengths = {}
    best_time, best_fac = None, None
    for fnode, fname in zip(facility_nodes, facility_names):
        t = lengths.get(fnode)
        if t is not None and (best_time is None or t < best_time):
            best_time, best_fac = t, fname
    return best_time, best_fac  # None, None if nothing reachable within cutoff

def main():
    print("Loading pickled weighted graph...")
    with open("data/graph_weighted.pkl", "rb") as f:
        blob = pickle.load(f)
    G, nodes = blob["G"], blob["nodes"]

    cp2 = json.load(open("data/checkpoint2_results.json", encoding="utf-8"))
    villages = cp2["villages"]
    facilities = cp2["facilities"]
    facility_nodes = [f["node_id"] for f in facilities]
    facility_names = [f["name"] for f in facilities]

    TARGET_WAY_IDS = {1349602615, 387007016, 1349602626}
    target_edges = [(u, v) for u, v, d in G.edges(data=True) if d["way_id"] in TARGET_WAY_IDS]
    total_len = sum(G[u][v]["length_m"] for u, v in target_edges)
    print(f"Target corridor: {len(target_edges)} edges across {len(TARGET_WAY_IDS)} way_ids, {total_len:.0f}m total")

    print("\n=== BEFORE removal ===")
    t0 = time.time()
    before = {}
    for v in villages:
        t, fac = nearest_facility(G, v["node_id"], facility_nodes, facility_names)
        before[v["name"]] = {"time_min": t, "facility": fac}
    print(f"Computed {len(villages)} village->nearest-facility times in {time.time()-t0:.1f}s")
    unreachable_before = sum(1 for r in before.values() if r["time_min"] is None)
    print(f"Villages with no facility reachable within 120min cutoff (before): {unreachable_before}")

    print("\n=== Removing target corridor, recomputing ===")
    G2 = G.copy()
    G2.remove_edges_from(target_edges)
    # drop now-isolated nodes is unnecessary; dijkstra handles it fine

    t0 = time.time()
    after = {}
    for v in villages:
        t, fac = nearest_facility(G2, v["node_id"], facility_nodes, facility_names)
        after[v["name"]] = {"time_min": t, "facility": fac}
    print(f"Computed {len(villages)} village->nearest-facility times in {time.time()-t0:.1f}s (after removal)")

    # --- Compare ---
    affected = []
    for v in villages:
        name = v["name"]
        b, a = before[name], after[name]
        bt, at = b["time_min"], a["time_min"]
        if bt is None and at is None:
            continue
        if bt is None or at is None or abs((at or 1e9) - (bt or 1e9)) > 0.01 or b["facility"] != a["facility"]:
            affected.append({
                "village": name, "before_min": bt, "after_min": at,
                "before_facility": b["facility"], "after_facility": a["facility"],
            })

    print(f"\n=== CHECKPOINT 5 RESULT ===")
    print(f"[PROXY WARNING: 'Population affected' below is a HABITATION/PLACE-COUNT PROXY, "
          f"not real Census population data. Treat as a stand-in, not a real number.]\n")
    print(f"Villages affected: {len(affected)} / {len(villages)}")
    print(f"Population affected (PROXY = count of affected settlement points, NOT Census population): {len(affected)}")

    reachable_before = [a for a in affected if a["before_min"] is not None]
    if reachable_before:
        avg_before = sum(a["before_min"] for a in reachable_before) / len(reachable_before)
        still_reachable_after = [a for a in reachable_before if a["after_min"] is not None]
        if still_reachable_after:
            avg_after = sum(a["after_min"] for a in still_reachable_after) / len(still_reachable_after)
            print(f"Nearest facility travel time (avg over affected, reachable both sides): "
                  f"{avg_before:.1f} min -> {avg_after:.1f} min")

    newly_unreachable_60 = sum(1 for a in affected if (a["before_min"] or 999) <= 60 and (a["after_min"] is None or a["after_min"] > 60))
    total_newly_disconnected = sum(1 for a in affected if a["before_min"] is not None and a["after_min"] is None)
    print(f"Village-facility links that cross the 60-min threshold (reachable<=60min before, not after): {newly_unreachable_60}")
    print(f"Villages fully disconnected from ALL facilities after removal (within 120min cutoff): {total_newly_disconnected}")

    print(f"\nDetail on affected villages:")
    for a in affected:
        b = f"{a['before_min']:.1f}min via {a['before_facility']}" if a["before_min"] is not None else "UNREACHABLE"
        af = f"{a['after_min']:.1f}min via {a['after_facility']}" if a["after_min"] is not None else "UNREACHABLE"
        print(f"  {a['village']:25s} BEFORE: {b:45s} AFTER: {af}")

    json.dump({"before": before, "after": after, "affected": affected},
               open("data/checkpoint5_results.json", "w", encoding="utf-8"), indent=2, default=str)

if __name__ == "__main__":
    main()
