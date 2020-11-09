import pandas as pd
import requests
from catalog.models import *
import re
from psycopg2.extras import NumericRange



class CurationTemplate():
    def __init__(self):
        self.file_loc = None
        self.parsed_publication = None
        self.parsed_scores = {}
        self.parsed_samples_scores = []
        self.parsed_samples_testing = []
        self.parsed_performances = []
        self.table_mapschema = None

    def read_curation(self):
        '''ReadCuration takes as input the location of a study metadata file'''
        loc_excel = self.file_loc
        if loc_excel != None:
            self.table_publictation =  pd.read_excel(loc_excel, sheet_name='Publication Information', header=0, index_col=0)

            self.table_scores = pd.read_excel(loc_excel, sheet_name='Score(s)', header=[0, 1], index_col=0)

            self.table_samples = pd.read_excel(loc_excel, sheet_name='Sample Descriptions', header=0)
            # Parse to separate tables
            self.table_samples_scores = self.table_samples[self.table_samples.iloc[:,1] != 'Testing ']
            self.table_samples_scores.set_index(list(self.table_samples_scores.columns[[0, 1]]), inplace = True)
            self.table_samples_testing = self.table_samples[self.table_samples.iloc[:, 1] == 'Testing ']
            self.table_samples_testing.set_index(list(self.table_samples_testing.columns[[2]]), inplace=True)

            self.table_performances = pd.read_excel(loc_excel, sheet_name='Performance Metrics', header=[0,1], index_col=[0, 1])
            self.table_cohorts = pd.read_excel(loc_excel, sheet_name='Cohort Refr.', header=0, index_col=0)

    def extract_publication(self):
        '''parse_pub takes a curation dictionary as input and extracts the relevant info from the sheet and EuropePMC'''
        #current_schema = self.table_mapschema.loc['Publication Information'].set_index('Column')
        pinfo = self.table_publictation.iloc[0]
        c_doi = pinfo['doi']
        c_PMID = pinfo[0]

        # Check if this is already in the DB
        db_check = Publication.objects.filter(doi=c_doi)
        if len(db_check) == 1:
            parsed_publication = db_check[0]
        else:
            # Get data from europepmc
            try:
                payload = {'format' : 'json'}
                payload['query'] = 'doi:' + c_doi
                r = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
                r = r.json()
                r = r['resultList']['result'][0]
            except:
                payload = {'format': 'json'}
                payload['query'] = ['ext_id:' + str(c_PMID)]
                r = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
                r = r.json()
                r = r['resultList']['result'][0]

            if r['pubType'] == 'preprint':
                parsed_publication = Publication(doi = r['doi'],
                                                 journal = r['bookOrReportDetails']['publisher'],
                                                 firstauthor = r['authorString'].split(',')[0],
                                                 authors = r['authorString'],
                                                 title = r['title'],
                                                 date_publication = r['firstPublicationDate']
                                                )
            else:
                parsed_publication = Publication(doi = r['doi'],
                                                 PMID = r['pmid'],
                                                 journal = r['journalTitle'],
                                                 firstauthor = r['authorString'].split(',')[0],
                                                 authors = r['authorString'],
                                                 title = r['title'],
                                                 date_publication = r['firstPublicationDate']
                                            )
            parsed_publication.set_publication_ids(next_scorenumber(Publication))
            if self.table_publictation.shape[0] > 1:
                parsed_publication.curation_notes = self.table_publictation.iloc[1,0]
            parsed_publication.save()
        self.parsed_publication = parsed_publication

    def extract_scores(self):
        current_schema = self.table_mapschema.loc['Score(s)'].set_index('Column')
        for score_name, score_info in self.table_scores.iterrows():
            parsed_score = {'name' : score_name, 'publication' : self.parsed_publication.id}
            for col, val in score_info.iteritems():
                if pd.isnull(val) == False:
                    # Map to schema
                    if col[1] in current_schema.index:
                        m, f, _ = current_schema.loc[col[1]]
                    elif col[0] in current_schema.index:
                        m, f, _ = current_schema.loc[col[0]]
                    else:
                        m = None

                    # Add to extract if it's the same model
                    if m == 'Score':
                        if f == 'trait_efo':
                            efo_list = val.split(',')
                            parsed_score[f] = efo_list
                        else:
                            parsed_score[f] = val
            self.parsed_scores[score_name] = parsed_score

    def cohort_to_tuples(self, cstring):
        cohort_df = self.table_cohorts
        clist = []
        for cname in cstring.split(','):
            cname = cname.strip()
            if cname in cohort_df.index:
                clist.append((cname, cohort_df.loc[cname][0]))
            else:
                clist.append((cname, 'UNKNOWN'))
        return clist


    def extract_samples(self, gwas):
        current_schema = self.table_mapschema.loc['Sample Descriptions'].set_index('Column')

        # Extract data for training (GWAS + Score Development) sample
        for sample_ids, sample_info in self.table_samples_scores.iterrows():
            sample_remapped = {}
            for c, val in sample_info.to_dict().items():
                if c in current_schema.index:
                    if pd.isnull(val) == False:
                        f = current_schema.loc[c, 'Field']
                        if f == 'cohorts':
                            val = self.cohort_to_tuples(val)
                        elif f in ['sample_age', 'followup_time']:
                            val = str2demographic(val)

                        sample_remapped[f] = val
            # Parse from GWAS Catalog
            if ('sample_number' not in sample_remapped.keys()):
                if ('source_GWAS_catalog' in sample_remapped) and (sample_remapped['source_GWAS_catalog'] in gwas.index):
                    gwas_results = []
                    gwas_ss = gwas[gwas.index == sample_remapped['source_GWAS_catalog']]
                    for sid, ss in gwas_ss.iterrows():
                        c_sample = sample_remapped.copy()
                        for c, f in remap_gwas_model.items():
                            val = ss[c]
                            if pd.isnull(val) == False:
                                c_sample[f] = val
                        gwas_results.append(c_sample)
                    sample_remapped = gwas_results
            self.parsed_samples_scores.append((sample_ids, sample_remapped))

        # Extract data Testing samples
        for testset_name, testsets in self.table_samples_testing.groupby(level=0):
            results = []
            for sample_ids, sample_info in testsets.iterrows():
                sample_remapped = {}
                for c, val in sample_info.to_dict().items():
                    if c in current_schema.index:
                        if pd.isnull(val) == False:
                            f = current_schema.loc[c, 'Field']
                            if pd.isnull(f) == False:
                                if f == 'cohorts':
                                    val = self.cohort_to_tuples(val)
                                elif f in ['sample_age', 'followup_time']:
                                    val = str2demographic(val)

                                sample_remapped[f] = val
                results.append(sample_remapped)
            self.parsed_samples_testing.append((testset_name, results))

    def extract_performances(self):
        current_schema = self.table_mapschema.loc['Performance Metrics'].set_index('Column')
        for p_key, performance_info in self.table_performances.iterrows():
            parsed_performance = {'publication': self.parsed_publication.id,
                                  'metrics': []
            }
            for col, val in performance_info.iteritems():
                if pd.isnull(val) == False:
                    m = None
                    if col[1] in current_schema.index:
                        m, f, _ = current_schema.loc[col[1]]
                    elif col[0] in current_schema.index:
                        m, f, _ = current_schema.loc[col[0]]

                    if m is not None:
                        if f.startswith('metric'):
                            try:
                                parsed_performance['metrics'].append(str2metric(f, val))
                            except:
                                if ';' in val:
                                    for x in val.split(';'):
                                        parsed_performance['metrics'].append(str2metric(f, x))
                                else:
                                    print('Error parsing:', f, val)
                        else:
                            parsed_performance[f] = val
            self.parsed_performances.append((p_key,parsed_performance))


