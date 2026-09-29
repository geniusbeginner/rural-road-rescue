"""Documented rule for the curated health-facility list (data/health_facilities_final.json).

The 34 facilities were originally chosen by hand. This module writes that choice down as a mechanical rule plus
explicit, listed manual decisions, so it can be re-run and audited. Source: data/osm/wayanad_health.json
(Overpass snapshot 2026-09-16); every curated facility is an OSM element in that file (matched by name + coords).

Mechanical rule (applied in order):
  1. Element has a name matching a public-health facility type:
     PHC / FHC / CHC / urban PHC ("... Health Centre/Center"), "PHC"/"CHC"/"FHC", taluk / district / general /
     government hospital.
  2. Name does not match AYUSH, veterinary or sub-centre terms.
  3. Not tagged operator:type=private.
  4. Location (node, or way centre) lies inside the Wayanad district polygon.
  5. Generic names with no place name (exactly "Primary Health Centre", "Community Health Center", ...) are dropped.
  6. Elements within 50 m of each other are treated as one facility; DEDUPE_KEEP says which element is kept.
Manual decisions (not derivable from the rule), each with a specific reason and source:
  MANUAL_INCLUDE, MANUAL_EXCLUDE and COORD_OVERRIDE below. Reviewed 2026-09-29 against:
  [eHealth]  Kerala eHealth live institution table, https://dashboard.ehealth.kerala.gov.in/index.php/Init/ShowLiveTable
             (columns: Hospital Name, Type of Hospital, District, Date of Commission)
  [District] Wayanad district administration, https://wayanad.gov.in/en/public-utility/government-hospital-kainatty-kalpetta/
  [OSM]      landmark positions (police stations, post offices, place nodes) from current OpenStreetMap via Overpass.
Duplicate policy: where OSM has two records for one institution (confirmed by [eHealth] listing it once, or by a
shared OSM `ref` value), keep the record with more detail (address / `ref` / building outline) unless a landmark
check shows the other one is at the institution's actual location. The five nodes 8998387385-8998387390 are a
bulk entry with name + operator only (no address, no ref); they lose to any detailed record.
"""
import json
import math
import re
from shapely.geometry import Point, shape

NAME_RE = re.compile(r"(primary|family|community|urban primary)\s+health\s+(centre|center)|\b(phc|chc|fhc)\b|"
                     r"taluk.*hospital|district hospital|general hospital|gov(ernmen)?t\.?\s+hospital", re.I)
EXCLUDE_RE = re.compile(r"ayurved|homoe|homeo|homio|siddha|unani|veterinary|sub\s*-?\s*(family\s+)?(health\s+)?cent", re.I)
GENERIC_NAME_RE = re.compile(r"^\s*(urban\s+)?(primary|community|family)\s+health\s+(centre|center)\s*$|"
                             r"^\s*gov(ernmen)?t\.?\s+(taluk|general)\s+hospital\s*$", re.I)
DEDUPE_M = 50

