"""B. OSM edit history for the Bailey Bridge, the alternate-path ways, and bridge-tagged ways in the
Level 1-3 corridors and the Level-2 enclave. Also node histories at alternate-path junctions and crossings.
Read-only on data/; writes research/investigation/b_*."""
import csv
import json
import pickle
import time
import requests
import networkx as nx

OUT = "research/investigation"
EVENT = "2024-07-29T00:00:00Z"
UA = {"User-Agent": "rural-road-research/0.1 (bridge investigation)"}
LEVEL_WAYS = {"L1": [380928374, 380928376, 1426730512, 380928378, 380928389], "L2": [30778557], "L3": [380928408]}
LEVEL2_CUT = (3249489400, 3842231008)

def history(kind, i):
    for a in range(4):
        r = requests.get(f"https://api.openstreetmap.org/api/0.6/{kind}/{i}/history.json", headers=UA, timeout=60)
        if r.status_code == 200:
            return r.json()["elements"]
        time.sleep(3 * (a + 1))
    return [{"error": r.status_code}]

def summarize(kind, i, els):
    if "error" in els[0]:
        return {"kind": kind, "id": i, "error": els[0]["error"]}
    first, last = els[0], els[-1]
    changes = []
    for prev, cur in zip(els, els[1:]):
        what = []
        if kind == "way" and prev.get("nodes") != cur.get("nodes"):
            what.append("nodes")
        if kind == "node" and (prev.get("lat"), prev.get("lon")) != (cur.get("lat"), cur.get("lon")):
            what.append("position")
        if prev.get("tags") != cur.get("tags"):
            what.append("tags")
        if not cur.get("visible", True):
            what.append("deleted")
        changes.append((cur["version"], cur["timestamp"], ",".join(what) or "none"))
    return {"kind": kind, "id": i, "created": first["timestamp"], "created_tags": first.get("tags", {}),
            "n_versions": len(els), "latest_version": last["version"], "latest_timestamp": last["timestamp"],
            "latest_tags": last.get("tags", {}), "changes": changes,
            "created_after_event": first["timestamp"] > EVENT,
            "changed_after_event": [c for c in changes if c[1] > EVENT]}

def main():
    a = json.load(open(f"{OUT}/a_summary.json"))
    alt_ways = a["alternate_path_ways"]
    b = pickle.load(open("data/graph_buf10km.pkl", "rb"))
    G = b["G"]
    topo = json.load(open("data/osm/wayanad_roads_topology_buf10km.json", encoding="utf-8"))
    wtags = {e["id"]: e.get("tags", {}) for e in topo["elements"] if e["type"] == "way"}

    G2 = G.copy(); G2.remove_edge(*LEVEL2_CUT)
    enclave = min((nx.node_connected_component(G2, n) for n in LEVEL2_CUT), key=len)
    enclave_bridges = sorted({d["way_id"] for u, v, d in G.subgraph(enclave).edges(data=True)
                              if wtags.get(d["way_id"], {}).get("bridge") not in (None, "no")})
    level_bridges = sorted({w for ws in LEVEL_WAYS.values() for w in ws if wtags.get(w, {}).get("bridge") not in (None, "no")})
    print(f"Bridge-tagged ways in Level-2 enclave: {enclave_bridges}")
    print(f"Bridge-tagged ways in Level 1-3 corridor ways: {level_bridges}")

    targets = sorted(set([380928388] + alt_ways + enclave_bridges + level_bridges + [w for ws in LEVEL_WAYS.values() for w in ws]))
    rows = []
    for w in targets:
        s = summarize("way", w, history("way", w))
        role = []
        if w == 380928388: role.append("Bailey Bridge")
        if w in alt_ways: role.append("alternate path")
        if w in enclave_bridges: role.append("enclave bridge")
        for L, ws in LEVEL_WAYS.items():
            if w in ws: role.append(f"{L} corridor")
        s["role"] = "; ".join(role)
        rows.append(s)
        flag = " <<< CREATED AFTER 2024-07-29" if s.get("created_after_event") else (" <<< changed after 2024-07-29" if s.get("changed_after_event") else "")
        print(f"way {w} [{s['role']}] created {s.get('created')} v{s.get('latest_version')} latest {s.get('latest_timestamp')}{flag}")
        print(f"     created tags: {s.get('created_tags')}")
        print(f"     latest  tags: {s.get('latest_tags')}")
        for c in s.get("changes", []):
            print(f"     v{c[0]} {c[1]} changed: {c[2]}" + ("   (after event)" if c[1] > EVENT else ""))

    # node histories: junctions between consecutive alternate-path ways, and ends of crossing edges
    alt_edges = list(csv.DictReader(open(f"{OUT}/a_alternate_path_edges.csv", encoding="utf-8")))
    nodes = set()
    for prev, cur in zip(alt_edges, alt_edges[1:]):
        if prev["way_id"] != cur["way_id"]:
            nodes.add(int(cur["u"]))
    for e in alt_edges:
        if e["crosses_waterway"]:
            nodes |= {int(e["u"]), int(e["v"])}
    nodes |= {3842230570, 3842230578}  # Bailey ends
    nrows = []
    print(f"\nNode histories ({len(nodes)} nodes: alternate-path way junctions, waterway-crossing edge ends, Bailey ends):")
    for n in sorted(nodes):
        s = summarize("node", n, history("node", n)); nrows.append(s)
        flag = " <<< CREATED AFTER 2024-07-29" if s.get("created_after_event") else (" <<< changed after 2024-07-29" if s.get("changed_after_event") else "")
        print(f"  node {n} created {s.get('created')} v{s.get('latest_version')} latest {s.get('latest_timestamp')} "
              f"changes {s.get('changes')}{flag}")
    json.dump({"event_cutoff": EVENT, "ways": rows, "nodes": nrows}, open(f"{OUT}/b_edit_history.json", "w"), indent=1)

if __name__ == "__main__":
    main()
