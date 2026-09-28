"""Count ways in the 2026-09-16 extract carrying destroyed/damage/lifecycle tags while still tagged highway=*.
Read-only on data/."""
import json
import pickle
from collections import Counter

topo = json.load(open("data/osm/wayanad_roads_topology_buf10km.json", encoding="utf-8"))
ways = [e for e in topo["elements"] if e["type"] == "way"]
KEYS = ("destroyed", "destroyed:highway", "damage:event", "damage:type", "disused", "abandoned", "abandoned:highway",
        "disused:highway", "was:highway", "razed", "demolished")
hit = [w for w in ways if any(k in w.get("tags", {}) for k in KEYS)]
print(f"ways in extract: {len(ways)}; with destroyed/damage/lifecycle keys: {len(hit)}")
print("key counts:", dict(Counter(k for w in hit for k in w["tags"] if k in KEYS)))
print("damage:event values:", dict(Counter(w["tags"].get("damage:event") for w in hit)))
b = pickle.load(open("data/graph_buf10km.pkl", "rb"))
G = b["G"]
in_graph = {d["way_id"] for _, _, d in G.edges(data=True)}
for w in hit:
    t = w["tags"]
    print(f"  way {w['id']} in_graph={w['id'] in in_graph} highway={t.get('highway')} bridge={t.get('bridge','-')} "
          f"{ {k: t[k] for k in t if k in KEYS} }")
