import json
import re
import geopandas as gpd
from shapely.geometry import Point

CENSUS_POPULATION = {
    # Mananthavady taluk
    "Anchukunnu": 19078, "Cherukottur": 11462, "Edavaka": 16737, "Kanjirangad": 11811,
    "Mananthavady": 34663, "Nalloornad": 16928, "Panamaram": 12683, "Payyampally": 13311,
    "Periya": 11174, "Porunnanore": 22137, "Thavinhal": 17840, "Thirunelly": 12878,
    "Thondernad": 11752, "Thrissilery": 16818, "Valat": 10799, "Vellamunda": 18069,
    # Sulthanbathery taluk
    "Ambalavayal": 16988, "Cheeral": 15725, "Irulam": 21052, "Kidanganad": 9122,
    "Krishnagiri": 12952, "Kuppadi": 26662, "Nadavayal": 15795, "Nenmeni": 31225,
    "Noolpuzha": 14133, "Padichira": 28970, "Poothadi": 14578, "Pulpalli": 28322,
    "Purakkadi": 21022, "Sulthanbathery": 23333, "Thomattuchal": 17984,
    # Vythiri taluk
    "Kalpetta": 31580, "Achooranam": 11998, "Chundale": 7996, "Kaniambetta": 29363,
    "Kavumannam": 10106, "Kottappadi": 23384, "Kottathara": 17295, "Kunnathidavaka": 10309,
    "Kuppadithara": 9761, "Muppainad": 22892, "Muttil North": 12382, "Muttil South": 22355,
    "Padinharethara": 16146, "Pozhuthana": 6406, "Thariyode": 1653, "Thrikkaipatta": 8551,
    "Vellarimala": 7548, "Vengappally": 11692,
}

def norm(name):
    return re.sub(r"\s*\(part\)\s*", "", name).strip()

def main():
    vg = gpd.read_file("data/village_boundaries/village.shp")
    wayanad_vg = vg[vg["DISTRICT"].str.contains("WAYANAD", case=False, na=False)].copy()
    wayanad_vg["name_norm"] = wayanad_vg["NAME"].apply(norm)

    matched = wayanad_vg["name_norm"].map(CENSUS_POPULATION)
    print(f"Revenue village polygons: {len(wayanad_vg)}")
    print(f"Matched to Census population: {matched.notna().sum()} / {len(wayanad_vg)}")
    unmatched = wayanad_vg.loc[matched.isna(), "NAME"].tolist()
    if unmatched:
        print(f"UNMATCHED (flag): {unmatched}")
    wayanad_vg["population_2011"] = matched
    total_pop_check = wayanad_vg["population_2011"].sum()
    print(f"Sum of matched village populations: {total_pop_check:,.0f} "
          f"(official district total was 817,420 per Census 2011 — sanity check)")

    wayanad_vg.to_file("data/village_boundaries/wayanad_villages_pop.geojson", driver="GeoJSON")

    # --- Spatial join: 142 OSM settlement points -> containing revenue village ---
    places_raw = json.load(open("data/osm/wayanad_places.json", encoding="utf-8"))
    settlements = []
    for el in places_raw["elements"]:
        tags = el.get("tags", {})
        if tags.get("place") not in ("village", "town"):
            continue
        settlements.append({"name": tags.get("name", "(unnamed)"), "lat": el["lat"], "lon": el["lon"],
                             "node_id": el["id"]})

    pts = gpd.GeoDataFrame(
        settlements,
        geometry=[Point(s["lon"], s["lat"]) for s in settlements],
        crs="EPSG:4326",
    )

    joined = gpd.sjoin(pts, wayanad_vg[["NAME", "population_2011", "geometry"]], how="left", predicate="within")

    unmatched_pts = joined[joined["NAME"].isna()]
    print(f"\nSettlement points matched by point-in-polygon: {len(joined) - len(unmatched_pts)} / {len(joined)}")
    if len(unmatched_pts):
        print(f"Unmatched (falling outside all polygons, likely boundary/precision gaps): {len(unmatched_pts)}")
        # nearest-polygon fallback for unmatched points
        wayanad_vg_proj = wayanad_vg.to_crs(32643)
        pts_proj = pts.set_crs(4326).to_crs(32643)
        nearest = gpd.sjoin_nearest(pts_proj[pts_proj["name"].isin(unmatched_pts["name"])],
                                     wayanad_vg_proj[["NAME", "population_2011", "geometry"]],
                                     how="left", distance_col="dist_m")
        for _, row in nearest.iterrows():
            idx = joined[joined["name"] == row["name"]].index
            joined.loc[idx, "NAME"] = row["NAME"]
            joined.loc[idx, "population_2011"] = row["population_2011"]
        print(f"Nearest-polygon fallback applied to {len(unmatched_pts)} points (distances: "
              f"{nearest['dist_m'].round(0).tolist()} m)")

    crosswalk = joined[["name", "node_id", "NAME", "population_2011"]].rename(
        columns={"name": "osm_settlement", "NAME": "revenue_village"})
    crosswalk.to_csv("data/village_crosswalk.csv", index=False)

    print(f"\nSample of crosswalk (first 15 rows):")
    print(crosswalk.head(15).to_string(index=False))

    # how many settlement points per revenue village (sanity check for distribution)
    counts = crosswalk.groupby("revenue_village").size().sort_values(ascending=False)
    print(f"\nRevenue villages with >1 OSM settlement point mapped to them (top 10):")
    print(counts.head(10).to_string())
    print(f"\nRevenue villages with ZERO OSM settlement points mapped (no network representation): "
          f"{set(wayanad_vg['NAME']) - set(crosswalk['revenue_village'].dropna())}")

if __name__ == "__main__":
    main()
