from curation.imports.curation import CurationImport
from curation.config import *

# Main script
curation_import = CurationImport(
    data_path=curation_directories, studies_list=study_names_list, curation_status_by_default=default_curation_status,
    scoringfiles_format_version=scoringfiles_format_version, skip_scoringfiles=skip_scoringfiles,
    skip_curationtracker=skip_curationtracker, variant_positions_qc_config=variant_positions_qc_config)
curation_import.run_curation_import()
