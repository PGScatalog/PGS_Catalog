# Module storing constants used across the website

PGS_CITATIONS = [
    {
    'title': 'Enhancing the Polygenic Score Catalog with tools for score calculation and ancestry normalization',
    'doi': '10.1038/s41588-024-01937-x',
    'PMID': 39327485,
    'authors': 'Samuel A. Lambert, Benjamin Wingfield, Joel T. Gibson, Laurent Gil, Santhi Ramachandran, Florent Yvon, Shirin Saverimuttu, Emily Tinsley, Elizabeth Lewis, Scott C. Ritchie, Jingqin Wu, Rodrigo Canovas, Aoife McMahon, Laura W. Harris, Helen Parkinson, Michael Inouye',
    'journal': 'Nature Genetics', # TODO: Update volume/page when printed
    'year': 2024
    },
    {
    'title': 'The Polygenic Score Catalog as an open database for reproducibility and systematic evaluation',
    'doi': '10.1038/s41588-021-00783-5',
    'PMID': 33692568,
    'authors': 'Samuel A. Lambert, Laurent Gil, Simon Jupp, Scott C. Ritchie, Yu Xu, Annalisa Buniello, Aoife McMahon, Gad Abraham, Michael Chapman, Helen Parkinson, John Danesh, Jacqueline A. L. MacArthur, Michael Inouye ',
    'journal': 'Nature Genetics volume 53, pages420–425',
    'year': 2021
    }
]

PGS_PUBLICATIONS = [
    {
        'title': PGS_CITATIONS[0]['title'],
        'authors': 'Lambert, Wingfield et al',
        'year': PGS_CITATIONS[0]['year'],
        'doi': PGS_CITATIONS[0]['doi'],
        'PMID': PGS_CITATIONS[0]['PMID'],
        'journal': PGS_CITATIONS[0]['journal']
    },
    {
        'title': 'The NHGRI-EBI GWAS Catalog: knowledgebase and deposition resource',
        'authors': 'Sollis et al',
        'year': 2023,
        'doi': '10.1093/nar/gkac1010',
        'PMID': 36350656,
        'journal': 'Nucleic Acids Research 51(D1):D977-D985'
    },
    {
        'title': PGS_CITATIONS[1]['title'],
        'authors': 'Lambert et al',
        'year': PGS_CITATIONS[1]['year'],
        'doi': PGS_CITATIONS[1]['doi'],
        'PMID': PGS_CITATIONS[1]['PMID'],
        'journal': PGS_CITATIONS[1]['journal']
    }
]

ENSEMBL_VERSION = 105

USEFUL_URLS = {
    'NHGRI_URL'         : 'https://www.genome.gov/',
    'BAKER_URL'         : 'https://baker.edu.au',
    'EBI_URL'           : 'https://www.ebi.ac.uk',
    'HDR_UK_CAM_URL'    : 'https://www.hdruk.ac.uk/about-us/our-locations/health-data-research-uk-hdr-uk-cambridge/',
    'OLS_ROOT_URL'      : 'https://www.ebi.ac.uk/ols4',
    'PGS_CONTACT'       : 'pgs-info@ebi.ac.uk',
    'PGS_FTP_ROOT'      : 'ftp://ftp.ebi.ac.uk/pub/databases/spot/pgs',
    'PGS_FTP_HTTP_ROOT' : 'https://ftp.ebi.ac.uk/pub/databases/spot/pgs',
    'PGS_GITHUB'        : 'https://github.com/PGScatalog/',
    'PGS_TWITTER'       : '@PGSCatalog',
    'PGS_TWITTER_URL'   : 'https://www.twitter.com/pgscatalog',
    'PGS_WEBSITE_URL'   : 'https://www.pgscatalog.org/',
    'UOC_URL'           : 'https://www.phpc.cam.ac.uk/',
    'TERMS_OF_USE'      : 'https://www.ebi.ac.uk/about/terms-of-use',
    'TEMPLATEGoogleDoc_URL' : 'https://docs.google.com/spreadsheets/d/1UEGH0NNuQ8ifbsxIhe8HbnG9XYjsIwSF/edit?usp=sharing',
    'CurationGoogleDoc_URL' : 'https://drive.google.com/file/d/1QYdKBnEqAmhSZIuMux7ifpT3ZBk9gupT/view',
    'CATALOG_PUBLICATION_URL' : 'https://doi.org/' + PGS_CITATIONS[0]['doi'],
    'EPMC_REST_SEARCH'  : 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
}

SEARCH_EXAMPLES = ['breast cancer', 'glaucoma', 'BMI', 'EFO_0001645']

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
    'sample_sets': 'Information about the samples used in PGS performance evaluation. These samples have a PGS Catalog Sample Set (PSS) ID to link them to their associated performance metrics (and across different PGS)',
    'pgs_eval': 'A list of PGS that were developed and evaluated in this publication/study',
    'pgs_eval_ext': 'A list of PGS that were developed in other publications and re-evaluated in the current study'
}

ANNOUNCEMENT = '<div class="mb-1"><h5><i class="fa-solid fa-gears bigger"></i> Available tool: <b>pgsc_calc</b></h5></div>A reproducible workflow to calculate both PGS Catalog and custom polygenic scores.<a class="ml-2 btn btn-pgs-small pgs_no_icon_link" href="https://pgsc-calc.readthedocs.io/en/latest/"><i class="fas fas fa-angle-right"></i> See more information</a></div>'

TABLE_ROWS_THRESHOLD = 1000

