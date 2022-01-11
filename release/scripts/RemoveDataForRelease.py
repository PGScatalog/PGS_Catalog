from catalog.models import *
from datetime import datetime



class NonReleasedDataToRemove:


    def __init__(self):
        self.scores2del = {}
        self.perfs2del = {}
        self.pss2del = {}
        self.traits2del = {}
        self.non_asso_traits2del = {}
        self.publications = []


    def fetch_non_released_publications(self):
        self.publications = Publication.objects.filter(date_released__isnull=True).exclude(curation_status='C')


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
            e_pub = EmbargoedPublication.objects.create(id=id, firstauthor=firstauthor)
            title = publication.title
            if title and title != '':
                e_pub.title = title
                e_pub.save()
            count_e_publications += 1
            # Embargoed Score
            scores = publication.publication_score.all()
            if scores.count() > 0:
                for score in scores:
                    score_id = score.id
                    score_name = score.name
                    score_trait = score.trait_reported
                    EmbargoedScore.objects.create(
                        id=score_id,
                        name=score_name,
                        trait_reported = score_trait,
                        firstauthor=firstauthor
                    )
                    count_e_scores += 1
        print(" - Embargoed Publications: "+str(count_e_publications))
        print(" - Embargoed Scores: "+str(count_e_scores))


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


    def delete_entries(self):
        print('\n >> Start data deletion')
        # Performances to delete
        if len(self.perfs2del.keys()) > 0:
            for performance in self.perfs2del.values():
                performance.delete()
            print("  - Performance(s) deleted")
        # Samplesets to delete
        if len(self.pss2del.keys()) > 0:
            for sample_set in self.pss2del.values():
                sample_set.delete()
            print("  - Sample Set(s) deleted")
        # Scores to delete
        if len(self.scores2del.keys()) > 0:
            for score in self.scores2del.values():
                score.delete()
            print("  - Score(s) deleted")
        # Publications to delete
        if len(self.publications) > 0:
            for publication in self.publications:
                EvaluatedScore.objects.filter(publication=publication).delete()
                publication.delete()
            print("  - Publication(s) deleted")
        # Traits to delete
        if len(self.traits2del.keys()) > 0:
            for trait in self.traits2del.values():
                trait.delete()
            print("  - Trait(s) deleted")
        print('\n >> Extra data deletion')
        # Fetch EFOTrait not associated with a Score
        self.get_efotraits_to_delete()
        if len(self.non_asso_traits2del.keys()) > 0:
            for trait in self.non_asso_traits2del.values():
                trait.delete()
            print("  - Non associated Trait(s) deleted")



    def get_performances_list_to_delete(self, publication):
        return Performance.objects.filter(date_released__isnull=True, publication=publication)


    def get_scores_list_to_delete(self, publication):
        return Score.objects.filter(date_released__isnull=True, publication=publication)


    def get_efotraits_to_delete(self):
        for efo_trait in EFOTrait.objects.all().prefetch_related('associated_scores'):
            if len(efo_trait.associated_scores.all()) == 0:
                self.non_asso_traits2del[efo_trait.id] = efo_trait
        print("  - Number of non-associated EFOTraits to remove: "+str(len(self.non_asso_traits2del.keys())))
        if len(self.non_asso_traits2del.keys()) > 0:
            for trait_id in sorted(self.non_asso_traits2del.keys()):
                efo_trait = self.non_asso_traits2del[trait_id]
                print("\t> "+efo_trait.id+" ("+efo_trait.label+")")


    def remove_non_released_data(self):

        # Release
        lastest_release = Release.objects.latest('date')
        release_date = datetime.today().strftime('%Y-%m-%d')
        print(" - Latest release: "+str(lastest_release.date))
        print(" - New release: "+str(release_date))

        # Update the list of embargoed scores and publications
        self.update_embargoed_data()

        # Entries to delete
        self.list_entries_to_delete()

        print(" - Number of non curated Publications: "+str(self.publications.count()))

        print(" - Number of Scores to remove: "+str(len(self.scores2del.keys())))
        if len(self.scores2del.keys()) > 0:
            print('\t> '+'\n\t> '.join(sorted(self.scores2del.keys())))

        print("\n - Number of EFOTraits to remove: "+str(len(self.traits2del.keys())))
        if len(self.traits2del.keys()) > 0:
            print('\t> '+'\n\t> '.join(sorted(self.traits2del.keys())))

        print("\n - Number of Performances to remove : "+str(len(self.perfs2del.keys())))
        if len(self.perfs2del.keys()) > 0:
            print('\t> '+', '.join(sorted(self.perfs2del.keys())))

        print("\n - Number of Sample Sets to remove: "+str(len(self.pss2del.keys())))
        if len(self.pss2del.keys()) > 0:
            print('\t> '+', '.join(sorted(self.pss2del.keys())))

        # Delete selected entries
        self.delete_entries()


################################################################################

def run():

    # Create object to remove the non released data
    data2remove = NonReleasedDataToRemove()
    data2remove.remove_non_released_data()
