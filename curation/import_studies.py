from curation.imports.curation import CurationImport
from curation.config import *

# Main script
curation_import = CurationImport(curation_directories, study_names_list, default_curation_status, scoringfiles_format_version, skip_scoringfiles)
curation_import.run_curation_import()
