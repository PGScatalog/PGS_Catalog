import sys, os.path
from release.scripts.CreateRelease import CreateRelease
from release.scripts.UpdateEFO import *
from release.scripts.UpdateGWASSamples import *
from catalog.models import *

def run():

    # Check that the publications are associated to at least a Score or a Performance Metric
    check_publications_associations()

    # Create release
    call_create_release()

    # Update EFO data
    call_efo_update()

    # Update/add GWAS data
    ##call_gwas_update()


def check_publications_associations():
    """ Check the publications associations """

    publications = Publication.objects.all().order_by('num')
    pub_list = []

    for publication in publications:
        pub_id = publication.id
        is_associated = 0
        if Score.objects.filter(publication=publication):
            is_associated = 1
        elif Performance.objects.filter(publication=publication):
            is_associated = 1
        if not is_associated:
            pub_list.append(pub_id)

    if len(pub_list) > 0:
        print("ERROR: The following PGS publications are not associated to a Score or a Performance Metric:\n"+'\n'.join(pub_list))
        exit(1)
    else:
        print("Publications associations - OK: All the publications are associated to a Score or a Performance Metric!")


def call_create_release():
    """ Create release """

    lastest_release = Release.objects.latest('date').date

    release = CreateRelease()
    release.update_data_to_release()
    new_release = release.create_new_release()

    # Just a bunch of prints
    print("Latest release: "+str(lastest_release))
    print("New release: "+str(new_release.date))
    print("Number of new Scores: "+str(new_release.score_count))
    print(', '.join(release.new_scores.keys()))
    print("Number of new Publications: "+str(new_release.publication_count))
    print("Number of new Performances: "+str(new_release.performance_count))

    # Scores
    scores_direct = Score.objects.filter(date_released__isnull=True)

    # Performances
    perfs_direct = Performance.objects.filter(date_released__isnull=True)

    print("Number of new Scores (direct fetch): "+str(scores_direct.count()))
    print("Number of new Performances (direct fetch): "+str(perfs_direct.count()))


def call_efo_update():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog)."""
    for trait in EFOTrait.objects.all():
        update_efo_info(trait)
        update_efo_category_info(trait)


def call_gwas_update():
    """ Update the GWAS study entries."""
    for sample in Sample.objects.all():
        if sample.source_GWAS_catalog:
            get_gwas_info(sample.source_GWAS_catalog)
