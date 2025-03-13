from django.db.models import Count
from catalog.models import *
from release.scripts.RemoveDataForRelease import NonReleasedDataToRemove
from release.scripts.OnlyUpdateEFOAssociations import OnlyUpdateEFOAssociations
from release.scripts.UpdateScoreAncestry import UpdateScoreAncestry
from release.scripts.UpdateScoreEvaluated import UpdateScoreEvaluated
from release.scripts.UpdateReleasedCohorts import UpdateReleasedCohorts
from release.scripts.UpdateEFO import UpdateEFO


def run(*args):
    """
        Main method executed by the Django command:
        `python manage.py runscript run_post_processing_script`
    """

    #----------------------#
    #  DB post processing  #
    #----------------------#
    print("\n#### Start the database post-processing ####")

    # Cleanup the database: remove data for the non-released studies and add embargoed studies
    remove_data_for_release()

    # Update ancestry distribution
    update_ancestry_distribution()

    # Update list of evaluated scores
    update_score_evaluated()

    # Update the cohorts (update the Cohort "released" field)
    update_released_cohorts()

    if 'update_efo_associations_only' in args:
        # Simply update trait associations without rebuilding the ontology
        update_efo_associations_only()
    else:
        # Update the trait information and ontology
        update_efo()

    # Display the list of new EFO traits in the catalog
    display_new_efo()


#-----------#
#  Methods  #
#-----------#

def remove_data_for_release():
    """ Remove the data not yet ready for the release """
    report_header("Remove non released data")
    data2remove = NonReleasedDataToRemove()
    data2remove.remove_non_released_data()


def update_ancestry_distribution():
    """ Update the ancestry distribution in scores """
    report_header("Update ancestry distribution")
    score_ancestry = UpdateScoreAncestry()
    score_ancestry.update_ancestry()


def update_score_evaluated():
    """ Update list of evaluated scores """
    report_header("Update list of evaluated scores")
    score_evaluated = UpdateScoreEvaluated()
    score_evaluated.update_score_evaluated()


def update_released_cohorts():
    """ Update the Cohort model entries, setting the flag 'released' """
    report_header("Update the Cohort model entries, setting the flag 'released'")
    released_cohorts = UpdateReleasedCohorts()
    released_cohorts.update_cohorts()


def update_efo():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog) """
    report_header("Update the EFO entries and add/update the Trait categories (from GWAS Catalog)")
    update_efo = UpdateEFO()
    update_efo.launch_efo_updates()


def update_efo_associations_only():
    """ Skipping EFO rebuilding, just adding scores and traits associations """
    report_header("Skipping EFO rebuilding, just adding scores and traits associations.")
    update_efo_associations = OnlyUpdateEFOAssociations()
    update_efo_associations.add_efo_trait_associations()
    

def display_new_efo():
    """ Display the list of new Traits added with the new release """
    new_release = Release.objects.latest('date').date
    trait_ids_list = Score.objects.values_list('trait_efo__id', flat=True).filter(date_released=new_release).distinct()
    scores_by_trait_list = (Score.objects.filter(trait_efo__id__in=trait_ids_list)
        .values('trait_efo__id','trait_efo__label')
        .annotate(count_scores=Count('id'))
    )
    new_traits = []
    for scores_by_trait in scores_by_trait_list:
        count_scores = scores_by_trait['count_scores']
        if count_scores == 1:
            new_traits.append(f"- {scores_by_trait['trait_efo__label']} ({scores_by_trait['trait_efo__id']})")
    print(f"# {len(new_traits)} New Traits:")
    for new_trait in new_traits:
        print(new_trait)


def report_header(msg):
    print('\n# '+msg)
