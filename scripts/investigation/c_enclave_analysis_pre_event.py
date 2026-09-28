import csv
import json
import pickle
import sys
from collections import defaultdict
import networkx as nx

sys.path.insert(0, "scripts")
from build_graph import haversine_m

BUFFER_EDGE_RULE_M = 500  # labelled parameter (approved), not a finding

def load_json(p):
    return json.load(open(p, encoding="utf-8"))

# ---------------------------------------------------------------- population crosswalk
def load_crosswalk():
    """OSM place node id -> (revenue village, population); revenue village -> all its place node ids."""
    places = {}
    for el in load_json("data/osm/wayanad_places.json")["elements"]:
        if el.get("tags", {}).get("place") in ("village", "town"):
            places[(el["tags"].get("name", "(unnamed)"), el["lat"], el["lon"])] = el["id"]
    rv_of, pop_of, members = {}, {}, defaultdict(set)
    for r in csv.DictReader(open("data/village_crosswalk.csv", encoding="utf-8")):
        pid = int(r["node_id"])
        rv_of[pid] = r["revenue_village"]
        pop_of[r["revenue_village"]] = float(r["population_2011"]) if r["population_2011"] else None
        members[r["revenue_village"]].add(pid)
    return places, rv_of, pop_of, members

def population(place_ids, rv_of, pop_of, members):
    """Count a revenue village only if ALL its settlements are inside; otherwise unattributed."""
    rvs = {rv_of[p] for p in place_ids}
    full = {rv: pop_of[rv] for rv in rvs if members[rv] <= place_ids}
    partial = sorted(rv for rv in rvs if not members[rv] <= place_ids)
    return {"population_attributed": sum(v for v in full.values() if v),
            "revenue_villages_full": {rv: pop_of[rv] for rv in sorted(full)},
            "revenue_villages_partial_unattributed": {rv: {"population_2011": pop_of[rv],
                                                           "settlements_inside": len(members[rv] & place_ids),
                                                           "settlements_total": len(members[rv])}
                                                      for rv in partial}}

# ---------------------------------------------------------------- bridge tree
def bridge_tree_enclaves(G, village_nodes, facility_nodes, geo=True):
    """For every bridge, the side with zero facilities (rooted at a facility block) and its aggregates."""
    bridges = list(nx.bridges(G))
    Gb = G.copy()
    Gb.remove_edges_from(bridges)
    node_to_block, blocks = {}, []
    for bid, comp in enumerate(nx.connected_components(Gb)):
        blocks.append(comp)
        for n in comp:
            node_to_block[n] = bid
    agg = []
    for comp in blocks:
        a = {"n": len(comp), "fac": sum(1 for n in comp if n in facility_nodes),
             "vil": {n for n in comp if n in village_nodes}}
        if geo:
            a["min_d_boundary"] = min(G.nodes[n]["d_boundary_m"] for n in comp)
            a["min_d_bufedge"] = min(G.nodes[n]["d_bufedge_m"] for n in comp)
            a["n_outside"] = sum(1 for n in comp if not G.nodes[n]["inside"])
        agg.append(a)
    T = nx.Graph()
    T.add_nodes_from(range(len(blocks)))
    for u, v in bridges:
        T.add_edge(node_to_block[u], node_to_block[v], orig=(u, v))

    cuts, no_fac_components = [], []
    for tcomp in nx.connected_components(T):
        fac_blocks = [b for b in tcomp if agg[b]["fac"] > 0]
        if not fac_blocks:
            vil = set().union(*(agg[b]["vil"] for b in tcomp))
            if vil:
                no_fac_components.append({"villages": vil, "nodes": sum(agg[b]["n"] for b in tcomp)})
            continue
        root = fac_blocks[0]
        parent, order, stack = {root: None}, [root], [root]
        while stack:
            x = stack.pop()
            for y in T.neighbors(x):
                if y not in parent:
                    parent[y] = x
                    order.append(y)
                    stack.append(y)
        sub = {b: dict(agg[b], vil=set(agg[b]["vil"])) for b in order}
        for b in reversed(order):
            p = parent[b]
            if p is None:
                continue
            s, t = sub[b], sub[p]
            t["n"] += s["n"]; t["fac"] += s["fac"]; t["vil"] |= s["vil"]
            if geo:
                t["min_d_boundary"] = min(t["min_d_boundary"], s["min_d_boundary"])
                t["min_d_bufedge"] = min(t["min_d_bufedge"], s["min_d_bufedge"])
                t["n_outside"] += s["n_outside"]
        for b in order:
            p = parent[b]
            if p is None or sub[b]["fac"] > 0 or not sub[b]["vil"]:
                continue
            u, v = T[b][p]["orig"]
            inner = u if node_to_block[u] == b else v  # endpoint on the enclave side
            cuts.append({"edge": (u, v), "inner": inner, "outer": v if inner == u else u,
                         "block": b, **sub[b]})
    return cuts, no_fac_components, len(bridges), T, node_to_block