TRAIT_SOURCE_TO_REPLACE = ['Orphanet']

PGS_STAGES = ('gwas','dev','eval')

GENEBUILDS = ('GRCh37','GRCh38')

PGS_STAGES_HELPER = {
    'gwas': {
        'label': 'Source of Variant<br />Associations (<b>G</b>WAS)',
        'desc': 'Percentage based on the number of individuals associated with an ancestry category out of all the individuals.'
    },
    'dev': {
        'label': 'Score <b>D</b>evelopment/Training',
        'desc': 'Percentage based on the number of individuals associated with an ancestry category out of all the individuals.'
    },
    'eval': {
        'label': 'PGS <b>E</b>valuation',
        'desc': 'Percentage based on the number of Sample Set with an ancestry category out of all the Sample Sets.'
    }
}

ANCESTRY_MAPPINGS = {
    'Aboriginal Australian': 'OTH',
    'African American or Afro-Caribbean': 'AFR',
    'African unspecified' : 'AFR',
    'Asian unspecified': 'ASN',
    'Central Asian': 'ASN',
    'East Asian': 'EAS',
    'European': 'EUR',
    'Greater Middle Eastern (Middle Eastern, North African or Persian)': 'GME',
    'Hispanic or Latin American': 'AMR',
    'Native American': 'OTH',
    'Not reported': 'NR',
    'NR': 'NR', # Not reported
    'Oceanian': 'OTH',
    'Other': 'OTH',
    'Other admixed ancestry': 'OTH',
    'South Asian': 'SAS',
    'South East Asian': 'ASN',
    'Sub-Saharan African': 'AFR',
    'Sub-Saharan African, African American or Afro-Caribbean': 'AFR'
}

ANCESTRY_LABELS = {
    'MAE': 'Multi-ancestry (including European)',
    'MAO': 'Multi-ancestry (excluding European)',
    'AFR': 'African',
    'EAS': 'East Asian',
    'SAS': 'South Asian',
    'ASN': 'Additional Asian Ancestries',
    'EUR': 'European',
    'GME': 'Greater Middle Eastern',
    'AMR': 'Hispanic or Latin American',
    'OTH': 'Additional Diverse Ancestries',
    'NR' : 'Not Reported'
}

ANCESTRY_GROUP_LABELS = {
    'MAE': 'Multi-ancestry (including European)',
    'MAO': 'Multi-ancestry (excluding European)',
    'AFR': 'African Ancestry',
    'EAS': 'East Asian Ancestry',
    'SAS': 'South Asian Ancestry',
    'ASN': 'Additional Asian Ancestries',
    'EUR': 'European Ancestry',
    'GME': 'Greater Middle Eastern Ancestry',
    'AMR': 'Hispanic or Latin American Ancestry',
    'OTH': 'Additional Diverse Ancestries',
    'NR' : 'Ancestry Not Reported'
}

PGS_CONTRIBUTORS = [
    {'name': 'Sam Lambert','group': ['curators']},
    {'name': 'Laurent Gil','group': ['hdruk']},
    {'name': 'Benjamin Wingfield','group': ['ebi']},
    {'name': 'Florent Yvon','group': ['inouye']},
    {'name': 'Joel Gibson','group': ['curators','inouye']},
    {'name': 'Aoife McMahon', 'group': ['curators','nhgri-ebi']},
    {'name': 'Santhi Ramachandran','group': ['nhgri-ebi']},
    {'name': 'Elizabeth Lewis','group': ['nhgri-ebi']},
    {'name': 'Laura Harris','group': ['nhgri-ebi']},
    {'name': 'Helen Parkinson', 'group': ['spot']},
    {'name': 'Richard Houghton','group': ['hdruk']},
    {'name': 'Prof. John Danesh','group': ['hdruk']},
    {'name': 'Michael Inouye', 'group': ['inouye']}
]

PGS_GROUPS = {
    'inouye': {
        'name': 'Inouye Lab',
        'url': 'https://www.inouyelab.org/'
    },
    'curators': {
        'name': 'PGS Catalog Data Curators'
    },
    'hdruk': {
        'name': 'Health Data Research UK, Cambridge',
        'url': USEFUL_URLS['HDR_UK_CAM_URL']
    },
    'nhgri-ebi': {
        'name': 'NHGRI-EBI GWAS Catalog Team',
        'url': USEFUL_URLS['EBI_URL'] + '/gwas'
    },
    'spot': {
        'name': 'EMBL-EBI Samples Phenotypes and Ontologies Team',
        'url': USEFUL_URLS['EBI_URL'] + '/about/spot-team'
    },
    'ebi': {
        'name': 'European Bioinformatics Institute',
        'url': USEFUL_URLS['EBI_URL']
    }
}

PGS_PREVIOUS_CONTRIBUTORS = [
    {'name': 'Emily Tinsley','group': ['ebi']},
    {'name': 'Shirin Saverimuttu','group': ['ebi']},
    {'name': 'Jackie MacArthur','group': ['ebi']},
    {'name': 'Simon Jupp','group': ['ebi']},
    {'name': 'James Hayhurst','group': ['ebi']},
    {'name': 'Trish Whetzel','group': ['ebi']},
    {'name': 'Michael Chapman','group': ['hdruk']},
    {'name': 'Jonathan Marten', 'group': ['inouye']},
    {'name': 'Petar Scepanovic', 'group': ['inouye']},
    {'name': 'Gad Abraham', 'group': ['inouye']}
]
