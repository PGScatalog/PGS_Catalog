import sys, os.path, shutil, glob
from datetime import date
import tarfile
from catalog.models import *
from release.scripts.CreateRelease import CreateRelease
from release.scripts.UpdateEFO import UpdateEFO
from release.scripts.GenerateBulkExport import PGSExportAllMetadata
from release.scripts.PGSExport import PGSExport
from release.scripts.PGSBuildFtp import PGSBuildFtp


def run(*args):
    """
        Main method executed by the Django command:
        `python manage.py runscript run_release_script`
    """

    today = date.today()

    previous_release_date = get_previous_release_date()

    #--------------#
    #  DB release  #
    #--------------#
    print("# Start the database release")

    # Check that the publications are associated to at least a Score or a Performance Metric
    check_publications_associations()

    # Check that the EFO Traits are associated to at least a Score or a Performance Metric
    check_efotrait_associations()

    # Create release
    call_create_release()


#-----------#
#  Methods  #
#-----------#

#####  DB methods  #####

def check_publications_associations():
    """ Check the publications associations """
    print("\t- Check the publications associations")

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


def check_efotrait_associations():
    """ Check the EFO Trait associations """
    print("\t- Check the EFO Trait associations")

    efo_traits = EFOTrait.objects.all().order_by('id')
    traits_list = []

    for efo_trait in efo_traits:
        trait_id = efo_trait.id
        is_associated = 0
        if Score.objects.filter(trait_efo__in=[efo_trait]):
            is_associated = 1
        elif Performance.objects.filter(phenotyping_efo__in=[efo_trait]):
            is_associated = 1
        if not is_associated:
            traits_list.append(trait_id)

    if len(traits_list) > 0:
        print("ERROR: The following PGS EFO Traits are not associated to a Score or a Performance Metric:\n"+'\n'.join(traits_list))
        exit(1)
    else:
        print("EFOTrait associations - OK: All the traits are associated to a Score or a Performance Metric!")


def call_create_release():
    """ Create a new PGS Catalog release """
    print("\t- Create a new PGS Catalog release")

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

    if new_release.score_count == 0 or new_release.publication_count == 0 or new_release.performance_count == 0:
        print("Error: at least one of the main components (Score, Publication or Performance Metrics) hasn't a new entry this release")
        exit(1)


def get_previous_release_date():
    """ Fetch the previous release date (i.e. the release date of the current live database) """
    releases = Release.objects.all().order_by('-date')
    return str(releases[1].date)
