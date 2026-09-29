"""Spur-snap fix (approved): if a village's enclave would be only its own snap point - the snap node is a dead-end
tip (degree 1, no facility on it) whose single edge leads straight into a road loop - re-snap the village to the
nearest node that lies on a road loop (a 2-edge-connected block of more than one node), within the snap cap.
If no such node is within the cap, the original snap is kept."""
import math
import networkx as nx


def _hv(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def fix_spur_snaps(G, villages, facility_nodes, cap_m=500):
    """villages: list of dicts with name, lat, lon, node_id, dist_m, snapped. Returns (villages, changes)."""
    bridges = list(nx.bridges(G))
    Gb = G.copy()
    Gb.remove_edges_from(bridges)
    block_size = {}
    for comp in nx.connected_components(Gb):
        for n in comp:
            block_size[n] = len(comp)
    looped = [n for n, s in block_size.items() if s > 1]
    out, changes = [], []
    for v in villages:
        n = v["node_id"]
        spur_tip = (v["snapped"] and G.degree(n) == 1 and n not in facility_nodes
                    and block_size.get(next(iter(G.neighbors(n))), 1) > 1)
        if not spur_tip:
            out.append(v)
            continue
        best = min(((_hv(v["lat"], v["lon"], G.nodes[m]["lat"], G.nodes[m]["lon"]), m) for m in looped
                    if abs(G.nodes[m]["lat"] - v["lat"]) < 0.01 and abs(G.nodes[m]["lon"] - v["lon"]) < 0.01),
                   default=None)
        if best is None or best[0] > cap_m:
            out.append(v)
            changes.append((v["name"], n, None, "no looped node within cap - unchanged"))
            continue
        nv = dict(v, node_id=best[1], dist_m=best[0], spur_snap_fixed_from=n)
        out.append(nv)
        changes.append((v["name"], n, best[1], f"{v['dist_m']:.0f} m -> {best[0]:.0f} m"))
    return out, changes
