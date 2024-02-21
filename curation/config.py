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
    'ensembl_max_sequence_req_size': 50  # Maximum number of variants per request to the Ensembl sequence REST API
}