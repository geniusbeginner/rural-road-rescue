"""A5 bank check: which side of the Punnappuzha main stem each point lies on.
Main stem = 794270374 + 794270376 + (794270372 from its junction with 794270376 onward) + 793762963 + 1530896408.
The unnamed tributary (794270375 + western part of 794270372) is tested separately. Read-only on data/."""
import json
import math
import pickle
from shapely.geometry import LineString, Point
from shapely.ops import split, linemerge, unary_union

W = json.load(open("research/investigation/a_waterways_2026-09-16.json"))["data"]
nodes = {e["id"]: (e["lon"], e["lat"]) for e in W["elements"] if e["type"] == "node"}
ways = {e["id"]: e["nodes"] for e in W["elements"] if e["type"] == "way"}
PAPER = (76.1601, 11.4992)
KM = 1 / 111.0  # degrees per km (latitude); used only for the disc radius

def line(ns):
    return LineString([nodes[n] for n in ns if n in nodes])

j = (set(ways[794270372]) & set(ways[794270376])).pop()
i = ways[794270372].index(j)
print(f"794270372 / 794270376 junction node {j} at index {i} of {len(ways[794270372])} "
      f"({nodes[j][1]:.6f}, {nodes[j][0]:.6f})")
stem_parts = [ways[794270374], ways[794270376], ways[794270372][i:], ways[793762963], ways[1530896408]]
stem = linemerge(unary_union([line(p) for p in stem_parts]))
trib = linemerge(unary_union([line(ways[794270375]), line(ways[794270372][: i + 1])]))
print(f"main stem merged geometry: {stem.geom_type}, tributary: {trib.geom_type}")

b = pickle.load(open("data/graph_buf10km.pkl", "rb"))
G = b["G"]
vil = {v["name"]: v for v in b["villages"]}
pt = lambda n: (G.nodes[n]["lon"], G.nodes[n]["lat"])
P = {
    "paper coordinate 11.4992N 76.1601E": PAPER,
    "Chooralmala settlement point": (vil["Chooralmala"]["lon"], vil["Chooralmala"]["lat"]),
    f"Chooralmala snap node {vil['Chooralmala']['node_id']}": pt(vil["Chooralmala"]["node_id"]),
    "Mundakai settlement point": (vil["Mundakai"]["lon"], vil["Mundakai"]["lat"]),
    f"Mundakai snap node {vil['Mundakai']['node_id']}": pt(vil["Mundakai"]["node_id"]),
    "Bailey end node 3842230570": pt(3842230570),
    "Bailey end node 3842230578": pt(3842230578),
    "track bridge 794270381 end 7428737126": pt(7428737126),
    "track bridge 794270381 end 7428737125": pt(7428737125),
}
for name, geom in (("MAIN STEM (Punnappuzha)", stem), ("TRIBUTARY (unnamed 794270375 + W part of 794270372)", trib)):
    disc = Point(PAPER).buffer(2.0 * KM)
    pieces = sorted(split(disc, geom).geoms, key=lambda g: -g.area)
    print(f"\n{name}: 2 km disc split into {len(pieces)} pieces; relative areas "
          f"{[round(p.area / disc.area, 3) for p in pieces]}")
    for k, xy in P.items():
        p = Point(xy)
        idx = [n for n, pc in enumerate(pieces) if pc.buffer(1e-9).contains(p)]
        d = p.distance(geom) * 111000
        print(f"  {k:42s} piece {idx}   ~{d:.0f} m from line")
