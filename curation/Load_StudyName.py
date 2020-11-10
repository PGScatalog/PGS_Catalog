from curation.tools import *
from catalog.models import *
import os, gzip
import numpy as np

skip_scorefiles = False

loc_curation2schema = '../pgs_DBSourceFiles/Templates/TemplateColumns2Models_v6.xlsx'
curation2schema = pd.read_excel(loc_curation2schema, index_col = 0)

loc_curation2schema_scoring = '../pgs_DBSourceFiles/Templates/ScoringFileSchema.xlsx'
curation2schema_scoring = pd.read_excel(loc_curation2schema_scoring, index_col = 0)

loc_localGWAS = '../pgs_DBSourceFiles/local_GWASCatalog/'
gwas_studies, gwas_samples = load_GWAScatalog(loc_localGWAS, update=True)
gwas_studies.set_index('STUDY ACCESSION', inplace=True)
gwas_samples.set_index('STUDY ACCESSION', inplace=True)
gwas_samples = gwas_samples[gwas_samples['STAGE'] == 'initial'] # Get rid of replication studies

# StudyNames = ['Mavaddat2015','Mavaddat2019',
#               'Mega2015', 'Tada2016', 'Abraham2016',
#               'Khera2018', 'Inouye2018', 'Wunnemann2019', 'Paquette2017', 'Lall2017',
#               'Oram2016', 'Perry2018', 'Onengut-Gumuscu2019', 'Sharp2019', 'Chouraki2016',
#               'Desikan2017', 'Khera2019', 'Shieh2016', 'Schumacher2018', 'Vassy2014', 'Song2018',
#               'Weng2018', 'Mahajan2018', 'Udler2019', 'Belsky2013', 'RuttenJacobs2019', 'Abraham2019',
#               'Abraham2014', 'Abraham2015',
#               'Klarin2019','Pashayan2015a_GIM', 'Pashayan2015b_BRJ',
#               'Kuchenbaecker2017', 'Lecarpentier2018',
#               'Wen2016', 'Zhang2018', 'Lakeman2019', 'Patel2016', 'Tosto2017', 'Schmit2018','Paul2018',
#               'Natarajan2017', 'Morieri2018', 'Hajek2018',
#               'Johnson2015', 'Kuchenbaecker2019', 'Seibert2018', 'Yang2018', 'Dai2019', 'Graff2020',
#               'Xu2020', 'Canovas2020',
#               'Trinder2020', 'Elliott2020',
#               'Fritsche2019', 'HoLe2016', 'Homburger2019', 'Huynh-Le2019', 'Ibanez2017', 'Khera2019_VIRGO',
#               'MacGregor2018', 'Qi2017', 'Tin2019', 'Wheeler2017', 'Zheutlin2019', 'Craig2020',
#               'Cai2020', 'Hsu2015', 'IbanezSanz2017','Jeon2018', 'Smith2018', 'Weigl2018', 'Xin2018', 'Shi2019', 'Khera2016', 'Timmerman2019',
#               'Vuckovic2020', 'Kathiresan2008', 'Coleman2020', 'Knevel2019', 'Tikkanen2013', 'Dikilitas2020',
#               'Barr2020', 'Liyanarachchi2020', 'Shrine2019', 'Pihlstrøm2016', 'Zhang2020', ''Folkersen2020', 'Wang2020', 'Ferrat2020'
#               'Xie2020', 'Sharp2020''Shieh2020', ''Meisner2020', 'Chami2020', 'Flynn2020', 'Grove2019', 'Reid2019', 'Mars2020', 'Zhang2020_NatComm', 'Mars2020_BC']
# Loaded_v6 = ['Maukonen2020', 'Koyama2020', 'Kloosterman2020']

StudyNames = ['Law2020']

