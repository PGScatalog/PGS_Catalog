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
* the scoring file schema version: `schema_version`
* the study input directory: `curation_directories['studies_dir']`
* the scoring files output directory: `curation_directories['scoring_dir']`
* the list of study names to import: `study_names_list`
* the settings of the variant positions quality control: `variant_positions_qc_config`
* the location of the reported traits cleaning dictionary: `reported_traits_replacement_file`

You might need to change the value of `skip_scorefiles` to **True** if you only want to import the metadata (to test the study data for instance)

You might need to change the value of `skip_curationtracker` to **True** if you want to skip the step which update the curation status of the study in the curation tracker DB.

The default values of the attributes `default_curation_status` and `scoringfiles_format_version` shouldn't be changed.

Example of config file:
```
schema_version = '2.0'

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
    { 'name': 'ToroMartin2019' }
]

default_curation_status = 'IP'

scoringfiles_format_version = '2.0'

skip_scorefiles = False

skip_curationtracker = False

variant_positions_qc_config = {
    'skip': False,
    'n_requests': 4,
    'ensembl_max_variation_req_size': 10,
    'ensembl_max_sequence_req_size': 50,
    'minimum_match_rate': 0.9
}

reported_traits_replacement_file = '/Users/myhome/PGS/reported_traits_dict.tsv'
```

#### Additional attributes for the study_names_list

##### License
To indicate a license other than the default one ([EBI Terms of Use](https://www.ebi.ac.uk/about/terms-of-use/), a **license** attribute can be added, e.g.:
```
...
study_names_list = [
    { 'name': 'Bakshi2021' },
    { 'name': 'Darst2021_E', 'license': 'Creative Commons Attribution 4.0 International (CC BY 4.0)' },
    { 'name': 'Guffanti2019' },
    ...
...
```

##### Curation status
To indicate that an imported study has a different curation status (i.e. not the **default_curation_status**), a **status** attribute can be added, e.g.:
```
...
study_names_list = [
    { 'name': 'Bakshi2021' },
    { 'name': 'Darst2021_E', 'status': 'E' },
    { 'name': 'Guffanti2019' },
    ...
...
```
The value **E** corresponds to the curation status "Embargoed".


#### Variant positions quality control settings
This quality control step can be skipped by setting the attribute **skip** to **True**

###### **'n_requests'**: number of requests sent
The QC uses the Ensembl REST API to validate the variant positions. The requests have a limited size (see other parameters below), therefore multiple requests might be required to get an accurate result. Each request takes a random sample of variants with the specified size from the scoring file (without replacement). A higher number will increase the accuracy of the results but slow down the import.

###### **'ensembl_max_variation_req_size'**: the maximum number of variants sent the Ensembl Variation API
If the scoring file contains rsIDs, the Ensembl Variation API is used to validate the variant coordinates. In theory, variation requests maximum size is 200, however the API is likely to malfunction with that many variants. A smaller number like **10** is recommended.

###### **'ensembl_max_sequence_req_size'**: the maximum number of variants sent the Ensembl Sequence API
If the scoring file doesn't contain the rsIDs but only the chromosome and position of the variants, the Ensembl Sequence API is used to validate the variant positions. The test compares each variant effect allele and other allele with the nucleotide found in the reference genome at the variant position. Both alleles are used as there is no certainty about which of the alleles is the reference allele. This means that a scoring file with a wrongly assigned reference genome can get 50% success match rate. It is assumed that the variant alleles use the forward strand as reference.

###### **'minimum_match_rate'**: the threshold used to determine of the assigned reference genome of the scoring file is correct
A scoring file with a correctly assigned reference genome should get a match rate close to 100%. A scoring file with a wrongly assigned genome build can get 50% match rate. A threshold of 0.9 is recommended.

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
