from catalog.models import *
from datetime import datetime



class NonReleasedDataToRemove:


    def __init__(self):
        self.scores2del = {}
        self.perfs2del = {}
        self.pss2del = {}
        self.traits2del = {}
        self.publications = []


    def fetch_non_released_publications(self):
        self.publications = Publication.objects.filter(date_released__isnull=True).exclude(curation_status="C")


    def update_embargoed_data(self):
        """ Delete previously embargoed data and replace them with new embargoed data """
        # Delete previously embargoed data
        EmbargoedScore.objects.all().delete()
        EmbargoedPublication.objects.all().delete()

        # Add new embargoed data
        count_e_publications = 0
        count_e_scores = 0
        publications = Publication.objects.filter(curation_status='E').exclude(date_released__isnull=False)
        for publication in publications:
            # Embargoed Publication
            id = publication.id
            firstauthor = publication.firstauthor
            EmbargoedPublication.objects.create(id=id, firstauthor=firstauthor)
            count_e_publications += 1
            # Embargoed Score
            scores = publication.publication_score.all()
            if scores.count() > 0:
                for score in scores:
                    score_id = score.id
                    EmbargoedScore.objects.create(id=score_id, firstauthor=firstauthor)
                    count_e_scores += 1
        print("Embargoed Publications: "+str(count_e_publications))
        print("Embargoed Scores: "+str(count_e_scores))


    def list_entries_to_delete(self):

        #### Fetch non released publications
        self.fetch_non_released_publications()

        #### Fetch non curated data ####
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

        #### Fetch EFOTrait not associated with a Score
        self.get_efotraits_to_delete()


    def delete_entries(self):
        # Performances to delete
        if len(self.perfs2del.keys()) > 0:
            for performance in self.perfs2del.values():
                performance.delete()
            print("> Performance(s) deleted")
        # Samplesets to delete
        if len(self.pss2del.keys()) > 0:
            for sample_set in self.pss2del.values():
                sample_set.delete()
            print("> Sample Set(s) deleted")
        # Scores to delete
        if len(self.scores2del.keys()) > 0:
            for score in self.scores2del.values():
                score.delete()
            print("> Score(s) deleted")
        # Traits to delete
        if len(self.traits2del.keys()) > 0:
            for trait in self.traits2del.values():
                trait.delete()
            print("> Trait(s) deleted")
        # Publications to delete
        if len(self.publications) > 0:
            for publication in self.publications:
                publication.delete()
            print("> Publication(s) deleted")


    def get_performances_list_to_delete(self, publication):
        return Performance.objects.filter(date_released__isnull=True, publication=publication)

    def get_scores_list_to_delete(self, publication):
        return Score.objects.filter(date_released__isnull=True, publication=publication)

    def get_efotraits_to_delete(self):
        for efo_trait in EFOTrait.objects.all().prefetch_related('associated_scores'):
            if len(efo_trait.associated_scores.all()) == 0:
                print("Non linked trait: "+efo_trait.id+" ("+efo_trait.label+")")
                self.traits2del[efo_trait.id] = efo_trait



class RemoveHistory:

    def delete_history(self):
        # Performance history to delete
        Performance.history.all().delete()
        # Publication history to delete
        Publication.history.all().delete()
        # Scores history to delete
        Score.history.all().delete()()


def run():
    # Release
    lastest_release = Release.objects.latest('date')
    release_date = datetime.today().strftime('%Y-%m-%d')

    # Create object to remove the non released data
    data2remove = NonReleasedDataToRemove()

    # Update the list of embargoed scores and publications
    data2remove.update_embargoed_data()

    # Entries to delete
    data2remove.list_entries_to_delete()


    # Delete history records for the production database
    #history2remove = RemoveHistory()
    #history2remove.delete_history()

    print("Latest release: "+str(lastest_release.date))
    print("New release: "+str(release_date))
    print("Number of non curated Publications: "+str(data2remove.publications.count()))

    print("Number of Scores to remove: "+str(len(data2remove.scores2del.keys())))
    if len(data2remove.scores2del.keys()) > 0:
        print( ' - '+'\n - '.join(data2remove.scores2del.keys()))

    print("Number of Performances to remove : "+str(len(data2remove.perfs2del.keys())))
    if len(data2remove.perfs2del.keys()) > 0:
        print( ' - '+'\n - '.join(data2remove.perfs2del.keys()))

    print("Number of Sample Sets to remove: "+str(len(data2remove.pss2del.keys())))
    if len(data2remove.pss2del.keys()) > 0:
        print( ' - '+'\n - '.join(data2remove.pss2del.keys()))

    print("Number of EFOTraits to remove: "+str(len(data2remove.traits2del.keys())))
    if len(data2remove.traits2del.keys()) > 0:
        print( ' - '+'\n - '.join(data2remove.traits2del.keys()))

    # Delete selected entries
    data2remove.delete_entries()
