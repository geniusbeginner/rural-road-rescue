import json
import pickle
import time
import sys
from collections import defaultdict
import networkx as nx

def main():
    print("Loading pickled weighted graph...")
    with open("data/graph_weighted.pkl", "rb") as f:
        blob = pickle.load(f)
    G, nodes = blob["G"], blob["nodes"]

    cp2 = json.load(open("data/checkpoint2_results.json", encoding="utf-8"))
    villages = cp2["villages"]
    facilities = cp2["facilities"]
    facility_node_set = set(f["node_id"] for f in facilities)
    facility_name_by_node = {f["node_id"]: f["name"] for f in facilities}
    village_by_node = {v["node_id"]: v["name"] for v in villages}

    t0 = time.time()
    bridges = list(nx.bridges(G))
    print(f"Total bridges (exact): {len(bridges)}  ({time.time()-t0:.1f}s)")
    bridge_set = set(bridges) | set((v, u) for u, v in bridges)

    # --- Step 1: 2-edge-connected "blocks" = components after removing all bridges ---
    t0 = time.time()
    G_blocks = G.copy()
    G_blocks.remove_edges_from(bridges)
    block_components = list(nx.connected_components(G_blocks))
    node_to_block = {}
    block_size = {}
    block_facilities = defaultdict(set)
    block_villages = defaultdict(set)
    for bid, comp in enumerate(block_components):
        block_size[bid] = len(comp)
        for n in comp:
            node_to_block[n] = bid
            if n in facility_node_set:
                block_facilities[bid].add(n)
            if n in village_by_node:
                block_villages[bid].add(n)
    print(f"Blocks (2-edge-connected components): {len(block_components)}  ({time.time()-t0:.1f}s)")

    # --- Step 2: build bridge tree (nodes = blocks, edges = bridges) ---
    t0 = time.time()
    T = nx.Graph()
    T.add_nodes_from(block_size.keys())
    for u, v in bridges:
        bu, bv = node_to_block[u], node_to_block[v]
        T.add_edge(bu, bv, orig_edge=(u, v))
    print(f"Bridge tree: {T.number_of_nodes()} nodes, {T.number_of_edges()} edges  ({time.time()-t0:.1f}s)")

    # --- Step 3: single DFS per tree-component computing subtree node/facility/village counts ---
    t0 = time.time()
    results = []
    visited_tree_nodes = set()
    for root in T.nodes():
        if root in visited_tree_nodes:
            continue
        # BFS/DFS to get parent pointers + postorder
        parent = {root: None}
        order = [root]
        stack = [root]
        visited_tree_nodes.add(root)
        while stack:
            node = stack.pop()
            for nb in T.neighbors(node):
                if nb not in parent:
                    parent[nb] = node
                    order.append(nb)
                    visited_tree_nodes.add(nb)
                    stack.append(nb)

        subtree_nodes = {b: block_size[b] for b in order}
        subtree_fac = {b: len(block_facilities[b]) for b in order}
        subtree_vil = {b: set(block_villages[b]) for b in order}

        for b in reversed(order):
            p = parent[b]
            if p is not None:
                subtree_nodes[p] += subtree_nodes[b]
                subtree_fac[p] += subtree_fac[b]
                subtree_vil[p] |= subtree_vil[b]

        total_nodes_in_tree = subtree_nodes[root]
        total_fac_in_tree = subtree_fac[root]
        total_vil_in_tree = subtree_vil[root]

        for b in order:
            p = parent[b]
            if p is None:
                continue
            edge_data = T[b][p]
            u, v = edge_data["orig_edge"]
            highway = G[u][v]["highway"]
            child_side_nodes = subtree_nodes[b]
            child_side_fac = subtree_fac[b]
            child_side_vil = subtree_vil[b]
            other_side_nodes = total_nodes_in_tree - child_side_nodes
            other_side_fac = total_fac_in_tree - child_side_fac
            other_side_vil = total_vil_in_tree - child_side_vil

            # the "isolated" side = whichever side has fewer facilities (the side that loses access)
            if child_side_fac <= other_side_fac:
                isolated_fac, isolated_vil, isolated_nodes = child_side_fac, child_side_vil, child_side_nodes
            else:
                isolated_fac, isolated_vil, isolated_nodes = other_side_fac, other_side_vil, other_side_nodes

            if isolated_vil:  # only care about bridges that actually gate >=1 village
                results.append({
                    "edge": (u, v), "highway": highway,
                    "isolated_facilities": isolated_fac,
                    "isolated_villages": [village_by_node[n] for n in isolated_vil],
                    "isolated_side_size": isolated_nodes,
                })

    print(f"DFS aggregation across all tree components done in {time.time()-t0:.1f}s")
    print(f"Bridges gating >=1 village (either side): {len(results)}")

    zero_fac = [r for r in results if r["isolated_facilities"] == 0]
    print(f"\n*** Bridges where the village-side has ZERO facilities reachable (full disconnection) ***")
    print(f"Count: {len(zero_fac)}")
    for r in zero_fac:
        print(f"  edge={r['edge']} highway={r['highway']:12s} isolated_side_size={r['isolated_side_size']} villages={r['isolated_villages']}")

    track_zero_fac = [r for r in zero_fac if r["highway"] == "track"]
    print(f"\nOf those, track-class specifically: {len(track_zero_fac)}")
    for r in track_zero_fac:
        print(f"  edge={r['edge']} villages={r['isolated_villages']}")

    # low-facility-count near misses (isolated side has exactly 1 facility -- still fragile)
    one_fac = [r for r in results if r["isolated_facilities"] == 1]
    print(f"\nBridges where the village-side has exactly 1 facility (fragile, worth checking travel time): {len(one_fac)}")
    for r in sorted(one_fac, key=lambda x: x["isolated_side_size"])[:15]:
        print(f"  edge={r['edge']} highway={r['highway']:12s} isolated_side_size={r['isolated_side_size']} villages={r['isolated_villages']}")

    json.dump(results, open("data/fast_bridge_results.json", "w", encoding="utf-8"),
               indent=2, default=str)

if __name__ == "__main__":
    main()
