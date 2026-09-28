"""Tabulate the six f_variants runs side by side. Reads research/investigation/f_variants/*.json only."""
import json

D = "research/investigation/f_variants"
R = {(s, v): json.load(open(f"{D}/{s}_{v}.json")) for s in ("pre", "now") for v in ("V0", "V1", "V2")}
lab = {"pre": "2024-07-29", "now": "2026-09-16"}
out = []
p = lambda x="": (print(x), out.append(x))

p("GRAPH SIZE")
p(f"{'snap':10s} {'var':3s} {'ways kept':>12s} {'nodes':>8s} {'edges':>8s} {'comps':>6s} {'unsnapped v/f':>14s} {'snap moved':>10s}")
for (s, v), r in R.items():
    p(f"{lab[s]:10s} {v:3s} {r['ways_kept']:>6d}/{r['ways_total']:<5d} {r['nodes']:8d} {r['edges']:8d} {r['components']:6d} "
      f"{len(r['unsnapped_villages']):>6d}/{len(r['unsnapped_facilities']):<7d} {len(r['snap_moved_vs_V0']):10d}")

p("\n(i) FAILED BRIDGE (way 380928388, edge 3842230570-3842230578)")
for (s, v), r in R.items():
    i = r["i_failed_bridge"]; a = i["alternate"]
    txt = (f"CUT -> isolates {i['villages']} ({i['isolated_nodes']} nodes), population attributed {i['population_attributed']:,.0f}, "
           f"partial {list(i['revenue_villages_partial_unattributed'])}" if i["is_village_isolating_cut"] else "not a cut")
    alt = (f"alternate {a['n_edges']} edges {a['length_m']:.0f} m {a['time_min']:.2f} min via ways "
           + ", ".join(f"{w['way_id']}({w['highway']}{'/'+w['surface'] if w['surface'] else ''}{'/LIFECYCLE' if w['lifecycle'] else ''})" for w in a["ways"])
           if a["connected_without_bridge"] else "no alternate (C-M disconnected without it)")
    p(f"  {lab[s]} {v}: graph-bridge={i['is_graph_bridge']}; {txt}; {alt}")

p("\n(ii) CHOORALMALA-MUNDAKAI edge connectivity / one minimum cut")
for (s, v), r in R.items():
    ii = r["ii_edge_connectivity"]
    p(f"  {lab[s]} {v}: {ii['edge_connectivity']}  cut {ii['min_cut']}  (C node {r['chooralmala_node']}, M node {r['mundakai_node']})")

p("\n(iii) LEVEL-1 SH59 edge 3249489501-5870049103: side by side")
p(f"  {'var':3s} | {'2024-07-29':55s} | {'2026-09-16':55s}")
for v in ("V0", "V1", "V2"):
    cells = []
    for s in ("pre", "now"):
        l = R[(s, v)]["iii_level1"]
        cells.append(f"cut={l['is_village_isolating_cut']} {l.get('villages')} {l.get('isolated_nodes')} nodes pop {l.get('population_attributed')}")
    p(f"  {v:3s} | {cells[0]:55s} | {cells[1]:55s}")

p("\n(iv) ENCLAVES and changes vs V0 of the same snapshot")
for s in ("pre", "now"):
    base = {tuple(e["villages"]): e for e in R[(s, "V0")]["iv_enclaves"]}
    for v in ("V0", "V1", "V2"):
        E = {tuple(e["villages"]): e for e in R[(s, v)]["iv_enclaves"]}
        nreal = sum(e["flag"] == "real" for e in E.values())
        p(f"  {lab[s]} {v}: {len(E)} enclaves (real {nreal}, suspect {len(E)-nreal})")
        if v != "V0":
            for k in sorted(set(E) - set(base)):
                e = E[k]; p(f"      APPEARS  {list(k)}: {e['nodes']} nodes, {e['n_cuts']} cuts, flag {e['flag']}, pop {e['population_attributed']:,.0f}")
            for k in sorted(set(base) - set(E)):
                e = base[k]; p(f"      VANISHES {list(k)} (V0: {e['nodes']} nodes, flag {e['flag']})")
            for k in sorted(set(base) & set(E)):
                if base[k]["nodes"] != E[k]["nodes"] or base[k]["flag"] != E[k]["flag"]:
                    p(f"      CHANGES  {list(k)}: nodes {base[k]['nodes']} -> {E[k]['nodes']}, flag {base[k]['flag']} -> {E[k]['flag']}")

p("\n(v) VILLAGES WITH NO ROUTE TO ANY FACILITY IN THE BASE GRAPH")
for (s, v), r in R.items():
    x = r["v_no_facility_route"]
    p(f"  {lab[s]} {v}: {x['total']} of 142 (unsnapped {x['unsnapped']}, facility-free components {x['in_facility_free_components']})")
open("research/investigation/f_variants/summary.txt", "w", encoding="utf-8").write("\n".join(out))
