# Module storing constants used across the website

PGS_REST_API = {
    'version': 1.6,
    'changelog': [
        "New endpoint 'rest/info' with data such as the REST API version, latest release date and counts, PGS citation, ...",
        "New endpoint '/rest/cohort/all' returning all the Cohorts and their associated PGS.",
        "New endpoint '/rest/sample_set/all' returning all the Sample Set data."
    ]
}

PGS_CITATION = {
    'title': 'The Polygenic Score Catalog: an open database for reproducibility and systematic evaluation',
    'doi': '10.1101/2020.05.20.20108217',
    'authors': 'Samuel A. Lambert, Laurent Gil, Simon Jupp, Scott C. Ritchie, Yu Xu, Annalisa Buniello, Gad Abraham, Michael Chapman, Helen Parkinson, John Danesh, Jacqueline A.L. MacArthur, and Michael Inouye.',
    'journal': 'Preprint at medRxiv',
    'year': 2020
}

USEFUL_URLS = {
    'BAKER_URL'         : 'https://baker.edu.au',
    'EBI_URL'           : 'https://www.ebi.ac.uk',
    'HDR_UK_CAM_URL'    : 'https://www.hdruk.ac.uk/about/structure/hdr-uk-cambridge/',
    'PGS_CONTACT'       : 'pgs-info@ebi.ac.uk',
    'PGS_FTP_ROOT'      : 'ftp://ftp.ebi.ac.uk/pub/databases/spot/pgs',
    'PGS_FTP_HTTP_ROOT' : 'http://ftp.ebi.ac.uk/pub/databases/spot/pgs',
    'PGS_TWITTER_URL'   : 'https://www.twitter.com/pgscatalog',
    'UOC_URL'           : 'https://www.phpc.cam.ac.uk/',
    'TERMS_OF_USE'      : 'https://www.ebi.ac.uk/about/terms-of-use',
    'TEMPLATEGoogleDoc_URL' : 'https://docs.google.com/spreadsheets/d/1CGZUhxRraztW4k7p_6blfBmFndYTcmghn3iNnzJu1_0/edit?usp=sharing',
    'CurationGoogleDoc_URL' : 'https://drive.google.com/file/d/1iYoa0R3um7PtyfVO37itlGbK1emoZmD-/view',
    'CATALOG_PUBLICATION_URL' : 'https://doi.org/'+PGS_CITATION['doi']
}

SEARCH_EXAMPLES = ['breast cancer', 'glaucoma', 'EFO_0001645']

DISCLAIMERS = {
    'performance': """The performance metrics are displayed as reported by the source studies.
                    It is important to note that metrics are not necessarily comparable with
                    each other. For example, metrics depend on the sample characteristics
                    (described by the PGS Catalog Sample Set [PSS] ID), phenotyping, and
                    statistical modelling. Please refer to the source publication for additional
                    guidance on performance.""",
    'score': """The original published polygenic score is unavailable.
             The authors have provided an alternative polygenic for the Catalog.
             Please note some details and performance metrics may differ from the <a href="https://doi.org/{}">publication</a>."""
}

TABLE_HELPER = {
    'score_variant': 'Describes the samples used to define the variant associations/effect-sizes used in the PGS. These data are extracted from the NHGRI-EBI GWAS Catalog when a study ID (GCST) is available',
    'score_training': 'Describes the samples used to develop or train the score (e.g. not used for variant discovery, and non-overlapping with the samples used to evaluate the PGS predictive ability)',
    'score_perf_metrics': 'An index of performance metrics from cataloged evaluations of this PGS',
    'perf_metrics': 'An index of performance metrics from cataloged evaluations of the associated PGS(s)',
    'sample_sets': 'Information about the samples used in PGS performance evaluation. These samples have an PGS Catalog Sample Set (PSS) ID to link them to their associated performance metrics (and across different PGS)',
    'pgs_eval': 'A list of PGS that were developed and evaluated in this publication/study',
    'pgs_eval_ext': 'A list of PGS that were developed in other publications and re-evaluated in the current study'
}

ANNOUNCEMENT = ''