def load_GWAScatalog(outdir, update = False):
    dl_files = ['studies_ontology-annotated', 'ancestry']
    o = []
    for fn in dl_files:
        loc_local = '%s/gwas-catalog-%s.csv' % (outdir, fn)
        if outdir.endswith('/'):
            loc_local = outdir + 'gwas-catalog-%s.csv' %fn
        if update:
            print('Downloading: %s'%fn)
            df = pd.read_table('ftp://ftp.ebi.ac.uk/pub/databases/gwas/releases/latest/gwas-catalog-%s.tsv'%fn, index_col= False, sep = '\t')
            df.to_csv(loc_local, index = False)
        else:
            df = pd.read_csv(loc_local, index_col=False)
        o.append(df)
    return o

def next_scorenumber(obj):
    assigned = 1
    if len(obj.objects.all()) != 0:
        assigned = obj.objects.latest().pk + 1
    return assigned

def next_PSS_num():
    r = SampleSet.objects.last()
    if r == None:
        return 1
    else:
        return r.num + 1


remap_gwas_model = { 'PUBMEDID' : 'source_PMID',
                     'NUMBER OF INDIVDUALS' : 'sample_number',
                     'BROAD ANCESTRAL CATEGORY' : 'ancestry_broad',
                     'COUNTRY OF ORIGIN' : 'ancestry_free',
                     'COUNTRY OF RECRUITMENT' : 'ancestry_country',
                     'ADDITONAL ANCESTRY DESCRIPTION' : 'ancestry_additional'
                     }

# Needed for parsing confidence intervals
insquarebrackets = re.compile('\\[([^)]+)\\]')
inparentheses = re.compile('\((.*)\)')


