"""C1. Pre-event OSM road extract, pinned to 2024-07-29, same classes and 10 km buffer polygon as
scripts/buffered_extract.py (copied logic; the original is not modified). No fallback: if the date query fails, stop.
Raw output (gitignored): research/investigation/raw/; manifest: research/investigation/pre_event_manifest.json."""
import gzip
import hashlib
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
import requests
from shapely.geometry import shape

ROAD_CLASSES = ["trunk", "trunk_link", "primary", "primary_link", "secondary", "tertiary",
                "unclassified", "residential", "living_street", "service", "track", "road",
                "motorway", "motorway_link", "secondary_link", "tertiary_link"]
DATE = "2024-07-29T00:00:00Z"
URL = "https://overpass-api.de/api/interpreter"
RAW = "research/investigation/raw"
OUT_JSON = f"{RAW}/wayanad_roads_topology_buf10km_2024-07-29.json"

def main():
    os.makedirs(RAW, exist_ok=True)
    poly = shape(json.load(open("data/osm/wayanad_buffer_10km.geojson")))
    ps = " ".join(f"{lat:.6f} {lon:.6f}" for lon, lat in poly.exterior.coords)
    q = f"""[out:json][timeout:900][date:"{DATE}"];
way["highway"~"^({'|'.join(ROAD_CLASSES)})$"](poly:"{ps}");
(._;>;);
out body;"""
    r = None
    for i in range(8):
        t0 = time.time()
        r = requests.post(URL, data={"data": q}, timeout=900,
                          headers={"User-Agent": "rural-road-research/0.1 (bridge investigation)"})
        print(f"attempt {i+1}: HTTP {r.status_code}, {len(r.content)/1e6:.1f} MB, {time.time()-t0:.0f}s")
        if r.status_code in (429, 504):
            time.sleep(30 * (i + 1)); continue
        break
    retrieved = datetime.now(timezone.utc).isoformat()
    if r.status_code != 200:
        print("DATE QUERY FAILED - stopping, no substitution.\n", r.text[-800:]); sys.exit(1)
    d = r.json()
    if d.get("remark"):
        print("OVERPASS REMARK (treating as failure):", d["remark"]); sys.exit(1)
    open(OUT_JSON, "wb").write(r.content)
    with open(OUT_JSON, "rb") as f, gzip.open(OUT_JSON + ".gz", "wb") as g:
        g.write(f.read())
    counts = Counter(e["type"] for e in d["elements"])
    manifest = {
        "overpass_query": q, "date_parameter": DATE, "server_url": URL, "retrieved_utc": retrieved,
        "response_osm3s": d.get("osm3s"), "file": OUT_JSON, "file_size_bytes": os.path.getsize(OUT_JSON),
        "sha256": hashlib.sha256(r.content).hexdigest(), "gz_file": OUT_JSON + ".gz",
        "gz_size_bytes": os.path.getsize(OUT_JSON + ".gz"),
        "element_counts": dict(counts),
        "buffer_polygon_source": "data/osm/wayanad_buffer_10km.geojson (read-only)",
    }
    json.dump(manifest, open("research/investigation/pre_event_manifest.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in manifest.items() if k != "overpass_query"}, indent=1))

if __name__ == "__main__":
    main()
