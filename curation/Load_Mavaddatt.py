from curation.tools import *
from catalog.models import *

Metric.objects.all().delete()
Performance.objects.all().delete()
Sample.objects.all().delete()
Score.objects.all().delete()

loc_curation2schema = './curation/v3_SourceFiles/Templates/TemplateColumns2Models_v3.xlsx'
curation2schema = pd.read_excel(loc_curation2schema, index_col = 0)

loc_localGWAS = './curation/local_GWASCatalog/'
gwas_studies, gwas_samples = load_GWAScatalog(loc_localGWAS)
gwas_studies.set_index('STUDY ACCESSION', inplace = True)
gwas_samples.set_index('STUDY ACCCESSION', inplace = True)
gwas_samples = gwas_samples[gwas_samples['STAGE'] == 'initial'] # Get rid of replication studies


c_2015 = CurationTemplate()
c_2015.file_loc  = './curation/v3_SourceFiles/Mavaddat2015.xlsx'
c_2015.read_curation()
c_2015.table_mapschema = curation2schema
c_2015.extract_publication()
c_2015.extract_scores()
c_2015.extract_samples(gwas_samples)
c_2015.extract_performances()

#Save Scores
saved_scores = {}
for score_id, fields in c_2015.parsed_scores.items():
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
for x in c_2015.parsed_samples_scores:
    i, l = x
    current_score = saved_scores[i[0]]
    for fields in l:
        current_sample = Sample()
        for f, val in fields.items():
            setattr(current_sample, f, val)
        current_sample.save()
        if i[1] == 'GWAS/Variant associations':
            current_score.samples_variants.add(current_sample)
        elif i[1] == 'Score development':
            current_score.samples_training.add(current_sample)
        else:
            print('ERROR: Unclear how to add samples')

# Create testing sample sets
testset_to_PSS = {}
for x in c_2015.parsed_samples_testing:
    i, l = x
    sample_id = next_PSS_num()
    for fields in l:
        current_sample = Sample()
        current_sample.set_sample_ids(sample_id)
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
            else:
                setattr(current_sample, f, val)
        current_sample.save()
        for cohort in cohorts_toadd:
            current_sample.cohorts.add(cohort)
        testset_to_PSS[i] = current_sample.PSS_id

# Load + link performance
for x in c_2015.parsed_performances:
    i, fields = x
    current_score = saved_scores[i[0]]
    related_PSS_id = testset_to_PSS[i[1]]
    current_performance = Performance(publication=c_2015.parsed_publication, score = current_score, sampleset_id = related_PSS_id)
    for f, val in fields.items():
        if f not in ['publication', 'metrics']:
            setattr(current_performance, f, val)
    current_performance.set_score_ids(next_scorenumber(Performance))
    current_performance.save()

    # Parse metrics
    for m in fields['metrics']:
        current_metric = Metric(performance=current_performance)
        for f, val in m.items():
            setattr(current_metric, f, val)
        current_metric.save()




#############################
c_2019 = CurationTemplate()
c_2019.file_loc  = './curation/v3_SourceFiles/Mavaddat2019.xlsx'
c_2019.read_curation()
c_2019.table_mapschema = curation2schema
c_2019.extract_publication()
c_2019.extract_scores()
c_2019.extract_samples(gwas_samples)
c_2019.extract_performances()

for score_id, fields in c_2019.parsed_scores.items():
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
for x in c_2019.parsed_samples_scores:
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
testset_to_PSS = {}
for x in c_2019.parsed_samples_testing:
    i, l = x
    sample_id = next_PSS_num()
    for fields in l:
        current_sample = Sample()
        current_sample.set_sample_ids(sample_id)
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
            else:
                setattr(current_sample, f, val)
        current_sample.save()
        for cohort in cohorts_toadd:
            current_sample.cohorts.add(cohort)
        testset_to_PSS[i] = current_sample.PSS_id

for x in c_2019.parsed_performances:
    i, fields = x
    if i[0] in saved_scores:
        current_score = saved_scores[i[0]]
    else:
        current_score = Score.objects.get(id = i[0])
    related_PSS_id = testset_to_PSS[i[1]]
    current_performance = Performance(publication=c_2019.parsed_publication, score = current_score, sampleset_id = related_PSS_id)
    for f, val in fields.items():
        if f not in ['publication', 'metrics']:
            setattr(current_performance, f, val)
    current_performance.set_score_ids(next_scorenumber(Performance))
    current_performance.save()
    # Parse metrics
    for m in fields['metrics']:
        current_metric = Metric(performance=current_performance)
        for f, val in m.items():
            setattr(current_metric, f, val)
        current_metric.save()