from catalog.models import *
from datetime import datetime



class NonReleasedDataToRemove:


    def __init__(self):
        self.scores2del = {}
        self.perfs2del = {}
        self.pss2del = {}
        self.publications = []


    def fetch_non_released_publications(self):
        self.publications = Publication.objects.filter(date_released__isnull=True).exclude(curation_status="C")


    def list_entries_to_delete(self):
        if (len(self.publications) == 0):
            self.fetch_non_released_publications()

        #### Removing non curated data ####
        for publication in self.publications:
            # Performances + Sample sets
            performances_list = self.get_performances_list_to_delete(publication)
            for performance in performances_list:
                # Performance
                self.perfs2del[performance.id] = performance
                # Sampleset
                sample_set = performance.sampleset
                self.pss2del[sample_set.id] = sample_set

            # Scores
            scores_list = self.get_scores_list_to_delete(publication)
            for score in scores_list:
                self.scores2del[score.id] = score


    def delete_entries(self):
        # Performances to delete
        for performance in self.perfs2del.values():
            performance.delete()
        # Samplesets to delete
        for sample_set in self.pss2del.values():
            sample_set.delete()
        # Scores
        for score in self.scores2del.values():
            score.delete()


    def get_performances_list_to_delete(self, publication):
        return Performance.objects.filter(date_released__isnull=True, publication=publication)


    def get_scores_list_to_delete(self, publication):
        return Score.objects.filter(date_released__isnull=True, publication=publication)


def run():
    # Release
    lastest_release = Release.objects.latest('date')
    release_date = datetime.today().strftime('%Y-%m-%d')

    # Create object to remove the non released data
    data2remove = NonReleasedDataToRemove()

    # Entries to delete
    data2remove.list_entries_to_delete()

    # Delete selected entries
    #data2remove.delete_entries()

    print("Latest release: "+str(lastest_release.date))
    print("New release: "+str(release_date))
    print("Number of non curated Publications: "+str(data2remove.publications.count()))
    print("Number of Scores to remove: "+str(len(data2remove.scores2del.keys())))
    print( ' - '+'\n - '.join(data2remove.scores2del.keys()))
    print("Number of Performances to remove : "+str(len(data2remove.perfs2del.keys())))
    print( ' - '+'\n - '.join(data2remove.perfs2del.keys()))
    print("Number of Sample Sets to remove: "+str(len(data2remove.pss2del.keys())))
    print( ' - '+'\n - '.join(data2remove.pss2del.keys()))
