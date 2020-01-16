from catalog.models import *
from datetime import datetime

def run():
    # Release
    lastest_release = Release.objects.latest('date')
    release_date = datetime.today().strftime('%Y-%m-%d')

    # Publications
    #publications = Publication.objects.filter(date_released__isnull=True)
    publications = Publication.objects.filter(date_released__isnull=True).exclude(curation_status="C")

    scores2del = {}
    perfs2del = {}
    pss2del = {}
    #### Removing non curated data ####
    for publication in publications:
        # Remove performances
        performances_list = Performance.objects.filter(date_released__isnull=True, publication=publication)

        for performance in performances_list:
            perfs2del[performance.id] = 1
            performance.delete()
            # Remove sample sets
            sample_set = performance.sampleset
            pss2del[sample_set.id] = 1
            sample_set.delete()
            # Remove samples
            #for sample in sample_set.samples:
                # do something


        # Remove scores
        scores_list = Score.objects.filter(date_released__isnull=True, publication=publication)
        for score in scores_list:
            scores2del[score.id] = 1
            score.delete()
            # Remove samples (variants)
            #for sample_v in score.samples_variants:
                # do something
                #print("\tVARIANT: "+sample_v.name)
                # e.g. score.samples_variants.through.objects.filter(score_id=score.id).delete()

            # Remove samples (training)
            #for sample_t in score.samples_training:
                # do something
                #print("\tTRAINING: "+sample_t.name)

            # Remove traits
            #for trait in score.trait_efo:
                # do something
                #print("\tTRAIT: "+trait.label)

            # Delete Score - This should delete the Performance(s) and Metric(s)as well


    print("Latest release: "+str(lastest_release.date))
    print("New release: "+str(release_date))
    print("Number of non curated Publications: "+str(publications.count()))
    print("Number of Scores to remove: "+str(len(scores2del.keys())))
    print( ' - '+'\n - '.join(scores2del.keys()))
    print("Number of Performances to remove : "+str(len(perfs2del.keys())))
    print( ' - '+'\n - '.join(perfs2del.keys()))
    print("Number of Sample Sets to remove: "+str(len(pss2del.keys())))
    print( ' - '+'\n - '.join(pss2del.keys()))
