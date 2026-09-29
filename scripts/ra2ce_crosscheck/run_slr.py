"""Run RA2CE SINGLE_LINK_REDUNDANCY on the whole converted network (no hazard): every link removed one at a time,
reporting detour (0/1), alt length and diff. Reuses the base graph built by run_od.py (copied into run_slr/)."""
import time
from pathlib import Path
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData, AnalysisSectionLosses
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import AnalysisLossesEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import CleanupSection, NetworkConfigData, NetworkSection
from ra2ce.ra2ce_handler import Ra2ceHandler

W = Path("research/ra2ce/work").resolve()
root = W / "run_slr"
static = root / "static"
network = NetworkConfigData(root_path=root, static_path=static,
                            network=NetworkSection(source=SourceEnum.SHAPEFILE, primary_file=W / "network.shp",
                                                   file_id="lid", link_type_column="highway", directed=False,
                                                   save_gpkg=True, reuse_network_output=True),
                            cleanup=CleanupSection())
analysis = AnalysisConfigData(root_path=root, output_path=root / "output", static_path=static,
                              analyses=[AnalysisSectionLosses(name="slr", analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY,
                                                              weighing=WeighingEnum.LENGTH, save_csv=True, save_gpkg=True)])
t0 = time.time()
h = Ra2ceHandler.from_config(network=network, analysis=analysis)
h.configure()
print(f"configure done {time.time() - t0:.0f}s", flush=True)
h.run_analysis()
print(f"analysis done {time.time() - t0:.0f}s", flush=True)