# Which OSM element of a <=50 m cluster is kept (the rest are dropped). Choice among near-identical points was
# manual; by OSM id because 7 elements share the name "Community Health Centre Panamaram".
DEDUPE_KEEP = {
    "node/2000118622",   # Community Health Centre Porunnanore
    "way/799281118",     # Community Health Centre Panamaram
    "way/799282620",     # Community Health Centre, Meppady (49 m from 'Family Health Centre Ambalavayal')
    "way/799292778",     # Primary Health Centre Cheeral
    "node/8667718017",   # Community Health Center Meppadi
    "node/8002235743",   # Primary Health Centre Vazhavatta
    "way/798809158",     # Govt. Taluk Head Quarters Hospital, Sulthan Bathery
    "node/5276849449",   # TALUK HEAD QUARTERS HOSPITAL VYTHIRI
    "node/7462625817",   # Community Health Center Pulpally (has ref, address, phone); way/804135039 'CHC pulpally',
                         # the building outline 16 m away, is the same facility
}
# Manual additions: in the list although the rule excludes them.
MANUAL_INCLUDE = {
    "node/9000365107": ("WIMS Urban Health Center Kalpetta - carried over from the original curation. OSM tags "
                        "operator='Department of Health and Family Welfare' but operator:type=private; public/private "
                        "status NOT independently verified."),
    "node/10113779000": ("Government General Hospital (Kalpetta) - dropped by the generic-name rule only. Confirmed "
                         "operating: [eHealth] 'M S PADMAIAH GOWDER MEMORIAL GOVERNMENT GENERAL HOSPITAL KALPETTA', "
                         "'General Hospital', 'WAYANAD', commissioned '11-11-2022'; [District] 'Government Hospital, "
                         "Kainatty Kalpetta', 'Kainatty, Kalpetta , Wayanad, Kerala', pincode 673122. Position "
                         "corrected via COORD_OVERRIDE."),
}
# Name corrections: position kept as-is, name (and facility-type label) replaced.
NAME_OVERRIDE = {
    "way/799282620": ("Family Health Centre Ambalavayal",
                      "OSM name 'Community Health Centre, Meppady', but the record sits 49 m from way/858054200 "
                      "'Family Health Centre Ambalavayal', 7 km from Meppadi, while Meppadi's own facility is "
                      "node/8667718017. [eHealth] lists 'FAMILY HEALTH CENTRE AMBALAVAYAL' (commissioned 21-06-2022) "
                      "and no Meppadi CHC. Position kept; name corrected."),
}
# Why each swapped-in record is in the list (the record it replaced is in MANUAL_EXCLUDE).
SWAP_IN = {
    "way/799281364": "Community Health Centre Peria: replaces bulk node/8998387385 (more detailed record: ref 1991, address).",
    "way/798756818": "Primary Health Center Mullankolly: replaces bulk node/8998387387 (ref 1993, address, building).",
    "node/7462625817": "Community Health Center Pulpally: replaces way/799283331; 99 m from Pulpally police station.",
    "way/804522811": "Family Health Centre Vellamunda: replaces way/799292382; 39 m from Vellamunda police station.",
}
RULE_REASON = ("Passes rule steps 1-6: named public-health facility type (PHC/FHC/CHC/taluk/district hospital), "
               "not AYUSH/veterinary/sub-centre, not private, inside Wayanad, not generic, not a <=50 m duplicate.")

