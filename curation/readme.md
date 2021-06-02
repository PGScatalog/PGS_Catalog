## How to run the import script

### 1 - Import extra Python libraries (not in the requirements.txt - to keep the web app lighter)
You will need several libraries to parse the Excel spreadsheets:
* pandas
* xlrd
* openpyxl
* numpy

Here is a command line to install all the libraries:
```
pip install pandas xlrd openpyxl numpy
```


### 2 - Setup the configuration file
It is located under curation (`curation/config.py`). There you can configure different variables:
* the study input directory: `curation_directories['studies_dir']`
* the scoring files output directory: `curation_directories['scoring_dir']`
* the list of study names to import: `study_names_list`

You might need to change the value of `skip_scorefiles` to **True** if you only want to import the metadata (to test the study data for instance)

Example of config file:
```
curation_directories = {
    'template_schema': './curation/templates/TemplateColumns2Models.xlsx',
    'scoring_schema': './curation/templates/ScoringFileSchema.xlsx',
    'studies_dir': '/Users/myhome/PGS/SourceFiles/',
    'scoring_dir': '/Users/myhome/PGS/ScoringFiles/'
}

study_names_list = [
    { 'name': 'Bakshi2021' },
    { 'name': 'Darst2021_E' },
    { 'name': 'Guffanti2019' },
    { 'name': 'Lahrouchi2021' },
    { 'name': 'Sordillo2021' },
    { 'name': 'ToroMartin2019' },
    { 'name': 'Chen2020' },
    { 'name': 'Du2021' },
    { 'name': 'Innes2020' },
    { 'name': 'Liu2021' },
    { 'name': 'Tadros2021' },
    { 'name': 'Zhou2020' },
    { 'name': 'Clark2019' },
    { 'name': 'Fahmideh2019' },
    { 'name': 'Kachuri2020' },
    { 'name': 'Severance2019' },
    { 'name': 'Tangtanatakul2020' }
]

default_curation_status = 'IP'

skip_scorefiles = False
```

### 3 - Update the Django settings
In order to run the script, you might need to update the global settings of the Django project by adding the **Curation** app (`curation.apps.CurationConfig`) to the list of **INSTALLED_APPS**, in `pgs_web/settings.py`, e.g.:
```
INSTALLED_APPS = [
    'catalog.apps.CatalogConfig',
    'rest_api.apps.RestApiConfig',
    'curation.apps.CurationConfig',
    'search.apps.SearchConfig',
    ...
```

### 4 - Run the import script
The command line is fairly simple, from the root of the Django project:
```
python manage.py shell < curation/import_studies.py
```

For each study, the script runs 3 steps (only 2 if `skip_scorefiles` is set to **True**):
* Parsing the Excel file and store the data in temporary objects
* Import the data into the database, from these temporary objects.
* Update the Scoring files

Extensive reports are printed, for each study and at each step.
A final report summarise the study imports which succeed and failed.
