from catalog.models import Cohort, Score
from pgs_web import constants

class UpdateReleasedCohorts:
    cohorts_released = []
    cohorts_not_released = []

    def __init__(self):
        self.cohorts = Cohort.objects.only('id','released').all()
        self.score_id_list = Score.objects.values_list('id', flat=True).filter(date_released__isnull=False)

    def update_cohorts(self):
        count_all = 0
        for cohort in self.cohorts:
            c_associations = cohort.associated_pgs_ids
            associations_list = set( c_associations['development'] + c_associations['evaluation'] )

            released = False
            if (set(self.score_id_list).intersection(associations_list)):
                released = True

            if released == False:
                self.cohorts_not_released.append(cohort.id)
            else:
                self.cohorts_released.append(cohort.id)

        # Update DB with new values
        Cohort.objects.filter(id__in=self.cohorts_released).update(released=True)
        Cohort.objects.filter(id__in=self.cohorts_not_released).update(released=False)

        db_count_released = Cohort.objects.filter(released=True).count()
        db_count_not_released = Cohort.objects.filter(released=False).count()
        print(f' > Cohorts - all: {len(self.cohorts)}')
        print(f' > Cohorts - released: {len(self.cohorts_released)} | DB: {db_count_released}')
        print(f' > Cohorts - not released: {len(self.cohorts_not_released)} | DB: {db_count_not_released}')


def run():
    """ Update the Cohort entries, setting the flag 'released'."""
    released_cohorts = UpdateReleasedCohorts()
    released_cohorts.update_cohorts()
