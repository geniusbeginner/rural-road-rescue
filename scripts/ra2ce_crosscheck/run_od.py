"""Run RA2CE MULTI_LINK_ORIGIN_CLOSEST_DESTINATION with a synthetic single-cell hazard (FORCED: RA2CE has no direct
link-removal input for OD/isolation analyses; see research/ra2ce_crosscheck.md).
Usage (RA2CE venv): python run_od.py {sh59|bailey}"""
import sys
import time
from pathlib import Path
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData, AnalysisSectionLosses
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import AnalysisLossesEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (
    CleanupSection, HazardSection, NetworkConfigData, NetworkSection, OriginsDestinationsSection)
from ra2ce.ra2ce_handler import Ra2ceHandler

W = Path("research/ra2ce/work").resolve()

# WORKAROUND for a RA2CE 1.2.2 export bug (not the analysis itself): networks_utils.add_x_y_to_nodes falls back to the
# tuple (0.0, 0.0) and then calls .x on it, crashing when the graph returned by the OD analysis has nodes without
# geometry/x/y. Only the node/edge GeoPackage export uses it; origins/destinations/routes are unaffected.
import ra2ce.analysis.losses.multi_link_origin_closest_destination as _mlocd
_orig_export = _mlocd.get_nodes_and_edges_from_origin_graph
SKIPPED = []


def _guarded_export(graph):
    bad = [n for n, d in graph.nodes(data=True) if ("x" not in d or "y" not in d) and not hasattr(d.get("geometry"), "x")]
    SKIPPED.extend(bad)
    g = graph.copy()
    g.remove_nodes_from(bad)
    return _orig_export(g)


_mlocd.get_nodes_and_edges_from_origin_graph = _guarded_export


def main(scenario):
    root = W / f"run_{scenario}"
    static = root / "static"
    (static / "network").mkdir(parents=True, exist_ok=True)
    network = NetworkConfigData(
        root_path=root, static_path=static,
        network=NetworkSection(source=SourceEnum.SHAPEFILE,
                               primary_file=W / ("network_v1.shp" if scenario.endswith("_v1") else "network.shp"),
                               file_id="lid",
                               link_type_column="highway", directed=False, save_gpkg=True,
                               reuse_network_output=True),
        origins_destinations=OriginsDestinationsSection(origins=W / "origins.shp", destinations=W / "destinations.shp",
                                                        origin_count="POP", category="category"),
        hazard=HazardSection(hazard_map=[W / f"hazard_{scenario.removesuffix('_v1')}.tif"], aggregate_wl=AggregateWlEnum.MAX,
                             hazard_crs="EPSG:4326", overlay_segmented_network=False),
        cleanup=CleanupSection(),  # snapping/merge/cut_at_intersections all off: keep our topology
    )
    analysis = AnalysisConfigData(
        root_path=root, output_path=root / "output", static_path=static,
        analyses=[AnalysisSectionLosses(name=f"od_{scenario}",
                                        analysis=AnalysisLossesEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION,
                                        weighing=WeighingEnum.LENGTH, threshold=0.5,
                                        calculate_route_without_disruption=True, save_csv=True, save_gpkg=True)])
    t0 = time.time()
    h = Ra2ceHandler.from_config(network=network, analysis=analysis)
    h.configure()
    print(f"configure done {time.time() - t0:.0f}s", flush=True)
    h.run_analysis()
    print(f"analysis done {time.time() - t0:.0f}s", flush=True)
    print(f"export workaround: skipped {len(SKIPPED)} nodes without coordinates in the node/edge export: {SKIPPED[:10]}")


if __name__ == "__main__":
    main(sys.argv[1])