def group_enclaves(cuts):
    """Distinct village sets; outermost cut = largest enclave producing that set."""
    groups = defaultdict(list)
    for c in cuts:
        groups[frozenset(c["vil"])].append(c)
    out = []
    for vil, cs in groups.items():
        cs.sort(key=lambda c: -c["n"])
        out.append({"vil": vil, "outermost": cs[0], "n_cuts": len(cs), "cuts": cs})
    return out

def flag(c):
    if c["n_outside"] > 0 or c["min_d_bufedge"] <= BUFFER_EDGE_RULE_M:
        return "suspect"
    return "real"

def edge_info(G, u, v):
    d = G[u][v]
    return {"u": u, "v": v, "way_id": d["way_id"], "highway": d["highway"], "length_m": round(d["length_m"], 1),
            "u_latlon": [G.nodes[u]["lat"], G.nodes[u]["lon"]], "v_latlon": [G.nodes[v]["lat"], G.nodes[v]["lon"]]}

# ---------------------------------------------------------------- run one graph
def run(label, G, villages, facilities, geo=True):
    vnode = {}
    for v in villages:
        if v["snapped"]:
            vnode.setdefault(v["node_id"], []).append(v)
    fnodes = {f["node_id"] for f in facilities if f["snapped"]}
    cuts, nofac, nb, T, n2b = bridge_tree_enclaves(G, set(vnode), fnodes, geo)
    enclaves = group_enclaves(cuts)
    names = lambda vs: sorted(v["name"] for n in vs for v in vnode[n])
    print(f"[{label}] bridges: {nb}; bridges isolating >=1 village from all {len(fnodes)} facility nodes: {len(cuts)}; "
          f"distinct enclaves (village sets): {len(enclaves)}; villages in facility-free components: "
          f"{[names(c['villages']) for c in nofac]}")
    return {"cuts": cuts, "enclaves": enclaves, "vnode": vnode, "names": names, "nofac": nofac, "T": T, "n2b": n2b}

def outermost_by_first_seen(res):
    """Maximal enclaves: not strictly contained in another enclave's village set."""
    sets = [e["vil"] for e in res["enclaves"]]
    return [e for e in res["enclaves"] if not any(e["vil"] < s for s in sets)]

