from curation.imports.curation import CurationImport
from curation.config import *
from curation.imports.reported_trait_cleaner import ReportedTraitCleaner

reported_traits_cleaner = ReportedTraitCleaner(reported_traits_replacement_file=reported_traits_cleaning_config['replacement_file'])

# Main script
curation_import = CurationImport(
    data_path=curation_directories, studies_list=study_names_list, curation_status_by_default=default_curation_status,
    scoringfiles_format_version=scoringfiles_format_version, skip_scoringfiles=skip_scoringfiles,
    skip_curationtracker=skip_curationtracker, variant_positions_qc_config=variant_positions_qc_config,
    reported_traits_cleaner=reported_traits_cleaner)
curation_import.run_curation_import()

# Saving the reported trait cleaner for potential new terms
reported_traits_cleaner.export(curation_directories['studies_dir']+'/reported_traits_cleaner.tsv')
