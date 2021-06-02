# List the different versions of the REST API with their changelogs

PGS_REST_API = [
    {
        'version': '1.8',
        'date': '2021-06',
        'changelog': [
            "New endpoint `/rest/api_versions` providing the list of all the REST API versions and their changelogs.",
            "Change the data type of the field 'rest_api/version' in `/rest/info` to 'string'.",
            "Change the data structure of the `/rest/ancestry_categories` endpoint by adding the new fields 'display_category' and 'categories'."
        ]
    },
    {
        'version': '1.7',
        'date': '2021-04',
        'changelog': [
            "New data 'ancestry_distribution' in the `/rest/score` endpoints, providing information about ancestry distribution on each stage of the PGS",
            "New endpoint `/rest/ancestry_categories` providing the list of ancestry symbols and names."
        ]
    },
    {
        'version': '1.6',
        'date': '2021-03',
        'changelog': [
            "New endpoint `/rest/info` with data such as the REST API version, latest release date and counts, PGS citation, ...",
            "New endpoint `/rest/cohort/all` returning all the Cohorts and their associated PGS.",
            "New endpoint `/rest/sample_set/all` returning all the Sample Set data."
        ]
    },
    {
        'version': '1.5',
        'date': '2021-02',
        'changelog': [
            "Split the array of the field 'associated_pgs_ids' (from the `/rest/publication/` endpoint) in 2 arrays 'development' and 'evaluation'.",
            "New flag parameter 'include_parents' for the endpoint `/rest/trait/all` to display the traits in the catalog + their parent traits (default: 0)."
        ]
    },
    {
        'version': '1.4',
        'date': '2021-01',
        'changelog': [
            "Setup a maximum value for the `limit` parameter.",
            "Add a new field 'size' at the top of the paginated results, to indicate the number of results visible in the page.",
            "Replace the fields 'labels' and 'value' under performance_metrics:'effect_sizes'/'class_acc'/'othermetrics' in the `/rest/performance` endpoints by new fields: 'name_long', 'name_short', 'estimate', 'ci_lower', 'ci_upper' and 'se'.",
            "Restructure the 'samples'&rarr;'sample_age'/'followup_time' JSON (used in several endpoints): merge and replace the fields 'mean' and 'median' into generic fields 'estimate_type' and 'estimate', merge and replace the fields 'se' and 'sd' into generic fields 'variability_type' and 'variability', merge and replace the fields 'range' and 'iqr' by a new structure 'interval'. Note: The field 'type' can take the value 'range', 'iqr' or 'ci'."
        ]
    },
    {
        'version': '1.3',
        'date': '2020-11',
        'changelog': [
            "New endpoint `/rest/performance/all`.",
            "New field 'license' in the `/rest/score` endpoints."
        ]
    },
    {
        'version': '1.2',
        'date': '2020-07',
        'changelog': [
            "Update `/rest/trait/search`: new parameters 'include_children' and 'exact' and new field 'child_associated_pgs_ids'.",
            "Update `/rest/trait/{trait_id}`: new parameter 'include_children', new field 'child_associated_pgs_ids' and a new field 'child_traits' is present when the parameter 'include_children' is set to 1."
        ]
    },
    {
        'version': '1.1',
        'date': '2020-06',
        'changelog': [
            "New endpoint `/rest/trait_category/all`.",
            "New field 'trait_categories' in the `/rest/trait` endpoints."
        ]
    },
    {
        'version': '1.0',
        'date': '2020-05',
        'changelog': [
            "First version of the PGS Catalog REST API"
        ]
    }
]