def main():
    """Pre-event (2024-07-29) run. Functions above are a verbatim copy of scripts/enclave_analysis.py."""
    import math
    PAPER = (11.4992, 76.1601)
    hv = lambda a, b: 2 * 6371000 * math.asin(math.sqrt(math.sin(math.radians(b[0] - a[0]) / 2) ** 2 + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2))
    places, rv_of, pop_of, members = load_crosswalk()
    place_id = lambda v: places[(v["name"], v["lat"], v["lon"])]
    out = {}
    runs = {}
    for label, path in (("PRE-EVENT 2024-07-29", "research/investigation/raw/graph_pre_event.pkl"),
                        ("NOW 2026-09-16", "data/graph_buf10km.pkl")):
        b = pickle.load(open(path, "rb"))
        G = b["G"]
        print(f"\n================ {label} (facilities fixed: curated 34 + 31 buffer ring) ================")
        r = run(label, G, b["villages"], b["facilities34"] + b["facilities_ring"])
        runs[label] = (G, r)
        topo_path = ("research/investigation/raw/wayanad_roads_topology_buf10km_2024-07-29.json" if "PRE" in label
                     else "data/osm/wayanad_roads_topology_buf10km.json")
        wt = {e["id"]: e.get("tags", {}) for e in json.load(open(topo_path, encoding="utf-8"))["elements"] if e["type"] == "way"}
        # (i) what is at the failed-bridge location
        at = sorted({(d["way_id"], u, v) for u, v, d in G.edges(data=True)
                     if min(hv(PAPER, (G.nodes[u]["lat"], G.nodes[u]["lon"])), hv(PAPER, (G.nodes[v]["lat"], G.nodes[v]["lon"]))) <= 50})
        cutset = {frozenset(c["edge"]): c for c in r["cuts"]}
        print(f"Edges with an endpoint within 50 m of {PAPER}:")
        for w, u, v in at:
            c = cutset.get(frozenset((u, v)))
            t = wt.get(w, {})
            print(f"  way {w} edge {u}-{v} {G[u][v]['length_m']:.1f} m tags {t} | single-link cut isolating a village: "
                  + (f"YES -> {c['n']} nodes, villages {r['names'](c['vil'])}" if c else "NO"))
            if c:
                vs = [v_ for n in c["vil"] for v_ in r["vnode"][n]]
                pop = population({place_id(x) for x in vs}, rv_of, pop_of, members)
                print(f"      population rule: attributed {pop['population_attributed']:,.0f}; full {pop['revenue_villages_full']}; "
                      f"partial {list(pop['revenue_villages_partial_unattributed'])}")
        # all enclaves (for completeness)
        print(f"Enclaves ({len(r['enclaves'])}):")
        for e in sorted(r["enclaves"], key=lambda e: -e["outermost"]["n"]):
            o = e["outermost"]
            print(f"  {o['n']:6d} nodes {e['n_cuts']:4d} cuts flag={flag(o):7s} {r['names'](e['vil'])}")
        # (ii) Mundakai chain
        mund = [n for n, vs in r["vnode"].items() if any(x["name"] == "Mundakai" for x in vs)]
        choo = [n for n, vs in r["vnode"].items() if any(x["name"] == "Chooralmala" for x in vs)]
        chain = sorted((c for c in r["cuts"] if mund and mund[0] in c["vil"]), key=lambda c: -c["n"])
        print(f"Chain of single-link cuts isolating Mundakai: {len(chain)} cuts")
        levels = []
        prev = None
        for c in chain:
            vs = tuple(r["names"](c["vil"]))
            if vs != prev:
                cs = [x for x in chain if tuple(r["names"](x["vil"])) == vs]
                first, last = cs[0], cs[-1]
                ei = edge_info(G, *first["edge"])
                ways_in = sorted({G[x["edge"][0]][x["edge"][1]]["way_id"] for x in cs})
                lv = {"villages": list(vs), "n_cuts": len(cs), "isolated_nodes": first["n"],
                      "outermost_edge": ei, "outermost_outer_end": [G.nodes[first["outer"]]["lat"], G.nodes[first["outer"]]["lon"]],
                      "innermost_edge": [last["edge"][0], last["edge"][1]],
                      "innermost_inner_end": [G.nodes[last["inner"]]["lat"], G.nodes[last["inner"]]["lon"]],
                      "ways": {w: {k: wt.get(w, {}).get(k) for k in ("highway", "bridge", "name", "access", "destroyed")} for w in ways_in},
                      "road_length_m": round(sum(G[x["edge"][0]][x["edge"][1]]["length_m"] for x in cs))}
                levels.append(lv)
                print(f"  LEVEL {len(levels)}: isolates {vs} | {len(cs)} cuts, {lv['road_length_m']} m | outermost edge {ei['u']}-{ei['v']} "
                      f"way {ei['way_id']} {ei['highway']} {ei['length_m']} m outer end {lv['outermost_outer_end']} | innermost inner end {lv['innermost_inner_end']}")
                for w, t in lv["ways"].items():
                    print(f"        way {w}: {t}")
                prev = vs
        m_only = [c for c in chain if choo and choo[0] not in c["vil"]]
        print(f"Cuts isolating Mundakai but not Chooralmala: {len(m_only)}")
        out[label] = {"at_failed_bridge": [{"way": w, "u": u, "v": v, "is_cut": frozenset((u, v)) in cutset} for w, u, v in at],
                      "chain_levels": levels, "n_enclaves": len(r["enclaves"]), "n_cuts": len(r["cuts"])}
    json.dump(out, open("research/investigation/c_enclave_pre_vs_now.json", "w"), indent=1, default=str)

if __name__ == "__main__":
    main()
