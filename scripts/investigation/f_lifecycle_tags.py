"""Follow-up C: every way in the 2026-09-16 extract carrying a lifecycle tag (wide reporting list; V2 is NOT changed).
Reports counts by highway class, presence in the V0 graph, whether on either Chooralmala-Mundakai alternate path
(2024 or 2026), and whether any of its edges is a single-link cut (graph bridge) in the 2026 V0 graph. Read-only."""
import csv
import json
import pickle
from collections import Counter
import networkx as nx

FAMILIES = ("destroyed", "disused", "abandoned", "razed", "demolished", "removed", "dismantled", "was",
            "construction", "proposed")
V2_FAMILIES = ("destroyed", "disused", "abandoned")

def life(tags, fams):
    return {k: v for k, v in tags.items() if any(k == f or k.startswith(f + ":") for f in fams)}

topo = json.load(open("data/osm/wayanad_roads_topology_buf10km.json", encoding="utf-8"))
ways = [e for e in topo["elements"] if e["type"] == "way"]
hits = [(w, life(w.get("tags", {}), FAMILIES)) for w in ways]
hits = [(w, l) for w, l in hits if l]
damage = [w for w in ways if any(k.startswith("damage:") for k in w.get("tags", {}))]
print(f"ways in 2026 extract: {len(ways)}; with a lifecycle key (wide list {FAMILIES}): {len(hits)}")
print(f"  of which in V2's list {V2_FAMILIES}: {sum(1 for w, l in hits if life(w['tags'], V2_FAMILIES))}")
print(f"  lifecycle keys: {dict(Counter(k for _, l in hits for k in l))}")
print(f"  by highway class: {dict(Counter(w['tags'].get('highway') for w, _ in hits))}")
print(f"damage:* tagged ways (reported separately): {len(damage)} -> {[w['id'] for w in damage]}")

G = pickle.load(open("data/graph_buf10km.pkl", "rb"))["G"]
in_graph = {}
for u, v, d in G.edges(data=True):
    in_graph.setdefault(d["way_id"], []).append((u, v))
bridges = {frozenset(e) for e in nx.bridges(G)}
alt = {}
for label, f in (("2026 alternate", "research/investigation/c3_alternate_path_now.csv"),
                 ("2024 alternate", "research/investigation/c3_alternate_path_pre.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8")):
        alt.setdefault(int(r["way_id"]), set()).add(label)
rows = []
for w, l in hits:
    es = in_graph.get(w["id"], [])
    nb = sum(1 for e in es if frozenset(e) in bridges)
    row = {"way_id": w["id"], "highway": w["tags"].get("highway"), "bridge": w["tags"].get("bridge", ""),
           "lifecycle_tags": l, "in_V2_list": bool(life(w["tags"], V2_FAMILIES)), "in_V0_graph": bool(es),
           "edges_in_graph": len(es), "edges_that_are_single_link_cuts_2026_V0": nb,
           "on_alternate_path": sorted(alt.get(w["id"], []))}
    rows.append(row)
    print(f"  way {row['way_id']}: highway={row['highway']} bridge={row['bridge'] or '-'} {l} | in V0 graph {row['in_V0_graph']} "
          f"({len(es)} edges, {nb} of them graph bridges) | on alternate path: {row['on_alternate_path'] or 'no'}")
json.dump({"families_reported": FAMILIES, "v2_families": V2_FAMILIES, "ways": rows,
           "damage_tagged": [w["id"] for w in damage]}, open("research/investigation/f_lifecycle_tags.json", "w"), indent=1)
