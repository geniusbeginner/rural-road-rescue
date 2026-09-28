import json
import sys
import time
import requests
import geopandas as gpd
from shapely.geometry import shape, mapping

# Same vehicle classes as data/osm/wayanad_roads_topology.json, plus link/motorway classes
# that don't occur inside Wayanad but may occur in the buffer ring.
ROAD_CLASSES = ["trunk", "trunk_link", "primary", "primary_link", "secondary", "tertiary",
                "unclassified", "residential", "living_street", "service", "track", "road",
                "motorway", "motorway_link", "secondary_link", "tertiary_link"]

SNAPSHOT_DATE = "2026-09-16T10:45:02Z"  # timestamp_osm_base of the original extract
BUFFER_M = 10000
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def buffered_polygon(buffer_m):
    boundary = shape(json.load(open("data/osm/wayanad_boundary.geojson", encoding="utf-8")))
    g = gpd.GeoSeries([boundary], crs=4326).to_crs(32643)
    buf = g.buffer(buffer_m).simplify(100).to_crs(4326).iloc[0]
    return buf

def poly_string(poly):
    return " ".join(f"{lat:.6f} {lon:.6f}" for lon, lat in poly.exterior.coords)

def run_query(q, out_path, attempts=8):
    for i in range(attempts):
        t0 = time.time()
        r = requests.post(OVERPASS_URL, data={"data": q}, timeout=900,
                          headers={"User-Agent": "rural-road-vulnerability-research/0.1 (Wayanad kill test)"})
        print(f"  attempt {i+1}: HTTP {r.status_code}, {len(r.content)/1e6:.1f} MB, {time.time()-t0:.0f}s")
        if r.status_code in (429, 504):
            time.sleep(30 * (i + 1))
            continue
        break
    if r.status_code != 200:
        print(f"  body: {r.text[-500:]}")
    r.raise_for_status()
    d = r.json()
    if d.get("remark"):
        print(f"  OVERPASS REMARK: {d['remark']}")
    print(f"  osm3s: {d.get('osm3s')}")
    json.dump(d, open(out_path, "w", encoding="utf-8"))
    return d

def main():
    poly = buffered_polygon(BUFFER_M)
    ps = poly_string(poly)
    print(f"Buffer {BUFFER_M} m polygon: {len(poly.exterior.coords)} vertices")
    json.dump(mapping(poly), open(f"data/osm/wayanad_buffer_{BUFFER_M//1000}km.geojson", "w"))

    date = "" if "--current" in sys.argv else f'[date:"{SNAPSHOT_DATE}"]'
    classes = "|".join(ROAD_CLASSES)

    print("Roads query...")
    roads_q = f"""[out:json][timeout:900]{date};
way["highway"~"^({classes})$"](poly:"{ps}");
(._;>;);
out body;"""
    d = run_query(roads_q, f"data/osm/wayanad_roads_topology_buf{BUFFER_M//1000}km.json")
    print(f"  elements: {sum(1 for e in d['elements'] if e['type']=='node')} nodes, "
          f"{sum(1 for e in d['elements'] if e['type']=='way')} ways")

    print("Health facilities query...")
    health_q = f"""[out:json][timeout:600]{date};
(nwr["amenity"~"^(hospital|clinic|doctors)$"](poly:"{ps}");
 nwr["healthcare"](poly:"{ps}"););
out center tags;"""
    h = run_query(health_q, f"data/osm/wayanad_health_buf{BUFFER_M//1000}km.json")
    print(f"  elements: {len(h['elements'])}")

if __name__ == "__main__":
    main()