#Loop through studies to be included/loaded
for StudyName in StudyNames:
    print(StudyName)
    current_study = CurationTemplate()
    current_study.file_loc  = '../pgs_DBSourceFiles/{}/{}.xlsx'.format(StudyName,StudyName)
    current_study.read_curation()
    current_study.table_mapschema = curation2schema
    current_study.extract_publication()
    current_study.extract_scores()
    current_study.extract_samples(gwas_samples)
    current_study.extract_performances()

    saved_scores = {}

    for score_id, fields in current_study.parsed_scores.items():
        current_score = Score()
        current_score.set_score_ids(next_scorenumber(Score))
        for f, val in fields.items():
            if f == 'publication':
                current_score.publication = Publication.objects.get(id = val)
            elif f == 'trait_efo':
                efos_toadd = []
                for tid in val:
                    try:
                        efo = EFOTrait.objects.get(id=tid)
                    except:
                        efo = EFOTrait(id=tid)
                        efo.parse_api()
                        efo.save()
                    efos_toadd.append(efo)
            else:
                setattr(current_score, f, val)
        current_score.save()
        for efo in efos_toadd:
            current_score.trait_efo.add(efo)
        current_score.save()
        saved_scores[score_id] = current_score

    # Attach Samples 2 Scores
    for x in current_study.parsed_samples_scores:
        scores = []
        for s in x[0][0].split(','):
            scores.append(saved_scores[s.strip()])
        samples = x[1]
        for current_score in scores:
            if type(samples) == dict:
                samples = [samples]
            for fields in samples:
                current_sample = Sample()
                cohorts_toadd = []
                for f, val in fields.items():
                    if f == 'cohorts':
                        for name_short, name_full in val:
                            try:
                                cohort = Cohort.objects.get(name_short=name_short, name_full=name_full)
                            except:
                                cohort = Cohort(name_short=name_short, name_full=name_full)
                                cohort.save()
                            cohorts_toadd.append(cohort)
                    elif f in ['sample_age', 'followup_time']:
                        current_demographic = Demographic(**val)
                        current_demographic.save()
                        setattr(current_sample, f, current_demographic)
                    else:
                        setattr(current_sample, f, val)
                current_sample.save()
                for cohort in cohorts_toadd:
                    current_sample.cohorts.add(cohort)
                if x[0][1] == 'GWAS/Variant associations':
                    current_score.samples_variants.add(current_sample)
                elif x[0][1] == 'Score development':
                    current_score.samples_training.add(current_sample)
                else:
                    print('ERROR: Unclear how to add samples')

    # Create testing sample sets
    testset_to_sampleset = {}
    for x in current_study.parsed_samples_testing:
        test_name, sample_list = x

        # Initialize the current SampleSet
        current_sampleset = SampleSet()
        current_sampleset.set_ids(next_PSS_num())
        current_sampleset.save()

        # Attach underlying sample(s) and their descriptions to the SampleSet
        for sample_desc in sample_list:
            current_sample = Sample()
            cohorts_toadd = []
            for f, val in sample_desc.items():
                if f == 'cohorts':
                    for name_short, name_full in val:
                        try:
                            cohort = Cohort.objects.get(name_short=name_short, name_full=name_full)
                        except:
                            cohort = Cohort(name_short=name_short, name_full=name_full)
                            cohort.save()
                        cohorts_toadd.append(cohort)
                elif f in ['sample_age', 'followup_time']:
                    current_demographic = Demographic(**val)
                    current_demographic.save()
                    setattr(current_sample, f, current_demographic)
                else:
                    setattr(current_sample, f, val)
            current_sample.save()

            # Add cohort(s) to the sample
            for cohort in cohorts_toadd:
                current_sample.cohorts.add(cohort)
            current_sample.save()

            # Add sample to the SampleSet
            current_sampleset.samples.add(current_sample)
        current_sampleset.save()
        testset_to_sampleset[test_name] = current_sampleset

    for x in current_study.parsed_performances:
        i, fields = x
        if i[0] in saved_scores:
            current_score = saved_scores[i[0]]
        else:
            current_score = Score.objects.get(id = i[0])
        related_SampleSet = testset_to_sampleset[i[1]]
        current_performance = Performance(publication=current_study.parsed_publication, score = current_score, sampleset = related_SampleSet)
        for f, val in fields.items():
            if f not in ['publication', 'metrics']:
                setattr(current_performance, f, val)
        current_performance.set_performance_id(next_scorenumber(Performance))
        current_performance.save()
        # Parse metrics
        for m in fields['metrics']:
            current_metric = Metric(performance=current_performance)
            for f, val in m.items():
                setattr(current_metric, f, val)
            current_metric.save()

    # Read the PGS and re-format with header information
    if skip_scorefiles == False:
        for score_id, current_score in saved_scores.items():
            try:
                loc_scorefile = '../pgs_DBSourceFiles/{}/raw_scores/{}.txt'.format(StudyName, score_id)
                #print('reading scorefile: {}', loc_scorefile)
                df_scoring = pd.read_table(loc_scorefile, dtype='str', engine = 'python')
                # Check that columns are in the schema
                column_check = [x in curation2schema_scoring.index for x in df_scoring.columns]
                if all(column_check):
                    header = create_scoringfileheader(current_score)

                    #Check if weight_type in columns
                    if 'weight_type' in df_scoring.columns:
                        if all(df_scoring['weight_type']):
                            val = df_scoring['weight_type'][0]
                            if val == 'OR':
                                df_scoring = df_scoring.rename({'effect_weight' : 'OR'}, axis='columns').drop(['weight_type'], axis=1)
                    if 'effect_weight' not in df_scoring.columns:
                        if 'OR' in df_scoring.columns:
                            df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['OR']))
                            df_scoring['weight_type'] = 'log(OR)'
                        elif 'HR' in df_scoring.columns:
                            df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['HR']))
                            df_scoring['weight_type'] = 'log(HR)'

                    # Reorganize columns according to schema
                    corder = []
                    for x in curation2schema_scoring.index:
                        if x in df_scoring.columns:
                            corder.append(x)
                    df_scoring = df_scoring[corder]

                    with gzip.open('ScoringFiles/{}.txt.gz'.format(current_score.id), 'w') as outf:
                        outf.write('\n'.join(header).encode('utf-8'))
                        outf.write('\n'.encode('utf-8'))
                        outf.write(df_scoring.to_csv(sep='\t', index=False).encode('utf-8'))
                else:
                    badmaps = []
                    for i, v in enumerate(column_check):
                        if v == False:
                            badmaps.append(df_scoring.columns[i])
                    print('Error in {} ! bad columns: {}', loc_scorefile, badmaps)
            except:
                print('ERROR reading scorefile: {}', loc_scorefile)
