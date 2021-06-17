from catalog.models import Cohort, Score
from pgs_web import constants

class UpdateReleasedCohorts:

    def __init__(self):
        self.cohorts = Cohort.objects.all()
        self.score_id_list = Score.objects.values_list('id', flat=True).filter(date_released__isnull=False)

    def update_cohorts(self):
        count_all = 0
        count_released = 0
        count_not_released = 0
        for cohort in self.cohorts:
            c_associations = cohort.associated_pgs_ids
            released = False
            for score in c_associations['development']:
                if score in self.score_id_list:
                    released = True
                    break

            if released == False:
                for score in c_associations['evaluation']:
                    if score in self.score_id_list:
                        released = True
                        break
            count_all += 1
            if released == False:
                count_not_released += 1
            else:
                count_released += 1
            cohort.released = released
            cohort.save()

        db_count_released = Cohort.objects.filter(released=True).count()
        db_count_not_released = Cohort.objects.filter(released=False).count()
        print(f'> Cohorts - all: {count_all}')
        print(f'> Cohorts - released: {count_released} | DB: {db_count_released}')
        print(f'> Cohorts - not released: {count_not_released} | DB: {db_count_not_released}')


def run():
    """ Update the Cohort entries, setting the flag 'released'."""

    released_cohorts = UpdateReleasedCohorts()
    released_cohorts.update_cohorts()
