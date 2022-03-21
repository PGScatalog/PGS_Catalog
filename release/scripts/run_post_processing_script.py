import sys, os.path, shutil, glob
from catalog.models import *
from release.scripts.RemoveDataForRelease import NonReleasedDataToRemove
from release.scripts.UpdateScoreAncestry import UpdateScoreAncestry
from release.scripts.UpdateScoreEvaluated import UpdateScoreEvaluated
from release.scripts.UpdateReleasedCohorts import UpdateReleasedCohorts
from release.scripts.UpdateEFO import UpdateEFO


def run():
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

    # Update the trait information and ontology
    update_efo()


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


def report_header(msg):
    print('\n# '+msg)
