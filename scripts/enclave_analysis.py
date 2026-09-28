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
    places, rv_of, pop_of, members = load_crosswalk()
    place_id = lambda v: places[(v["name"], v["lat"], v["lon"])]

    # ---------------- baseline: original clipped graph (reproduces fast_bridge_search) -------------
    old = pickle.load(open("data/graph_weighted.pkl", "rb"))
    cp2 = load_json("data/checkpoint2_results.json")
    base = run("original clipped, 34 fac", old["G"], cp2["villages"], cp2["facilities"], geo=False)
    base_max = outermost_by_first_seen(base)
    print(f"\n=== Original 19 check: maximal enclaves in original graph: {len(base_max)} ===")
    for e in sorted(base_max, key=lambda e: -e["outermost"]["n"]):
        print(f"  {e['outermost']['n']:5d} nodes  {base['names'](e['vil'])}")
    print(f"  maximal enclaves >=10 nodes: {sum(e['outermost']['n'] >= 10 for e in base_max)}; "
          f">=20 nodes: {sum(e['outermost']['n'] >= 20 for e in base_max)}")
    print(f"  all distinct enclaves incl. nested: {len(base['enclaves'])} "
          f"(>=10: {sum(e['outermost']['n'] >= 10 for e in base['enclaves'])}, "
          f">=20: {sum(e['outermost']['n'] >= 20 for e in base['enclaves'])})")

    results = {}
    for km in (10, 5):
        b = pickle.load(open(f"data/graph_buf{km}km.pkl", "rb"))
        G = b["G"]
        print(f"\n================ {km} km buffer ================")
        r34 = run(f"buf{km}, curated 34 only", G, b["villages"], b["facilities34"])
        rext = run(f"buf{km}, 34 + ring", G, b["villages"], b["facilities34"] + b["facilities_ring"])
        results[km] = {"G": G, "b": b, "r34": r34, "rext": rext}

    # ---------------- Step 2: flag table on 10 km, extended facilities -----------------------------
    G10, r10 = results[10]["G"], results[10]["rext"]
    r5 = results[5]["rext"]
    flags5 = {e["vil"]: flag(e["outermost"]) for e in r5["enclaves"]}
    flags10_34 = {e["vil"]: e for e in results[10]["r34"]["enclaves"]}
    print("\n=== STEP 2: enclaves on 10 km buffered graph, facilities = curated 34 + buffer ring ===")
    print(f"{'nodes':>6} {'cuts':>4} {'d_bnd_m':>8} {'d_bufedge_m':>11} {'n_out':>5} {'flag10':>7} {'flag5':>7}  villages")
    for e in sorted(r10["enclaves"], key=lambda e: -e["outermost"]["n"]):
        o = e["outermost"]
        print(f"{o['n']:6d} {e['n_cuts']:4d} {o['min_d_boundary']:8.0f} {o['min_d_bufedge']:11.0f} {o['n_outside']:5d} "
              f"{flag(o):>7} {flags5.get(e['vil'], 'absent'):>7}  {r10['names'](e['vil'])}")
    only34 = [k for k in flags10_34 if k not in {e['vil'] for e in r10['enclaves']}]
    print(f"\nEnclaves that exist with curated-34 only but vanish once buffer-ring facilities are added: "
          f"{[r10['names'](k) for k in only34]}")
    changed = [(r10['names'](e['vil']), flag(e['outermost']), flags5.get(e['vil'], 'absent'))
               for e in r10["enclaves"] if flags5.get(e['vil'], 'absent') != flag(e['outermost'])]
    only5 = [r5['names'](e['vil']) for e in r5['enclaves'] if e['vil'] not in {x['vil'] for x in r10['enclaves']}]
    print(f"Flag differences 10 km vs 5 km: {changed}")
    print(f"Enclaves present at 5 km but not at 10 km: {only5}")

    # old 19 -> new status
    print("\n=== Original maximal enclaves -> status on 10 km graph (34 + ring) ===")
    name_to_new = defaultdict(list)
    for e in r10["enclaves"]:
        for nm in r10["names"](e["vil"]):
            name_to_new[nm].append(e)
    for e in sorted(base_max, key=lambda e: -e["outermost"]["n"]):
        nms = base["names"](e["vil"])
        exact = [x for x in r10["enclaves"] if set(r10["names"](x["vil"])) == set(nms)]
        if exact:
            x = exact[0]
            status = f"SURVIVES same villages, {x['outermost']['n']} nodes, flag={flag(x['outermost'])}"
        elif any(name_to_new[nm] for nm in nms):
            status = "CHANGED: " + "; ".join(f"{nm} in {r10['names'](x['vil'])}" for nm in nms for x in name_to_new[nm][:1])
        else:
            status = "GONE: no single cut isolates these villages"
        print(f"  {str(nms):55s} old {e['outermost']['n']:5d} nodes -> {status}")

    # ---------------- spur snaps -------------------------------------------------------------------
    print("\n=== spur_snap: villages whose snap node is a dead end (degree 1) on the 10 km graph ===")
    spur = {}
    for v in results[10]["b"]["villages"]:
        if v["snapped"] and G10.degree(v["node_id"]) == 1:
            spur[v["name"]] = v
    bridges10 = {frozenset(c["edge"]) for c in r10["cuts"]}
    # for the proposal: nearest node that lies in a 2-edge-connected block of >1 node, within the 500 m cap
    n2b = r10["n2b"]
    block_size = defaultdict(int)
    for n, bb in n2b.items():
        block_size[bb] += 1
    for nm, v in sorted(spur.items()):
        best = None
        for n in G10.nodes:
            if block_size[n2b.get(n, -1)] > 1:
                d = haversine_m(v["lat"], v["lon"], G10.nodes[n]["lat"], G10.nodes[n]["lon"])
                if d <= 500 and (best is None or d < best[1]):
                    best = (n, d)
        in_enc = any(v["node_id"] in c["vil"] for c in r10["cuts"])
        print(f"  {nm:28s} snap {v['dist_m']:4.0f} m to dead-end node {v['node_id']}; in an enclave: {in_enc}; "
              f"nearest looped-block node within 500 m: " + (f"{best[0]} at {best[1]:.0f} m" if best else "none"))

    # ---------------- Step 3: atlas ------------------------------------------------------------------
    atlas = []
    for e in sorted(r10["enclaves"], key=lambda e: -e["outermost"]["n"]):
        o = e["outermost"]
        vs = [v for n in e["vil"] for v in r10["vnode"][n]]
        pids = {place_id(v) for v in vs}
        atlas.append({
            "villages": sorted(v["name"] for v in vs),
            "road_nodes": o["n"],
            "facilities_inside": o["fac"],
            "n_single_link_cuts_producing_it": e["n_cuts"],
            "outermost_cut": edge_info(G10, *o["edge"]),
            "min_distance_to_district_boundary_m": round(o["min_d_boundary"]),
            "min_distance_to_buffer_edge_m": round(o["min_d_bufedge"]),
            "nodes_outside_district": o["n_outside"],
            "flag_10km": flag(o),
            "flag_5km": flags5.get(e["vil"], "enclave absent at 5 km"),
            "spur_snap_villages": sorted(v["name"] for v in vs if v["name"] in spur),
            **population(pids, rv_of, pop_of, members),
        })
    json.dump({"parameters": {"buffer_km": 10, "buffer_edge_rule_m": BUFFER_EDGE_RULE_M, "snap_cap_m": 500,
                              "suspect_rule": "any node outside district OR within buffer_edge_rule_m of buffer edge",
                              "population_rule": "revenue village counted only if all its OSM settlements are inside",
                              "facilities": "curated 34 + rule-selected buffer-ring facilities",
                              "osm_snapshot": "2026-09-16T10:45:02Z"},
               "enclaves": atlas,
               "villages_in_facility_free_components": [r10["names"](c["villages"]) for c in r10["nofac"]]},
              open("data/enclave_atlas.json", "w", encoding="utf-8"), indent=1)
    print(f"\n=== STEP 3: wrote data/enclave_atlas.json with {len(atlas)} enclaves ===")
    for a in atlas:
        print(f"  {a['road_nodes']:5d} nodes fac={a['facilities_inside']} {a['flag_10km']:7s} pop={a['population_attributed']:>8,.0f} "
              f"full={list(a['revenue_villages_full'])} partial={list(a['revenue_villages_partial_unattributed'])} "
              f"spur={a['spur_snap_villages']}  {a['villages']}")

    # ---------------- Step 4: Chooralmala chain, before and after -----------------------------------
    for label, G, res in (("BEFORE (original clipped graph)", old["G"], base), ("AFTER (10 km buffered graph)", G10, r10)):
        print(f"\n=== STEP 4 chain {label} ===")
        mund = [n for n, vs in res["vnode"].items() if any(v["name"] == "Mundakai" for v in vs)]
        choo = [n for n, vs in res["vnode"].items() if any(v["name"] == "Chooralmala" for v in vs)]
        chain = sorted((c for c in res["cuts"] if mund[0] in c["vil"]), key=lambda c: -c["n"])
        if not chain:
            print("  no single cut isolates Mundakai")
            continue
        start = chain[0]["outer"]
        dist = nx.single_source_dijkstra_path_length(G, start, weight="length_m")
        prev = None
        for c in chain:
            vs = tuple(res["names"](c["vil"]))
            if vs != prev:
                ei = edge_info(G, *c["edge"])
                print(f"  +{dist.get(c['outer'], float('nan')):7.0f} m from outermost cut | isolates {c['n']:5d} nodes | {list(vs)}")
                print(f"      first cut for this set: {ei}")
                prev = vs
        m_only = [c for c in chain if choo[0] not in c["vil"]]
        print(f"  Cuts that isolate Mundakai but NOT Chooralmala: {len(m_only)}")
        if m_only:
            c = max(m_only, key=lambda c: c["n"])
            G2 = G.copy()
            G2.remove_edge(*c["edge"])
            print(f"  outermost such cut: {edge_info(G, *c['edge'])}")
            print(f"  verify: remove it -> path Chooralmala<->Mundakai exists? {nx.has_path(G2, choo[0], mund[0])}")

if __name__ == "__main__":
    main()