# Position corrections for records whose OSM position is contradicted by the sources.
COORD_OVERRIDE = {
    # OSM node sits in south Kalpetta, 3,409 m from Kainatty (the official address). Replacement position is the one
    # encoded in the Mappls listing 'Government General Hospital, Wayanad Road, Kainatty, Kalpetta, Kerala, 673122'
    # (https://www.mappls.com/place-government+general+hospital-wayanad+road-kainatty-kalpetta-kerala-673122-O05U1M);
    # OSM node/10113293169 'Medical Superintendent Office' lies 54 m from it.
    "node/10113779000": (11.633806, 76.089468),
}
# Manual removals: pass the rule and are not within 50 m of a kept record, but are excluded for the reason given.
MANUAL_EXCLUDE = {
    # Duplicates of an institution [eHealth] lists once; the kept record has more detail.
    "node/8998387386": ("Family Health Centre Edavaka - bulk node (no address/ref); duplicate of node/7479173997 "
                        "'Family Health centre  Edavaka' (ref 1986, address Pallikkal / Ellumannam PO), 1,480 m away. "
                        "[eHealth] lists one 'FAMILY HEALTH CENTRE EDAVAKA'."),
    "node/8998387388": ("Family Health Centre Vengapally - bulk node; duplicate of 'Family Health Center, Vengapally' "
                        "(ref 1972, Thekkumthara P O), 2,243 m away. [eHealth] lists one 'FAMILY HEALTH CENTRE VENGAPALLY'."),
    "node/8998387389": ("Family Health Centre Vazhavatta - bulk node; duplicate of node/8002235743 'Primary Health Centre "
                        "Vazhavatta' (ref 1964), whose position two more OSM records within 17 m corroborate. [eHealth] "
                        "lists one 'FAMILY HEALTH CENTRE VAZHAVATTA' (renamed PHC -> FHC)."),
    "node/8998387390": ("Family Health Centre Noolpuzha - bulk node; duplicate of way/857068370 'Noolpuzha Family Health "
                        "Centre' (ref 1975, building outline), 1,256 m away. [eHealth] lists one 'FAMILY HEALTH CENTER "
                        "NOOLPUZHA'. Consistency fix: this pair had both been kept."),
    "way/1084062616": ("Family Health Center, Varadhoor - name-only record; duplicate of way/799300978 'Primary Health "
                       "Centre Varadoor' (ref 1963, addr:street Varadoor, operator), 1,652 m away. [eHealth] lists one "
                       "'FAMILY HEALTH CENTRE VARADOOR'. Consistency fix: this pair had both been kept."),
    # Swaps: the originally kept record lost to a more detailed record of the same institution.
    "node/8998387385": ("Community Health Centre Peria - bulk node; replaced by way/799281364 (same name, ref 1991, "
                        "address 'varayal' 670644, building outline), 3,113 m away. Peria is not in [eHealth]; "
                        "chosen on record detail only."),
    "node/8998387387": ("Primary Health Centre Mullankolly - bulk node; replaced by way/798756818 'Primary Health Center "
                        "Mullankolly' (ref 1993, addr:street 'PHC padichira - Lourde Nagar road', building outline), "
                        "3,278 m away. [eHealth] lists one 'PRIMARY HEALTH CENTRE MULLANKOLLY'."),
    "way/799283331": ("Community Health Centre, Pulpally - same ref (1992) as node/7462625817; [eHealth] lists one "
                      "'COMMUNITY HEALTH CENTRE PULPALLY'. Location check: node/7462625817 is 99 m from OSM 'Police "
                      "Station,Pulpally' and 122 m from 'Pulpally Post Office SO' (Justdial: 'Near To Police Station "
                      "Pulpally'); this way is 1,245 m from the police station."),
    "way/799292382": ("Primary Health Centre Vellamunda - same ref (1985) as way/804522811 'Family Health Centre "
                      "Vellamunda'; [eHealth] lists one 'FAMILY HEALTH CENTRE VELLAMUNDA'. Location check: way/804522811 "
                      "is 39 m from OSM 'Police Station,Vellamunda' and 82 m from 'Post Office , Vellamunda' (directory "
                      "address 'Vellamunda P.O.'); this way is 4,040 m from the police station."),
    # Existence not confirmed.
    "way/1017372482": ("PHC Tholpetty - name-only OSM record (no operator/ref/address). Not in [eHealth]; a web search "
                       "found no listing. Excluded until an independent source confirms it exists."),
}


def _latlon(e):
    return (e["lat"], e["lon"]) if e["type"] == "node" else (e["center"]["lat"], e["center"]["lon"])


