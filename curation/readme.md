## How to run the import script

### 1 - Setup the configuration file
It is located under curation (`curation/config.py`). There you can configure different variables:
* the study input directory: `curation_directories['studies_dir']`
* the scoring files output directory: `curation_directories['scoring_dir']`
* the list of study names to import: `study_names_list`

You might need to change the value of `skip_scorefiles` to **True** if you only want to import the metadata (to test the study data for instance)

### 2 - Update the Django settings
In order to run the script, you might need to update the global settings of the Django project by adding the **Curation** app (`curation.apps.CurationConfig`) to the list of **INSTALLED_APPS**, in `pgs_web/settings.py`, e.g.:
```
INSTALLED_APPS = [
	'catalog.apps.CatalogConfig',
    'rest_api.apps.RestApiConfig',
    'curation.apps.CurationConfig',
    'search.apps.SearchConfig',
    ...
```

### 3 - Run the import script
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
