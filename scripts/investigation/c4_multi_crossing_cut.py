"""C4. On both graphs: remove combinations of the three main-stem crossing edges and test Chooralmala<->Mundakai
connectivity; also the edge connectivity and a minimum edge cut between the two settlement snap nodes. Read-only."""
import itertools
import json
import pickle
import networkx as nx

CROSS = {"380928388 (failed bridge / Bailey)": (3842230570, 3842230578),
         "794270381 (track bridge)": (7428737125, 7428737126),
         "794270379 (residential bridge)": (7428737123, 7428737124)}
out = {}
for key, pkl in (("PRE 2024-07-29", "research/investigation/raw/graph_pre_event.pkl"), ("NOW 2026-09-16", "data/graph_buf10km.pkl")):
    b = pickle.load(open(pkl, "rb")); G = b["G"]
    vil = {v["name"]: v for v in b["villages"]}
    s, t = vil["Chooralmala"]["node_id"], vil["Mundakai"]["node_id"]
    print(f"\n=== {key} ===  all crossing edges present: {[G.has_edge(*e) for e in CROSS.values()]}")
    rows = []
    for k in range(0, 4):
        for combo in itertools.combinations(CROSS, k):
            H = nx.restricted_view(G, [], [CROSS[c] for c in combo])
            ok = nx.has_path(H, s, t)
            extra = ""
            if ok:
                p = nx.shortest_path(H, s, t, weight="length_m")
                extra = f"{sum(G[a][c]['length_m'] for a, c in zip(p, p[1:])):.0f} m"
            print(f"  removed {list(combo) or 'none'}: connected={ok} {extra}")
            rows.append({"removed": list(combo), "connected": ok, "path": extra})
    # 2-edge-connected component check around the two nodes (local subgraph = component after removing Level-2 cut)
    G2 = G.copy(); G2.remove_edge(3249489400, 3842231008)
    enc = min((nx.node_connected_component(G2, n) for n in (3249489400, 3842231008)), key=len)
    Hs = nx.Graph(G.subgraph(enc))
    ec = nx.edge_connectivity(Hs, s, t)
    cut = nx.minimum_edge_cut(Hs, s, t)
    print(f"  edge connectivity Chooralmala-Mundakai: {ec}; a minimum edge cut: {[(e, G.edges[e]['way_id']) for e in cut]}")
    out[key] = {"combos": rows, "edge_connectivity": ec, "min_cut": [[*e, G.edges[e]["way_id"]] for e in cut]}
json.dump(out, open("research/investigation/c4_multi_crossing_cut.json", "w"), indent=1)