def _hv(a, b):
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def curate_facilities(health_path="data/osm/wayanad_health.json", boundary_path="data/osm/wayanad_boundary.geojson"):
    """Return (facilities, report). facilities: list of {name, lat, lon, osm}; report: counts per rule step."""
    elements = json.load(open(health_path, encoding="utf-8"))["elements"]
    district = shape(json.load(open(boundary_path)))
    report = {"elements": len(elements)}
    step = []
    for e in elements:
        t = e.get("tags", {})
        name = t.get("name", "")
        if not name or not NAME_RE.search(name) or EXCLUDE_RE.search(name) or t.get("operator:type") == "private":
            continue
        lat, lon = _latlon(e)
        if not district.contains(Point(lon, lat)):
            continue
        step.append({"name": name, "lat": lat, "lon": lon, "osm": f"{e['type']}/{e['id']}"})
    report["rule_steps_1_4"] = len(step)
    generic = [f for f in step if GENERIC_NAME_RE.search(f["name"])]
    step = [f for f in step if not GENERIC_NAME_RE.search(f["name"])]
    report["dropped_generic_name"] = [f["name"] for f in generic]
    # 50 m clusters
    kept, dropped_dupes = [], []
    for f in sorted(step, key=lambda f: (f["osm"] not in DEDUPE_KEEP, f["osm"])):
        if any(_hv((f["lat"], f["lon"]), (k["lat"], k["lon"])) <= DEDUPE_M for k in kept):
            dropped_dupes.append(f["name"])
        else:
            kept.append(f)
    report["dropped_duplicates_within_50m"] = dropped_dupes
    report["manual_exclude_applied"] = [MANUAL_EXCLUDE[f["osm"]] for f in kept if f["osm"] in MANUAL_EXCLUDE]
    kept = [f for f in kept if f["osm"] not in MANUAL_EXCLUDE]
    for e in elements:
        k = f"{e['type']}/{e['id']}"
        if k in MANUAL_INCLUDE and all(f["osm"] != k for f in kept):
            lat, lon = _latlon(e)
            kept.append({"name": e["tags"]["name"], "lat": lat, "lon": lon, "osm": k})
    report["manual_include_applied"] = list(MANUAL_INCLUDE.values())
    for f in kept:
        k = f["osm"]
        f["reason"] = MANUAL_INCLUDE.get(k) or SWAP_IN.get(k) or RULE_REASON
        if k in COORD_OVERRIDE:
            f["osm_position"] = [f["lat"], f["lon"]]
            f["lat"], f["lon"] = COORD_OVERRIDE[k]
        if k in NAME_OVERRIDE:
            f["osm_name"] = f["name"]
            f["name"], why = NAME_OVERRIDE[k]
            f["reason"] = f"{RULE_REASON} Name corrected: {why}"
    report["coord_override_applied"] = [f["osm"] for f in kept if "osm_position" in f]
    report["name_override_applied"] = [f["osm"] for f in kept if "osm_name" in f]
    report["final_count"] = len(kept)
    return sorted(kept, key=lambda f: f["name"].lower()), report


if __name__ == "__main__":
    fac, rep = curate_facilities()
    print(f"OSM health elements: {rep['elements']}")
    print(f"after name/type/exclusion/private/district rule (steps 1-4): {rep['rule_steps_1_4']}")
    print(f"dropped as generic names (step 5): {len(rep['dropped_generic_name'])} {rep['dropped_generic_name']}")
    print(f"dropped as <=50 m duplicates (step 6): {len(rep['dropped_duplicates_within_50m'])}")
    print(f"MANUAL removals: {len(rep['manual_exclude_applied'])}")
    for r in rep["manual_exclude_applied"]:
        print(f"   - {r}")
    print(f"MANUAL additions: {len(rep['manual_include_applied'])}")
    for r in rep["manual_include_applied"]:
        print(f"   + {r}")
    print(f"position overrides: {rep['coord_override_applied']}")
    print(f"\nFINAL: {rep['final_count']}")
    for i, f in enumerate(fac, 1):
        print(f"  {i:2d}. {f['name']:55s} {f['lat']:.7f}, {f['lon']:.7f}  {f['osm']}")
    ref = json.load(open("data/health_facilities_final.json", encoding="utf-8"))
    a = {(f["name"], round(f["lat"], 7), round(f["lon"], 7)) for f in fac}
    b = {(f["name"], round(f["lat"], 7), round(f["lon"], 7)) for f in ref}
    print(f"\nvs data/health_facilities_final.json: identical={a == b}")
    for x in sorted(a - b):
        print(f"   + new/moved: {x}")
    for x in sorted(b - a):
        print(f"   - removed/moved: {x}")
    import sys
    if "--write" in sys.argv:
        json.dump([{k: f[k] for k in ("name", "lat", "lon", "osm", "reason") } | ({"osm_position": f["osm_position"]} if "osm_position" in f else {})
                   | ({"osm_name": f["osm_name"]} if "osm_name" in f else {}) for f in fac],
                  open("data/health_facilities_final.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"wrote data/health_facilities_final.json ({len(fac)} facilities)")
