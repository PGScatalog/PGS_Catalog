curation_directories = {
    'template_schema': './curation/templates/TemplateColumns2Models.xlsx',
    'scoring_schema': './curation/templates/ScoringFileSchema.xlsx',
    'studies_dir': '<studies_dir_path>',
    'scoring_dir': '<studies_dir_path>/ScoringFiles/'
}

study_names_list = [
    {'name': '<study_name>'},
]

default_curation_status = 'IP'

scoringfiles_format_version = '2.0'

skip_scoringfiles = False

skip_curationtracker = False

variant_positions_qc_config = {
    'skip': False,  # Set to True to ignore the variant positions QC step
    'n_requests': 4,  # Maximum number of requests allowed per score to the Ensembl REST API
    'ensembl_max_variation_req_size': 10,  # Maximum number of variants per request to the Ensembl variation REST API
    'ensembl_max_sequence_req_size': 50,  # Maximum number of variants per request to the Ensembl sequence REST API
    'minimum_match_rate': 0.9  # The minimum required match rate for the QC to be satisfactory
}

# TSV file containing the reported traits to be replaced for homogeneity.
# Required columns: "trait_reported", "corrected", optional: "date_added".
reported_traits_cleaning_config = {
    'replacement_file': '<local_dir>/reported_traits_dict.tsv'
}
