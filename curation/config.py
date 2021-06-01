curation_directories = {
    'template_schema': './curation/templates/TemplateColumns2Models.xlsx',
    'scoring_schema': './curation/templates/ScoringFileSchema.xlsx',
    'studies_dir': '..../SourceFiles/Input/MyStudies/',       # To be replaced with existing path
    'scoring_dir': '..../SourceFiles/Output/ScoringFiles/'    # To be replaced with existing path
}

# To be replaced with existing study names
study_names_list = [
    { 'name': 'Lambert2021' },
    { 'name': 'Inouye2021' }
]

default_curation_status = 'IP'

skip_scorefiles = False