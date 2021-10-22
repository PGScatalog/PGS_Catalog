import sys, os.path, shutil, glob
from datetime import date
import tarfile
from catalog.models import *
from release.scripts.CreateRelease import CreateRelease
from release.scripts.UpdateEFO import UpdateEFO
from release.scripts.EuropePMCLinkage import EuropePMCLinkage
from release.scripts.UpdateScoreAncestry import UpdateScoreAncestry
from release.scripts.UpdateReleasedCohorts import UpdateReleasedCohorts


error_prefix = '  /!\  Error:'
output_prefix = '  > '

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

    # Check of there are duplicated cohort names in the database
    check_duplicated_cohorts()

    # Update ancestry distribution
    update_ancestry_distribution()

    # Create release
    call_create_release()

    # Update the cohorts (update the Cohort "released" field)
    update_released_cohorts()

    # # Generate EuropePMC linkage XML file
    generate_europePMC_linkage_xml_file()


#-----------#
#  Methods  #
#-----------#

#####  DB methods  #####

def check_publications_associations():
    """ Check the publications associations """
    print("- Check the publications associations")

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
        error_report("The following PGS publications are not associated to a Score or a Performance Metric:\n"+'\n'.join(pub_list))
    else:
        output_report("Publications associations - OK: All the publications are associated to a Score or a Performance Metric!")


def check_efotrait_associations():
    """ Check the EFO Trait associations """
    print("- Check the EFO Trait associations")

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
        error_report("The following PGS EFO Traits are not associated to a Score or a Performance Metric:\n"+'\n'.join(traits_list))
    else:
        output_report("EFOTrait associations - OK: All the traits are associated to a Score or a Performance Metric!")


def check_duplicated_cohorts():
    """ Check if there are duplicated cohorts """
    print("- Check duplicated cohorts")
    cohorts_first_found = {}
    cohorts_found_lower = set()
    cohorts_duplicated = {}
    for cohort in Cohort.objects.all():
        name = cohort.name_short
        name_lower = name.lower()
        if name_lower in cohorts_found_lower:
            if name_lower not in cohorts_duplicated:
                cohorts_duplicated[name_lower] = set()
                cohorts_duplicated[name_lower].add(cohorts_first_found[name_lower])
            cohorts_duplicated[name_lower].add(name)
        else:
            cohorts_found_lower.add(name_lower)
            cohorts_first_found[name_lower] = name

    if len(cohorts_duplicated.keys()):
        error_msg = "The following cohorts seem duplicated in the database:"
        for key,val in cohorts_duplicated.items():
            error_msg += "\n\t- Cohorts: "+', '.join(list(val))
        error_report(error_msg)
    else:
        output_report("Cohort duplication - OK: No duplicated cohort found!")


def update_ancestry_distribution():
    """ Update the ancestry distribution in scores """
    print("- Update ancestry distribution")
    score_ancestry = UpdateScoreAncestry()
    score_ancestry.update_ancestry()


def call_create_release():
    """ Create a new PGS Catalog release """
    print("- Create a new PGS Catalog release")

    lastest_release = Release.objects.latest('date').date

    release = CreateRelease()
    release.update_data_to_release()
    new_release = release.create_new_release()

    # Just a bunch of prints
    output_report("Latest release: "+str(lastest_release))
    output_report("New release: "+str(new_release.date))
    output_report("Number of new Scores: "+str(new_release.score_count))
    output_report(', '.join(release.new_scores.keys()))
    output_report("Number of new Publications: "+str(new_release.publication_count))
    output_report("Number of new Performances: "+str(new_release.performance_count))

    if new_release.score_count == 0 or new_release.publication_count == 0 or new_release.performance_count == 0:
        error_report("at least one of the main components (Score, Publication or Performance Metrics) hasn't a new entry this release")


def update_released_cohorts():
    """ Update the Cohort model entries, setting the flag 'released' """
    print("- Update the Cohort model entries, setting the flag 'released'")
    released_cohorts = UpdateReleasedCohorts()
    released_cohorts.update_cohorts()


def generate_europePMC_linkage_xml_file():
    """ Generate the XML linkage file for EuropePMC """
    print("- Generate the XML linkage file for EuropePMC")
    # EuropePMC linkage (XML file)
    xml_link = EuropePMCLinkage()
    # Fetch data and generate XML file
    xml_link.generate_xml_file()
    # Print the report of the generated XML file
    xml_link.print_xml_report()


def get_previous_release_date():
    """ Fetch the previous release date (i.e. the release date of the current live database) """
    releases = Release.objects.all().order_by('-date')
    return str(releases[1].date)


def error_report(msg):
    print('  /!\  Error: '+msg)
    exit(1)

def output_report(msg):
    print('  > '+msg)