def str2metric(field, val):
    _, ftype, fname = field.split('_')

    # Find out what type of metric it is
    ftype_choices = {
        'other' : 'Other Metric',
        'beta'  : 'Effect Size',
        'class' : 'Classification Metric'
    }
    current_metric = {'type': ftype_choices[ftype]}

    # Find out if it's a common metric and stucture the information
    fname_common = {
        'OR': ('Odds Ratio', 'OR'),
        'HR': ('Hazard Ratio', 'HR'),
        'AUROC': ('Area Under the Receiver-Operating Characteristic Curve', 'AUROC'),
        'Cindex': ('Concordance Statistic', 'C-index'),
        'R2': ('Proportion of the variance explained', 'R²'),
    }
    if fname in fname_common:
        current_metric['name'] = fname_common[fname][0]
        current_metric['name_short'] = fname_common[fname][1]
    elif (ftype == 'beta') and (fname == 'other'):
        current_metric['name'] = 'Beta'
        current_metric['name_short'] = 'β'
    else:
        fname, val = val.split('=')
        current_metric['name'] = fname.strip()

    # Parse out the confidence interval and estimate
    if type(val) == float:
        current_metric['estimate'] = val
    else:
        matches_square = insquarebrackets.findall(val)
        #Check if an alternative metric has been declared
        if '=' in val:
            mname, val = [x.strip() for x in val.split('=')]
            # Check if it has short + long name
            matches_parentheses = inparentheses.findall(mname)
            if len(matches_parentheses) == 1:
                current_metric['name'] = mname.split('(')[0]
                current_metric['name_short'] = matches_parentheses[0]

        #Check if SE is reported
        matches_parentheses = inparentheses.findall(val)
        if len(matches_parentheses) == 1:
            val = val.split('(')[0].strip()
            try:
                current_metric['estimate'] = float(val)
            except:
                val, unit = val.split(" ", 1)
                current_metric['estimate'] = float(val)
                current_metric['unit'] = unit
            current_metric['se'] = matches_parentheses[0]

        elif len(matches_square) == 1:
            current_metric['estimate'] = float(val.split('[')[0])
            ci_match = tuple(map(float, matches_square[0].split(' - ')))
            current_metric['ci'] = NumericRange(lower=ci_match[0], upper=ci_match[1], bounds='[]')
        else:
            current_metric['estimate'] = float(val.split('[')[0])

    return current_metric

def str2demographic(val):
    current_demographic = {}
    if type(val) == float:
        current_demographic['estimate'] = val
    else:
        #Split by ; in case of multiple sub-fields
        l = val.split(';')
        for x in l:
            name, value = x.split('=')
            name = name.strip()
            value = value.strip()

            # Check if it contains a range item
            matches = insquarebrackets.findall(value)
            if len(matches) == 1:
                range_match = tuple(map(float, matches[0].split(' - ')))
                current_demographic['range'] = NumericRange(lower=range_match[0], upper=range_match[1], bounds='[]')
                current_demographic['range_type'] = name.strip()
            else:
                if name.lower().startswith('m'):
                    current_demographic['estimate_type'] = name.strip()
                    with_units = re.match("([-+]?\d*\.\d+|\d+) ([a-zA-Z]+)", value, re.I)
                    if with_units:
                        items = with_units.groups()
                        current_demographic['estimate'] = items[0]
                        current_demographic['unit'] = items[1]
                    else:
                        current_demographic['estimate'] = value

                elif name.lower().startswith('s'):
                    current_demographic['variability_type'] = name.strip()
                    with_units = re.match("([-+]?\d*\.\d+|\d+) ([a-zA-Z]+)", value, re.I)
                    if with_units:
                        items = with_units.groups()
                        current_demographic['variability']  = items[0]
                        current_demographic['unit'] = items[1]
                    else:
                        current_demographic['variability'] = value
    #print(val, current_demographic)
    return current_demographic


def create_scoringfileheader(cscore):
    """Function to extract score & publication information for the PGS Catalog Scoring File commented header"""
    pub = cscore.publication
    lines = [
        '### PGS CATALOG SCORING FILE - see www.pgscatalog.org/downloads/#dl_ftp for additional information',
        '## POLYGENIC SCORE (PGS) INFORMATION',
        '# PGS ID = {}'.format(cscore.id),
        '# Reported Trait = {}'.format(cscore.trait_reported),
        '# Original Genome Build = {}'.format(cscore.variants_genomebuild),
        '# Number of Variants = {}'.format(cscore.variants_number),
        '## SOURCE INFORMATION',
        '# PGP ID = {}'.format(pub.id),
        '# Citation = {} et al. {} ({}). doi:{}'.format(pub.firstauthor, pub.journal, pub.date_publication.strftime('%Y'), pub.doi)
    ]
    if cscore.license != Score._meta.get_field('license')._get_default():
        ltext = cscore.license.replace('\n', ' ')  # Make sure there are no new-lines that would screw up the commenting
        lines.append('# LICENSE = {}'.format(ltext))  # Append to header
    return lines
